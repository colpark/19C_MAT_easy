"""Stage 4b analysis (V5_SPEC J.12 with amendment A), from graded logs (mcenv.grade4b). Pre-registered before any model run.
  python -m mcenv.analyze_stage4b GRADED4B.jsonl OUT.json [TRANSCRIPT_CITES.json]
Pair resolution: both twins of a scenario at the same k receive the truth verdict and it is correct (J.8). Primary: Sonnet interaction
on P over k = 1..3 with a scenario-level bootstrap (10,000 draws: scenarios with replacement, then k within each drawn scenario); exact
two-sided sign test on the per-scenario interaction; scenarios carrying the effect (no-prior pair resolution at least 0.4 below FM, k
1..5). Gate S4b: interaction >= 0.35 with the interval above zero; fm-dft - dftpriced >= 0.25 on the R scenarios of P (k 1..5, same
bootstrap) with the interval above zero; blind-fm at chance. Trust endpoints (U, W; FM-conditioned) are reported apart and carry no gate.
Voided episodes are excluded (primary)."""
import json, math, sys
from collections import defaultdict
import numpy as np
from .analyze_stage1 import wilson

B = 10000
P_SCENS = tuple(range(71, 83))


def load(p): return [json.loads(l) for l in open(p) if l.strip()]


def pairs(G):
    by = defaultdict(dict)
    for g in G: by[(g['model'], g['arm'], g['scen'], g['k'])][g['world']] = g
    out = defaultdict(dict)
    for (m, a, s, k), v in by.items():
        if len(v) == 2: out[(m, a)][(s, k)] = int(all(x['correct'] and x['verdict'] == x['truth'] for x in v.values()))
    return out


def boot(fn, scens, ks, seed=0):
    rng = np.random.default_rng(seed); vals = []
    for _ in range(B):
        ss = rng.choice(scens, len(scens)); draw = [(s, k) for s in ss for k in rng.choice(ks, len(ks))]
        v = fn(draw)
        if v is not None: vals.append(v)
    return [round(float(np.percentile(vals, 2.5)), 4), round(float(np.percentile(vals, 97.5)), 4)] if vals else None


def sign_test(xs):
    """exact two-sided binomial sign test on nonzero values."""
    pos = sum(x > 0 for x in xs); neg = sum(x < 0 for x in xs); n = pos + neg
    if n == 0: return dict(n=0, pos=0, neg=0, p=None)
    k = min(pos, neg); p = min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)
    return dict(n=n, pos=pos, neg=neg, p=round(p, 5))


def interaction(PT, model, scens, ks):
    arms = ('4b-active-fm', '4b-active-noprior', '4b-blind-fm', '4b-blind-noprior')
    T = {a: PT.get((model, a), {}) for a in arms}
    cells = {(s, k) for s in scens for k in ks if all((s, k) in T[a] for a in arms)}
    if not cells: return None

    def f(draw):
        d = [c for c in draw if c in cells]
        if not d: return None
        m = {a: np.mean([T[a][c] for c in d]) for a in arms}
        return (m['4b-active-fm'] - m['4b-active-noprior']) - (m['4b-blind-fm'] - m['4b-blind-noprior'])
    per = {}
    for s in scens:
        cs = [c for c in cells if c[0] == s]
        if cs: per[s] = f(cs)
    return dict(ks=list(ks), n_cells=len(cells), estimate=round(float(f(sorted(cells))), 4), ci95=boot(f, list(scens), list(ks)),
                per_scenario={str(s): round(float(v), 4) for s, v in per.items()}, sign_test=sign_test(list(per.values())),
                arms={a: round(float(np.mean([T[a][c] for c in cells])), 4) for a in arms})


