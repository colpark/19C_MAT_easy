"""Shadow D for PanelBench v6 B1, written from V5_SPEC.md sections 1.2, 3.1 and Appendix A only.

Run: ~/v5env/bin/python shadow_d_b1.py [--workers 16] [--only WORLD] [--si-mode same|separate]
"""
import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import sys
import json
import time
import argparse
import multiprocessing as mp

import numpy as np
from scipy.optimize import nnls, minimize
from scipy.stats import qmc

HERE = os.path.dirname(os.path.abspath(__file__))
LAM = 1.5406
ETA = 0.5
R_MM = 240.0
DEG = 180.0 / np.pi
UVW = {"standard": (0.012, -0.002, 0.0085),
       "high_resolution": (0.0011, -0.00018, 0.00077),
       "neutron": (0.06, -0.03, 0.09)}
FLUX = {"standard": 1.0, "high_resolution": 0.25, "neutron": 1.0}
S_BOX = (-0.2, 0.2)
Z_BOX = (-0.01, 0.01)
L_FAC = (0.7, 1.3)
SI_A = 5.43102

# ---------------------------------------------------------------------------------------------
# Si internal standard peak table. peak_tables.json has no "Si standard" entry, so it is computed
# here (see si_table()): diamond Si, Fd-3m, a = 5.43102, Cu Ka1, |F|^2 x Lorentz-polarisation x
# multiplicity, one entry per family (positions only depend on d), atomic form factor in the
# pymatgen parameterisation f(s) = Z - 41.78214 s^2 sum a_i exp(-b_i s^2), s = sin(theta)/lambda.
# Its absolute normalisation per unit weight is then set by SI_NORM (see notes in the report).
SI_FF = [[2.129, 57.775], [2.533, 16.476], [0.835, 2.88], [0.322, 0.386]]  # pymatgen atomic_scattering_params, Si
SI_Z = 14
# Normalisation inferred from peak_tables.json itself: for every cubic phase whose structure is unambiguous
# (LiRu3 Pm-3m, four Fm-3m Heuslers) the table intensity of a family representative equals
# |F|^2 x LP x multiplicity x N_A*1e-24 / (V_cell[A^3] x M_cell[g/mol]) to 1e-4, i.e. 1/(rho V^2).
SI_NORM_DEFAULT = 0.602214076 / (SI_A ** 3 * 8 * 28.0855)
SI_NORM = SI_NORM_DEFAULT


def si_table(radiation, norm):
    """hkl families of diamond Si; returns (d, intensity) arrays, intensity per unit weight."""
    a = SI_A
    basis = np.array([[0, 0, 0], [0.5, 0.5, 0], [0.5, 0, 0.5], [0, 0.5, 0.5],
                      [0.25, 0.25, 0.25], [0.75, 0.75, 0.25], [0.75, 0.25, 0.75], [0.25, 0.75, 0.75]])
    fam = {}
    rng = range(-12, 13)
    for h in rng:
        for k in rng:
            for l in rng:
                if h == k == l == 0:
                    continue
                d = a / np.sqrt(h * h + k * k + l * l)
                if LAM / (2 * d) >= 1:
                    continue
                F = np.exp(2j * np.pi * (basis @ np.array([h, k, l]))).sum()
                if abs(F) < 1e-6:
                    continue
                key = h * h + k * k + l * l
                fam.setdefault(key, []).append(abs(F) ** 2)
    ds, Is = [], []
    for key, f2 in sorted(fam.items()):
        d = a / np.sqrt(key)
        st = LAM / (2 * d)
        th = np.arcsin(st)
        s = st / LAM
        if radiation == "xray":
            f = SI_Z - 41.78214 * s * s * sum(ai * np.exp(-bi * s * s) for ai, bi in SI_FF)
            lp = (1 + np.cos(2 * th) ** 2) / (np.sin(th) ** 2 * np.cos(th))
        else:
            raise ValueError("the Si standard is never in a neutron measurement")
        I = sum(f2) * f * f * lp  # sum over all family members = |F|^2 * multiplicity
        ds.append(d)
        Is.append(I)
    Is = np.array(Is)
    return np.array(ds), Is * norm


