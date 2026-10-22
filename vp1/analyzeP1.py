"""vP.1 analysis (PREREG.md, VP1-4), on analyzeF's and analyzeG's frozen functions (imported unchanged) and the kit's crossfit.py.
Conventions as v7: evidence key first (evidence7.py), registered key beside it (B1: a truth verdict with D >= 25; H and T: grade7
'resolved'); bootstrap 10,000 with seed 20261019, compounds resampled within strata (B1 K/E, H M/E, T K/E), then seeds within compound,
paired on the (compound, seed) cells both sides hold; exact two-sided sign test on per-compound gaps. Every contrast is reported as
offline (or manipulated) minus online (or fm). Family-weighted pooled estimates give each family the same weight: the pooled gap is the
mean of the family gaps, and its interval comes from the per-family bootstrap draws (same seed per family as the per-family contrast),
averaged draw by draw.
Inputs: v7's graded records (frozen; host A ~/Documents/harbor/v7/v7/runs/F/graded and v6's runs/bench/v6_10/graded_claude.json, read
only), v7 round G's run records (v7/F/sllm/run_G), vP.1's graded records (VP1_GRADED, default ~/vp1grade: graded_*.json from
ops/grade_vp1.py, replay_*.json from P/replay7.py), vP.1's run records (vp1/runs/*/episodes*.jsonl) and injection logs
(vp1/runs/inject/*.jsonl). Exclusions as v7: void and not-started episodes, hold worlds, development and determinism batches (never
graded). A program episode with a crash, a time-out or an audit breach counts as unanswered.
Labels: Sonnet, Haiku and Qwen agents '<model>-fm'; manipulated agents 'sonnet-fm-late', 'sonnet-fit-once', 'sonnet-fm-flip'; programs
'sllmG-R1' (Sonnet, round G), 'sllmGH-R1' (Haiku), 'sllmGQ-R1' (Qwen), and 'sllmG-R1@fit-once' under fit-once.
  python vp1/analyzeP1.py OUT.json"""
import glob, json, os, random, sys
from collections import defaultdict, Counter
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'kit', 'ref'))
import analyzeF as AF  # noqa: E402
import analyzeG as AG  # noqa: E402
import evidence7 as EV  # noqa: E402
import crossfit as CF  # noqa: E402

V7 = os.path.expanduser(os.environ.get('VP1_V7', '~/Documents/harbor/v7/v7'))
V7GR = os.path.join(V7, 'runs', 'F', 'graded')
V6B1 = os.path.expanduser(os.environ.get('VP1_V6B1', '~/Documents/harbor/v6/v6/runs/bench/v6_10/graded_claude.json'))
V7RUNG = os.path.join(HERE, '..', 'v7', 'F', 'sllm', 'run_G')
VGR = os.path.expanduser(os.environ.get('VP1_GRADED', '~/vp1grade'))
RUNS = os.path.join(HERE, 'runs')
FOLDS = {f: {c['scen']: c['fold'] for c in d['compounds']} for f, d in json.load(open(os.path.join(HERE, 'folds.json')))['families'].items()}
BENCH = {f: set(d) for f, d in FOLDS.items()}
MANIP = ('fm-late', 'fit-once', 'fm-flip')
PROG_PRE = {'sonnet': 'sllmG-', 'haiku': 'sllmGH-', 'qwen': 'sllmGQ-'}
ONLINE = {'sonnet': 'sonnet-fm', 'haiku': 'haiku-fm', 'qwen': 'qwen3-8b-fm'}
SEEDS = {'sonnet': {'B1': (1, 2, 3, 4), 'H': (1, 2, 3, 4), 'T': (1, 2, 3, 4)}, 'haiku': {'B1': (1, 2), 'H': (1, 2), 'T': (1,)},
         'qwen': {'B1': (1,), 'H': (1,), 'T': (1,)}}
CONTRAST_SEEDS = {'sonnet': {'B1': {1, 2, 3, 4}, 'H': {1, 2, 3, 4}, 'T': {1}}, 'haiku': {'B1': {1, 2}, 'H': {1, 2}, 'T': {1}},
                  'qwen': {'B1': {1}, 'H': {1}, 'T': {1}}}
FAMS = ('B1', 'H', 'T')


def label(g):
    m, a = str(g.get('model') or ''), g.get('arm')
    if m.startswith(('sllmG-', 'sllmGH-', 'sllmGQ-')): return m + ('@fit-once' if a == 'fit-once' else '')
    if a in MANIP: return f'{m}-{a}'
    return AG.label(g)


