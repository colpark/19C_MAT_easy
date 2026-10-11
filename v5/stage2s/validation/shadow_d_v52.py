"""Shadow implementation of the separation D (V5_SPEC section 3.1, Appendix A, E.3/E.6, F.4/F.7) for v5.2 stages 2s and 3.

Written from the specification only (no reference code read). numpy + scipy.
Run: OPENBLAS_NUM_THREADS=1 ~/v5env/bin/python v5/stage2s/validation/shadow_d_v52.py [--workers 16] [--nsobol 256]
"""
import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import argparse
import json
import sys
import time
from multiprocessing import Pool

import numpy as np
from scipy.optimize import minimize, nnls
from scipy.stats import qmc

HERE = os.path.dirname(os.path.abspath(__file__))
V5 = os.path.dirname(os.path.dirname(HERE))
LAM = 1.5406
R_MM = 240.0
ETA = 0.5
UVW = {"standard": (0.012, -0.002, 0.0085),
       "high_resolution": (0.0011, -0.00018, 0.00077),
       "neutron": (0.06, -0.03, 0.09)}
FLUX = {"standard": 1.0, "high_resolution": 0.25, "neutron": 1.0}
S_BOX = (-0.2, 0.2)
Z_BOX = (-0.01, 0.01)
L_FRAC = (0.7, 1.3)

# ----------------------------------------------------------------------------------------------------------------- tables
_TABLES = {}


def load_tables(stage):
    if stage not in _TABLES:
        p = json.load(open(os.path.join(V5, stage, "peak_tables.json")))
        _TABLES[stage] = p
    return _TABLES[stage]


def lattice_matrix(stage, phase, params):
    rule = load_tables(stage)["lattice"][phase]
    ls = float(params.get("lattice_scale", 1.0))
    if isinstance(rule, dict):
        M = np.array(rule["reference_matrix"], float)
        if rule.get("scaled_by") == "lattice_scale":
            M = M * ls
        return M
    if phase == "Si1-xGex":
        x = float(params["x"])
        a = ((1 - x) * 5.43114 + x * 5.6579) * ls
        return np.eye(3) * a
    if phase == "Mo1-xWx":
        x = float(params["x"])
        a = ((1 - x) * 3.1470 + x * 3.1652) * ls
        return np.eye(3) * a
    if phase == "BaTiO3 cubic":
        return np.eye(3) * float(params["a_pc"])
    if phase == "BaTiO3 tetragonal":
        apc = float(params["a_pc"]); ca = float(params["c_over_a"])
        a = apc * ca ** (-1.0 / 3.0); c = apc * ca ** (2.0 / 3.0)
        return np.diag([a, a, c])
    raise KeyError(phase)


def table(stage, phase, rad, key):
    return load_tables(stage)["tables"]["%s|%s|%s" % (phase, rad, key)]


def phase_peaks(stage, phase, params, rad):
    """Unshifted 2theta (deg) and intensity per unit weight."""
    if "S" in params:
        t0 = table(stage, phase, rad, "S=0.0"); t1 = table(stage, phase, rad, "S=1.0")
        hkl0 = [tuple(h) for h in t0["hkl"]]; hkl1 = [tuple(h) for h in t1["hkl"]]
        S = float(params["S"])
        d0 = dict(zip(hkl0, t0["intensity_per_weight"])); d1 = dict(zip(hkl1, t1["intensity_per_weight"]))
        keys = list(dict.fromkeys(hkl0 + hkl1))
        hkl = np.array(keys, float)
        I0 = np.array([d0.get(k, 0.0) for k in keys]); I1 = np.array([d1.get(k, 0.0) for k in keys])
        I = I0 + S * S * (I1 - I0)
    elif "x" in params:
        x = round(float(params["x"]), 2)
        t = table(stage, phase, rad, "x=%s" % repr(float(x)))
        hkl = np.array(t["hkl"], float); I = np.array(t["intensity_per_weight"], float)
    else:
        t = table(stage, phase, rad, "")
        hkl = np.array(t["hkl"], float); I = np.array(t["intensity_per_weight"], float)
    M = lattice_matrix(stage, phase, params)
    B = np.linalg.inv(M).T  # rows: reciprocal vectors (no 2pi)
    G = hkl @ B
    d = 1.0 / np.linalg.norm(G, axis=1)
    sarg = LAM / (2 * d)
    ok = sarg < 1
    tt = 2 * np.degrees(np.arcsin(sarg[ok]))
    return tt, I[ok]


# ---------------------------------------------------------------------------------------------------------------- forward
def meas_grid(m):
    return m["start"] + np.arange(int(m["n"])) * m["step"]