def contrast(PT, model, a1, a2, scens, ks):
    T1, T2 = PT.get((model, a1), {}), PT.get((model, a2), {})
    cells = {(s, k) for s in scens for k in ks if (s, k) in T1 and (s, k) in T2}
    if not cells: return None

    def f(draw):
        d = [c for c in draw if c in cells]
        return None if not d else np.mean([T1[c] - T2[c] for c in d])
    return dict(contrast=f'{a1} - {a2}', ks=list(ks), n_cells=len(cells), estimate=round(float(f(sorted(cells))), 4),
                ci95=boot(f, sorted({c[0] for c in cells}), list(ks)))


def carrying(PT, model, scens):
    fm, no = PT.get((model, '4b-active-fm'), {}), PT.get((model, '4b-active-noprior'), {})
    out = []
    for s in scens:
        a = [fm[c] for c in fm if c[0] == s]; b = [no[c] for c in no if c[0] == s]
        if a and b and np.mean(b) <= np.mean(a) - 0.4: out.append(s)
    return dict(n=len(out), scenarios=out)


def rate(xs): n = len(xs); k = sum(bool(x) for x in xs); return dict(k=k, n=n, rate=round(k / n, 4) if n else None)


def cell(eps, PT, m, a, cites):
    pr = PT.get((m, a), {}); wrong = [g for g in eps if g['wrong_conclusion']]; att = defaultdict(int)
    for g in wrong: att[g['wrong_attribution'] or 'none'] += 1
    band = [g for g in eps if g['in_band']]
    rr = lambda ss: [v for (s, k), v in pr.items() if s in ss]
    return dict(n=len(eps), pair_resolution=dict(k=sum(pr.values()), n=len(pr), rate=round(sum(pr.values()) / len(pr), 4) if pr else None),
                per_scenario={str(s): f"{sum(v for (ss, k), v in pr.items() if ss == s)}/{sum(1 for (ss, k) in pr if ss == s)}" for s in sorted({s for s, k in pr})},
                pairs_R=rate(rr([g['scen'] for g in eps if g['claim_type'] == 'R'])), correct=rate([g['correct'] for g in eps]),
                wrong_conclusions=rate([g['wrong_conclusion'] for g in eps]), cannot_tell=rate([g['verdict'] == 'CANNOT_TELL' for g in eps]),
                id_decisive=rate([g['id_decisive'] for g in eps]), measured_beyond_m0=rate([g['measured_beyond_m0'] for g in eps]),
                fm_tool_used=rate([g['fm_calls'] > 0 for g in eps]), dft_calls_mean=round(float(np.mean([g['dft_calls'] for g in eps])), 3) if eps else None,
                cost_mean=round(float(np.mean([g['cost'] for g in eps])), 2) if eps else None,
                partial_evidence=rate([g['partial_evidence'] for g in eps]), partial_among_wrong=rate([g['partial_evidence'] for g in wrong]),
                wrong_attribution=dict(att),
                found_implies_stable=dict(sup_on_false=rate([g['verdict'] == 'SUPPORTED' for g in eps if not g['holds'] and g['claim_type'] in ('R', 'H')]),
                                          ref_on_true=rate([g['verdict'] == 'REFUTED' for g in eps if g['holds'] and g['claim_type'] in ('R', 'H')])),
                in_band=dict(n=len(band), cannot_tell=rate([g['verdict'] == 'CANNOT_TELL' for g in band]), dft_call=rate([g['dft_calls'] > 0 for g in band]),
                             acts=rate([g['verdict'] == 'CANNOT_TELL' or g['dft_calls'] > 0 for g in band]),
                             cites=rate([bool(cites and cites.get(g['token'])) for g in band]) if cites else None,
                             unsupported_determinate=rate([g['verdict'] in ('SUPPORTED', 'REFUTED') and g['dft_calls'] == 0 for g in band])),
                triage=dict(dft_calls_in_band_worlds=sum(g['dft_calls'] for g in band), dft_calls_total=sum(g['dft_calls'] for g in eps)))


