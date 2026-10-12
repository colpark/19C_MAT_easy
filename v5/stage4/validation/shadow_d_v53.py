"""Independent shadow implementation of D (V5_SPEC Appendix A) for stage 4. numpy/scipy only."""
import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import json, sys, math
import numpy as np
from scipy.optimize import nnls, minimize
from scipy.stats import qmc
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
ST4 = os.path.dirname(HERE)
LAM = 1.5406
UVW = {"standard": (0.012, -0.002, 0.0085), "high_resolution": (0.0011, -0.00018, 0.00077),
       "neutron": (0.06, -0.03, 0.09)}
FLUX = {"standard": 1.0, "high_resolution": 0.25, "neutron": 1.0}
ETA = 0.5

WORLDS = json.load(open(os.path.join(ST4, "WORLDS.json")))["worlds"]
PT = json.load(open(os.path.join(ST4, "peak_tables.json")))
TABLES, LATT = PT["tables"], PT["lattice"]


class MissingTable(Exception):
    pass


_pk_cache = {}


def phase_peaks(name, params, rad):
    """(two_theta_deg array, intensity per unit weight) for a phase."""
    key = (name, json.dumps(params, sort_keys=True), rad)
    if key in _pk_cache:
        return _pk_cache[key]
    tk = f"{name}|{rad}|"
    if tk not in TABLES:
        raise MissingTable(tk)
    tb = TABLES[tk]
    hkl = np.array(tb["hkl"], float)
    I = np.array(tb["intensity_per_weight"], float)
    M = np.array(LATT[name]["reference_matrix"], float) * float(params.get("lattice_scale", 1.0))
    rec = np.linalg.inv(M).T  # rows a*,b*,c* (lattice vectors are rows of M)
    g = hkl @ rec
    d = 1.0 / np.linalg.norm(g, axis=1)
    s = LAM / (2 * d)
    ok = s < 1.0
    tt = np.degrees(2 * np.arcsin(s[ok]))
    _pk_cache[key] = (tt, I[ok])
    return _pk_cache[key]


def group_peaks(group, rad, si):
    """group: list of [name, params, weight]; returns (2theta, amp)."""
    T, A = [], []
    for name, params, w in group:
        tt, I = phase_peaks(name, params, rad)
        T.append(tt); A.append(w * (0.8 if si else 1.0) * I)
    if si:
        tt, I = phase_peaks("Si standard", {}, rad)
        T.append(tt); A.append(0.2 * I)
    return np.concatenate(T), np.concatenate(A)


def signal(x, tt, amp, optics, z, s, L_nm, xray):
    if xray:
        th = np.radians(tt / 2)
        obs = tt + z - np.degrees(2 * s * np.cos(th) / 240.0)
    else:
        obs = tt
    th = np.radians(obs / 2)
    U, V, W = UVW[optics]
    tn = np.tan(th)
    Hi2 = np.maximum(U * tn ** 2 + V * tn + W, 1e-8)
    Hs = np.degrees(0.9 * 0.15406 / (L_nm * np.cos(th)))
    H = np.sqrt(Hi2 + Hs ** 2)
    lo, hi = x[0], x[-1]
    sel = (obs + 25 * H >= lo) & (obs - 25 * H <= hi) & (amp != 0)
    if not sel.any():
        return np.zeros_like(x)
    obs, H, a = obs[sel], H[sel], amp[sel]
    out = np.zeros_like(x)
    CH = 256
    for i in range(0, len(obs), CH):
        o, h, aa = obs[i:i + CH, None], H[i:i + CH, None], a[i:i + CH, None]
        dl = x[None, :] - o
        lor = ETA * 2 / (np.pi * h) / (1 + 4 * dl ** 2 / h ** 2)
        gau = (1 - ETA) * (2 / h) * math.sqrt(math.log(2) / math.pi) * np.exp(-4 * math.log(2) * dl ** 2 / h ** 2)
        out += (aa * np.where(np.abs(dl) <= 25 * h, lor + gau, 0.0)).sum(0)
    return out


def grid(m):
    return m["start"] + np.arange(m["n"]) * m["step"]


