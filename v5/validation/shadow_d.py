"""Shadow implementation of the separation statistic D (V5_SPEC.md Appendix A).

Written from V5_SPEC.md (sections 1.2, 3.1, Appendix A), MANUAL.md, WORLDS.json and
peak_tables.json only. Uses numpy, scipy and numba.

Usage: python shadow_d.py [n_workers]   -> writes results.json
"""
import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
import sys
import json
import math
import time
import itertools
import numpy as np
from scipy.optimize import nnls, minimize
import numba

HERE = os.path.dirname(os.path.abspath(__file__))
LAM = 1.5406  # Angstrom
ETA = 0.5
R_MM = 240.0
UVW = {
    "standard": (0.012, -0.002, 0.0085),
    "high_resolution": (0.0011, -0.00018, 0.00077),
    "neutron": (0.06, -0.03, 0.09),
}
FLUX = {"standard": 1.0, "high_resolution": 0.25, "neutron": 1.0}

with open(os.path.join(HERE, "peak_tables.json")) as fh:
    _PT = json.load(fh)
TABLES = _PT["tables"]
LATTICE = _PT["lattice"]
with open(os.path.join(HERE, "WORLDS.json")) as fh:
    WORLDS = json.load(fh)["worlds"]


# ---------------------------------------------------------------- lattice / peaks
def lattice_matrix(name, params):
    rule = LATTICE[name]
    ls = float(params.get("lattice_scale", 1.0))
    if isinstance(rule, dict):
        M = np.array(rule["reference_matrix"], dtype=float)
        if rule.get("scaled_by") == "lattice_scale":
            M = M * ls
        return M
    if name == "Si1-xGex":
        x = float(params["x"])
        a = ((1 - x) * 5.43114 + x * 5.6579) * ls
        return np.diag([a, a, a])
    if name == "Mo1-xWx":
        x = float(params["x"])
        a = ((1 - x) * 3.1470 + x * 3.1652) * ls
        return np.diag([a, a, a])
    if name == "BaTiO3 cubic":
        a = float(params["a_pc"])
        return np.diag([a, a, a])
    if name == "BaTiO3 tetragonal":
        apc = float(params["a_pc"])
        ca = float(params["c_over_a"])
        a = apc * ca ** (-1.0 / 3.0)
        c = apc * ca ** (2.0 / 3.0)
        return np.diag([a, a, c])
    raise KeyError(name)


def _fmt(v):
    return repr(float(v))


def table_hkl_int(name, params, radiation):
    """Return (hkl array (n,3), intensity per unit weight (n,))."""
    if name == "Ni3Al":
        S = float(params.get("S", 0.0))
        t0 = TABLES[f"Ni3Al|{radiation}|S=0.0"]
        t1 = TABLES[f"Ni3Al|{radiation}|S=1.0"]
        d = {}
        for h, I in zip(t0["hkl"], t0["intensity_per_weight"]):
            d.setdefault(tuple(h), [0.0, 0.0])[0] += I
        for h, I in zip(t1["hkl"], t1["intensity_per_weight"]):
            d.setdefault(tuple(h), [0.0, 0.0])[1] += I
        hk = list(d.keys())
        I0 = np.array([d[k][0] for k in hk])
        I1 = np.array([d[k][1] for k in hk])
        return np.array(hk, dtype=float), I0 + S * S * (I1 - I0)
    if name in ("Si1-xGex", "Mo1-xWx"):
        x = round(float(params["x"]), 2)
        key = f"{name}|{radiation}|x={_fmt(x)}"
        if key not in TABLES:  # tolerate formatting like 0.50
            for k in TABLES:
                if k.startswith(f"{name}|{radiation}|x=") and abs(float(k.split("=")[1]) - x) < 1e-9:
                    key = k
                    break
        t = TABLES[key]
    else:
        t = TABLES[f"{name}|{radiation}|"]
    return np.array(t["hkl"], dtype=float), np.array(t["intensity_per_weight"], dtype=float)


_cache = {}


def phase_peaks(name, params, radiation):
    """Unshifted 2theta (deg) and intensity per unit weight."""
    key = (name, tuple(sorted((k, float(v)) for k, v in params.items())), radiation)
    r = _cache.get(key)
    if r is not None:
        return r
    hkl, I = table_hkl_int(name, params, radiation)
    M = lattice_matrix(name, params)
    G = hkl @ np.linalg.inv(M).T  # reciprocal vectors (rows of inv(M).T are a*, b*, c*)
    dinv = np.sqrt((G * G).sum(1))
    sinth = LAM * dinv / 2.0
    keep = (sinth < 1.0) & (dinv > 0)
    tt = 2.0 * np.degrees(np.arcsin(sinth[keep]))
    r = (tt, I[keep])
    if len(_cache) < 20000:
        _cache[key] = r
    return r


