"""Shadow implementation of the separation D (V5_SPEC sections 1.2, 3.1, Appendix A) for the family H worlds.

Written from the specification only. numpy + scipy. Run with ~/v5env/bin/python.
"""
import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
import json
import sys
import time
import numpy as np
from scipy.optimize import nnls, minimize
from scipy.stats import qmc
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
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

WORLDS = json.load(open(os.path.join(HERE, "WORLDS.json")))["worlds"]
PT = json.load(open(os.path.join(HERE, "peak_tables.json")))
PLANS = json.load(open(os.path.join(HERE, "shadow_plans.json")))["worlds"]

_phase_cache = {}


def phase_peaks(name, rad):
    """Unshifted 2theta (deg) and intensity per unit weight for phase `name`, radiation `rad`."""
    key = (name, rad)
    if key in _phase_cache:
        return _phase_cache[key]
    tab = PT["tables"]["%s|%s|" % (name, rad)]
    lat = PT["lattice"][name]
    M = np.array(lat["reference_matrix"], float)  # rows = lattice vectors; lattice_scale = 1
    hkl = np.array(tab["hkl"], float)
    I = np.array(tab["intensity_per_weight"], float)
    recip = np.linalg.inv(M).T  # rows = reciprocal vectors (no 2pi)
    G = hkl @ recip
    d = 1.0 / np.linalg.norm(G, axis=1)
    sx = LAM / (2.0 * d)
    ok = sx < 1.0
    tth = 2.0 * np.degrees(np.arcsin(sx[ok]))
    out = (tth, I[ok])
    _phase_cache[key] = out
    return out


def group_peaks(group, rad, si):
    """Concatenate peaks of a group (list of [phase, params, weight])."""
    pos, amp = [], []
    for ph, params, w in group:
        if params:
            raise NotImplementedError("parameterised phase not expected in family H")
        t, I = phase_peaks(ph, rad)
        ww = w * (0.8 if si else 1.0)
        pos.append(t)
        amp.append(ww * I)
    if si:
        t, I = phase_peaks("Si standard", rad)
        pos.append(t)
        amp.append(0.2 * I)
    return np.concatenate(pos), np.concatenate(amp)


def pattern(x, pos0, amp, optics, s, z, L, xray):
    """sig(x) of Appendix A.3-A.5."""
    if xray:
        th0 = np.radians(pos0 / 2.0)
        pos = pos0 + z - np.degrees(2.0 * s * np.cos(th0) / R_MM)
    else:
        pos = pos0
    th = np.radians(pos / 2.0)
    U, V, W = UVW[optics]
    tn = np.tan(th)
    Hi2 = np.maximum(U * tn * tn + V * tn + W, 1e-8)
    Hs = np.degrees(0.9 * 0.15406 / (L * np.cos(th)))
    H = np.sqrt(Hi2 + Hs * Hs)
    lo, hi = x[0], x[-1]
    sel = (pos + 25 * H >= lo) & (pos - 25 * H <= hi) & (amp != 0)
    pos, H, a = pos[sel], H[sel], amp[sel]
    out = np.zeros_like(x)
    if pos.size == 0:
        return out
    step = x[1] - x[0] if x.size > 1 else 1.0
    # chunk to bound memory
    for c0 in range(0, pos.size, 400):
        p = pos[c0:c0 + 400, None]
        h = H[c0:c0 + 400, None]
        aa = a[c0:c0 + 400, None]
        D = x[None, :] - p
        q = (D / h) ** 2
        prof = ETA * 2.0 / (np.pi * h) / (1.0 + 4.0 * q) + \
            (1.0 - ETA) * (2.0 / h) * np.sqrt(np.log(2) / np.pi) * np.exp(-4.0 * np.log(2) * q)
        prof = np.where(np.abs(D) <= 25.0 * h, prof, 0.0)
        out += (aa * prof).sum(axis=0)
    return out