def true_mu(w, m):
    x = grid(m); xr = m["radiation"] == "xray"
    f = FLUX[m["optics"]]; t = m["t"]
    sig = np.zeros_like(x)
    for grp in w["truth_groups"]:
        tt, a = group_peaks(grp, m["radiation"], m["si_standard"] and xr)
        sig += signal(x, tt, a, m["optics"], w["zero_deg"], w["disp_mm"], w["L_nm"], xr)
    u = (x - 80) / 70
    if xr:
        return t * f * (w["A_xray"] * sig + w["b0"] + w["b1"] * u)
    return t * (w["A_neutron"] * sig + w["bn0"] + w["bn1"] * u)


class Problem:
    def __init__(self, wid, plan):
        self.w = w = WORLDS[wid]
        self.plan = plan
        self.mus = [true_mu(w, m) for m in plan]
        self.xs = [grid(m) for m in plan]
        self.has_x = any(m["radiation"] == "xray" for m in plan)
        self.branches = w["other_side"]
        self.L0 = w["L_nm"]
        self.wt = [1.0 / mu for mu in self.mus]
        self.mu_all = np.concatenate(self.mus)
        self.sw = np.sqrt(np.concatenate(self.wt))
        self.y = self.mu_all * self.sw
        self.npts = [len(x) for x in self.xs]
        self.off = np.concatenate([[0], np.cumsum(self.npts)])

    def groups_for(self, br, u):
        # parameters enter linearly: interpolate params/weights between lo and hi
        glo, ghi = br["groups_at_lo"], br["groups_at_hi"]
        if not br["lo"]:
            return glo
        lo = np.array(br["lo"], float); hi = np.array(br["hi"], float)
        tfrac = float(np.ravel((np.asarray(u) - lo) / (hi - lo))[0]) if np.ndim(u) else float((u - lo) / (hi - lo))
        out = []
        for gl, gh in zip(glo, ghi):
            g = []
            for pl, ph in zip(gl, gh):
                params = {k: pl[1][k] + tfrac * (ph[1][k] - pl[1][k]) if isinstance(pl[1][k], (int, float)) else pl[1][k] for k in pl[1]}
                g.append([pl[0], params, pl[2] + tfrac * (ph[2] - pl[2])])
            out.append(g)
        return out

    def cost(self, p, br, with_u):
        s, z, Lf = p[0], p[1], p[2]
        u = p[3:] if with_u else None
        groups = self.groups_for(br, u[0] if with_u else None)
        L = Lf * self.L0
        cols = []  # (column vector over all points)
        N = self.off[-1]
        insts = ["xray", "neutron"]
        blocks = []
        for inst in insts:
            idx = [i for i, m in enumerate(self.plan) if m["radiation"] == inst]
            if not idx:
                continue
            xr = inst == "xray"
            # signal columns, one per group
            for g in groups:
                col = np.zeros(N)
                for i in idx:
                    m = self.plan[i]
                    tt, a = group_peaks(g, inst, m["si_standard"] and xr)
                    sg = signal(self.xs[i], tt, a, m["optics"], z, s, L, xr)
                    col[self.off[i]:self.off[i + 1]] = m["t"] * FLUX[m["optics"]] * sg
                blocks.append(col)
            c0 = np.zeros(N); c1 = np.zeros(N)
            for i in idx:
                m = self.plan[i]; tf = m["t"] * FLUX[m["optics"]]
                c0[self.off[i]:self.off[i + 1]] = tf
                c1[self.off[i]:self.off[i + 1]] = tf * (self.xs[i] - 80) / 70
            blocks += [c0, c1, -c1]
        X = np.stack(blocks, 1) * self.sw[:, None]
        # column scaling for conditioning
        sc = np.linalg.norm(X, axis=0); sc[sc == 0] = 1
        beta, rn = nnls(X / sc, self.y, maxiter=50 * X.shape[1])
        return rn ** 2

    def box(self, br):
        lo = [-0.2, -0.01, 0.7]; hi = [0.2, 0.01, 1.3]
        if not self.has_x:
            lo[0] = lo[1] = hi[0] = hi[1] = 0.0
        if br["lo"]:
            lo += list(np.atleast_1d(br["lo"])); hi += list(np.atleast_1d(br["hi"]))
        return np.array(lo, float), np.array(hi, float)

    def D_branch(self, br):
        lo, hi = self.box(br)
        with_u = bool(br["lo"])
        free = hi > lo
        span = np.where(free, hi - lo, 1.0)

        def phys(c):
            return lo + np.clip(c, 0, 1) * span

        def f(c):
            return self.cost(phys(c), br, with_u)

        nd = len(lo)
        cands = [np.full(nd, 0.5)]
        sob = qmc.Sobol(nd, scramble=True, seed=12345).random(256)
        cands += list(sob)
        s_true = self.w["disp_mm"]
        ugrid = [0.0, 0.5, 1.0] if with_u else [None]
        for sv in [-0.15, -0.05, 0.05, 0.15, s_true]:
            for ug in ugrid:
                c = np.full(nd, 0.5)
                c[0] = (sv - lo[0]) / span[0] if free[0] else 0.5
                c[1] = 0.5
                c[2] = (1.0 - lo[2]) / span[2]
                if ug is not None:
                    c[3] = ug
                cands.append(c)
        for uf in ([0.0, 1.0] if with_u else []):
            c = np.full(nd, 0.5); c[3] = uf; cands.append(c)
        cands = [np.where(free, c, 0.5) for c in cands]
        vals = np.array([f(c) for c in cands])
        order = np.argsort(vals)
        chosen = []
        for i in order:
            if all(np.linalg.norm(cands[i] - cands[j]) > 0.05 for j in chosen):
                chosen.append(i)
            if len(chosen) == 8:
                break
        bounds = [(0, 1) if fr else (0.5, 0.5) for fr in free]
        best, bx = np.inf, None
        for i in chosen:
            r = minimize(f, cands[i], method="L-BFGS-B", bounds=bounds, options={"eps": 1e-5, "maxiter": 200})
            if r.fun < best:
                best, bx = r.fun, np.clip(r.x, 0, 1)
        if vals[order[0]] < best:
            best, bx = vals[order[0]], cands[order[0]]
        for _ in range(6):
            prev = best
            r = minimize(f, bx, method="Powell", bounds=bounds, options={"xtol": 1e-4, "ftol": 1e-8, "maxiter": 3000})
            if r.fun < best:
                best, bx = r.fun, np.clip(r.x, 0, 1)
            r = minimize(f, bx, method="L-BFGS-B", bounds=bounds, options={"eps": 1e-5, "maxiter": 200})
            if r.fun < best:
                best, bx = r.fun, np.clip(r.x, 0, 1)
            if prev - best < 1e-6 * max(abs(best), 1e-12):
                break
        return best

    def D(self):
        return min(self.D_branch(br) for br in self.branches)