def profile_sum(x, pos_unshift, inten, m, s, z, L):
    """sum over peaks of a * pseudo-Voigt on grid x for measurement m."""
    if len(inten) == 0:
        return np.zeros_like(x)
    xray = m["radiation"] == "xray"
    th0 = np.radians(pos_unshift / 2)
    if xray:
        pos = pos_unshift + z - np.degrees(2 * s * np.cos(th0) / R_MM)
    else:
        pos = pos_unshift.copy()
    th = np.radians(pos / 2)
    U, V, W = UVW[m["optics"]]
    tn = np.tan(th)
    Hi2 = np.maximum(U * tn * tn + V * tn + W, 1e-8)
    Hs = np.degrees(0.9 * 0.15406 / (L * np.cos(th)))
    H = np.sqrt(Hi2 + Hs * Hs)
    lo, hi = x[0], x[-1]
    keep = (pos + 25 * H >= lo) & (pos - 25 * H <= hi) & (inten != 0)
    if not keep.any():
        return np.zeros_like(x)
    pos = pos[keep]; H = H[keep]; a = inten[keep]
    D = x[None, :] - pos[:, None]
    Hc = H[:, None]
    q = (D / Hc) ** 2
    lor = 2.0 / (np.pi * Hc) / (1 + 4 * q)
    gau = (2.0 / Hc) * np.sqrt(np.log(2) / np.pi) * np.exp(-4 * np.log(2) * q)
    prof = ETA * lor + (1 - ETA) * gau
    prof = np.where(np.abs(D) <= 25 * Hc, prof, 0.0)
    return a @ prof


def group_signal(stage, group, m, x, s, z, L, cache=None):
    """group: list of [phase, params, weight]. Si standard handled here."""
    rad = m["radiation"]
    std = bool(m.get("si_standard")) and rad == "xray"
    pos_all = []; I_all = []
    for phase, params, w in group:
        if w == 0:
            continue
        key = (phase, tuple(sorted((k, float(v)) for k, v in params.items())), rad)
        if cache is not None and key in cache:
            tt, I = cache[key]
        else:
            tt, I = phase_peaks(stage, phase, params, rad)
            if cache is not None:
                cache[key] = (tt, I)
        f = w * (0.8 if std else 1.0)
        pos_all.append(tt); I_all.append(I * f)
    if std:
        key = ("Si standard", (), rad)
        if cache is not None and key in cache:
            tt, I = cache[key]
        else:
            tt, I = phase_peaks(stage, "Si standard", {}, rad)
            if cache is not None:
                cache[key] = (tt, I)
        pos_all.append(tt); I_all.append(I * 0.2)
    if not pos_all:
        return np.zeros_like(x)
    return profile_sum(x, np.concatenate(pos_all), np.concatenate(I_all), m, s, z, L)


def truth_mu(stage, world, plan):
    out = []
    for m in plan:
        x = meas_grid(m)
        t = m["t"]; f = FLUX[m["optics"]]
        if m["radiation"] == "xray":
            sig = sum(group_signal(stage, g, m, x, world["disp_mm"], world["zero_deg"], world["L_nm"]) for g in world["truth_groups"])
            mu = t * f * (world["A_xray"] * sig + world["b0"] + world["b1"] * (x - 80) / 70)
        else:
            sig = sum(group_signal(stage, g, m, x, 0.0, 0.0, world["L_nm"]) for g in world["truth_groups"])
            mu = t * (world["A_neutron"] * sig + world["bn0"] + world["bn1"] * (x - 80) / 70)
        out.append(mu)
    return out


# ---------------------------------------------------------------------------------------------------------------- branches
def branch_groups(branch, u):
    """Linear interpolation of params and weights between groups_at_lo and groups_at_hi."""
    lo = np.array(branch["lo"], float); hi = np.array(branch["hi"], float)
    if lo.size == 0:
        return branch["groups_at_lo"]
    u = np.asarray(u, float)
    frac_all = (u - lo) / (hi - lo)

    def interp(vlo, vhi):
        if vlo == vhi:
            return vlo
        if lo.size == 1:
            return vlo + (vhi - vlo) * frac_all[0]
        for j in range(lo.size):
            if abs(vlo - lo[j]) < 1e-12 and abs(vhi - hi[j]) < 1e-12:
                return u[j]
        # generic: affine in the single dimension whose span matches the change ratio
        for j in range(lo.size):
            return vlo + (vhi - vlo) * frac_all[j]

    groups = []
    for glo, ghi in zip(branch["groups_at_lo"], branch["groups_at_hi"]):
        g = []
        for (ph, plo, wlo), (ph2, phi, whi) in zip(glo, ghi):
            assert ph == ph2
            params = {k: interp(float(plo[k]), float(phi[k])) for k in plo}
            g.append([ph, params, interp(float(wlo), float(whi))])
        groups.append(g)
    return groups