# ---------------------------------------------------------------------------------------------
class Phases:
    def __init__(self, path):
        pt = json.load(open(path))
        self.T = pt["tables"]
        self.L = pt["lattice"]
        self.cache = {}

    def peaks(self, phase, radiation):
        """returns (two_theta_unshifted, intensity per unit weight) for valid hkl."""
        key = (phase, radiation)
        if key in self.cache:
            return self.cache[key]
        if phase == "Si standard":
            d, I = si_table(radiation, SI_NORM)
        else:
            tab = self.T[f"{phase}|{radiation}|"]
            hkl = np.array(tab["hkl"], dtype=float)
            I = np.array(tab["intensity_per_weight"], dtype=float)
            lat = self.L[phase]
            M = np.array(lat["reference_matrix"], dtype=float)  # rows = lattice vectors, lattice_scale = 1
            B = np.linalg.inv(M).T                                # rows = reciprocal vectors (no 2 pi)
            g = hkl @ B
            d = 1.0 / np.linalg.norm(g, axis=1)
        x = LAM / (2 * d)
        ok = x < 1
        tt = 2 * np.degrees(np.arcsin(x[ok]))
        out = (tt, I[ok])
        self.cache[key] = out
        return out


def group_peaks(phases, group, radiation, si):
    """concatenate peaks of one amplitude group (list of [phase, params, weight])."""
    tts, Is = [], []
    for ph, params, w in group:
        if params:
            raise NotImplementedError("phase parameters not used in B1: %r" % (params,))
        tt, I = phases.peaks(ph, radiation)
        ww = w * (0.8 if si else 1.0)
        tts.append(tt)
        Is.append(I * ww)
    return np.concatenate(tts), np.concatenate(Is)


def profile_sum(x, tt0, I, s, z, L, optics, xray):
    """sig(x) for peaks at unshifted 2theta tt0 with intensities I."""
    if xray:
        th0 = np.radians(tt0 / 2)
        tt = tt0 + z - DEG * 2 * s * np.cos(th0) / R_MM
    else:
        tt = tt0
    th = np.radians(tt / 2)
    U, V, W = UVW[optics]
    tn = np.tan(th)
    hi2 = np.maximum(U * tn * tn + V * tn + W, 1e-8)
    hs = DEG * 0.9 * 0.15406 / (L * np.cos(th))
    H = np.sqrt(hi2 + hs * hs)
    start, step, n = x[0], x[1] - x[0], len(x)
    # window |x - tt| <= 25 H on the grid
    lo = np.ceil((tt - 25 * H - start) / step - 1e-9).astype(np.int64)
    hi = np.floor((tt + 25 * H - start) / step + 1e-9).astype(np.int64)
    lo = np.clip(lo, 0, n)
    hi = np.clip(hi, -1, n - 1)
    cnt = hi - lo + 1
    keep = cnt > 0
    out = np.zeros(n)
    if not keep.any():
        return out
    lo, cnt, tt, H, I = lo[keep], cnt[keep], tt[keep], H[keep], I[keep]
    tot = int(cnt.sum())
    pk = np.repeat(np.arange(len(cnt)), cnt)
    offs = np.arange(tot) - np.repeat(np.cumsum(cnt) - cnt, cnt)
    idx = lo[pk] + offs
    dlt = x[idx] - tt[pk]
    Hp = H[pk]
    # exact inclusion test |Delta| <= 25 H per point
    m = np.abs(dlt) <= 25 * Hp
    idx, dlt, Hp, Ip = idx[m], dlt[m], Hp[m], I[pk][m]
    r2 = dlt * dlt / (Hp * Hp)
    val = Ip * (ETA * 2 / (np.pi * Hp) / (1 + 4 * r2)
                + (1 - ETA) * (2 / Hp) * np.sqrt(np.log(2) / np.pi) * np.exp(-4 * np.log(2) * r2))
    out += np.bincount(idx, weights=val, minlength=n)
    return out