AF.label = label


def fam_of(g):
    if g.get('family') in ('H', 'T'): return g['family']
    w = g['world']
    return 'B1' if 2000 <= w < 3000 else 'H' if 4000 <= w < 5000 else 'T'


# ---------------------------------------------------------------- loading
def bad_programs():
    bad = {}
    files = glob.glob(os.path.join(V7RUNG, 'episodes*.jsonl')) + glob.glob(os.path.join(RUNS, '*', 'episodes*.jsonl'))
    for f in files:
        for l in open(f):
            r = json.loads(l)
            if 'prog' not in r: continue
            why = 'breach' if r.get('breach') else ('crash' if (r.get('rc') != 0 or r.get('program_error')) else ('unanswered' if not r.get('answered') else None))
            if why: bad[r['token'][:12]] = why
    return bad


def load():
    tabs = EV.load_tables(); bad = bad_programs()
    v7 = {'B1': [V6B1, os.path.join(V7GR, 'graded_B1_sllmG.json')],
          'H': [os.path.join(V7GR, f) for f in ('graded_v7-4-H.json', 'graded_qwen_HT.json', 'graded_H_sllmG.json')],
          'T': [os.path.join(V7GR, f) for f in ('graded_v7-4-T.json', 'graded_qwen_HT.json', 'graded_T_sllmG.json')]}
    keep_lab = lambda lab: lab in ('sonnet-fm', 'haiku-fm', 'qwen3-8b-fm') or lab.startswith('sllmG-')
    R = defaultdict(list); raw = {}; seen = set()
    for fam, files in v7.items():
        for p in files:
            for g in json.load(open(p)):
                if fam != 'B1' and g.get('family') != fam: continue
                if g.get('void') or g.get('not_started') or not AF.base_world(g, fam) or not keep_lab(label(g)): continue
                if g['scen'] not in BENCH[fam] or g['token'] in seen: continue
                seen.add(g['token']); R[fam].append(AF.norm(g, fam, tabs, bad)); raw[g['token']] = (fam, g)
    for p in sorted(glob.glob(os.path.join(VGR, 'graded_*.json'))):
        for g in json.load(open(p)):
            fam = fam_of(g)
            if g.get('void') or g.get('not_started') or not AF.base_world(g, fam): continue
            if str(g.get('batch', '')).startswith(('vp1-det', 'vp1-2-dev')) or g['token'] in seen: continue
            seen.add(g['token']); R[fam].append(AF.norm(g, fam, tabs, bad)); raw[g['token']] = (fam, g)
    return R, raw, tabs, bad


# ---------------------------------------------------------------- contrasts (offline or manipulated minus online or fm)
def flip(c):
    if not c: return c
    st = c['sign_test']
    return dict(c, a=c['b'], b=c['a'], gap=round(-c['gap'], 4), ci95=[round(-c['ci95'][1], 4), round(-c['ci95'][0], 4)],
                sign_test=dict(st, positive=st['negative'], negative=st['positive']))


def draws(A, B, strata, ks):
    """AF.contrast's bootstrap draws of mean(A - B), with its resampling and seed, plus the point estimate and per-compound gaps."""
    a, b = AF.per_comp(A, ks), AF.per_comp(B, ks)
    comps = sorted(s for s in a if s in b)
    common = {s: sorted(set(a[s]) & set(b[s])) for s in comps}
    comps = [s for s in comps if common[s]]
    if not comps: return None
    stat = lambda smp: sum(sum(a[s][k] for k in kk) / len(kk) - sum(b[s][k] for k in kk) / len(kk) for s, kk in smp) / len(smp)
    full = [(s, common[s]) for s in comps]
    rng = random.Random(AF.SEED); by = defaultdict(list)
    for s in comps: by[strata.get(s, 'all')].append(s)
    out = []
    for _ in range(AF.NB):
        smp = []
        for st, ss in by.items():
            for s in (rng.choice(ss) for _ in ss):
                smp.append((s, [rng.choice(common[s]) for _ in common[s]]))
        out.append(stat(smp))
    gaps = [sum(a[s][k] for k in kk) / len(kk) - sum(b[s][k] for k in kk) / len(kk) for s, kk in full]
    return dict(point=stat(full), draws=out, gaps=gaps, n=len(comps))


