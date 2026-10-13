"""Stage 2s plan costs and tuning constraints (V5_SPEC E.3, E.4). Truth only, no FM call.
  V5_2S_TUNE='{"47": {"N": 20}}' V5_2S_BUDGET='{"47": 70}' python -m mcenv.tune2s OUT.json SCENS [--procs 19] [--no-locdec]
Per scenario: c_dec (cheapest plan with planning D >= 40 in both worlds; alternatives' lattices free within +-1 %; continuous time by
homogeneity), c_loc (cheapest 60-degree survey with 2 sigma(lattice_scale) <= 1 % by the Cramer-Rao bound, all nuisances free) and the
default-scan survey, c_loc|dec (cheapest further plan counting the survey), c_pla (the plan a placebo-quality hypothesis chooses within
B, with its key D on each true world), budget B and the checks T1, T2, T2', T3 (46: control C1s)."""
import os
for _v in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ.setdefault(_v, '1')
import argparse, itertools, json, math, time
from multiprocessing import Pool
import numpy as np
from . import stage2s as S2S
from . import stage2 as S2
from . import scenarios as SC
from . import separation as SP
from . import physics as P

S2S.install()
TRUST = 0.01
D_PLAN = 40.0
RATIOS = (0.25, 0.5, 1.0, 2.0, 4.0)
PAIR_CFG = ((0.02, 'standard'), (0.04, 'standard'), (0.01, 'high_resolution'), (0.02, 'high_resolution'))
PAIR_CFG_FAST = ((0.02, 'standard'), (0.01, 'high_resolution'))
RATIOS_FAST = (0.5, 1.0, 2.0)
STEPS = (0.01, 0.02, 0.04)
OPTICS = ('standard', 'high_resolution')
STD_PREP = 10.0
CAP = 2000
T_MIN, T_MAX = 0.1, 20.0
N_GROUPS = 10
TIMES_1B = (0.5, 0.6, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.5, 15.0, 20.0)


# ---------------------------------------------------------------- hypotheses
def lat_free(br, centers=None, trust=TRUST):
    """br with every phase's lattice_scale free within +-trust around centers[name] (default 1) times the branch's own value."""
    c = centers or {}
    names = []
    for g in br.groups(br.lo if br.dim else []):
        for n, p, w in g:
            if n not in names: names.append(n)
    k = br.dim

    def groups(u, br=br, names=names, k=k):
        return [[(n, dict(p, lattice_scale=p.get('lattice_scale', 1.0) * u[k + names.index(n)]), w) for n, p, w in g] for g in br.groups(u[:k])]
    lo = list(br.lo) + [c.get(n, 1.0) * (1 - trust) for n in names]; hi = list(br.hi) + [c.get(n, 1.0) * (1 + trust) for n in names]
    return SC.Branch(groups, lo, hi, br.label + ' (lattices +-%g %%)' % (100 * trust))


def placebo_factor(name, p):
    """lattice factor of the placebo volume table for this phase (cube root of placebo over true volume; FM_CHECK method)."""
    st = P.PHASES[name].structure(p)
    return float((S2.placebo_volume(st) / st.volume) ** (1 / 3))


def scaled_groups(groups, fac):
    return [[(n, dict(p, lattice_scale=p.get('lattice_scale', 1.0) * fac[n]), w) for n, p, w in g] for g in groups]


def placebo_tr(world):
    tr = SP.world_truth(world)
    fac = {n: placebo_factor(n, p) for g in tr['groups'] for n, p, w in g}
    return dict(tr, groups=scaled_groups(tr['groups'], fac)), fac


def alts(world, centers=None):
    return [lat_free(br, centers) for br in SC.other_side(world)]


FAST = [False]          # search mode: a lighter minimiser for ranking plans; the chosen plan is re-evaluated at full precision (final())


