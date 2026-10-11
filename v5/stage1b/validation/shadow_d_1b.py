"""Shadow implementation of the stage 1b separation D (V5_SPEC 1.2, 3.1, Appendix A, Appendix C).

Written from the specification and the data files only (WORLDS.json, peak_tables.json, shadow_plans.json).
Self-contained: numpy and scipy only.

Usage: OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 ~/v5env/bin/python shadow_d_1b.py [--workers 12] [--worlds 201,202]
"""
import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import argparse
import itertools
import json
import math
import time
from functools import lru_cache
from multiprocessing import Pool

import numpy as np
from scipy.optimize import minimize, nnls
from scipy.stats import qmc

HERE = os.path.dirname(os.path.abspath(__file__))
STAGE = os.path.dirname(HERE)
LAM = 1.5406
ETA = 0.5
UVW = {"standard": (0.012, -0.002, 0.0085),
       "high_resolution": (0.0011, -0.00018, 0.00077),
       "neutron": (0.06, -0.03, 0.09)}
FLUX = {"standard": 1.0, "high_resolution": 0.25, "neutron": 1.0}
R_MM = 240.0
DEG = 180.0 / math.pi
LN2 = math.log(2.0)

_TABLES = None
_LATT = None
_WORLDS = None


def load():
    global _TABLES, _LATT, _WORLDS
    if _TABLES is None:
        pt = json.load(open(os.path.join(STAGE, "peak_tables.json")))
        _TABLES = pt["tables"]
        _LATT = pt["lattice"]
        _WORLDS = json.load(open(os.path.join(STAGE, "WORLDS.json")))["worlds"]


# ---------------------------------------------------------------- lattices and peak lists
def _matrix(name, params):
    """Real-space lattice matrix (rows = lattice vectors) for a phase with the given params."""
    lr = _LATT[name]
    ls = float(params.get("lattice_scale", 1.0))
    if isinstance(lr, dict):
        M = np.array(lr["reference_matrix"], float)
        if lr.get("scaled_by") == "lattice_scale":
            M = M * ls
        return M
    if name == "Si1-xGex":
        x = float(params["x"])
        a = ((1 - x) * 5.43114 + x * 5.6579) * ls
        return np.eye(3) * a
    if name == "Mo1-xWx":
        x = float(params["x"])
        a = ((1 - x) * 3.1470 + x * 3.1652) * ls
        return np.eye(3) * a
    if name == "BaTiO3 cubic":
        return np.eye(3) * float(params["a_pc"])
    if name == "BaTiO3 tetragonal":
        apc = float(params["a_pc"])
        ca = float(params["c_over_a"])
        a = apc * ca ** (-1.0 / 3.0)
        c = apc * ca ** (2.0 / 3.0)
        return np.diag([a, a, c])
    raise KeyError(name)


@lru_cache(maxsize=None)
def _table(name, rad, key):
    t = _TABLES["%s|%s|%s" % (name, rad, key)]
    return np.array(t["hkl"], float), np.array(t["intensity_per_weight"], float)


def phase_peaks(name, params, rad):
    """Unshifted 2theta (deg) and intensity per unit weight for one phase."""
    if name == "Ni3Al":
        S = float(params.get("S", 0.0))
        h0, i0 = _table(name, rad, "S=0.0")
        h1, i1 = _table(name, rad, "S=1.0")
        hkl = np.vstack([h0, h1])
        inten = np.concatenate([i0 * (1 - S * S), i1 * S * S])
    elif name in ("Si1-xGex", "Mo1-xWx"):
        xr = round(float(params["x"]), 2)
        hkl, inten = _table(name, rad, "x=%r" % xr)
    else:
        hkl, inten = _table(name, rad, "")
    M = _matrix(name, params)
    B = np.linalg.inv(M).T  # reciprocal rows (no 2pi)
    G = hkl @ B
    d = 1.0 / np.sqrt((G * G).sum(1))
    sx = LAM / (2 * d)
    keep = sx < 1.0
    tt = 2 * np.degrees(np.arcsin(sx[keep]))
    return tt, inten[keep]


def group_peaks(group, rad, si_std):
    tts, ins = [], []
    fac = 0.8 if si_std else 1.0
    for name, params, w in group:
        if w == 0:
            continue
        tt, I = phase_peaks(name, params, rad)
        tts.append(tt)
        ins.append(I * w * fac)
    if si_std:
        tt, I = phase_peaks("Si standard", {}, rad)
        tts.append(tt)
        ins.append(I * 0.2)
    if not tts:
        return np.zeros(0), np.zeros(0)
    return np.concatenate(tts), np.concatenate(ins)