class Problem:
    def __init__(self, phases, world, plan, si_mode="same"):
        self.world = world
        self.meas = []
        for m in plan:
            x = m["start"] + m["step"] * np.arange(m["n"])
            xray = m["radiation"] == "xray"
            si = bool(m["si_standard"]) and xray
            self.meas.append(dict(x=x, xray=xray, si=si, t=m["t"], optics=m["optics"],
                                  f=FLUX[m["optics"]] if xray else 1.0, rad=m["radiation"]))
        self.has_x = any(mm["xray"] for mm in self.meas)
        self.phases = phases
        self.si_mode = si_mode
        self.Ltrue = world["L_nm"]
        # truth
        mus = []
        for mm in self.meas:
            sig = np.zeros(len(mm["x"]))
            for gtt, gI in self._groups(world["truth_groups"], mm, include_si=True):
                sig += profile_sum(mm["x"], gtt, gI, world["disp_mm"], world["zero_deg"], world["L_nm"],
                                   mm["optics"], mm["xray"])
            u = (mm["x"] - 80) / 70
            if mm["xray"]:
                mu = mm["t"] * mm["f"] * (world["A_xray"] * sig + world["b0"] + world["b1"] * u)
            else:
                mu = mm["t"] * (world["A_neutron"] * sig + world["bn0"] + world["bn1"] * u)
            mus.append(mu)
        self.muT = np.concatenate(mus)
        if np.any(self.muT <= 0):
            raise ValueError("non-positive truth counts")
        self.sw = 1 / np.sqrt(self.muT)
        self.y = self.muT * self.sw
        self.branches = []
        for br in world["other_side"]:
            assert br["lo"] == [] and br["hi"] == []
            self.branches.append(br["groups_at_lo"])

    def _groups(self, groups, mm, include_si):
        """list of (tt, I) per amplitude group for measurement mm."""
        out = []
        for g in groups:
            out.append(group_peaks(self.phases, g, mm["rad"], mm["si"]))
        if mm["si"]:
            stt, sI = self.phases.peaks("Si standard", "xray")
            sI = sI * 0.2
            if self.si_mode == "same" or include_si:
                # Si folded into the first group (fixed ratio) -- for the truth only the sum matters
                out[0] = (np.concatenate([out[0][0], stt]), np.concatenate([out[0][1], sI]))
            else:
                out.append((stt, sI))
        return out

    def design(self, groups, s, z, L):
        ng = len(groups) + (1 if self.si_mode == "separate" else 0)
        insts = ["xray", "neutron"]
        cols_per = ng + 3
        X = np.zeros((len(self.muT), 2 * cols_per))
        r0 = 0
        for mm in self.meas:
            n = len(mm["x"])
            base = (0 if mm["xray"] else 1) * cols_per
            tf = mm["t"] * mm["f"]
            gl = self._groups(groups, mm, include_si=False)
            for j, (gtt, gI) in enumerate(gl):
                X[r0:r0 + n, base + j] = tf * profile_sum(mm["x"], gtt, gI, s, z, L, mm["optics"], mm["xray"])
            u = (mm["x"] - 80) / 70
            X[r0:r0 + n, base + ng] = tf
            X[r0:r0 + n, base + ng + 1] = tf * u
            X[r0:r0 + n, base + ng + 2] = -tf * u
            r0 += n
        used = np.abs(X).sum(axis=0) > 0
        return X[:, used]

    def chi2(self, groups, s, z, L):
        X = self.design(groups, s, z, L) * self.sw[:, None]
        beta, rn = nnls(X, self.y, maxiter=2000)
        r = self.y - X @ beta
        return float(r @ r)

    # ---- minimisation over (s, z, L) in the unit cube ----
    def box(self):
        if self.has_x:
            lo = np.array([S_BOX[0], Z_BOX[0], L_FAC[0] * self.Ltrue])
            hi = np.array([S_BOX[1], Z_BOX[1], L_FAC[1] * self.Ltrue])
        else:
            lo = np.array([L_FAC[0] * self.Ltrue])
            hi = np.array([L_FAC[1] * self.Ltrue])
        return lo, hi

    def f_unit(self, groups, q):
        lo, hi = self.box()
        p = lo + np.clip(q, 0, 1) * (hi - lo)
        if self.has_x:
            return self.chi2(groups, p[0], p[1], p[2])
        return self.chi2(groups, 0.0, 0.0, p[0])

    def minimise_branch(self, groups, nsobol=256, nrefine=8, extra=False):
        lo, hi = self.box()
        dim = len(lo)
        f = lambda q: self.f_unit(groups, q)
        cands = [np.full(dim, 0.5)]
        sob = qmc.Sobol(dim, scramble=True, seed=12345).random(nsobol)
        cands += list(sob)
        tounit = lambda p: (np.asarray(p, float) - lo) / (hi - lo)
        if self.has_x:
            for s in [-0.15, -0.05, 0.05, 0.15, self.world["disp_mm"]]:
                cands.append(tounit([s, 0.0, self.Ltrue]))
            if extra:
                for s in np.linspace(-0.2, 0.2, 21):
                    for z in [-0.01, 0, 0.01]:
                        for L in [0.7, 1.0, 1.3]:
                            cands.append(tounit([s, z, L * self.Ltrue]))
        else:
            cands.append(tounit([self.Ltrue]))
            cands += [np.array([v]) for v in np.linspace(0, 1, 41)]
        vals = np.array([f(c) for c in cands])
        order = np.argsort(vals)
        chosen = []
        for i in order:
            if all(np.linalg.norm(cands[i] - cands[j]) > 0.05 for j in chosen):
                chosen.append(i)
            if len(chosen) >= nrefine:
                break
        best_v, best_q = vals[order[0]], cands[order[0]].copy()
        bnds = [(0.0, 1.0)] * dim
        for i in chosen:
            r = minimize(f, cands[i], method="L-BFGS-B", bounds=bnds,
                         options=dict(eps=1e-5, maxiter=500))
            if r.fun < best_v:
                best_v, best_q = float(r.fun), np.clip(r.x, 0, 1)
        # polish: alternate Powell and L-BFGS-B
        for _ in range(20):
            prev = best_v
            r = minimize(f, best_q, method="Powell", bounds=bnds, options=dict(xtol=1e-6, ftol=1e-10, maxiter=4000))
            if r.fun < best_v:
                best_v, best_q = float(r.fun), np.clip(r.x, 0, 1)
            r = minimize(f, best_q, method="L-BFGS-B", bounds=bnds, options=dict(eps=1e-5, maxiter=500))
            if r.fun < best_v:
                best_v, best_q = float(r.fun), np.clip(r.x, 0, 1)
            if prev - best_v <= 1e-6 * max(abs(prev), 1e-300):
                break
        return best_v, lo + best_q * (hi - lo)

    def D(self, extra=False):
        best = (np.inf, None, None)
        for bi, g in enumerate(self.branches):
            v, p = self.minimise_branch(g, extra=extra)
            if v < best[0]:
                best = (v, p, bi)
        return best