def D_alts(tr, ms, alt, fast=None):
    mu = [SP.mu_truth(tr, m) for m in ms]; y = np.concatenate(mu); w = 1.0 / np.maximum(y, 1e-9)
    has_x = any(m.radiation == 'xray' for m in ms); best = np.inf
    fast = FAST[0] if fast is None else fast
    for br in alt:
        st = SP.default_starts(br, tr['L_nm'], has_x, tr['disp_mm'] if has_x else None)
        kw = dict(n_sobol=48, n_refine=3, polish=False) if fast else {}
        best = min(best, SP.fit_branch(ms, y, w, br, tr['L_nm'], st, **kw)[0])
    return float(best)


def final(best, trs, al, pre=(), budget=None):
    """full-precision D of the chosen plan against every target; without pre-measurements the times are rescaled exactly to D = 40
    (homogeneity), with them the last measurement's time is bisected again at full precision."""
    if best is None: return None
    pl = list(best[2])
    d = min(D_alts(tr, list(pre) + pl, a, fast=False) for tr, a in zip(trs, al))
    if not pre and not any(m.radiation == 'neutron' for m in pl):
        lam = D_PLAN / d
        if lam * max(m.t for m in pl) > T_MAX: return None
        lam = max(lam, T_MIN / min(m.t for m in pl)); pl = [with_t(m, m.t * lam) for m in pl]; d = d * lam
    elif d < D_PLAN:
        saved = FAST[0]; FAST[0] = False
        _W.clear(); _W.update(trs=trs, alts=al, pre=list(pre))
        r = _bisect((pl[-1], pl[:-1])); FAST[0] = saved
        if r is None: return None
        pl = list(r[2]); d = min(D_alts(tr, list(pre) + pl, a, fast=False) for tr, a in zip(trs, al))
    c = plan_cost(pl)
    if budget is not None and c > budget + 1e-9: return None
    return (c, d, tuple(pl))


# ---------------------------------------------------------------- plan grid (stage 2r grid, continuous time)
def windows(group_sets, L, widths):
    """stage 2r windows: peak groups of the hypotheses ranked by their high-resolution difference, top 10, widths around each, plus
    the two full ranges."""
    x = P.grid(5.0, 0.01, 14501)
    sigs = [sum(P.signal(x, grp, 'xray', 'high_resolution', L) for grp in gs) for gs in group_sets]
    diff = np.zeros_like(x)
    for a, b in itertools.combinations(sigs, 2): diff += (a - b) ** 2 / np.maximum(a + b, 1e-12)
    cents = []
    for gs in group_sets:
        for grp in gs:
            for n, p, w in grp:
                tt, I = P.peak_table(n, p, 'xray'); cents += list(tt[(I > 0.003 * I.max()) & (tt > 6) & (tt < 149)])
    cents = np.sort(np.array(cents)); groups = []
    for cc in cents:
        if groups and cc - groups[-1][-1] < 0.5: groups[-1].append(cc)
        else: groups.append([cc])
    centres = [float(np.mean(g)) for g in groups]
    score = [float(diff[(x > cc - 1) & (x < cc + 1)].sum()) for cc in centres]
    top = sorted(centres[i] for i in np.argsort(score)[::-1][:N_GROUPS])
    out = [(10.0, 70.0), (70.0, 149.96)]
    for cc in top:
        for wd in widths: out.append((round(cc - wd / 2, 2), round(cc + wd / 2, 2)))
    return out


def meas(lo, hi, step, t, opt, std):
    lo = max(P.TT_MIN, lo); hi = min(P.TT_MAX, hi)
    n = int(math.floor((hi - lo) / step + 1e-9)) + 1
    if n > CAP: return None
    return SP.Meas('xray', round(lo, 4), step, n, float(t), opt, std)


def configs(wins):
    return [(lo, hi, st, opt, std) for (lo, hi), st, opt, std in itertools.product(wins, STEPS, OPTICS, (False, True))
            if meas(lo, hi, st, 1.0, opt, std) is not None]


def plan_cost(ms): return sum(m.cost for m in ms) + (STD_PREP if any(m.si_standard for m in ms) else 0.0)


def with_t(m, t): return SP.Meas(m.radiation, m.start, m.step, m.n, float(t), m.optics, m.si_standard)


_W = {}
PROCS = [19]