def group_peaks(group, radiation, si_standard):
    """group = list of [name, params, weight]; returns (2theta, intensity)."""
    tts, Is = [], []
    wscale = 0.8 if (si_standard and radiation == "xray") else 1.0
    for name, params, w in group:
        w = float(w) * wscale
        if w == 0.0:
            continue
        tt, I = phase_peaks(name, params, radiation)
        tts.append(tt)
        Is.append(I * w)
    if si_standard and radiation == "xray":
        tt, I = phase_peaks("Si standard", {}, "xray")
        tts.append(tt)
        Is.append(I * 0.2)
    if not tts:
        return np.zeros(0), np.zeros(0)
    return np.concatenate(tts), np.concatenate(Is)


# ---------------------------------------------------------------- profile
@numba.njit(cache=True)
def _accumulate(out, start, step, n, pos, amp, H):
    c_l = 2.0 / math.pi
    c_g = 2.0 * math.sqrt(math.log(2.0) / math.pi)
    l4 = 4.0 * math.log(2.0)
    for p in range(pos.shape[0]):
        h = H[p]
        x0 = pos[p]
        a = amp[p]
        if a == 0.0:
            continue
        lo = int(math.floor((x0 - 25.0 * h - start) / step)) - 1
        hi = int(math.ceil((x0 + 25.0 * h - start) / step)) + 1
        if lo < 0:
            lo = 0
        if hi > n - 1:
            hi = n - 1
        for i in range(lo, hi + 1):
            x = start + i * step
            dlt = x - x0
            if abs(dlt) <= 25.0 * h:
                q = dlt * dlt / (h * h)
                out[i] += a * (ETA * c_l / h / (1.0 + 4.0 * q)
                               + (1.0 - ETA) * c_g / h * math.exp(-l4 * q))


def signal(meas, tt, I, s, z, L_nm):
    """sig(x) on the measurement grid for peaks (tt, I)."""
    n = int(meas["n"])
    out = np.zeros(n)
    if tt.size == 0:
        return out
    if meas["radiation"] == "xray":
        th = np.radians(tt / 2.0)
        pos = tt + z - (180.0 / math.pi) * 2.0 * s * np.cos(th) / R_MM
        U, V, W = UVW[meas["optics"]]
    else:
        pos = tt.copy()
        U, V, W = UVW["neutron"]
    tho = np.radians(pos / 2.0)
    tn = np.tan(tho)
    Hi2 = np.maximum(U * tn * tn + V * tn + W, 1e-8)
    Hs = (180.0 / math.pi) * 0.9 * 0.15406 / (L_nm * np.cos(tho))
    H = np.sqrt(Hi2 + Hs * Hs)
    _accumulate(out, float(meas["start"]), float(meas["step"]), n,
                pos.astype(np.float64), I.astype(np.float64), H.astype(np.float64))
    return out


def xgrid(meas):
    return float(meas["start"]) + np.arange(int(meas["n"])) * float(meas["step"])


def tf(meas):
    f = FLUX["neutron"] if meas["radiation"] == "neutron" else FLUX[meas["optics"]]
    return float(meas["t"]) * f


# ---------------------------------------------------------------- truth
def mu_truth(world, plan):
    mus = []
    for m in plan:
        x = xgrid(m)
        sig = np.zeros(int(m["n"]))
        for g in world["truth_groups"]:
            tt, I = group_peaks(g, m["radiation"], bool(m["si_standard"]))
            sig += signal(m, tt, I, world["disp_mm"], world["zero_deg"], world["L_nm"])
        if m["radiation"] == "xray":
            mu = tf(m) * (world["A_xray"] * sig + world["b0"] + world["b1"] * (x - 80.0) / 70.0)
        else:
            mu = tf(m) * (world["A_neutron"] * sig + world["bn0"] + world["bn1"] * (x - 80.0) / 70.0)
        mus.append(mu)
    return np.concatenate(mus)