def pooled(parts):
    """parts: list of draws() outputs, one per family; equal family weights."""
    parts = [p for p in parts if p]
    if not parts: return None
    d = sorted(sum(p['draws'][i] for p in parts) / len(parts) for i in range(AF.NB))
    return dict(families=len(parts), n_compounds=sum(p['n'] for p in parts), gap=round(sum(p['point'] for p in parts) / len(parts), 4),
                ci95=[round(d[int(0.025 * AF.NB)], 4), round(d[int(0.975 * AF.NB) - 1], 4)], sign_test=AF.sign_test([g for p in parts for g in p['gaps']]))


def unit_cost(recs, fam):
    grp = defaultdict(list)
    for r in recs: grp[(r['arm'], r['scen'], r['k'])].append(r['cost'])
    return {k: sum(v) / len(v) for k, v in grp.items() if len(v) == AF.UNIT[fam]}


# ---------------------------------------------------------------- offline against online (VP1-1, VP1-2)
def offline_online(R, ST):
    out = {}
    for model in ('sonnet', 'haiku', 'qwen'):
        M = {}; parts = {'ev': [], 'reg': []}
        for fam in FAMS:
            recs = R[fam]; U = {k: AF.units(recs, fam, k) for k in ('ev', 'reg')}; C = unit_cost(recs, fam)
            on = ONLINE[model]; seeds = SEEDS[model][fam]; ks = CONTRAST_SEEDS[model][fam]
            progs = sorted(a for a in U['ev'] if a.startswith(PROG_PRE[model]) and '@' not in a)
            if not progs or on not in U['ev']: M[fam] = dict(missing=dict(programs=progs, online=on in U['ev'])); continue
            ev = {(p, s, k): v for p in progs for (s, k), v in U['ev'][p].items() if k in seeds}
            reg = {(p, s, k): v for p in progs for (s, k), v in U['reg'][p].items() if k in seeds}
            cost = {(p, s, k): C[(p, s, k)] for p in progs for (s, k) in U['ev'][p] if k in seeds and (p, s, k) in C}
            xf = CF.crossfit(progs, ev, reg, cost, FOLDS[fam], seeds, seeds)
            X = {'ev': {(r['compound'], r['seed']): float(r['ev']) for r in xf['rows']},
                 'reg': {(r['compound'], r['seed']): float(r['reg']) for r in xf['rows'] if r['reg'] is not None}}
            f = dict(programs=progs, chosen={str(k): v for k, v in xf['chosen'].items()}, seeds_selection=list(seeds), seeds_contrast=sorted(ks),
                     online=on, rates={})
            for key in ('ev', 'reg'):
                on_cells = {c: v for c, v in U[key][on].items() if c[1] in ks}
                f['rates'][key] = dict(online=AF.rate(on_cells, ks), crossfit=AF.rate(X[key], ks), crossfit_all_seeds=AF.rate(X[key]),
                                       **{p: AF.rate({c: v for c, v in U[key][p].items() if c[1] in seeds}) for p in progs})
                f[key] = {'cross-fitted minus online': AF.contrast(X[key], [on_cells], ST[fam], ks),
                          'mean of five minus online': flip(AF.contrast(on_cells, [U[key][p] for p in progs], ST[fam], ks, 'mean')),
                          'post hoc best minus online': flip(AF.contrast(on_cells, [U[key][p] for p in progs], ST[fam], ks, 'max'))}
                b = f[key]['post hoc best minus online']
                if b and b.get('chosen') is not None: b['chosen'] = progs[b['chosen']]
                parts[key].append(draws(X[key], on_cells, ST[fam], ks))
            f['per_compound'] = {str(s): dict(fold=FOLDS[fam].get(s), crossfit_ev=[X['ev'].get((s, k)) for k in sorted(ks)],
                                              online_ev=[U['ev'][on].get((s, k)) for k in sorted(ks)]) for s in sorted(FOLDS[fam])}
            M[fam] = f
        M['pooled (family-weighted)'] = {key: {'cross-fitted minus online': pooled(parts[key])} for key in ('ev', 'reg')}
        out[model] = M
    return out


# ---------------------------------------------------------------- manipulations (VP1-3)
def inject_events():
    ev = defaultdict(list)
    for f in glob.glob(os.path.join(RUNS, 'inject', '*.jsonl')):
        for l in open(f):
            e = json.loads(l); ev[e['episode'][:12]].append(e)
    return ev


def identified(g):
    s = g.get('structured') or {}
    return g.get('identified') or s.get('identified_phase')