# ---------------------------------------------------------------- profile
def signal(meas, tt, I, s, z, L):
    rad = meas["radiation"]
    start, step, n = float(meas["start"]), float(meas["step"]), int(meas["n"])
    out = np.zeros(n)
    if tt.size == 0:
        return out
    if rad == "xray":
        th0 = np.radians(tt / 2)
        pos = tt + z - DEG * 2 * s * np.cos(th0) / R_MM
        U, V, W = UVW[meas["optics"]]
    else:
        pos = tt
        U, V, W = UVW["neutron"]
    th = np.radians(pos / 2)
    tn = np.tan(th)
    hi2 = np.maximum(U * tn * tn + V * tn + W, 1e-8)
    hs = DEG * 0.9 * 0.15406 / (L * np.cos(th))
    H = np.sqrt(hi2 + hs * hs)
    lo = np.ceil((pos - 25 * H - start) / step - 1e-9).astype(np.int64)
    hi = np.floor((pos + 25 * H - start) / step + 1e-9).astype(np.int64)
    lo = np.maximum(lo, 0)
    hi = np.minimum(hi, n - 1)
    ok = (hi >= lo) & (I != 0)
    if not ok.any():
        return out
    pos, H, I, lo, hi = pos[ok], H[ok], I[ok], lo[ok], hi[ok]
    K = int((hi - lo).max()) + 1
    idx = lo[:, None] + np.arange(K)[None, :]
    mask = idx <= hi[:, None]
    x = start + idx * step
    dlt = x - pos[:, None]
    Hc = H[:, None]
    q = dlt * dlt / (Hc * Hc)
    mask &= np.abs(dlt) <= 25 * Hc
    prof = I[:, None] * (ETA * 2 / (np.pi * Hc) / (1 + 4 * q)
                         + (1 - ETA) * (2 / Hc) * math.sqrt(LN2 / math.pi) * np.exp(-4 * LN2 * q))
    out += np.bincount(idx[mask], weights=prof[mask], minlength=n)
    return out


def xgrid(meas):
    return float(meas["start"]) + np.arange(int(meas["n"])) * float(meas["step"])


def tf(meas):
    t = float(meas["t"])
    f = FLUX[meas["optics"]] if meas["radiation"] == "xray" else 1.0
    return t * f


def truth_mu(world, plan):
    mus = []
    for m in plan:
        x = xgrid(m)
        sig = np.zeros(int(m["n"]))
        for g in world["truth_groups"]:
            tt, I = group_peaks(g, m["radiation"], m["radiation"] == "xray" and m["si_standard"])
            sig += signal(m, tt, I, world["disp_mm"], world["zero_deg"], world["L_nm"])
        if m["radiation"] == "xray":
            A, b0, b1 = world["A_xray"], world["b0"], world["b1"]
        else:
            A, b0, b1 = world["A_neutron"], world["bn0"], world["bn1"]
        mus.append(tf(m) * (A * sig + b0 + b1 * (x - 80) / 70))
    return np.concatenate(mus)


# ---------------------------------------------------------------- branches
def branch_groups(br, u):
    lo, hi = br["lo"], br["hi"]
    dim = len(lo)
    gl, gh = br["groups_at_lo"], br["groups_at_hi"]
    if dim == 0:
        return gl

    def interp(vl, vh):
        if vl == vh:
            return vl
        if dim == 1:
            t = (u[0] - lo[0]) / (hi[0] - lo[0])
            return vl + t * (vh - vl)
        for j in range(dim):
            if abs(vl - lo[j]) < 1e-12 and abs(vh - hi[j]) < 1e-12:
                return u[j]
        raise ValueError("cannot map branch parameter")

    out = []
    for g_l, g_h in zip(gl, gh):
        grp = []
        for (nl, pl, wl), (nh, ph, wh) in zip(g_l, g_h):
            assert nl == nh
            params = {k: interp(pl[k], ph[k]) for k in pl}
            grp.append((nl, params, interp(wl, wh)))
        out.append(grp)
    return out