# ---------------------------------------------------------------- branches
def branch_groups(branch, u):
    """Interpolate the branch's groups at parameter vector u."""
    lo, hi = branch["lo"], branch["hi"]
    glo, ghi = branch["groups_at_lo"], branch["groups_at_hi"]
    d = len(lo)
    if d == 0:
        return glo

    def interp(vlo, vhi):
        vlo = float(vlo)
        vhi = float(vhi)
        if vlo == vhi:
            return vlo
        # a value that equals lo_j at lo and hi_j at hi is u_j itself
        for j in range(d):
            if abs(vlo - lo[j]) < 1e-12 and abs(vhi - hi[j]) < 1e-12:
                return float(u[j])
        if d == 1:
            frac = (u[0] - lo[0]) / (hi[0] - lo[0])
            return vlo + frac * (vhi - vlo)
        raise ValueError("cannot map interpolated value to a branch dimension")

    out = []
    for gl, gh in zip(glo, ghi):
        grp = []
        for (nl, pl, wl), (nh, ph, wh) in zip(gl, gh):
            assert nl == nh
            p = {k: interp(pl[k], ph[k]) for k in pl}
            grp.append([nl, p, interp(wl, wh)])
        out.append(grp)
    return out


# ---------------------------------------------------------------- D evaluator
class DEval:
    def __init__(self, world, plan):
        self.world = world
        self.plan = plan
        self.muT = mu_truth(world, plan)
        self.sw = 1.0 / np.sqrt(self.muT)
        self.has_x = any(m["radiation"] == "xray" for m in plan)
        self.has_n = any(m["radiation"] == "neutron" for m in plan)
        self.offsets = np.cumsum([0] + [int(m["n"]) for m in plan])
        self.N = int(self.offsets[-1])
        bg = []
        for inst in ("xray", "neutron"):
            if not (self.has_x if inst == "xray" else self.has_n):
                continue
            c0 = np.zeros(self.N)
            c1 = np.zeros(self.N)
            for k, m in enumerate(self.plan):
                if m["radiation"] != inst:
                    continue
                sl = slice(self.offsets[k], self.offsets[k + 1])
                c0[sl] = tf(m)
                c1[sl] = tf(m) * (xgrid(m) - 80.0) / 70.0
            bg += [c0, c1, -c1]
        self.bg = np.array(bg).T
        self.b = self.muT * self.sw
        self.L0 = float(world["L_nm"])

    def resid(self, branch, s, z, Lrel, u):
        groups = branch_groups(branch, u)
        L = self.L0 * Lrel
        cols = []
        for inst in ("xray", "neutron"):
            if not (self.has_x if inst == "xray" else self.has_n):
                continue
            for g in groups:
                col = np.zeros(self.N)
                for k, m in enumerate(self.plan):
                    if m["radiation"] != inst:
                        continue
                    tt, I = group_peaks(g, inst, bool(m["si_standard"]))
                    col[self.offsets[k]:self.offsets[k + 1]] = tf(m) * signal(m, tt, I, s, z, L)
                cols.append(col)
        X = np.column_stack(cols + [self.bg])
        Xw = X * self.sw[:, None]
        # scale columns for conditioning (does not change the NNLS optimum)
        cn = np.sqrt((Xw * Xw).sum(0))
        cn[cn == 0] = 1.0
        beta, rnorm = nnls(Xw / cn, self.b, maxiter=50 * Xw.shape[1])
        r = self.b - (Xw / cn) @ beta
        return float(r @ r)


DENSE = int(os.environ.get("SHADOW_DENSE", "1"))


