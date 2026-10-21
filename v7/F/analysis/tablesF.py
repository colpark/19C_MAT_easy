"""V7-F6 report tables from analyzeF.py's output (F/analysis/analysisF.json) -> F/analysis/TABLES_F.md."""
import json, os
H = os.path.dirname(os.path.abspath(__file__)); A = json.load(open(os.path.join(H, 'analysisF.json')))
ORDER = ['blind-FM (floor)', 'qwen3-8b-noprior', 'qwen3-8b-fm', 'haiku-noprior', 'haiku-fm', 'sonnet-noprior', 'opus-noprior', 'sonnet-fm', 'opus-fm',
         'sonnet-fm-planner', 'fm-hint', 's-broad', 's-neutron', 's-plan', 'gold-oracle (ceiling, k 1)']
f = lambda x: '-' if x is None else f'{x:.3f}'
out = []
out.append('## Baseline ladder (k = 1, on Sonnet fm\'s compounds; evidence key / registered key)\n')
out.append('| arm | B1 (30 pairs) | H (23 pairs) | T (24 quads) |\n|---|---|---|---|')
arms = ORDER + ['S-llm mean of 5 (V7-E4)'] + [f'sllm-{x}{i}' for x in 'RHT' for i in range(1, 6)]
for a in arms:
    row = [a]
    for fam in ('B1', 'H', 'T'):
        L = A[fam]['ladder_matched_k1']['arms']
        if a.startswith('S-llm mean'):
            s = [v for k, v in L.items() if k.startswith('sllm-')]
            row.append(f"{f(sum(v['evidence'] for v in s) / len(s))} / {f(sum(v['registered'] for v in s) / len(s))}" if s else '-')
        elif a in L:
            v = L[a]; n = v.get('compounds'); nC = len(A[fam]['ladder_matched_k1']['compounds'])
            row.append(f"{f(v['evidence'])} / {f(v['registered'])}" + (f' (n {n})' if isinstance(n, int) and n != nC else ''))
        else: row.append('')
    if any(row[1:]): out.append('| ' + ' | '.join(row) + ' |')
out.append('\n## Scripts on every compound they ran (all k; evidence / registered)\n')
out.append('| arm | B1 | H | T |\n|---|---|---|---|')
for a in ('sonnet-fm', 's-broad', 's-neutron', 's-plan'):
    row = [a]
    for fam in ('B1', 'H', 'T'):
        v = A[fam]['ladder'].get(a); row.append(f"{f(v['evidence'])} / {f(v['registered'])} ({v['compounds']} compounds, k {','.join(map(str, v['ks']))})" if v else '')
    out.append('| ' + ' | '.join(row) + ' |')
NAMES = ['sonnet-fm vs S-llm mean (k1)', 'sonnet-fm vs S-llm best (k1)', 'fm-hint vs s-neutron (k1)', 'fm-hint vs sonnet-fm (k1)',
         'sonnet-fm vs s-broad (k1)', 'sonnet-fm vs s-neutron (k1)', 'V7-P primary: sonnet-fm vs stronger of s-broad, s-neutron (all k)',
         'V7-P primary: sonnet-fm vs stronger of s-broad, s-neutron (k1)', 'sonnet-fm-planner vs s-plan', 'sonnet-fm vs sonnet-noprior (k1)',
         'haiku-fm vs haiku-noprior', 'sonnet-fm-planner vs sonnet-fm']
for key, kn in (('ev', 'evidence key'), ('reg', 'registered key')):
    out.append(f'\n## Contrasts, {kn} (a minus b; bootstrap 10,000, seed 20261019; exact sign test)\n')
    out.append('| family | contrast | n | a | b | a minus b | 95 % CI | sign test (+/-/0, p) |\n|---|---|---|---|---|---|---|---|')
    for fam in ('B1', 'H', 'T'):
        for nm in NAMES:
            v = A[fam]['contrasts'][key].get(nm)
            if not v: continue
            ch = f" ({v['chosen']})" if isinstance(v.get('chosen'), str) else ''
            st = v['sign_test']
            out.append(f"| {fam} | {nm}{ch} | {v['n_compounds']} | {f(v['a'])} | {f(v['b'])} | {v['gap']:+.3f} | [{v['ci95'][0]:+.3f}, {v['ci95'][1]:+.3f}] | {st['positive']}/{st['negative']}/{st['ties']}, {st['p']} |")
out.append('\n## Recipe stratification (k = 1, evidence key; a compound is recipe-solvable when S-broad or S-neutron resolves it)\n')
out.append('| family | stratum sizes (solvable / fails) | arm: solvable / fails |\n|---|---|---|')
for fam in ('B1', 'H', 'T'):
    rs = A[fam]['recipe_strata_k1']['ev']
    cells = '; '.join(f"{a} {f(v['solvable'])} / {f(v['fails'])}" for a, v in rs['arms'].items() if a in ('sonnet-fm', 'sonnet-fm-planner', 'haiku-fm', 'fm-hint', 's-plan', 'opus-fm') or a.startswith('sllm-') and (v['solvable'] or v['fails']))
    out.append(f"| {fam} | {len(rs['solvable'])} / {len(rs['fails'])} (fails: {', '.join(map(str, rs['fails']))}) | {cells} |")
out.append('\n## Behaviour per arm (all episodes of the arm)\n')
out.append('| family | arm | episodes | neutron | free scans only | FM called | world rate ev / reg | evidence loss | wrong | D >= 25 | mean cost (min) | F3 | F4 | F6 | F9 | F10 | FMU |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
for fam in ('B1', 'H', 'T'):
    for a, b in A[fam]['behaviour'].items():
        c = b['codes']
        out.append(f"| {fam} | {a} | {b['episodes']} | {b['neutron_share']:.2f} | {b['free_scan_only_share']:.2f} | {b['fm_called_share']:.2f} | {b['world_rate_evidence']:.2f} / {b['world_rate_registered']:.2f} | {b['evidence_loss']:.2f} | {b['wrong_conclusions']} | {b['decisive_D25']} | {b['mean_cost']} | {c['F3']} | {c['F4']} | {c['F6']} | {c['F9']} | {c['F10']} | {c['FMU']} |")
out.append('\n## S-replay (the decision core on each agent episode\'s own measurements; matched by episode)\n')
out.append('| family | agent | episodes | agent ev / reg | replay ev / reg | replay minus agent (reg), 95 % CI |\n|---|---|---|---|---|---|')
for fam in ('B1', 'H', 'T'):
    for a, v in A[fam]['s_replay'].items():
        c = v['reg']['contrast_replay_minus_agent']
        out.append(f"| {fam} | {a} | {v['episodes']} | {f(v['ev']['agent'])} / {f(v['reg']['agent'])} | {f(v['ev']['replay'])} / {f(v['reg']['replay'])} | {c['gap']:+.3f} [{c['ci95'][0]:+.3f}, {c['ci95'][1]:+.3f}] |")
if A['T'].get('sllm_sensitivity_breach_as_answered'):
    out.append('\nSensitivity (V7-X15 breach episode counted as answered), T S-llm: ' + json.dumps(A['T']['sllm_sensitivity_breach_as_answered']))
open(os.path.join(H, 'TABLES_F.md'), 'w').write('\n'.join(out) + '\n'); print('\n'.join(out)[:6000])