def _ev(job):
    """job: (key, plan list of Meas) -> (key, [D per target]); targets and pre-measurements from _W (inherited by fork)."""
    key, ms = job
    pre = _W.get('pre', [])
    return key, [D_alts(tr, pre + list(ms), al) for tr, al in zip(_W['trs'], _W['alts'])]


def _bisect(job):
    """smallest t in [0.1, 20] with D >= 40 against every target (D monotone in t) for plan extra + [m(t)] on top of _W['pre']."""
    m, extra = job
    ev = lambda t: min(_ev(('b', list(extra) + [with_t(m, t)]))[1])
    if ev(T_MAX) < D_PLAN: return None
    lo, hi = math.log(T_MIN), math.log(T_MAX)
    if ev(T_MIN) >= D_PLAN: t = T_MIN
    else:
        for _ in range(7):
            mid = 0.5 * (lo + hi)
            if ev(math.exp(mid)) >= D_PLAN: hi = mid
            else: lo = mid
        t = math.exp(hi)
    pl = tuple(extra) + (with_t(m, t),)
    return (plan_cost(pl), None, pl)


def _pmap(f, jobs):
    if not jobs: return []
    with Pool(min(PROCS[0], len(jobs))) as pool: return pool.map(f, jobs, chunksize=1)


def search(trs, al, wins, budget=None, pre=(), wmid=4.0):
    """cheapest plan with D >= 40 against every (tr, alternatives) target. Without pre-measurements D is homogeneous in time:
    singles at t* = 40 / D(t = 1), pairs of the 30 cheapest singles at RATIOS scaled, the neutron pattern, and neutron + X-ray
    (bisection). With pre-measurements (c_loc|dec) every single's time is found by bisection, and pairs of the 15 cheapest at ratio 1."""
    _W.clear(); _W.update(trs=trs, alts=al, pre=list(pre)); wd_mid = [wmid]
    cf = configs(wins); base = [meas(*c[:2], c[2], 1.0, c[3], c[4]) for c in cf]
    rows = []
    if not pre:
        res = dict(_pmap(_ev, [(i, [m]) for i, m in enumerate(base)]))
        for i, m in enumerate(base):
            d1 = min(res[i])
            if d1 <= 0: continue
            t = D_PLAN / d1
            if t > T_MAX: continue
            t = max(t, T_MIN); mm = with_t(m, t); rows.append((plan_cost([mm]), d1 * t, (mm,)))
        cand = [r[2][0] for r in sorted(rows, key=lambda r: r[0])[:30]]
        # window pairs (X40): without m0 a window holding only superlattice or impurity peaks has D = 0 alone (scale free), so it never
        # enters the efficiency pool; every pair of windows at the scenario's middle width (and the full ranges) is tried as well
        mid = wd_mid[0]
        pw = [w for w in wins if w in ((10.0, 70.0), (70.0, 149.96)) or abs((w[1] - w[0]) - mid) < 1e-6]
        pool_r = [meas(lo, hi, st, 1.0, opt, False) for (lo, hi) in pw for st, opt in (PAIR_CFG_FAST if FAST[0] else PAIR_CFG)]
        pool_r = [m for m in pool_r if m is not None]
        seen, jobs = set(), []
        for a, b in list(itertools.combinations(cand, 2)) + list(itertools.combinations(pool_r, 2)):
            ka = (a.start, a.n, a.step, a.optics, a.si_standard); kb = (b.start, b.n, b.step, b.optics, b.si_standard)
            if ka == kb or (ka, kb) in seen or (kb, ka) in seen: continue
            seen.add((ka, kb))
            for r in (RATIOS_FAST if FAST[0] else RATIOS): jobs.append((len(jobs), [with_t(a, 1.0), with_t(b, r)]))
        res = dict(_pmap(_ev, jobs))
        for key, (a, b) in jobs:
            d1 = min(res[key])
            if d1 <= 0: continue
            lam = D_PLAN / d1
            if lam * max(a.t, b.t) > T_MAX: continue
            lam = max(lam, T_MIN / min(a.t, b.t)); pl = (with_t(a, lam * a.t), with_t(b, lam * b.t))
            rows.append((plan_cost(pl), d1 * lam, pl))
        nres = dict(_pmap(_ev, [('n', [SP.NEUTRON])]))
        if min(nres['n']) >= D_PLAN: rows.append((plan_cost([SP.NEUTRON]), min(nres['n']), (SP.NEUTRON,)))
        else:
            top = [r[2][0] for r in sorted([r for r in rows if len(r[2]) == 1], key=lambda r: r[0])[:10]]
            rows += [r for r in _pmap(_bisect, [(m, [SP.NEUTRON]) for m in top]) if r]
    else:
        sing = [r for r in _pmap(_bisect, [(m, []) for m in base]) if r]
        rows += sing
        cand = [r[2][0] for r in sorted(sing, key=lambda r: r[0])[:15]]
        pj = [(a, [b]) for a, b in itertools.combinations(cand, 2)]
        rows += [r for r in _pmap(_bisect, pj) if r]
    if budget is not None: rows = [r for r in rows if r[0] <= budget + 1e-9]
    best = min(rows, key=lambda r: (r[0], sum(m.n for m in r[2]))) if rows else None
    return best, rows


