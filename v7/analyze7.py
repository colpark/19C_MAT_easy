"""V7-5 analysis (written before any v7 agent episode is graded). Inputs: grade7 records (graded episodes, base worlds only), the frozen
worlds, the FM checks (v7/T/fm/fm_check.json, v7/H/fm/fm_check.json), the B1 graded Sonnet episodes and fm check for the T-against-R
comparison. Conventions as B1 (bench/analyze_b1.py): 10,000 bootstrap replicates (seed 20261019), compounds resampled within strata, then
seeds k, paired across arms (the same k draw for fm and noprior); exact two-sided sign test on the per-compound gaps.

Resolution (V7-X4): a world is resolved when its verdict counts (hard rule 3) and the samples identify (D >= 25; T: min(D_pre, D_post));
a T quad is resolved when its four worlds are resolved at the same k; an H pair when both twins are; also reported, B1's truth-only
resolution (a determinate verdict equal to the truth).
T strata: the stage 4b panel stratum (K, E) of the compound (B1's for the paired set, V6-8's for the fresh set); sets (paired, fresh) reported.
H strata: type M (primary), type E (secondary, "under waiver, n = 15", V7-X6); the panel stratum is reported.
Failure codes (per episode; an episode can carry several):
  F2 no quantitative prediction before the first targeted measurement (no simulate of every library polymorph on that measurement's grid)
  F3 diluted scan (an X-ray scan wider than 20 deg)      F4 budget trap (D < 25 at the answer, budget left below 20 min)
  F5 asymmetry (T: within a quad at one k, some worlds resolved and some not; H: one twin resolved, the other not)
  F6 weak-data verdict (determinate with D < 25)          F8 prior error (noprior, a wrong determinate verdict with D >= 25)
  F1 and F7 n/a (no flip arm; every frame plan was decisive within 108 min)
  T only: F9 a sample never measured beyond its free scan; F10 a determinate verdict on a change cell (1 or 4) without an energy call
Gates and expectations: v7/PREREG.md (with the V7-X6 addendum).
  python v7/analyze7.py OUT.json GRADED_T.json GRADED_H.json [B1_GRADED_CLAUDE.json]"""
import json, math, os, random, re, sys
from collections import defaultdict, Counter
HERE = os.path.dirname(os.path.abspath(__file__))
NB, SEED = 10000, 20261019
FM, NOP = {'T': 'v7t-fm', 'H': 'v7h-fm'}, {'T': 'v7t-noprior', 'H': 'v7h-noprior'}
RANK_RX = re.compile(r'lowest|ground state|most stable|rank|lower[- ]energy polymorph|not the lowest|higher[- ]energy polymorph', re.I)


def boot(cells, scens, strata, arm_a, arm_b, rng):
    by = defaultdict(list)
    for s in scens: by[strata[s]].append(s)
    draws = []
    for _ in range(NB):
        gaps = []
        for st, ss in by.items():
            for s in (rng.choice(ss) for _ in ss):
                a, b = cells.get((s, arm_a), {}), cells.get((s, arm_b), {})
                ks = sorted(set(a) & set(b))
                if not ks: continue
                kk = [rng.choice(ks) for _ in ks]
                gaps.append(sum(a[k] for k in kk) / len(kk) - sum(b[k] for k in kk) / len(kk))
        draws.append(sum(gaps) / len(gaps))
    draws.sort()
    return [round(draws[int(0.025 * NB)], 4), round(draws[int(0.975 * NB) - 1], 4)]


def sign_test(gaps):
    pos, neg = sum(g > 0 for g in gaps), sum(g < 0 for g in gaps); n = pos + neg
    if n == 0: return dict(positive=0, negative=0, ties=len(gaps), p=1.0)
    t = min(pos, neg); return dict(positive=pos, negative=neg, ties=len(gaps) - n, p=round(min(1.0, 2 * sum(math.comb(n, i) for i in range(t + 1)) / 2 ** n), 6))