class Problem:
    def __init__(self, world, plan, br):
        self.world, self.plan, self.br = world, plan, br
        self.mu = truth_mu(world, plan)
        self.sw = 1.0 / np.sqrt(self.mu)
        self.y = self.mu * self.sw
        L0 = world["L_nm"]
        self.lo = np.array([-0.2, -0.01, 0.7 * L0] + list(br["lo"]), float)
        self.hi = np.array([0.2, 0.01, 1.3 * L0] + list(br["hi"]), float)
        self.dim = len(self.lo)
        self.ng = len(br["groups_at_lo"])
        self.insts = sorted(set(m["radiation"] for m in plan))
        offs = np.cumsum([0] + [int(m["n"]) for m in plan])
        self.slices = [slice(offs[i], offs[i + 1]) for i in range(len(plan))]
        self.N = offs[-1]
        # background columns (constant per plan)
        nb = 3 * len(self.insts)
        self.ncol = self.ng * len(self.insts) + nb
        self.Xbg = np.zeros((self.N, nb))
        for mi, m in enumerate(self.plan):
            k = self.insts.index(m["radiation"])
            x = xgrid(m)
            c = tf(m)
            sl = self.slices[mi]
            self.Xbg[sl, 3 * k] = c
            self.Xbg[sl, 3 * k + 1] = c * (x - 80) / 70
            self.Xbg[sl, 3 * k + 2] = -c * (x - 80) / 70
        self.Xbg *= self.sw[:, None]
        self.cache = {}
        self.fixed_groups = None
        if self.dim == 3:
            self.fixed_groups = self._peaks(branch_groups(br, []))

    def _peaks(self, groups):
        res = []
        for m in self.plan:
            si = m["radiation"] == "xray" and m["si_standard"]
            res.append([group_peaks(g, m["radiation"], si) for g in groups])
        return res

    def value(self, p):
        p = np.clip(np.asarray(p, float), self.lo, self.hi)
        key = tuple(np.round(p, 14))
        if key in self.cache:
            return self.cache[key]
        s, z, L = p[0], p[1], p[2]
        pk = self.fixed_groups if self.fixed_groups is not None else self._peaks(branch_groups(self.br, list(p[3:])))
        Xs = np.zeros((self.N, self.ng * len(self.insts)))
        for mi, m in enumerate(self.plan):
            k = self.insts.index(m["radiation"])
            sl = self.slices[mi]
            c = tf(m)
            for g in range(self.ng):
                tt, I = pk[mi][g]
                Xs[sl, k * self.ng + g] = c * signal(m, tt, I, s, z, L)
        Xs *= self.sw[:, None]
        X = np.hstack([Xs, self.Xbg])
        # drop all-zero columns (e.g. a group with no peaks in range)
        nz = np.any(X != 0, axis=0)
        beta, _ = nnls(X[:, nz], self.y, maxiter=50 * X.shape[1])
        r = self.y - X[:, nz] @ beta
        v = float(r @ r)
        self.cache[key] = v
        return v

    # unit-cube helpers
    def to_p(self, q):
        return self.lo + np.asarray(q) * (self.hi - self.lo)

    def to_q(self, p):
        return (np.asarray(p) - self.lo) / (self.hi - self.lo)

    def f(self, q):
        return self.value(self.to_p(np.clip(q, 0, 1)))