def true_phase(g, fam, tabs):
    W = tabs[fam][0]; w = W[g['scen']]; nm = w['names_by_id']
    return nm[w['a'] if g['world'] % 10 in (1, 3, 4, 5) else w['b']]


def fit_once_measures(raw, recs_by_tok, labs, inj, tabs):
    out = {}
    for lab in labs:
        toks = [t for t, (fam, g) in raw.items() if label(g) == lab]
        rows = []
        for t in toks:
            fam, g = raw[t]; r = recs_by_tok[t]; tp = true_phase(g, fam, tabs); idn = identified(g)
            e = [x for x in inj.get(t[:12], []) if x['kind'] == 'fit-once']
            fired = bool(e); rival = e[0]['rival'] if e else None
            calls = g.get('calls') or []
            fits = [i for i, c in enumerate(calls) if c.get('tool') == 'fit']
            idx = next((i for i in fits if e and (calls[i].get('result') or {}).get('chi2') == e[0]['reported_chi2']), None)
            recheck = bool(idx is not None and any(i > idx and [p.get('name') for p in ((calls[i].get('args') or {}).get('spec') or {}).get('phases', [])] == [tp] for i in fits))
            rows.append(dict(fam=fam, fired=fired, propagated=bool(fired and idn == rival), recovered=idn == tp, recheck=recheck,
                             answered=r['answered'], ev=r['ev'], reg=r['reg']))
        n = len(rows); fr = [x for x in rows if x['fired']]
        share = lambda L, k: round(sum(x[k] for x in L) / len(L), 4) if L else None
        out[lab] = dict(episodes=n, fired=len(fr), fired_share=share(rows, 'fired'),
                        intent_to_treat=dict(n=n, propagation=share(rows, 'propagated'), recovery=share(rows, 'recovered'),
                                             recheck=round(sum(x['fired'] and x['recheck'] for x in rows) / n, 4) if n else None),
                        per_protocol=dict(n=len(fr), propagation=share(fr, 'propagated'), recovery=share(fr, 'recovered'), recheck=share(fr, 'recheck')),
                        by_family={f: dict(episodes=sum(1 for x in rows if x['fam'] == f), fired=sum(1 for x in fr if x['fam'] == f),
                                           propagation_pp=share([x for x in fr if x['fam'] == f], 'propagated'),
                                           recovery_pp=share([x for x in fr if x['fam'] == f], 'recovered'),
                                           recheck_pp=share([x for x in fr if x['fam'] == f], 'recheck')) for f in ('B1', 'H')})
    return out


def flip_follow(raw, tabs):
    """fm-flip: the share of determinate verdicts equal to the verdict the swapped FM gives for the agent's identified phase (the true
    phase where none is named); also the share equal to the truth."""
    rows = []
    for t, (fam, g) in raw.items():
        if label(g) != 'sonnet-fm-flip': continue
        v = g.get('verdict')
        if v not in ('SUPPORTED', 'REFUTED'): rows.append(dict(fam=fam, determinate=False)); continue
        W, FM = tabs[fam]; w = W[g['scen']]; nm = w['names_by_id']; a, b = nm[w['a']], nm[w['b']]; fm = FM[str(g['scen'])]
        sw = lambda n: b if n == a else a if n == b else n
        idn = identified(g); tp = true_phase(g, fam, tabs); ph = idn if idn in nm.values() else tp
        if fam == 'B1':
            polys = [nm[i] for i in w['polymorph_ids']]
            e = {p: fm[sw(p)]['e_form'] for p in polys}
            implied = 'SUPPORTED' if ph in e and e[ph] <= min(e.values()) else 'REFUTED'
        else:
            implied = 'SUPPORTED' if fm[sw(ph)]['e_hull'] <= EV.HULL_T else 'REFUTED'
        rows.append(dict(fam=fam, determinate=True, follows=v == implied, truth=v == g['truth'], identified_known=idn in nm.values()))
    det = [r for r in rows if r['determinate']]
    sh = lambda L, k: round(sum(r[k] for r in L) / len(L), 4) if L else None
    return dict(episodes=len(rows), determinate=len(det), follow_swapped_share=sh(det, 'follows'), truth_share=sh(det, 'truth'),
                identified_named=sum(r['identified_known'] for r in det),
                by_family={f: dict(determinate=sum(1 for r in det if r['fam'] == f), follow_swapped_share=sh([r for r in det if r['fam'] == f], 'follows'))
                           for f in ('B1', 'H')})