class Plan:
    def __init__(self, wid, plan):
        self.w = WORLDS[wid]
        self.meas = []
        for m in plan:
            x = m["start"] + np.arange(m["n"]) * m["step"]
            xray = m["radiation"] == "xray"
            f = FLUX[m["optics"]] if xray else 1.0
            self.meas.append(dict(x=x, xray=xray, optics=m["optics"], t=m["t"], f=f,
                                  si=bool(m["si_standard"]) and xray, rad=m["radiation"]))
        self.has_x = any(m["xray"] for m in self.meas)
        self.has_n = any(not m["xray"] for m in self.meas)
        self.Ltrue = self.w["L_nm"]
        self.mu_T = self.truth()
        self.sw = 1.0 / np.sqrt(self.mu_T)

    def sigs(self, groups, s, z, L):
        """list over groups of concatenated sig over measurements (zero where wrong instrument handled by columns)."""
        res = []
        for g in groups:
            parts = []
            for m in self.meas:
                pos, amp = group_peaks(g, m["rad"], m["si"])
                parts.append(pattern(m["x"], pos, amp, m["optics"], s, z, L, m["xray"]))
            res.append(parts)
        return res

    def truth(self):
        w = self.w
        sg = self.sigs(w["truth_groups"], w["disp_mm"], w["zero_deg"], w["L_nm"])
        mus = []
        for i, m in enumerate(self.meas):
            sig = sum(sg[g][i] for g in range(len(sg)))
            xr = (m["x"] - 80.0) / 70.0
            if m["xray"]:
                mu = m["t"] * m["f"] * (w["A_xray"] * sig + w["b0"] + w["b1"] * xr)
            else:
                mu = m["t"] * (w["A_neutron"] * sig + w["bn0"] + w["bn1"] * xr)
            mus.append(mu)
        return np.concatenate(mus)

    def design(self, groups, s, z, L):
        sg = self.sigs(groups, s, z, L)
        cols = []
        for inst in ([True] if self.has_x else []) + ([False] if self.has_n else []):
            for g in range(len(groups)):
                cols.append(np.concatenate([m["t"] * m["f"] * sg[g][i] if m["xray"] == inst else np.zeros(m["x"].size)
                                            for i, m in enumerate(self.meas)]))
            tf = [m["t"] * m["f"] * np.ones(m["x"].size) if m["xray"] == inst else np.zeros(m["x"].size) for m in self.meas]
            sl = [m["t"] * m["f"] * (m["x"] - 80.0) / 70.0 if m["xray"] == inst else np.zeros(m["x"].size) for m in self.meas]
            cols.append(np.concatenate(tf))
            c = np.concatenate(sl)
            cols.append(c)
            cols.append(-c)
        return np.array(cols).T

    def chi2(self, groups, s, z, L):
        X = self.design(groups, s, z, L) * self.sw[:, None]
        y = self.mu_T * self.sw
        beta, rn = nnls(X, y, maxiter=2000)
        return rn * rn


def minimise_branch(P, groups, extra_starts=True):
    Lt = P.Ltrue
    if P.has_x:
        lo = np.array([S_BOX[0], Z_BOX[0], L_FRAC[0] * Lt])
        hi = np.array([S_BOX[1], Z_BOX[1], L_FRAC[1] * Lt])
    else:
        lo = np.array([L_FRAC[0] * Lt])
        hi = np.array([L_FRAC[1] * Lt])
    d = lo.size

    def phys(u):
        return lo + np.clip(u, 0, 1) * (hi - lo)

    cache = {}

    def f(u):
        u = np.clip(np.asarray(u, float), 0, 1)
        k = tuple(np.round(u, 12))
        if k in cache:
            return cache[k]
        p = phys(u)
        if P.has_x:
            v = P.chi2(groups, p[0], p[1], p[2])
        else:
            v = P.chi2(groups, 0.0, 0.0, p[0])
        cache[k] = v
        return v

    def tounit(p):
        return (np.asarray(p, float) - lo) / (hi - lo)

    cands = [np.full(d, 0.5)]
    sob = qmc.Sobol(d, scramble=True, seed=12345).random(256)
    cands += list(sob)
    if P.has_x:
        for s in [-0.15, -0.05, 0.05, 0.15, P.w["disp_mm"]]:
            cands.append(tounit([s, 0.0, Lt]))
        if extra_starts:
            cands.append(tounit([P.w["disp_mm"], P.w["zero_deg"], Lt]))
            for s in np.linspace(-0.2, 0.2, 9):
                for z in [-0.01, 0.0, 0.01]:
                    for L in [0.7 * Lt, Lt, 1.3 * Lt]:
                        cands.append(tounit([s, z, L]))
    else:
        cands.append(tounit([Lt]))
        if extra_starts:
            for L in np.linspace(0.7, 1.3, 13) * Lt:
                cands.append(tounit([L]))
    vals = np.array([f(c) for c in cands])
    order = np.argsort(vals)
    chosen = []
    for i in order:
        if all(np.linalg.norm(cands[i] - cands[j]) > 0.05 for j in chosen):
            chosen.append(i)
        if len(chosen) >= (12 if extra_starts else 8):
            break
    best_u, best_v = cands[order[0]], vals[order[0]]
    bounds = [(0, 1)] * d
    for i in chosen:
        r = minimize(f, cands[i], method="L-BFGS-B", bounds=bounds, options=dict(eps=1e-5, maxiter=500))
        if r.fun < best_v:
            best_u, best_v = np.clip(r.x, 0, 1), r.fun
    # polish
    for _ in range(20):
        prev = best_v
        r = minimize(f, best_u, method="Powell", bounds=bounds, options=dict(xtol=1e-6, ftol=1e-10, maxiter=4000))
        if r.fun < best_v:
            best_u, best_v = np.clip(r.x, 0, 1), r.fun
        r = minimize(f, best_u, method="L-BFGS-B", bounds=bounds, options=dict(eps=1e-5, maxiter=500))
        if r.fun < best_v:
            best_u, best_v = np.clip(r.x, 0, 1), r.fun
        if prev - best_v <= 1e-6 * max(abs(prev), 1e-300):
            break
    return float(best_v), phys(best_u).tolist()


