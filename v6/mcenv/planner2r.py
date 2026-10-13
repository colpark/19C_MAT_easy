"""Stage 2r gate planner (V5_SPEC D.6). Plays episodes through the stage 2r server code path; it sees only what the arm's tools return.
1. builds the claim-side and other-side hypotheses from prototypes and relaxes them with the arm's relax;
2. refines lattice_scale of each hypothesis on m0 within +-5 % of the relaxed value (crystallite size and nuisances free);
3. plans the cheapest grid plan (v5 grid: windows on its own hypotheses' peak groups and the full ranges, steps, optics, standard,
   v5 times, neutron; singles and pairs of the 30 most efficient singles) with D >= 40 in both directions, D computed by
   mcenv/separation.py with its own hypothesis substituted for the truth (scale and background from its m0 fit) and the other side's
   hypothesis family as the alternatives (lattice_scale free within +-1 % of the refined value; impurity lattices +-2 % of relaxed);
4. measures and reads by likelihood ratio with the same freedom.
  MCENV_STATE=... python -m mcenv.planner2r OUT_TOKENS.txt ARMS KS [SCENS]"""
import itertools, json, math, os, sys
for _v in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ.setdefault(_v, '1')
import numpy as np
from pymatgen.core import Composition, Element, Structure
from . import server2r as S2RS          # installs stage 2r, extends the server
from . import server2 as S2S
from . import server as S
from . import scenarios as SC
from . import separation as SP
from . import plangrid as PG
from . import physics as P
from . import stage2 as S2
from . import stage2r as S2R
from . import admin as A

D_PLAN = 40.0
REFINE = 0.05            # +-5 % lattice refinement on m0
TRUST = 0.01             # +-1 % around the refined lattice in planning and reading
IMP_TRUST = 0.02         # impurity lattice +-2 % around relaxed
V5_TIMES = (0.5, 2.0, 5.0, 10.0, 20.0)


def call(tok, tool, **a): return S.call(tok, tool, a)[0]


def relaxed(tok, proto, sites, params=None):
    b = call(tok, 'build', prototype=proto, sites=sites, params=params or {})
    r = call(tok, 'relax', structure_id=b['structure_id'])
    rec = S2S._structs(S.get_episode(tok))[r['structure_id']]
    return rec['phase'], Structure.from_dict(rec['structure'])


def abx(formula):
    """A = the larger cation (12-coordinated site), B = the other, X = the anion."""
    c = Composition(formula); els = [e.symbol for e in c.elements]
    X = [e for e in els if not Element(e).is_metal and e not in ('B', 'Si', 'Ge', 'As', 'Sb', 'Te')] or [els[-1]]
    X = max(X, key=lambda e: Element(e).X)
    cat = sorted([e for e in els if e != X], key=lambda e: -(Element(e).atomic_radius or 0))
    return dict(A=cat[0], B=cat[1], X=X)


def build_params(proto):
    return dict(dz_B=0.02, dz_X=0.02, c_over_a=1.01) if proto == 'tetragonal perovskite' else {}


# ---------------------------------------------------------------- step 2: refinement on m0
def _chi2_fixed(meas, y, groups, L):
    Xd, _, _ = SP._design(meas, groups, 0.0, 0.0, L)
    return SP._lin_solve(Xd, y, 1.0 / np.maximum(y, 1.0))[0]


def refine(meas, y, groups_at, L0=100.0):
    """groups_at(ls) -> groups. Coarse scan of ls in [1-REFINE, 1+REFINE] (s = z = 0), the 5 best local minima refined with all
    nuisances free. Returns (ls, chi2, theta)."""
    grid = np.linspace(1 - REFINE, 1 + REFINE, 201)
    c = np.array([_chi2_fixed(meas, y, groups_at(g), L0) for g in grid])
    loc = [i for i in range(len(c)) if (i == 0 or c[i] <= c[i - 1]) and (i == len(c) - 1 or c[i] <= c[i + 1])]
    loc = sorted(loc, key=lambda i: c[i])[:5]
    w0 = 1.0 / np.maximum(y, 1.0)
    base = SP.fit_branch(meas, y, w0, SC.Branch(lambda u: groups_at(1.0), [], []), L0, L_bounds=(20.0, 1000.0), n_sobol=32, n_refine=3)
    best = (np.inf, None, None)
    for i in loc:
        lo, hi = max(1 - REFINE, grid[i] - 0.002), min(1 + REFINE, grid[i] + 0.002)
        br = SC.Branch(lambda u: groups_at(u[0]), [lo], [hi])
        w = 1.0 / np.maximum(y, 1.0)
        chi, th = SP.fit_branch(meas, y, w, br, L0, L_bounds=(20.0, 1000.0), n_sobol=32, n_refine=3)
        if chi < best[0]: best = (chi, th['u'][0], th)
    if best[0] > base[0] - 25.0:                # significance gate (V5-E15): keep the relaxed lattice unless m0 prefers another by dchi2 >= 25
        return 1.0, base[0], base[1]
    return best[1], best[0], best[2]