def world_measures(recs, arm, comps):
    L = [r for r in recs if r['arm'] == arm and r['scen'] in comps and r['k'] == 1]
    if not L: return None
    n = len(L)
    return dict(worlds=n, answered=sum(r['answered'] for r in L), evidence=round(sum(r['ev'] for r in L) / n, 4), registered=round(sum(r['reg'] for r in L) / n, 4),
                free_scan_only_share=round(sum(r['free_only'] for r in L) / n, 4), D25_rate=round(sum(r['D'] >= 25 for r in L) / n, 4),
                FMU=sum('FMU' in r['codes'] for r in L), FMU_share=round(sum('FMU' in r['codes'] for r in L) / n, 4), fm_called_share=round(sum(r['fm_called'] for r in L) / n, 4),
                wrong=sum(r['wrong'] for r in L), mean_cost=round(sum(r['cost'] for r in L) / n, 2))


def manipulations(R, raw, tabs, ST, RP):
    out = {}; recs_by_tok = {r['token']: r for fam in R for r in R[fam]}
    for m in MANIP:
        arm = f'sonnet-{m}'; M = {}; parts = {'ev': [], 'reg': []}
        for fam in ('B1', 'H'):
            recs = R[fam]; U = {k: AF.units(recs, fam, k) for k in ('ev', 'reg')}
            if arm not in U['ev'] or 'sonnet-fm' not in U['ev']: continue
            comps = sorted({s for s, k in U['ev'][arm]})
            f = dict(compounds=len(comps), world_level={a: world_measures(recs, a, set(comps)) for a in (arm, 'sonnet-fm')})
            for key in ('ev', 'reg'):
                A = {c: v for c, v in U[key][arm].items() if c[1] == 1}; B = {c: v for c, v in U[key]['sonnet-fm'].items() if c[1] == 1 and c[0] in comps}
                f[key] = dict(manipulated=AF.rate(A, {1}), fm=AF.rate(B, {1}), contrast=AF.contrast(A, [B], ST[fam], {1}))
                parts[key].append(draws(A, B, ST[fam], {1}))
            L = [r for r in recs if r['arm'] == arm and r['token'] in RP]
            if L:
                rr = [dict(r, reg=RP[r['token']]['reg'], ev=RP[r['token']]['ev'], arm='replay') for r in L]
                ua = {k: AF.units(L, fam, k) for k in ('ev', 'reg')}; ur = {k: AF.units(rr, fam, k) for k in ('ev', 'reg')}
                f['s_replay'] = dict(episodes=len(L), errors=sum(1 for r in L if RP[r['token']].get('error')),
                                     **{k: dict(agent=AF.rate(ua[k].get(arm, {})), replay=AF.rate(ur[k].get('replay', {})),
                                                contrast_replay_minus_agent=AF.contrast(ur[k].get('replay', {}), [ua[k].get(arm, {})], ST[fam]) if ur[k].get('replay') else None)
                                        for k in ('ev', 'reg')})
            M[fam] = f
        M['pooled (family-weighted)'] = {key: pooled(parts[key]) for key in ('ev', 'reg')}
        L = [r for fam in ('B1', 'H') for r in R[fam] if r['arm'] == arm]
        M['pooled_world_level'] = dict(episodes=len(L), free_scan_only_share=round(sum(r['free_only'] for r in L) / len(L), 4) if L else None,
                                       D25_rate=round(sum(r['D'] >= 25 for r in L) / len(L), 4) if L else None,
                                       FMU_share=round(sum('FMU' in r['codes'] for r in L) / len(L), 4) if L else None)
        out[m] = M
    inj = inject_events()
    progs = sorted({label(g) for _, g in raw.values() if label(g).endswith('@fit-once')})
    out['fit-once']['measures'] = fit_once_measures(raw, recs_by_tok, ['sonnet-fit-once'] + progs, inj, tabs)
    pp = [x for p in progs for x in [out['fit-once']['measures'][p]]]
    fired = sum(x['per_protocol']['n'] for x in pp)
    out['fit-once']['programs_pooled'] = dict(programs=progs, fired=fired, propagation_pp=round(sum(x['per_protocol']['propagation'] * x['per_protocol']['n'] for x in pp if x['per_protocol']['n']) / fired, 4) if fired else None)
    out['fm-flip']['follow'] = flip_follow(raw, tabs)
    return out