def codes(g):
    c = []; calls = g.get('calls') or []
    ms = g['measurements']
    allm = [m for v in ms.values() for m in v[1:]] if isinstance(ms, dict) else ms[1:]
    first = next((i for i, x in enumerate(calls) if x['tool'] == 'measure'), None)
    if allm:
        ok = any(x['tool'] == 'simulate' for x in (calls[:first] if first is not None else calls))
        if not ok: c.append('F2')
    else: c.append('F2')
    def span(sp): return sp['step'] * (sp['n'] - 1) if sp.get('radiation') != 'neutron' else 145.0
    if any(m['spec'].get('radiation') != 'neutron' and span(m['spec']) > 20.0 for m in allm): c.append('F3')
    budget = 240.0 if g['family'] == 'T' else 180.0
    if g['D'] < 25 and budget - g['cost'] < 20.0: c.append('F4')
    v = g['verdict']
    if v in ('SUPPORTED', 'REFUTED') and g['D'] < 25: c.append('F6')
    if g['arm'] == NOP[g['family']] and v in ('SUPPORTED', 'REFUTED') and v != g['truth'] and g['D'] >= 25: c.append('F8')
    if g['family'] == 'T':
        if any(len(v2) <= 1 for v2 in ms.values()): c.append('F9')
        if g['cell'] in (1, 4) and v in ('SUPPORTED', 'REFUTED') and not any(x['tool'] in ('energy', 'hull') for x in calls): c.append('F10')
    return c