# ---------------------------------------------------------------- step 1-2: hypotheses
def hypotheses(tok, scen):
    """returns dict(claim=[Branch], other=[Branch], pseudo=(claim groups, other groups), info) after relax and refinement on m0."""
    d = SC.SCEN[scen]; ep = S.get_episode(tok)
    m0 = [SP.DEFAULT]; y0 = ep.counts('m0')
    fam = lambda groups_fn, lo, hi, lab='': SC.Branch(groups_fn, lo, hi, lab)
    info = {}
    if scen in (41, 42):
        names = []
        for p in d['protos']:
            pr = S2R.PROTO_NAME[p]; ph, st = relaxed(tok, pr, abx(d['composition']), build_params(pr)); names.append((p, ph))
        refined = {}
        for p, ph in names:
            ls, chi, th = refine(m0, y0, lambda g, ph=ph: [[(ph, {'lattice_scale': g}, 1.0)]]); refined[p] = (ph, ls, th); info[p] = dict(ls=ls, chi2=chi)
        # the claim's first-named structure is the claim side (claim text: "has the X structure rather than the Y structure")
        cl_name = d['claim'].split('has the ')[1].split(' structure rather')[0]
        cl = [p for p, _ in names if S2R.PROTO_NAME[p] == cl_name][0]; ot = [p for p, _ in names if p != cl][0]
        def side(p):
            ph, ls, _ = refined[p]
            return [fam(lambda u, ph=ph: [[(ph, {'lattice_scale': u[0]}, 1.0)]], [ls - TRUST], [ls + TRUST])]
        claim, other = side(cl), side(ot)
        pc = [[(refined[cl][0], {'lattice_scale': refined[cl][1]}, 1.0)]]; po = [[(refined[ot][0], {'lattice_scale': refined[ot][1]}, 1.0)]]
        th = refined[cl][2]
    elif scen == 43:
        pm_name = S2R.PROTO_NAME[d['main_proto']]
        phM, _ = relaxed(tok, pm_name, abx(d['composition']), build_params(pm_name))
        lsM, chi, th = refine(m0, y0, lambda g: [[(phM, {'lattice_scale': g}, 1.0)]]); info['main'] = dict(ls=lsM, chi2=chi)
        imps = []
        for fi, pi in zip(d['impurity_formulas'], d['impurity_protos']):
            c = Composition(fi); els = [e.symbol for e in c.elements]; X = 'O' if 'O' in els else els[-1]; Aa = [e for e in els if e != X][0]
            ph, _ = relaxed(tok, S2R.PROTO_NAME[pi], dict(A=Aa, X=X)); imps.append(ph)
        def side(ph):
            return [fam(lambda u, ph=ph: [[(phM, {'lattice_scale': lsM}, 1 - u[0]), (ph, {'lattice_scale': u[1]}, u[0])]],
                        [S2R.IMP_LO, 1 - IMP_TRUST], [S2R.IMP_HI, 1 + IMP_TRUST])]
        claim, other = side(imps[0]), side(imps[1])
        pc = [[(phM, {'lattice_scale': lsM}, 1 - S2R.IMP_LO), (imps[0], {'lattice_scale': 1.0}, S2R.IMP_LO)]]
        po = [[(phM, {'lattice_scale': lsM}, 1 - S2R.IMP_LO), (imps[1], {'lattice_scale': 1.0}, S2R.IMP_LO)]]
    elif scen in (44, 45):
        Aa, Bb = d['A'], d['B']
        if scen == 44:
            phO, sO = relaxed(tok, 'L1_2', dict(A=Aa, B=Bb), dict(S=1.0))
            pl = S2.register_l12(f'plan:{tok[:8]}:ord', Aa, Bb, sO.lattice.a)
        else:
            phO, sO = relaxed(tok, 'B2', dict(A=Aa, B=Bb))
            pl = S2R.register_b2_order(f'plan:{tok[:8]}:ord', Aa, Bb, sO.lattice.a)
        ls, chi, th = refine(m0, y0, lambda g: [[(pl, {'S': 1.0, 'lattice_scale': g}, 1.0)]]); info['ord'] = dict(ls=ls, chi2=chi)
        Sf = lambda lo, hi: fam(lambda u: [[(pl, {'S': u[0], 'lattice_scale': u[1]}, 1.0)]], [lo, ls - TRUST], [hi, ls + TRUST])
        ordered_claim = 'above 0.3' in d['claim']
        ordS, disS = [Sf(0.3, 1.0)], [Sf(0.0, 0.3)]
        claim, other = (ordS, disS) if ordered_claim else (disS, ordS)
        po_ord = [[(pl, {'S': 0.65, 'lattice_scale': ls}, 1.0)]]; po_dis = [[(pl, {'S': 0.0, 'lattice_scale': ls}, 1.0)]]
        pc, po = (po_ord, po_dis) if ordered_claim else (po_dis, po_ord)
    else:
        raise ValueError(scen)
    ng = th['ng']; coef = th['coef']
    Nn = SC.TUNE[scen]['Nn']                          # the manual's neutron count statement (counts at the strongest peak)
    sn = sum(P.signal(SP.NEUTRON.x, g, 'neutron', 'neutron', th['L_nm']) for g in pc)
    L = float(np.clip(th['L_nm'], 20, 1000))
    # size prior when m0 cannot tell (V5-E15): L = 100 nm unless m0 prefers another size by dchi2 >= 9
    br0 = SC.Branch(lambda u: pc, [], [])
    c100 = SP.fit_branch(m0, y0, 1.0 / np.maximum(y0, 1.0), br0, 100.0, L_bounds=(100.0, 100.0), n_sobol=16, n_refine=2)[0]
    cfree = SP.fit_branch(m0, y0, 1.0 / np.maximum(y0, 1.0), br0, 100.0, L_bounds=(20.0, 1000.0), n_sobol=16, n_refine=2)[0]
    if c100 - cfree < 9.0: L = 100.0
    info['L_fit'] = float(th['L_nm']); info['L_used'] = L
    sx = sum(P.signal(SP.DEFAULT.x, g, 'xray', 'standard', L) for g in pc)          # the manual's count statement fixes the scale (V5-E15)
    return dict(An=Nn / (SP.NEUTRON.t * max(sn.max(), 1e-12)), bgn=Nn / 20.0, claim=claim, other=other, pseudo=(pc, po), L=L,
                A=SC.TUNE[scen]['N'] / (SP.DEFAULT.t * max(sx.max(), 1e-12)), A_fit=float(sum(coef[:ng - 3])), b0=float(coef[ng - 3]),
                b1=float(coef[ng - 2] - coef[ng - 1]), info=info)