class Problem:
    def __init__(self, stage, world, plan, branch):
        self.stage = stage; self.world = world; self.plan = plan; self.branch = branch
        self.mu = truth_mu(stage, world, plan)
        self.mu_all = np.concatenate(self.mu)
        self.sw = 1.0 / np.sqrt(self.mu_all)
        self.has_x = any(m["radiation"] == "xray" for m in plan)
        self.has_n = any(m["radiation"] == "neutron" for m in plan)
        self.ng = len(branch["groups_at_lo"])
        self.nu = len(branch["lo"])
        Lt = world["L_nm"]
        lo = []; hi = []; names = []
        if self.has_x:
            lo += [S_BOX[0], Z_BOX[0]]; hi += [S_BOX[1], Z_BOX[1]]; names += ["s", "z"]
        lo.append(L_FRAC[0] * Lt); hi.append(L_FRAC[1] * Lt); names.append("L")
        lo += list(branch["lo"]); hi += list(branch["hi"]); names += ["u%d" % i for i in range(self.nu)]
        self.lo = np.array(lo, float); self.hi = np.array(hi, float); self.names = names
        self.dim = len(lo)
        self.grids = [meas_grid(m) for m in plan]
        self.cache = {} if self.nu == 0 else None
        self.nev = 0

    def unpack(self, p):
        v = self.lo + np.clip(p, 0, 1) * (self.hi - self.lo)
        i = 0
        if self.has_x:
            s, z = v[0], v[1]; i = 2
        else:
            s = z = 0.0
        L = v[i]; u = v[i + 1:]
        return s, z, L, u

    def design(self, p):
        s, z, L, u = self.unpack(p)
        groups = branch_groups(self.branch, u)
        insts = (["xray"] if self.has_x else []) + (["neutron"] if self.has_n else [])
        ncol = len(insts) * (self.ng + 3)
        N = len(self.mu_all)
        X = np.zeros((N, ncol))
        r0 = 0
        for m, x in zip(self.plan, self.grids):
            n = len(x)
            ii = insts.index("xray" if m["radiation"] == "xray" else "neutron")
            c0 = ii * (self.ng + 3)
            tf = m["t"] * FLUX[m["optics"]]
            for gi, g in enumerate(groups):
                X[r0:r0 + n, c0 + gi] = tf * group_signal(self.stage, g, m, x, s, z, L, self.cache)
            X[r0:r0 + n, c0 + self.ng] = tf
            X[r0:r0 + n, c0 + self.ng + 1] = tf * (x - 80) / 70
            X[r0:r0 + n, c0 + self.ng + 2] = -tf * (x - 80) / 70
            r0 += n
        return X

    def f(self, p):
        self.nev += 1
        X = self.design(p)
        A = X * self.sw[:, None]
        b = self.mu_all * self.sw
        # column scaling for conditioning
        cs = np.linalg.norm(A, axis=0); cs[cs == 0] = 1.0
        beta, rn = nnls(A / cs, b, maxiter=50 * A.shape[1])
        return float(rn * rn)


def minimise(prob, nsobol=256, nbest=8, seed=12345):
    d = prob.dim
    cands = [np.full(d, 0.5)]
    if d > 0:
        sob = qmc.Sobol(d, scramble=True, seed=seed).random(nsobol)
        cands += list(sob)
    # anchors
    ix = 0
    Lt = prob.world["L_nm"]
    Lc = (Lt - prob.lo[2 if prob.has_x else 0]) / (prob.hi[2 if prob.has_x else 0] - prob.lo[2 if prob.has_x else 0])
    s_vals = [-0.15, -0.05, 0.05, 0.15, prob.world["disp_mm"]] if prob.has_x else [None]
    ugrids = [np.array([0.0, 0.5, 1.0])] * prob.nu
    import itertools
    for sv in s_vals:
        for ucomb in itertools.product(*ugrids) if prob.nu else [()]:
            p = np.full(d, 0.5)
            if prob.has_x:
                p[0] = (sv - S_BOX[0]) / (S_BOX[1] - S_BOX[0]); p[1] = 0.5; p[2] = Lc
            else:
                p[0] = Lc
            for j, uc in enumerate(ucomb):
                p[d - prob.nu + j] = uc
            cands.append(p)
    # faces u = lo, u = hi (on Sobol points, and centre)
    if prob.nu:
        for q in [np.full(d, 0.5)] + list(cands[1:1 + 32]):
            for face in (0.0, 1.0):
                p = q.copy(); p[d - prob.nu:] = face; cands.append(p)
    cands = np.clip(np.array(cands), 0, 1)
    vals = np.array([prob.f(p) for p in cands])
    order = np.argsort(vals)
    chosen = []
    for i in order:
        if all(np.max(np.abs(cands[i] - cands[j])) > 0.05 for j in chosen):
            chosen.append(i)
        if len(chosen) >= nbest:
            break
    best_x = cands[order[0]].copy(); best_v = vals[order[0]]
    bounds = [(0, 1)] * d
    for i in chosen:
        r = minimize(prob.f, cands[i], method="L-BFGS-B", bounds=bounds, options={"eps": 1e-5, "maxiter": 500})
        if r.fun < best_v:
            best_v, best_x = float(r.fun), np.clip(r.x, 0, 1)
    # polish
    for _ in range(20):
        prev = best_v
        r = minimize(prob.f, best_x, method="Powell", bounds=bounds, options={"xtol": 1e-7, "ftol": 1e-10, "maxfev": 4000})
        if r.fun < best_v:
            best_v, best_x = float(r.fun), np.clip(r.x, 0, 1)
        r = minimize(prob.f, best_x, method="L-BFGS-B", bounds=bounds, options={"eps": 1e-6, "maxiter": 500})
        if r.fun < best_v:
            best_v, best_x = float(r.fun), np.clip(r.x, 0, 1)
        if prev - best_v <= 1e-6 * max(abs(prev), 1e-12):
            break
    return best_v, best_x