# ---------------------------------------------------------------------------------------------
PH = None
WORLDS = None
ARGS = None


def init(si_norm, si_mode):
    global PH, WORLDS, SI_NORM, ARGS
    SI_NORM = si_norm
    PH = Phases(os.path.join(HERE, "peak_tables.json"))
    WORLDS = json.load(open(os.path.join(HERE, "WORLDS.json")))["worlds"]
    ARGS = dict(si_mode=si_mode)


def agree(mine, ref):
    if ref < 5:
        return abs(mine - ref) <= 0.05 or abs(mine - ref) <= 0.01 * abs(ref)
    return abs(mine - ref) <= 0.01 * abs(ref)


def job(task):
    wid, pi, plan, ref, extra = task
    t0 = time.time()
    pr = Problem(PH, WORLDS[wid], plan, si_mode=ARGS["si_mode"])
    v, p, bi = pr.D(extra=extra)
    if not agree(v, ref) and v > ref and not extra:
        v2, p2, bi2 = pr.D(extra=True)
        if v2 < v:
            v, p, bi = v2, p2, bi2
        extra = True
    return dict(world=wid, plan_index=pi, D=v, D_ref=ref, agree=bool(agree(v, ref)),
                argmin=[float(a) for a in p], branch=int(bi), extra_search=bool(extra),
                si=any(m["si_standard"] for m in plan), seconds=round(time.time() - t0, 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--only", default=None)
    ap.add_argument("--si-only", action="store_true")
    ap.add_argument("--no-si", action="store_true")
    ap.add_argument("--si-norm", type=float, default=SI_NORM_DEFAULT)
    ap.add_argument("--si-mode", default="same")
    ap.add_argument("--out", default=os.path.join(HERE, "shadow_results.json"))
    a = ap.parse_args()
    plans = json.load(open(os.path.join(HERE, "shadow_plans.json")))["worlds"]
    tasks = []
    for wid in sorted(plans):
        if a.only and wid not in a.only.split(","):
            continue
        for pi, pl in enumerate(plans[wid]):
            si = any(m["si_standard"] for m in pl["plan"])
            if (a.si_only and not si) or (a.no_si and si):
                continue
            tasks.append((wid, pi, pl["plan"], pl["D"], True))  # always the extended start grid
    with mp.Pool(min(16, a.workers), initializer=init, initargs=(a.si_norm, a.si_mode)) as pool:
        res = []
        for r in pool.imap_unordered(job, tasks):
            res.append(r)
            print(f"{r['world']} {r['plan_index']} D={r['D']:.6g} ref={r['D_ref']:.6g} agree={r['agree']} "
                  f"si={r['si']} {r['seconds']}s", flush=True)
    res.sort(key=lambda r: (r["world"], r["plan_index"]))
    out = dict(n_plans=len(res), n_agree=sum(r["agree"] for r in res),
               tolerance="1% relative, or 0.05 absolute where reference D < 5",
               si_norm=a.si_norm, si_mode=a.si_mode, results=res)
    json.dump(out, open(a.out, "w"), indent=1)
    print("plans", out["n_plans"], "agree", out["n_agree"])


if __name__ == "__main__":
    main()