def minimise(prob, n_sobol=256, n_refine=8, seed=12345):
    d = prob.dim
    w = prob.world
    cands = [np.full(d, 0.5)]
    sob = qmc.Sobol(d, scramble=True, seed=seed).random(n_sobol)
    cands += list(sob)
    ugrids = [np.linspace(prob.lo[j], prob.hi[j], 3) for j in range(3, d)]
    for s in (-0.15, -0.05, 0.05, 0.15, w["disp_mm"]):
        for us in itertools.product(*ugrids) if ugrids else [()]:
            cands.append(prob.to_q([s, 0.0, w["L_nm"]] + list(us)))
    # faces u = lo / hi with nuisances at truth and centre
    for j in range(3, d):
        for e in (0.0, 1.0):
            for base in (prob.to_q([w["disp_mm"], w["zero_deg"], w["L_nm"]] + [0.5 * (a + b) for a, b in zip(prob.lo[3:], prob.hi[3:])]),
                         np.full(d, 0.5)):
                q = np.clip(np.array(base, float), 0, 1)
                q[j] = e
                cands.append(q)
    cands = [np.clip(c, 0, 1) for c in cands]
    vals = np.array([prob.f(c) for c in cands])
    order = np.argsort(vals)
    starts = []
    for i in order:
        if all(np.linalg.norm(cands[i] - s) > 0.05 for s in starts):
            starts.append(cands[i])
        if len(starts) >= n_refine:
            break
    best_q, best_v = None, np.inf
    bounds = [(0.0, 1.0)] * d
    for s0 in starts:
        r = minimize(prob.f, s0, method="L-BFGS-B", bounds=bounds,
                     options={"eps": 1e-5, "maxiter": 500, "ftol": 1e-13, "gtol": 1e-10})
        if r.fun < best_v:
            best_q, best_v = np.clip(r.x, 0, 1), float(r.fun)
    # polish: alternate Powell and L-BFGS-B
    for _ in range(20):
        prev = best_v
        r = minimize(prob.f, best_q, method="Powell", bounds=bounds,
                     options={"xtol": 1e-7, "ftol": 1e-12, "maxfev": 4000})
        if r.fun < best_v:
            best_q, best_v = np.clip(r.x, 0, 1), float(r.fun)
        r = minimize(prob.f, best_q, method="L-BFGS-B", bounds=bounds,
                     options={"eps": 1e-6, "maxiter": 500, "ftol": 1e-14, "gtol": 1e-11})
        if r.fun < best_v:
            best_q, best_v = np.clip(r.x, 0, 1), float(r.fun)
        if prev - best_v <= 1e-6 * max(abs(prev), 1e-12):
            break
    return best_v, prob.to_p(best_q)


def compute_D(wid, plan, n_sobol=256, n_refine=8, seed=12345):
    load()
    world = _WORLDS[wid]
    best = (np.inf, None, None)
    for bi, br in enumerate(world["other_side"]):
        prob = Problem(world, plan, br)
        v, p = minimise(prob, n_sobol=n_sobol, n_refine=n_refine, seed=seed)
        if v < best[0]:
            best = (v, bi, p)
    return best


def job(args):
    wid, idx, plan, n_sobol, n_refine, seed = args
    t0 = time.time()
    v, bi, p = compute_D(wid, plan, n_sobol, n_refine, seed)
    return wid, idx, v, bi, [float(a) for a in p], time.time() - t0


def agree(mine, ref):
    if ref < 5 and abs(mine - ref) <= 0.05:
        return True
    return abs(mine - ref) <= 0.01 * abs(ref)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--worlds", default="")
    ap.add_argument("--sobol", type=int, default=256)
    ap.add_argument("--refine", type=int, default=8)
    ap.add_argument("--seed", type=int, default=12345)
    ap.add_argument("--out", default=os.path.join(HERE, "shadow_results.json"))
    a = ap.parse_args()
    load()
    plans = json.load(open(os.path.join(HERE, "shadow_plans.json")))
    wsel = set(a.worlds.split(",")) if a.worlds else None
    jobs = []
    for wid, lst in plans.items():
        if wsel and wid not in wsel:
            continue
        for i, e in enumerate(lst):
            jobs.append((wid, i, e["plan"], a.sobol, a.refine, a.seed))
    # longest jobs first (more points, more branch parameters)
    jobs.sort(key=lambda j: -sum(m["n"] for m in j[2]))
    t0 = time.time()
    res = {}
    with Pool(min(a.workers, 12)) as pool:
        for wid, i, v, bi, p, dt in pool.imap_unordered(job, jobs):
            ref = plans[wid][i]["D"]
            res.setdefault(wid, {})[i] = {"plan_index": i, "D_shadow": round(v, 6), "D_reference": ref,
                                          "agree": agree(v, ref), "branch": bi, "argmin": p,
                                          "seconds": round(dt, 2)}
            print(wid, i, round(v, 4), ref, agree(v, ref), round(dt, 1), flush=True)
    out = {"worlds": {w: [res[w][i] for i in sorted(res[w])] for w in sorted(res)},
           "n_plans": sum(len(v) for v in res.values()),
           "n_agree": sum(r["agree"] for v in res.values() for r in v.values()),
           "runtime_s": round(time.time() - t0, 1),
           "settings": {"sobol": a.sobol, "refine": a.refine, "seed": a.seed}}
    json.dump(out, open(a.out, "w"), indent=1)
    print("plans", out["n_plans"], "agree", out["n_agree"], "runtime", out["runtime_s"])


if __name__ == "__main__":
    main()