# ---------------------------------------------------------------- step 3: planning with separation.py
_CTX = {}


def _pseudo_tr(groups):
    c = _CTX
    return dict(groups=groups, A=c['A'], An=c['An'], b0=c['b0'], b1=c['b1'], bn0=c['bgn'], bn1=SP.BG_SLOPE * c['bgn'], disp_mm=0.0, zero_deg=0.0, L_nm=c['L'])


def _D_dir(ms, groups, alts):
    tr = _pseudo_tr(groups)
    y = np.concatenate([SP.mu_truth(tr, m) for m in ms]); w = 1.0 / np.maximum(y, 1e-9)
    has_x = any(m.radiation == 'xray' for m in ms)
    best = np.inf
    for br in alts:
        st = SP.default_starts(br, _CTX['L'], has_x)
        best = min(best, SP.fit_branch(ms, y, w, br, _CTX['L'], st, n_sobol=64, n_refine=4)[0])
    return best


def D_both(plan):
    c = _CTX; ms = [SP.DEFAULT] + list(plan)
    return min(_D_dir(ms, c['pc'], c['other']), _D_dir(ms, c['po'], c['claim']))


def windows(pc, po, L):
    x = P.grid(5.0, 0.01, 14501)
    sig = lambda g: sum(P.signal(x, grp, 'xray', 'high_resolution', L) for grp in g)
    a, b = sig(pc), sig(po); diff = (a - b) ** 2 / np.maximum(a + b, 1e-12)
    cents = []
    for g in (pc, po):
        for grp in g:
            for n, p, w in grp:
                tt, I = P.peak_table(n, p, 'xray'); cents += list(tt[(I > 0.003 * I.max()) & (tt > 6) & (tt < 149)])
    cents = np.sort(np.array(cents)); groups = []
    for cc in cents:
        if groups and cc - groups[-1][-1] < 0.5: groups[-1].append(cc)
        else: groups.append([cc])
    centres = [float(np.mean(g)) for g in groups]
    score = [float(diff[(x > cc - 1) & (x < cc + 1)].sum()) for cc in centres]
    top = sorted(centres[i] for i in np.argsort(score)[::-1][:PG.N_GROUPS])
    out = [(10.0, 70.0), (70.0, 149.96)]
    for cc in top:
        for wd in PG.WIDTHS: out.append((round(cc - wd / 2, 2), round(cc + wd / 2, 2)))
    return out