def minimise_branch(ev, branch, n_s=None):
    """Multi-start + bounded optimisation over normalised coordinates in [0,1]^k."""
    lo = np.array(branch["lo"], dtype=float)
    hi = np.array(branch["hi"], dtype=float)
    du = len(lo)
    w = ev.world
    S_LO, S_HI, Z_LO, Z_HI, LR_LO, LR_HI = -0.2, 0.2, -0.01, 0.01, 0.7, 1.3
    use_sz = ev.has_x

    def unpack(v):
        i = 0
        if use_sz:
            s = S_LO + v[0] * (S_HI - S_LO)
            z = Z_LO + v[1] * (Z_HI - Z_LO)
            i = 2
        else:
            s, z = 0.0, 0.0
        Lr = LR_LO + v[i] * (LR_HI - LR_LO)
        u = lo + v[i + 1:i + 1 + du] * (hi - lo)
        return s, z, Lr, u

    def f(v):
        v = np.clip(v, 0.0, 1.0)
        s, z, Lr, u = unpack(v)
        return ev.resid(branch, s, z, Lr, u)

    def norm(s, z, Lr, ufrac):
        v = []
        if use_sz:
            v += [(s - S_LO) / (S_HI - S_LO), (z - Z_LO) / (Z_HI - Z_LO)]
        v += [(Lr - LR_LO) / (LR_HI - LR_LO)]
        v += list(ufrac)
        return np.clip(np.array(v, dtype=float), 0, 1)

    # start grid
    if n_s is None:
        n_s = 33 if DENSE else 9
    nz, nL, nu = (7, 7, 9) if DENSE else (3, 5, 5)
    s_vals = list(np.linspace(S_LO, S_HI, n_s)) + [w["disp_mm"]] if use_sz else [0.0]
    z_vals = list(np.linspace(Z_LO, Z_HI, nz)) + [w["zero_deg"]] if use_sz else [0.0]
    L_vals = list(np.linspace(0.7, 1.3, nL))
    u_vals = list(np.linspace(0.0, 1.0, nu)) if du else []
    u_grid = list(itertools.product(u_vals, repeat=du)) if du else [()]
    starts = []
    for s in s_vals:
        for z in z_vals:
            for Lr in L_vals:
                for uf in u_grid:
                    v = norm(s, z, Lr, uf)
                    starts.append((f(v), v))
    starts.sort(key=lambda t: t[0])
    best_val, best_v = starts[0]
    # refine the best few distinct starts
    picked = []
    for val, v in starts:
        if all(np.max(np.abs(v - p)) > 0.05 for _, p in picked):
            picked.append((val, v))
        if len(picked) >= (12 if DENSE else 6):
            break
    bounds = [(0.0, 1.0)] * len(best_v)
    for val, v in picked:
        try:
            r = minimize(f, v, method="L-BFGS-B", bounds=bounds,
                         options={"maxiter": 200, "eps": 1e-5, "ftol": 1e-13, "gtol": 1e-10})
            if r.fun < best_val:
                best_val, best_v = float(r.fun), np.clip(r.x, 0, 1)
        except Exception:
            pass
    # derivative-free polish from the best point
    for method, opts in (("Powell", {"xtol": 1e-6, "ftol": 1e-12, "maxfev": 4000}),
                         ("Nelder-Mead", {"xatol": 1e-7, "fatol": 1e-10, "maxfev": 3000})):
        try:
            r = minimize(f, best_v, method=method, bounds=bounds, options=opts)
            if r.fun < best_val:
                best_val, best_v = float(r.fun), np.clip(r.x, 0, 1)
        except Exception:
            pass
    s, z, Lr, u = unpack(best_v)
    return best_val, {"s": s, "z": z, "Lrel": Lr, "u": list(map(float, u))}


def compute_D(world, plan, detail=False):
    ev = DEval(world, plan)
    best = (math.inf, None, None)
    for br in world["other_side"]:
        val, par = minimise_branch(ev, br)
        if val < best[0]:
            best = (val, br["label"], par)
    if detail:
        return best
    return best[0]


def _job(args):
    wid, idx, plan = args
    t0 = time.time()
    val, label, par = compute_D(WORLDS[wid], plan, detail=True)
    return wid, idx, val, label, par, time.time() - t0


def main():
    nw = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    nw = min(nw, 12)
    with open(os.path.join(HERE, "plans.json")) as fh:
        plans = json.load(fh)
    jobs = [(wid, i, p) for wid, pl in plans.items() for i, p in enumerate(pl)]
    # long jobs first
    jobs.sort(key=lambda j: -sum(int(m["n"]) for m in j[2]) * (1 + len(WORLDS[j[0]]["other_side"][0]["lo"])))
    res = {wid: [None] * len(pl) for wid, pl in plans.items()}
    det = {wid: [None] * len(pl) for wid, pl in plans.items()}
    t0 = time.time()
    import multiprocessing as mp
    with mp.get_context("fork").Pool(nw) as pool:
        for k, (wid, idx, val, label, par, dt) in enumerate(pool.imap_unordered(_job, jobs)):
            res[wid][idx] = val
            det[wid][idx] = {"D": val, "branch": label, "params": par, "sec": dt}
            if k % 20 == 0:
                print(f"{k+1}/{len(jobs)} {time.time()-t0:.0f}s", flush=True)
    with open(os.path.join(HERE, "results.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    with open(os.path.join(HERE, "results_detail.json"), "w") as fh:
        json.dump(det, fh, indent=1)
    print(f"done in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