# ---------------------------------------------------------------- Cramer-Rao bound on lattice_scale
def crb_sigma(tr, m, h=None):
    """1 sigma of a common lattice_scale from one measurement, every nuisance free (scale, b0, b1, s, z, ln L), Fisher at the truth."""
    x = m.x; tf = m.t * m.flux; xl = (x - 80) / 70

    def sig(s, z, lnL, ls):
        return sum(P.signal(x, [(n, dict(p, lattice_scale=p.get('lattice_scale', 1.0) * ls), w) for n, p, w in g], 'xray', m.optics,
                            math.exp(lnL), s, z, m.si_standard) for g in tr['groups'])
    th0 = np.array([tr['disp_mm'], tr['zero_deg'], math.log(tr['L_nm']), 1.0])
    hs = h or [1e-3, 1e-4, 1e-3, 1e-5]
    s0 = sig(*th0)
    mu = tf * (tr['A'] * s0 + tr['b0'] + tr['b1'] * xl)
    J = [tf * s0, tf * np.ones_like(x), tf * xl]
    for k in range(4):
        a = th0.copy(); b = th0.copy(); a[k] += hs[k]; b[k] -= hs[k]
        J.append(tf * tr['A'] * (sig(*a) - sig(*b)) / (2 * hs[k]))
    J = np.array(J)
    F = (J / np.maximum(mu, 1e-9)) @ J.T
    try: C = np.linalg.inv(F)
    except np.linalg.LinAlgError: return float('inf')
    return float(math.sqrt(max(C[-1, -1], 0.0)))


def c_loc(worlds):
    out = []
    trs = [SP.world_truth(w) for w in worlds]
    for a in range(5, 95, 5):
        m = SP.Meas('xray', float(a), 0.04, 1501, 1.0, 'standard', False)
        sg = [crb_sigma(tr, m) for tr in trs]
        t = max((2 * s / 0.01) ** 2 for s in sg)                 # sigma ~ t^-1/2
        if t > T_MAX: out.append(dict(start=a, sigma_t1=sg, feasible=False)); continue
        t = max(t, T_MIN); mm = with_t(m, t)
        out.append(dict(start=a, sigma_t1=[round(s, 6) for s in sg], t=round(t, 4), cost=round(plan_cost([mm]), 3), feasible=True,
                        two_sigma=[round(2 * s / math.sqrt(t), 6) for s in sg], meas=mm.key()))
    feas = [r for r in out if r['feasible']]
    best = min(feas, key=lambda r: r['cost']) if feas else None
    dsg = [crb_sigma(tr, SP.DEFAULT) for tr in trs]
    return best, out, dict(cost=round(plan_cost([SP.DEFAULT]), 3), two_sigma=[round(2 * s, 6) for s in dsg])


# ---------------------------------------------------------------- report
def fmt(r, trs=None):
    if r is None: return None
    return dict(cost=round(r[0], 3), D=None if r[1] is None else round(r[1], 3), plan=[m.key() for m in r[2]])