def family(fam, G, W, fmc, strata, label):
    G = [g for g in G if g['family'] == fam and not g.get('void') and not g.get('not_started') and not g.get('hold')]
    for g in G: g['codes'] = codes(g)
    unit = 4 if fam == 'T' else 2
    grp = defaultdict(dict)
    for g in G: grp[(g['arm'], g['scen'], g['k'])][g['cell'] if fam == 'T' else (1 if g['world'] % 10 == 1 else 2)] = g
    cells, cells_truth = defaultdict(dict), defaultdict(dict)
    for (a, s, k), d in grp.items():
        if len(d) != unit: continue
        cells[(s, a)][k] = all(x['resolved'] for x in d.values())
        cells_truth[(s, a)][k] = all(x['resolved_truth'] for x in d.values())
        if len({x['resolved'] for x in d.values()}) > 1:
            for x in d.values(): x['codes'].append('F5')
    rate = lambda s, a, C=cells: (sum(C[(s, a)].values()) / len(C[(s, a)])) if (s, a) in C and C[(s, a)] else None
    scens = sorted({s for (s, a) in cells})
    out = dict(n_compounds=len(scens), unit='quad' if fam == 'T' else 'twin pair')
    fa, na = FM[fam], NOP[fam]
    sc = [s for s in scens if (s, fa) in cells and (s, na) in cells]
    gap = {s: rate(s, fa) - rate(s, na) for s in sc}
    out['rate'] = {a: round(sum(rate(s, a) for s in sc) / len(sc), 4) for a in (na, fa)} if sc else {}
    out['rate_truth_only'] = {a: round(sum(rate(s, a, cells_truth) for s in sc) / len(sc), 4) for a in (na, fa)} if sc else {}
    out['gap'] = round(sum(gap.values()) / len(gap), 4) if gap else None
    out['ci95'] = boot(cells, sc, strata, fa, na, random.Random(SEED)) if sc else None
    out['sign_test'] = sign_test(list(gap.values()))
    groups = {'stratum': lambda s: strata[s], 'fm_status': lambda s: fmc[s]['fm_status']}
    if fam == 'T': groups['set'] = lambda s: W[s]['set']
    else: groups['type'] = lambda s: W[s]['type']
    for gname, fn in groups.items():
        out[f'by_{gname}'] = {}
        for val in sorted({fn(s) for s in sc}):
            ss = [s for s in sc if fn(s) == val]
            out[f'by_{gname}'][val] = dict(n=len(ss), noprior=round(sum(rate(s, na) for s in ss) / len(ss), 4), fm=round(sum(rate(s, fa) for s in ss) / len(ss), 4),
                                         gap=round(sum(gap[s] for s in ss) / len(ss), 4),
                                         ci95=boot(cells, ss, {s: 'all' for s in ss}, fa, na, random.Random(SEED)) if len(ss) > 1 else None,
                                         sign_test=sign_test([gap[s] for s in ss]))
    out['per_compound'] = {str(s): dict(formula=W[s]['formula'], stratum=strata[s], fm_status=fmc[s]['fm_status'],
                                        **({'set': W[s]['set']} if fam == 'T' else {'type': W[s]['type']}),
                                        noprior=rate(s, na), fm=rate(s, fa), gap=round(gap[s], 4)) for s in sc}
    arms = {}
    for a in (na, fa):
        eps = [g for g in G if g['arm'] == a]; cs = Counter(c for g in eps for c in set(g['codes']))
        arms[a] = dict(episodes=len(eps), wrong_conclusions=sum(g['wrong_conclusion'] for g in eps), decisive=sum(g['D'] >= 25 for g in eps),
                       cannot_tell=sum(g['verdict'] == 'CANNOT_TELL' for g in eps), unanswered=sum(not g['answered'] for g in eps),
                       mean_cost=round(sum(g['cost'] for g in eps) / max(1, len(eps)), 2), neutron_share=round(sum(any(
                           (m['spec'].get('radiation') == 'neutron') for m in ([x for v in g['measurements'].values() for x in v] if fam == 'T' else g['measurements']))
                           for g in eps) / max(1, len(eps)), 4),
                       codes={c: cs.get(c, 0) for c in (['F2', 'F3', 'F4', 'F5', 'F6', 'F8'] + (['F9', 'F10'] if fam == 'T' else []))}, F1='n/a', F7='n/a')
        if fam == 'T':
            cellacc = {}
            for c in (1, 2, 3, 4):
                ec = [g for g in eps if g['cell'] == c]
                cellacc[str(c)] = dict(n=len(ec), correct=sum(g['correct'] for g in ec), resolved=sum(g['resolved'] for g in ec),
                                       supported=sum(g['verdict'] == 'SUPPORTED' for g in ec), refuted=sum(g['verdict'] == 'REFUTED' for g in ec),
                                       cannot_tell=sum(g['verdict'] == 'CANNOT_TELL' for g in ec))
            arms[a]['cells'] = cellacc
            det4 = [g for g in eps if g['cell'] == 4 and g['verdict'] in ('SUPPORTED', 'REFUTED')]
            arms[a]['shortcut_signatures'] = dict(
                post_only_L_to_L_SUPPORTED=cellacc['2']['supported'], pre_only_H_to_H_SUPPORTED=cellacc['3']['supported'],
                downhill_L_to_H_SUPPORTED=cellacc['4']['supported'], L_to_H_determinate=len(det4),
                downhill_share_of_determinate_L_to_H=round(sum(g['verdict'] == 'SUPPORTED' for g in det4) / len(det4), 4) if det4 else None)
            arms[a]['measured_both_share'] = round(sum(g['measured_both'] for g in eps) / max(1, len(eps)), 4)
        else:
            mA = [g for g in eps if W[g['scen']]['type'] == 'M' and g['world'] % 10 == 1]
            arms[a]['R_reasoning_signature_M_twinA'] = dict(n=len(mA), refuted=sum(g['verdict'] == 'REFUTED' for g in mA),
                refuted_citing_rank=sum(g['verdict'] == 'REFUTED' and bool(RANK_RX.search(((g.get('structured') or {}).get('decision_rule') or '') + ' ' + (g.get('rationale') or ''))) for g in mA))
            by_type = {}
            for t in ('M', 'E'):
                ss = [s for s in sc if W[s]['type'] == t]
                pr = [v for s in ss for v in cells[(s, a)].values()]
                by_type[t] = dict(n=len(ss), pairs=len(pr), resolved=sum(pr))
            arms[a]['by_type'] = by_type
        arms[a]['by_stratum'] = {st: dict(units=sum(len(cells[(s, a)]) for s in sc if strata[s] == st),
                                          resolved=sum(v for s in sc if strata[s] == st for v in cells[(s, a)].values())) for st in sorted({strata[s] for s in sc})}
    out['arms'] = arms
    if fam == 'H':
        rel = defaultdict(lambda: [0, 0])
        for g in G:
            if g['arm'] != fa: continue
            s = g['scen']; tw = 'A' if g['world'] % 10 == 1 else 'B'; m = abs(fmc[s]['twins'][tw]['margin'])
            b = '<0.02' if m < 0.02 else ('0.02-0.05' if m < 0.05 else '>=0.05')
            rel[b][0] += g['resolved']; rel[b][1] += 1
        out['fm_resolution_by_hull_margin'] = {k: dict(resolved=v[0], episodes=v[1]) for k, v in sorted(rel.items())}
    out['episodes'] = [dict(token=g['token'][:12], arm=g['arm'], scen=g['scen'], k=g['k'], cell=g.get('cell'), world=g['world'], verdict=g['verdict'],
                            D=g['D'], cost=g['cost'], resolved=g['resolved'], codes=sorted(set(g['codes']))) for g in G]
    return out