def job(args):
    wid, k, plan = args
    try:
        return wid, k, Problem(wid, plan).D(), None
    except MissingTable as e:
        return wid, k, None, f"missing peak table: {e.args[0]}"


def main():
    plans = json.load(open(os.path.join(HERE, "shadow_plans.json")))["worlds"]
    jobs = [(wid, k, p["plan"]) for wid, ps in plans.items() for k, p in enumerate(ps)]
    with Pool(min(16, len(jobs))) as pool:
        res = pool.map(job, jobs, chunksize=1)
    out = {}
    nag = 0
    for wid, k, D, err in res:
        ref = plans[wid][k]["D"]
        if D is None:
            rec = {"plan": k, "D_shadow": None, "D_ref": ref, "agree": False, "error": err}
        else:
            tol = 0.05 if ref < 5 else 0.01 * abs(ref)
            ag = abs(D - ref) <= tol
            rec = {"plan": k, "D_shadow": D, "D_ref": ref, "agree": bool(ag),
                   "direction": "ok" if ag else ("shadow_lower" if D < ref else "shadow_higher")}
        nag += rec["agree"]
        out.setdefault(wid, []).append(rec)
    json.dump({"n_plans": len(res), "n_agree": nag, "worlds": out}, open(os.path.join(HERE, "shadow_results.json"), "w"), indent=1)
    print(len(res), nag)


if __name__ == "__main__":
    main()