def _scan_cfg(cfg):
    lo, hi, step, opt, std = cfg
    ms = [PG.window_meas(lo, hi, step, t, opt, std) for t in V5_TIMES]
    ms = [m for m in ms if m is not None and PG.plan_cost([m]) <= PG.BUDGET]
    if not ms: return []
    rows = {}
    def ev(i):
        if i not in rows: rows[i] = D_both([ms[i]])
        return rows[i]
    if ev(len(ms) - 1) >= D_PLAN:
        a, b = -1, len(ms) - 1
        while b - a > 1:
            mid = (a + b) // 2
            if ev(mid) >= D_PLAN: b = mid
            else: a = mid
    return [(PG.plan_cost([ms[i]]), D, (ms[i],)) for i, D in sorted(rows.items())]


def plan_for(H, scen, procs=18):
    from multiprocessing import Pool
    _CTX.update(pc=H['pseudo'][0], po=H['pseudo'][1], claim=H['claim'], other=H['other'], L=H['L'], A=H['A'], b0=H['b0'], b1=H['b1'],
                An=H['An'], bgn=H['bgn'] / SP.NEUTRON.t)
    cfgs = [(lo, hi, st, opt, std) for (lo, hi), st, opt, std in itertools.product(windows(H['pseudo'][0], H['pseudo'][1], H['L']), PG.STEPS, PG.OPTICS, (False, True))
            if PG.window_meas(lo, hi, st, 1.0, opt, std) is not None]
    with Pool(procs) as pool:
        singles = [r for rr in pool.map(_scan_cfg, cfgs, chunksize=2) for r in rr]
        singles.append((PG.plan_cost([SP.NEUTRON]), D_both([SP.NEUTRON]), (SP.NEUTRON,)))
        cand = sorted([r for r in singles if r[0] > 0], key=lambda r: -r[1] / r[0])[:30]
        combos = [p1 + p2 for (c1, d1, p1), (c2, d2, p2) in itertools.combinations(cand, 2) if PG.plan_cost(p1 + p2) <= PG.BUDGET and p1[0] != p2[0]]
        ds = pool.map(D_both, combos, chunksize=2)
    rows = singles + [(PG.plan_cost(ms), D, ms) for ms, D in zip(combos, ds)]
    ok = [r for r in rows if r[1] >= D_PLAN]
    best = min(ok, key=lambda r: (r[0], sum(m.n for m in r[2]))) if ok else None
    return (None if best is None else list(best[2])), dict(n_rows=len(rows), best_D=max(r[1] for r in rows), chosen_D=best and best[1])