def compute_D(task):
    stage, wid, idx, plan, nsobol, nbest = task
    W = json.load(open(os.path.join(V5, stage, "WORLDS.json")))["worlds"][wid]
    if not plan:
        return (stage, wid, idx, 0.0, None)
    best = np.inf; info = None
    for bi, br in enumerate(W["other_side"]):
        prob = Problem(stage, W, plan, br)
        v, x = minimise(prob, nsobol=nsobol, nbest=nbest)
        if v < best:
            best = v
            s, z, L, u = prob.unpack(x)
            info = {"branch": br["label"], "s": float(s), "z": float(z), "L": float(L), "u": [float(a) for a in u]}
    return (stage, wid, idx, float(best), info)


def agree(mine, ref):
    if ref < 5:
        return abs(mine - ref) <= 0.05 or abs(mine - ref) <= 0.01 * abs(ref)
    return abs(mine - ref) <= 0.01 * abs(ref)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--nsobol", type=int, default=256)
    ap.add_argument("--nbest", type=int, default=8)
    ap.add_argument("--stages", default="stage2s,stage3")
    ap.add_argument("--only", default="", help="comma list stage:world:idx to recompute (merged into existing results)")
    args = ap.parse_args()
    stages = args.stages.split(",")
    tasks = []; refs = {}
    only = set(args.only.split(",")) if args.only else None
    for st in stages:
        P = json.load(open(os.path.join(V5, st, "validation", "shadow_plans.json")))["worlds"]
        for wid, plans in P.items():
            for i, q in enumerate(plans):
                refs[(st, wid, i)] = q["D"]
                if only is None or "%s:%s:%d" % (st, wid, i) in only:
                    tasks.append((st, wid, i, q["plan"], args.nsobol, args.nbest))
    # heavy tasks first
    tasks.sort(key=lambda t: -sum(m["n"] for m in t[3]))
    t0 = time.time()
    res = {}
    with Pool(min(16, args.workers)) as pool:
        for k, r in enumerate(pool.imap_unordered(compute_D, tasks)):
            res[(r[0], r[1], r[2])] = r
            print("%d/%d %.0fs %s %s %d mine=%.6g ref=%.6g" % (k + 1, len(tasks), time.time() - t0, r[0], r[1], r[2], r[3], refs[(r[0], r[1], r[2])]), flush=True)
    for st in stages:
        path = os.path.join(V5, st, "validation", "shadow_results.json")
        old = {}
        if only is not None and os.path.exists(path):
            for wid, lst in json.load(open(path))["worlds"].items():
                for e in lst:
                    old[(st, wid, e["plan_index"])] = e
        P = json.load(open(os.path.join(V5, st, "validation", "shadow_plans.json")))["worlds"]
        out = {}; n = 0; na = 0
        for wid, plans in P.items():
            lst = []
            for i, q in enumerate(plans):
                key = (st, wid, i)
                if key in res:
                    mine = res[key][3]; info = res[key][4]
                    e = {"plan_index": i, "D_shadow": round(mine, 6), "D_reference": q["D"], "agree": bool(agree(mine, q["D"])),
                         "shadow_lower_than_reference": bool(mine < q["D"] and not agree(mine, q["D"])), "argmin": info}
                elif key in old:
                    e = old[key]
                else:
                    continue
                lst.append(e); n += 1; na += e["agree"]
            out[wid] = lst
        json.dump({"note": "shadow D (fresh implementation from V5_SPEC only, stage2s/validation/shadow_d_v52.py); agreement: 1 % relative, "
                           "or 0.05 absolute where the reference D < 5", "n_plans": n, "n_agree": na, "worlds": out},
                  open(path, "w"), indent=1)
        print(st, "plans", n, "agree", na)


if __name__ == "__main__":
    main()