def main():
    G = [g for g in load(sys.argv[1]) if not g.get('void')]
    cites = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else None
    strata = {'P': [g for g in G if g['stratum'] == 'P'], 'U': [g for g in G if g['stratum'] == 'U'], 'W': [g for g in G if g['stratum'] == 'W']}
    res = {}
    for st, GG in strata.items():
        PT = pairs(GG); cells = defaultdict(list)
        for g in GG: cells[(g['model'], g['arm'])].append(g)
        res[st] = {f'{m}|{a}': cell(e, PT, m, a, cites) for (m, a), e in sorted(cells.items())}
    PT = pairs(strata['P']); son = 'sonnet'
    R_P = sorted({g['scen'] for g in strata['P'] if g['claim_type'] == 'R'})
    tests = dict(primary_interaction=interaction(PT, son, P_SCENS, (1, 2, 3)),
                 carrying_effect=carrying(PT, son, P_SCENS),
                 amortization_R=contrast(PT, son, '4b-active-fm-dft', '4b-active-dftpriced', R_P, (1, 2, 3, 4, 5)),
                 fm_minus_dftpriced_R=contrast(PT, son, '4b-active-fm', '4b-active-dftpriced', R_P, (1, 2, 3, 4, 5)),
                 fmdft_minus_fm_P=contrast(PT, son, '4b-active-fm-dft', '4b-active-fm', P_SCENS, (1, 2, 3, 4, 5)),
                 ceiling_minus_fm_P=contrast(PT, son, '4b-active-ceiling', '4b-active-fm', P_SCENS, (1, 2, 3)))
    PU = pairs(strata['U']); U_S = sorted({g['scen'] for g in strata['U']})
    tests['U_stated_minus_unstated_pairs'] = contrast(PU, son, '4b-active-fm', '4b-active-fm-unstated', U_S, (1, 2, 3))
    band_ct = lambda arm: {(g['scen'], g['k']): float(np.mean([x['verdict'] == 'CANNOT_TELL' for x in strata['U'] if x['model'] == son and x['arm'] == arm and x['scen'] == g['scen'] and x['k'] == g['k'] and x['in_band']] or [np.nan]))
                           for g in strata['U'] if g['model'] == son and g['arm'] == arm and g['in_band']}
    a1, a2 = band_ct('4b-active-fm'), band_ct('4b-active-fm-unstated')
    cc = {c for c in a1 if c in a2}
    if cc:
        f = lambda draw: (lambda d: None if not d else float(np.mean([a1[c] - a2[c] for c in d])))([c for c in draw if c in cc])
        tests['U_inband_cannot_tell_stated_minus_unstated'] = dict(estimate=round(f(sorted(cc)), 4), ci95=boot(f, sorted({c[0] for c in cc}), [1, 2, 3]), n_cells=len(cc))
    for mod in ('haiku', 'opus', 'qwen3-8b'):
        tests[f'active_contrast_P|{mod}'] = contrast(PT, mod, '4b-active-fm', '4b-active-noprior', P_SCENS, (1, 2, 3))
    pi = tests['primary_interaction']; am = tests['amortization_R']
    bf = res['P'].get(f'{son}|4b-blind-fm', {})
    gate = None
    if pi and pi['ci95'] and am and am['ci95']:
        gate = dict(interaction=pi['estimate'], interaction_ci95=pi['ci95'], interaction_ok=pi['estimate'] >= 0.35 and pi['ci95'][0] > 0,
                    amortization=am['estimate'], amortization_ci95=am['ci95'], amortization_ok=am['estimate'] >= 0.25 and am['ci95'][0] > 0,
                    blind_fm_pairs=bf.get('pair_resolution', {}).get('rate'))
        gate['blind_fm_at_chance'] = gate['blind_fm_pairs'] == 0
        gate['pass_'] = gate['interaction_ok'] and gate['amortization_ok'] and gate['blind_fm_at_chance']
    json.dump(dict(cells=res, tests=tests, gate_S4b=gate, rule='J.12 with amendment A'), open(sys.argv[2], 'w'), indent=1, default=float)
    print(json.dumps(dict(gate=gate, primary=pi, amortization=am), indent=1, default=float))


if __name__ == '__main__':
    main()