def plan_D(args):
    wid, idx, plan = args
    t0 = time.time()
    P = Plan(wid, plan)
    best = None
    per = []
    for br in P.w["other_side"]:
        assert br["lo"] == [] and br["hi"] == []
        v, p = minimise_branch(P, br["groups_at_lo"])
        per.append(dict(label=br["label"], D=v, params=p))
        if best is None or v < best:
            best = v
    return wid, idx, best, per, time.time() - t0


def main():
    jobs = []
    for wid, plans in PLANS.items():
        for i, p in enumerate(plans):
            jobs.append((wid, i, p["plan"]))
    # dedupe identical plans per world
    keymap, uniq = {}, []
    for j in jobs:
        k = (j[0], json.dumps(j[2], sort_keys=True))
        if k not in keymap:
            keymap[k] = len(uniq)
            uniq.append(j)
    print("plans", len(jobs), "unique", len(uniq), flush=True)
    # heavy jobs first
    uniq_sorted = sorted(range(len(uniq)), key=lambda i: -sum(m["n"] for m in uniq[i][2]))
    res = {}
    with Pool(16) as pool:
        for n, out in enumerate(pool.imap_unordered(plan_D, [uniq[i] for i in uniq_sorted])):
            wid, idx, D, per, dt = out
            res[(wid, idx)] = (D, per)
            if n % 10 == 0:
                print(n, wid, idx, round(D, 4), round(dt, 1), flush=True)
    results = {}
    n_agree = 0
    disagree = []
    for j in jobs:
        wid, i, _ = j
        k = (wid, json.dumps(j[2], sort_keys=True))
        u = uniq[keymap[k]]
        D, per = res[(u[0], u[1])]
        ref = PLANS[wid][i]["D"]
        tol = max(0.01 * abs(ref), 0.05 if ref < 5 else 0.0)
        agree = abs(D - ref) <= tol
        n_agree += agree
        rec = dict(plan_index=i, D_shadow=D, D_reference=ref, agree=bool(agree),
                   rel_diff=(D - ref) / ref if ref else None,
                   direction=("agree" if agree else ("shadow_lower" if D < ref else "shadow_higher")),
                   branches=per)
        results.setdefault(wid, []).append(rec)
        if not agree:
            disagree.append((wid, i, D, ref))
    out = dict(n_plans=len(jobs), n_agree=int(n_agree),
               tolerance="1% relative, or 0.05 absolute where reference D < 5",
               disagreements=[dict(world=w, plan_index=i, D_shadow=d, D_reference=r,
                                   direction="shadow_lower" if d < r else "shadow_higher") for w, i, d, r in disagree],
               worlds=results)
    json.dump(out, open(os.path.join(HERE, "shadow_results.json"), "w"), indent=1)
    print("n_plans", len(jobs), "n_agree", n_agree)
    for d in disagree:
        print("DISAGREE", d)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "one":
        wid, i = sys.argv[2], int(sys.argv[3])
        print(plan_D((wid, i, PLANS[wid][i]["plan"])))
    else:
        main()