def scen_report(s, locdec=True):
    t0 = time.time(); ws = SC.twins(s); d = SC.SCEN[s]; B = d['budget']; wd = d['widths']
    trs = [SP.world_truth(w) for w in ws]; al = [alts(w) for w in ws]
    wins = windows([tr['groups'] for tr in trs], trs[0]['L_nm'], wd)
    wmid = sorted(wd)[len(wd) // 2]
    dec, _ = search(trs, al, wins, wmid=wmid); dec = final(dec, trs, al)
    out = dict(scen=s, tune=SC.TUNE[s], budget=B, widths=list(wd), worlds=ws, c_dec=fmt(dec))
    if dec:
        out['c_dec']['D_pl_per_world'] = [round(D_alts(tr, list(dec[2]), a), 3) for tr, a in zip(trs, al)]
        out['c_dec']['D_key_per_world'] = [round(SP.separation(w, list(dec[2])), 3) for w in ws]
    best_loc, all_loc, dflt = c_loc(ws)
    out['c_loc'] = best_loc; out['default_survey'] = dflt
    out['default_survey']['D_key_per_world'] = [round(SP.separation(w, [SP.DEFAULT]), 3) for w in ws]
    if locdec and best_loc and dec:
        sv = SP.meas_from(best_loc['meas'])
        ld, _ = search(trs, al, wins, pre=[sv], wmid=wmid); ld = final(ld, trs, al, pre=[sv])
        out['c_loc_dec'] = fmt(ld); out['survey_D_pl'] = [round(D_alts(tr, [sv], a), 3) for tr, a in zip(trs, al)]
    # placebo-quality planning
    pts = [placebo_tr(w) for w in ws]
    ptrs = [p[0] for p in pts]; facs = [p[1] for p in pts]
    pal = [alts(w, centers=f) for w, f in zip(ws, facs)]
    pwins = windows([tr['groups'] for tr in ptrs], trs[0]['L_nm'], wd)
    pla, prow = search(ptrs, pal, pwins, budget=B, wmid=wmid); pla = final(pla, ptrs, pal, budget=B)
    out['placebo_factor'] = [{n: round(v, 5) for n, v in f.items()} for f in facs]
    out['c_pla'] = fmt(pla)
    if pla: out['c_pla']['D_key_true'] = [round(SP.separation(w, list(pla[2])), 3) for w in ws]
    out['checks'] = checks(out)
    out['sec'] = round(time.time() - t0)
    return out


def checks(r):
    s = r['scen']; B = r['budget']; C = {}
    cd = r['c_dec']['cost'] if r['c_dec'] else None
    if s == S2S.CONTROL:
        C['C1s'] = all(D >= 25 for D in r['default_survey']['D_key_per_world'])
        return C
    cl = r['c_loc']['cost'] if r['c_loc'] else None
    C['T1'] = cd is not None and 1.2 * cd - 1e-6 <= B <= 1.3 * cd + 1e-6
    C['T2'] = cd is not None and cl is not None and cl + cd > B
    if 'c_loc_dec' in r: C['T2p'] = cl is not None and (r['c_loc_dec'] is None or cl + r['c_loc_dec']['cost'] > B)
    C['T3'] = r['c_pla'] is None or all(D < 9 for D in r['c_pla']['D_key_true'])
    return C


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('scens'); ap.add_argument('--procs', type=int, default=19)
    ap.add_argument('--no-locdec', action='store_true'); ap.add_argument('--fast', action='store_true')
    a = ap.parse_args(); scens = [int(x) for x in a.scens.split(',')]
    res = dict(env={k: os.environ.get(k) for k in ('V5_2S_TUNE', 'V5_2S_BUDGET', 'V5_2S_WIDTHS')}, fast=a.fast, scen={})
    PROCS[0] = a.procs; FAST[0] = a.fast
    for s in scens:
        res['scen'][s] = scen_report(s, not a.no_locdec); print(json.dumps(res['scen'][s]), flush=True)
        json.dump(res, open(a.out, 'w'), indent=1)


if __name__ == '__main__':
    main()
