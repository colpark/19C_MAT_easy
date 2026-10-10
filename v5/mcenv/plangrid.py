"""Plan grid and oracle search (V5_SPEC 3.4).

Windows: peak groups of the scenario's twin and other-side structures (X-ray), ranked by the twin difference they carry, top 10 groups,
windows of 2, 4, 6 deg centred on each, plus the full ranges 10-70 and 70-150 (point cap 2000). Steps 0.01, 0.02, 0.04; times 0.5, 2,
5, 10, 20 s; standard and high-resolution optics; Si standard off and on; plus the neutron pattern. A plan = m0 plus one or two grid
measurements; the Si standard's 10 min preparation is charged once."""
import itertools, math
import numpy as np
from . import physics as P
from . import scenarios as SC
from .separation import Meas, DEFAULT, NEUTRON, separation, world_truth, mu_truth

STEPS = (0.01, 0.02, 0.04)
TIMES = (0.5, 2.0, 5.0, 10.0, 20.0)
OPTICS = ('standard', 'high_resolution')
WIDTHS = (2.0, 4.0, 6.0)
N_GROUPS = 10
STD_PREP = 10.0
BUDGET = 180.0
CAP = 2000


def window_meas(lo, hi, step, t, optics, std):
    lo = max(P.TT_MIN, lo); hi = min(P.TT_MAX, hi)
    n = int(math.floor((hi - lo) / step + 1e-9)) + 1
    if n > CAP: return None
    return Meas('xray', round(lo, 4), step, n, t, optics, std)


def peak_groups(scen):
    """centres of X-ray peak groups (within 0.5 deg) ranked by twin difference on a fine reference scan."""
    ws = SC.twins(scen)
    trs = [world_truth(w) for w in ws]
    x = P.grid(5.0, 0.01, 14501)
    ref = Meas('xray', 5.0, 0.01, 14501, 1.0, 'high_resolution', False)
    mus = [mu_truth(tr, ref) for tr in trs]
    diff = np.zeros_like(x)
    for a, b in itertools.combinations(mus, 2): diff += (a - b) ** 2 / np.maximum(a, 1e-9)
    # candidate centres: peaks of every phase in the twins and sides
    cents = []
    for tr in trs:
        for g in tr['groups']:
            for name, p, wgt in g:
                tt, I = P.peak_table(name, p, 'xray')
                cents += list(tt[(I > 0.003 * I.max()) & (tt > 6) & (tt < 149)])
    cents = np.sort(np.array(cents))
    groups = []
    for c in cents:
        if groups and c - groups[-1][-1] < 0.5: groups[-1].append(c)
        else: groups.append([c])
    centres = [float(np.mean(g)) for g in groups]
    score = [float(diff[(x > c - 1) & (x < c + 1)].sum()) for c in centres]
    order = np.argsort(score)[::-1][:N_GROUPS]
    return sorted(centres[i] for i in order)


def windows(scen):
    out = [(10.0, 70.0), (70.0, 149.96)]
    for c in peak_groups(scen):
        for w in WIDTHS: out.append((round(c - w / 2, 2), round(c + w / 2, 2)))
    return out


def singles(scen):
    out = []
    for (lo, hi), step, opt, std in itertools.product(windows(scen), STEPS, OPTICS, (False, True)):
        for t in TIMES:
            m = window_meas(lo, hi, step, t, opt, std)
            if m is not None: out.append(m)
    out.append(NEUTRON)
    return out


def plan_cost(ms):
    return sum(m.cost for m in ms) + (STD_PREP if any(m.si_standard for m in ms) else 0.0)


def d_plan(world, ms, tr=None): return separation(world, [DEFAULT] + list(ms), tr)


def configs(scen):
    """(window, step, optics, std) configurations; each expands over TIMES."""
    out = []
    for (lo, hi), step, opt, std in itertools.product(windows(scen), STEPS, OPTICS, (False, True)):
        if window_meas(lo, hi, step, 1.0, opt, std) is not None: out.append((lo, hi, step, opt, std))
    return out


def _scan_config(world, cfg, max_cost, thr):
    """times affordable for this config, D at the largest one, and the cheapest decisive time by bisection (D monotone in t)."""
    lo, hi, step, opt, std = cfg
    ms = [window_meas(lo, hi, step, t, opt, std) for t in TIMES]
    ms = [m for m in ms if plan_cost([m]) <= max_cost]
    if not ms: return []
    rows = {}
    def ev(i):
        if i not in rows: rows[i] = d_plan(world, [ms[i]])
        return rows[i]
    if ev(len(ms) - 1) >= thr:
        a, b = -1, len(ms) - 1                      # invariant: D(b) >= thr, D(a) < thr (a = -1 means none tested)
        while b - a > 1:
            mid = (a + b) // 2
            if ev(mid) >= thr: b = mid
            else: a = mid
    return [(plan_cost([ms[i]]), D, (ms[i],)) for i, D in sorted(rows.items())]


def scan_world(world, pairs=True, pair_pool=30, max_cost=BUDGET, thr=25.0, pool=None, cfgs=None):
    """D over the plan grid: every config at its largest affordable time plus the bisection points, the neutron plan, and pairs.
    Returns rows (cost, D, plan)."""
    scen = SC.WORLD_SCEN[world]
    cfgs = cfgs if cfgs is not None else configs(scen)
    rows = [(0.0, d_plan(world, []), ())]
    args = [(world, c, max_cost, thr) for c in cfgs]
    res = pool.starmap(_scan_config, args, chunksize=4) if pool else [_scan_config(*a) for a in args]
    singles_rows = [r for rr in res for r in rr]
    if plan_cost([NEUTRON]) <= max_cost: singles_rows.append((plan_cost([NEUTRON]), d_plan(world, [NEUTRON]), (NEUTRON,)))
    rows += singles_rows
    if pairs:
        cand = sorted(singles_rows, key=lambda r: -r[1] / r[0])[:pair_pool]
        combos = [(p1 + p2) for (c1, d1, p1), (c2, d2, p2) in itertools.combinations(cand, 2)
                  if plan_cost(p1 + p2) <= max_cost and p1[0] != p2[0]]
        ds = pool.starmap(d_plan, [(world, ms) for ms in combos], chunksize=4) if pool else [d_plan(world, ms) for ms in combos]
        rows += [(plan_cost(ms), D, ms) for ms, D in zip(combos, ds)]
    return rows


def cheapest(rows, thr=25.0):
    ok = [r for r in rows if r[1] >= thr]
    return min(ok, key=lambda r: (r[0], sum(m.n for m in r[2]))) if ok else None


def best_affordable(rows, max_cost=BUDGET, pred=None):
    ok = [r for r in rows if r[0] <= max_cost and (pred is None or all(pred(m) for m in r[2]))]
    return max(ok, key=lambda r: r[1]) if ok else None