# ---------------------------------------------------------------- expectations (PREREG, written before any run)
def expectations(OO, MP):
    E = []
    s = OO['sonnet']
    above = lambda c: bool(c and c['ci95'][0] > 0)
    ev_fams = [f for f in FAMS if above((s.get(f, {}).get('ev') or {}).get('cross-fitted minus online'))]
    reg_ht = all(above((s.get(f, {}).get('reg') or {}).get('cross-fitted minus online')) for f in ('H', 'T'))
    E.append(dict(n=1, text='cross-fitted Sonnet program beats Sonnet fm, interval above zero on >= 2 families (evidence key) and on H and T (registered key)',
                  met=len(ev_fams) >= 2 and reg_ht, value=dict(evidence_families_above_zero=ev_fams, registered_H_and_T_above_zero=reg_ht)))
    pts = {f: (s.get(f, {}).get('ev') or {}).get('cross-fitted minus online', {}) or {} for f in FAMS}
    E.append(dict(n=2, text='cross-fitted Sonnet program at or above Sonnet fm on all three families (point estimate, evidence key)',
                  met=all(pts[f].get('gap') is not None and pts[f]['gap'] >= 0 for f in FAMS), value={f: pts[f].get('gap') for f in FAMS}))
    h = OO['haiku']; hp = {f: ((h.get(f, {}).get('ev') or {}).get('cross-fitted minus online') or {}).get('gap') for f in FAMS}
    E.append(dict(n=3, text="Haiku's cross-fitted program at or above Haiku online on >= 2 families (point estimate, evidence key)",
                  met=sum(1 for v in hp.values() if v is not None and v >= 0) >= 2, value=hp))
    q = OO['qwen']; qv = {}
    for f in FAMS:
        r = (q.get(f, {}).get('rates') or {}).get('ev') or {}
        progs = q.get(f, {}).get('programs') or []
        mean5 = sum(r[p] for p in progs if r.get(p) is not None) / len(progs) if progs else None
        qv[f] = dict(online=r.get('online'), offline_mean=round(mean5, 4) if mean5 is not None else None)
    E.append(dict(n=4, text="Qwen's offline mean exceeds 0 on >= 1 family where Qwen online is 0 (evidence key)",
                  met=any(v['online'] == 0 and (v['offline_mean'] or 0) > 0 for v in qv.values()), value=qv))
    fl = MP['fm-late']; pg = (fl['pooled (family-weighted)'] or {}).get('ev') or {}
    fso = fl['pooled_world_level']['free_scan_only_share']
    E.append(dict(n=5, text='fm-late raises evidence-key resolution over fm by >= 0.10 on B1 and H pooled, and cuts free-scan-only below 5 %',
                  met=bool(pg and pg['gap'] >= 0.10 and fso is not None and fso < 0.05), value=dict(pooled_gap=pg.get('gap'), ci95=pg.get('ci95'), free_scan_only=fso)))
    fo = MP['fit-once']; sp = fo['measures'].get('sonnet-fit-once', {}).get('per_protocol', {}).get('propagation'); pr = fo['programs_pooled']['propagation_pp']
    E.append(dict(n=6, text='under fit-once, Sonnet propagates in >= 30 % of fired episodes, and the programs at no more than half that rate',
                  met=bool(sp is not None and sp >= 0.30 and pr is not None and pr <= sp / 2), value=dict(sonnet=sp, programs=pr)))
    ff = MP['fm-flip']['follow']['follow_swapped_share']
    E.append(dict(n=7, text="under fm-flip, >= 80 % of Sonnet's determinate verdicts follow the swapped FM", met=bool(ff is not None and ff >= 0.80), value=ff))
    return E


def main():
    outp = sys.argv[1]
    R, raw, tabs, bad = load()
    ST = AF.strata_of()
    gr0 = AF.GR; AF.GR = VGR; RP = AF.replay(raw, tabs, bad); AF.GR = gr0          # vP.1's S-replay records (replay_*.json)
    res = dict(note=__doc__.split('\n\n')[0], keys='evidence key first (ev), registered key beside (reg)',
               counts={fam: dict(Counter(r['arm'] for r in R[fam])) for fam in FAMS})
    res['offline_vs_online'] = OO = offline_online(R, ST)
    res['manipulations'] = MP = manipulations(R, raw, tabs, ST, RP)
    res['behaviour'] = {fam: AF.behaviour(R[fam]) for fam in FAMS}
    res['expectations'] = expectations(OO, MP)
    json.dump(res, open(outp, 'w'), indent=1)
    for e in res['expectations']: print(e['n'], 'MET' if e['met'] else 'not met', json.dumps(e['value'])[:200])


if __name__ == '__main__':
    main()