# ---------------------------------------------------------------- step 4: reading
def _fit_side(meas, y, side, L0):
    best = np.inf
    for br in side:
        w = 1.0 / np.maximum(y, 1.0)
        c, th = SP.fit_branch(meas, y, w, br, L0, n_sobol=64, n_refine=4)            # size within +-30 % of the planner's estimate, as in planning (V5-E16)
        mu = SP._model(meas, br, th); w = 1.0 / np.maximum(mu, 1.0)
        c, th = SP.fit_branch(meas, y, w, br, L0, n_sobol=64, n_refine=4)
        best = min(best, c)
    return best


def _measure(tok, m):
    if m.radiation == 'neutron': return call(tok, 'measure', radiation='neutron')
    return call(tok, 'measure', start=m.start, stop=round(m.start + m.step * (m.n - 1), 6), step=m.step, time_per_step=m.t, optics=m.optics,
                si_standard=m.si_standard)


def play(tok, scen, plan):
    H = hypotheses(tok, scen); ep = S.get_episode(tok)
    if plan is None:
        call(tok, 'answer', verdict='CANNOT_TELL', region='', rationale='no affordable plan separates my hypotheses'); return
    for m in plan: _measure(tok, m)
    ms = [SP.meas_from(r['spec']) for r in ep.state['measurements']]; ys = np.concatenate([ep.counts(r['id']) for r in ep.state['measurements']])
    cc = _fit_side(ms, ys, H['claim'], H['L']); co = _fit_side(ms, ys, H['other'], H['L'])
    m = plan[-1]
    reg = '5.00-150.00' if m.radiation == 'neutron' else f'{m.start:.2f}-{m.start + m.step * (m.n - 1):.2f}'
    call(tok, 'answer', verdict='SUPPORTED' if cc < co else 'REFUTED', region=reg, rationale=f'chi2 claim {cc:.1f} other {co:.1f}')


def _play_job(args):
    tok, scen, keys = args
    try: play(tok, scen, None if keys is None else [SP.meas_from(k) for k in keys]); return tok, None
    except Exception:
        import traceback; return tok, traceback.format_exc()[-1200:]


def main():
    """phase 1: per (scenario, arm) a planning episode (batch v5-10-plan, not graded) builds, relaxes and refines its hypotheses on its
    m0 and computes the plan; phase 2: every gate episode (batch v5-10-gate) rebuilds its own hypotheses and plays that plan."""
    out, arms, ks = sys.argv[1], sys.argv[2].split(','), [int(k) for k in sys.argv[3].split(',')]
    scens = [int(s) for s in (sys.argv[4].split(',') if len(sys.argv) > 4 else '41,42,43,44,45'.split(','))]
    batch = os.environ.get('V5_GATE_BATCH', 'v5-10-gate')
    pp = out + '.plans.json'
    plans = json.load(open(pp)) if os.path.exists(pp) else {}
    for s in scens:
        for arm in arms:
            if f'{s}|{arm}' in plans: continue
            tok = A._register([dict(world=SC.twins(s)[0], arm=arm, k=1, model='scripted:planner2r', batch=batch + '-plan')])[0]
            H = hypotheses(tok, s)
            plan, meta = plan_for(H, s)
            plans[f'{s}|{arm}'] = dict(plan=None if plan is None else [m.key() for m in plan], meta=meta, info=H['info'], L=H['L'])
            json.dump(plans, open(pp, 'w'), indent=1)
            print('plan', s, arm, json.dumps(plans[f'{s}|{arm}']), flush=True)
    items = [dict(world=w, arm=arm, k=k, model='scripted:planner2r', batch=batch) for arm in arms for s in scens for w in SC.twins(s) for k in ks]
    toks = A._register(items)
    jobs = [(t, SC.WORLD_SCEN[it['world']], plans[f"{SC.WORLD_SCEN[it['world']]}|{it['arm']}"]['plan']) for it, t in zip(items, toks)]
    from multiprocessing import Pool
    with Pool(int(os.environ.get('V5_PROCS', '16'))) as pool, open(out, 'a') as f:
        for tok, err in pool.imap_unordered(_play_job, jobs):
            f.write(tok + '\n'); f.flush()
            if err: print('ERROR', tok[:8], err, flush=True)


if __name__ == '__main__':
    main()