def main():
    outp = sys.argv[1]; GT = json.load(open(sys.argv[2])); GH = json.load(open(sys.argv[3])) if len(sys.argv) > 3 and os.path.exists(sys.argv[3]) else []
    WT = {w['scen']: w for w in json.load(open(os.path.join(HERE, 'T', 'WORLDS_T.json')))['worlds'] if w.get('in_bench', w.get('slot', 'take') == 'take')}
    FT = {r['scen']: r for r in json.load(open(os.path.join(HERE, 'T', 'fm', 'fm_check.json')))['rows']}
    res = dict(disclosure=('T includes the 30 B1 compounds, which already carry MACE values; T selects none of them on the FM. H runs under '
                           "David's waiver (V7-X6): Gate H-supply failed (15 E against 16), decided after V7-3 on truth-only counts with no FM or LLM contact. "
                           'No number is a population rate.'))
    res['T'] = family('T', GT, WT, FT, {s: WT[s]['stratum'] for s in WT}, 'T')
    if GH:
        WH = {w['scen']: w for w in json.load(open(os.path.join(HERE, 'H', 'WORLDS_H.json')))['worlds']}
        FH = {r['scen']: r for r in json.load(open(os.path.join(HERE, 'H', 'fm', 'fm_check.json')))['rows']}
        res['H'] = family('H', GH, WH, FH, {s: WH[s]['type'] for s in WH}, 'H')
    # T against B1 R on the paired set (Sonnet fm and noprior, k = 1, 2)
    if len(sys.argv) > 4:
        B = [g for g in json.load(open(sys.argv[4])) if g.get('model') == 'sonnet' and g['arm'] in ('v6-active-fm', 'v6-active-noprior') and g['k'] in (1, 2) and not g.get('void')]
        pr = defaultdict(dict)
        for g in B: pr[(g['arm'], g['world'] // 10, g['k'])][g['world'] % 10] = bool(g['correct']) and g['verdict'] == ('SUPPORTED' if g['world'] % 10 == 1 else 'REFUTED')
        rr = defaultdict(list)
        for (a, s, k), d in pr.items():
            if len(d) == 2: rr[(a, s)].append(d[1] and d[2])
        comp = {}
        for w in WT.values():
            if w['set'] != 'paired': continue
            s1 = w['b1_scen']; tq = res['T']['per_compound'].get(str(w['scen']))
            if not tq: continue
            R = {a: (sum(rr[(a, s1)]) / len(rr[(a, s1)]) if rr[(a, s1)] else None) for a in ('v6-active-fm', 'v6-active-noprior')}
            comp[str(w['scen'])] = dict(b1_scen=s1, formula=w['formula'], R_fm=R['v6-active-fm'], R_noprior=R['v6-active-noprior'], T_fm=tq['fm'], T_noprior=tq['noprior'])
        d = [v['T_fm'] - v['R_fm'] for v in comp.values() if v['R_fm'] is not None]
        res['T_vs_R_paired'] = dict(n=len(d), mean_T_fm=round(sum(v['T_fm'] for v in comp.values()) / len(comp), 4),
                                    mean_R_fm=round(sum(v['R_fm'] for v in comp.values() if v['R_fm'] is not None) / len(d), 4),
                                    mean_T_fm_minus_R_fm=round(sum(d) / len(d), 4), sign_test=sign_test(d), per_compound=comp,
                                    note='R: B1 Sonnet pair resolution (truth-only, B1 keys) at k = 1, 2; T: quad resolution (V7-X4) at k = 1, 2')
    gT = res['T']; gate_T = dict(fm_minus_noprior_ci_above_zero=bool(gT['ci95'] and gT['ci95'][0] > 0))
    res['gate_T_item3'] = gate_T
    if 'H' in res:
        res['gate_H_item2'] = dict(fm_minus_noprior_ci_above_zero=bool(res['H']['ci95'] and res['H']['ci95'][0] > 0))
    json.dump(res, open(outp, 'w'), indent=1)
    for fam in ('T', 'H'):
        if fam in res:
            r = res[fam]; print(fam, 'rate', r['rate'], 'gap', r['gap'], r['ci95'], r['sign_test'])
            for k in [x for x in r if x.startswith('by_')]: print('  ', k, {v: (d['gap'], d['n']) for v, d in r[k].items()})


if __name__ == '__main__':
    main()
