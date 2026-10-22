"""V7-G3: the V7-G expectations and interpretation rules (PREREG.md and PREREG_P.md, V7-G addendum), each reported as met or not met
with the numbers it rests on, and the V7-G report tables (TABLES_G.md). Evidence key first, registered key beside it. Expectation 1's
premise ("S-neutron's 0" on the fresh set) was the V7-E6 artifact; the expectation is evaluated as written against the rerun.
  python G/analysis/gatesG.py"""
import json, os
H = os.path.dirname(os.path.abspath(__file__)); A = json.load(open(os.path.join(H, 'analysisG.json')))
F, O = A['fresh_T'], A['offline_vs_online']
items = []
f3 = lambda x: '-' if x is None else f'{x:.3f}'


def add(name, met, value, kind='expectation'):
    items.append(dict(item=name, kind=kind, result=('met' if met else 'not met') if kind == 'expectation' else ('yes' if met else 'no'), value=value))


q = {a: F['per_quad'][a]['evidence'] for a in F['per_quad']}
add('1. Sonnet fm resolves at least 0.10 of the fresh quads, above S-neutron\'s 0 and below S-plan\'s 0.93',
    q['sonnet-fm'] >= 0.10 and q['sonnet-fm'] > q['s-neutron'] and q['sonnet-fm'] < q['s-plan'],
    f"Sonnet fm {f3(q['sonnet-fm'])}, S-neutron {f3(q['s-neutron'])} (its premised 0 was the V7-E6 artifact), S-plan {f3(q['s-plan'])}")
w = F['per_world']['fm-hint']
add('2. fm-hint takes the neutron in at least 80 % of fresh episodes and resolves no more than Sonnet fm on the fresh set',
    w['neutron_share'] >= 0.8 and q['fm-hint'] <= q['sonnet-fm'], f"neutron {w['neutron_share']:.3f}; fm-hint {f3(q['fm-hint'])} vs Sonnet fm {f3(q['sonnet-fm'])}")
meas, neut = {}, {}
for fam in ('B1', 'H', 'T'):
    P = O[fam]['G (corrected)']['programs']
    meas[fam] = [a for a, v in P.items() if v['measured_share'] > 0.5]; neut[fam] = [a for a, v in P.items() if v['neutron_share'] > 0.5]
add('3. At least 3 of 5 corrected programs per family measure, and at most 2 per family take the neutron',
    all(len(meas[f]) >= 3 and len(neut[f]) <= 2 for f in meas),
    '; '.join(f"{f}: measure {len(meas[f])} of 5, neutron {len(neut[f])} ({', '.join(neut[f]) or 'none'})" for f in meas) + ' (a program counts when it does so in most of its episodes)')
within = {f: O[f]['G (corrected)']['ev']['sonnet-fm vs S-llm mean'] for f in O}
best = {f: O[f]['G (corrected)']['ev']['sonnet-fm vs S-llm best'] for f in O}
add('4. The corrected S-llm mean lands within 0.15 of Sonnet fm per family, and the best program beats Sonnet fm on at least one family with an interval above zero',
    all(abs(within[f]['gap']) <= 0.15 for f in within) and any(best[f]['ci95'][1] < 0 for f in best),
    '; '.join(f"{f}: mean {f3(within[f]['b'])} vs Sonnet {f3(within[f]['a'])} (Sonnet minus mean {within[f]['gap']:+.3f}), best {best[f]['chosen']} {f3(best[f]['b'])} (Sonnet minus best {best[f]['gap']:+.3f}, CI [{best[f]['ci95'][0]:+.3f}, {best[f]['ci95'][1]:+.3f}])" for f in within))
C = F['contrasts']['ev']
c = C['sonnet-fm vs s-neutron']
add('Sonnet fm beats S-neutron on the fresh set with an interval above zero (the agent adapts where a fixed recipe fails)', c['ci95'][0] > 0,
    f"Sonnet fm minus S-neutron {c['gap']:+.3f}, CI [{c['ci95'][0]:+.3f}, {c['ci95'][1]:+.3f}]", 'rule')
c = C['fm-hint vs sonnet-fm']
add('fm-hint resolves less than Sonnet fm on the fresh set with an interval below zero (the advice misleads where the recipe fails)', c['ci95'][1] < 0,
    f"fm-hint minus Sonnet fm {c['gap']:+.3f}, CI [{c['ci95'][0]:+.3f}, {c['ci95'][1]:+.3f}]", 'rule')
for key, kn in (('ev', 'evidence key'), ('reg', 'registered key')):
    bb = {f: O[f]['G (corrected)'][key]['sonnet-fm vs S-llm best'] for f in O}
    fams = [f for f in bb if bb[f]['ci95'][1] < 0]
    add(f'The corrected best program beats Sonnet fm with intervals above zero on at least two families ({kn})', len(fams) >= 2,
        '; '.join(f"{f}: best minus Sonnet {-bb[f]['gap']:+.3f}, CI [{-bb[f]['ci95'][1]:+.3f}, {-bb[f]['ci95'][0]:+.3f}] ({bb[f]['chosen']})" for f in bb), 'rule')
    mm = {f: O[f]['G (corrected)'][key]['sonnet-fm vs S-llm mean'] for f in O}
    add(f'The corrected S-llm mean reaches Sonnet fm ({kn}; read as: the mean is at least Sonnet fm\'s point estimate)', all(mm[f]['b'] >= mm[f]['a'] for f in mm),
        '; '.join(f"{f}: mean {f3(mm[f]['b'])} vs Sonnet {f3(mm[f]['a'])} (mean minus Sonnet {-mm[f]['gap']:+.3f}, CI [{-mm[f]['ci95'][1]:+.3f}, {-mm[f]['ci95'][0]:+.3f}])" for f in mm), 'rule')
json.dump(items, open(os.path.join(H, 'gatesG.json'), 'w'), indent=1)
L = ['| kind | item | result | value |', '|---|---|---|---|'] + [f"| {i['kind']} | {i['item']} | **{i['result']}** | {i['value']} |" for i in items]
open(os.path.join(H, 'GATES_G.md'), 'w').write('\n'.join(L) + '\n')
# ------------------------------------------------ tables
T = ['## Fresh T (30 quads, k = 1)\n', '| arm | quads ev / reg | worlds ev / reg | neutron | free scans only | FMU | D >= 25 | wrong | mean cost (min) |', '|---|---|---|---|---|---|---|---|---|']
for a in ('sonnet-fm', 'fm-hint', 's-broad', 's-neutron', 's-plan', 'gold-oracle (ceiling, k 1)'):
    p = F['per_quad'][a]; w = F['per_world'].get(a)
    T.append(f"| {a} | {f3(p['evidence'])} / {f3(p['registered'])} | " + (f"{w['evidence']:.3f} / {w['registered']:.3f} | {w['neutron_share']:.2f} | {w['free_scan_only_share']:.2f} | {w['FMU']} | {w['D25_rate']:.2f} | {w['wrong']} | {w['mean_cost']} |" if w else '- | - | - | - | - | - | - |'))
T += ['\n### Fresh T contrasts (a minus b, per quad; bootstrap 10,000, seed 20261019)\n', '| key | contrast | a | b | a minus b | 95 % CI | sign test (+/-/0, p) |', '|---|---|---|---|---|---|---|']
for key in ('ev', 'reg'):
    for n, v in F['contrasts'][key].items():
        s = v['sign_test']; T.append(f"| {key} | {n} | {f3(v['a'])} | {f3(v['b'])} | {v['gap']:+.3f} | [{v['ci95'][0]:+.3f}, {v['ci95'][1]:+.3f}] | {s['positive']}/{s['negative']}/{s['ties']}, {s['p']} |")
T += ['\n### S-replay on the fresh agent episodes (decision core on each episode\'s own measurements)\n', '| agent | episodes | agent ev / reg | replay ev / reg | replay minus agent (reg), CI |', '|---|---|---|---|---|']
for a, v in F['s_replay'].items():
    c = v['reg']['contrast_replay_minus_agent']; T.append(f"| {a} | {v['episodes']} | {f3(v['ev']['agent'])} / {f3(v['reg']['agent'])} | {f3(v['ev']['replay'])} / {f3(v['reg']['replay'])} | {c['gap']:+.3f} [{c['ci95'][0]:+.3f}, {c['ci95'][1]:+.3f}] |")
T += ['\n## Offline against online (k = 1, on Sonnet fm\'s compounds)\n', '| family | round | program | ev | reg | measures | neutron |', '|---|---|---|---|---|---|---|']
for fam, o in O.items():
    T.append(f"| {fam} | online | Sonnet fm | {f3(o['sonnet-fm']['evidence'])} | {f3(o['sonnet-fm']['registered'])} | | |")
    for rnd in ('G (corrected)', 'F3 (compromised by V7-E4)'):
        for a, v in o[rnd]['programs'].items():
            T.append(f"| {fam} | {rnd} | {a} | {f3(v['evidence'])} | {f3(v['registered'])} | {v['measured_share']:.2f} | {v['neutron_share']:.2f} |")
T += ['\n### Offline against online contrasts (Sonnet fm minus S-llm; best chosen inside every replicate)\n', '| family | round | key | contrast | Sonnet | S-llm | Sonnet minus S-llm | 95 % CI | sign p |', '|---|---|---|---|---|---|---|---|---|']
for fam, o in O.items():
    for rnd in ('G (corrected)', 'F3 (compromised by V7-E4)'):
        for key in ('ev', 'reg'):
            for n, v in o[rnd][key].items():
                ch = f" ({v['chosen']})" if isinstance(v.get('chosen'), str) else ''
                T.append(f"| {fam} | {rnd} | {key} | {n}{ch} | {f3(v['a'])} | {f3(v['b'])} | {v['gap']:+.3f} | [{v['ci95'][0]:+.3f}, {v['ci95'][1]:+.3f}] | {v['sign_test']['p']} |")
T += ['\n## Combined T table (k = 1; evidence / registered; compounds in brackets)\n', '| arm | paired, 24 Sonnet quads | paired, all 25 | fresh, 30 |', '|---|---|---|---|']
for a, row in A['T_combined'].items():
    cell = lambda nm: f"{f3(row[nm]['evidence'])} / {f3(row[nm]['registered'])} ({row[nm]['compounds']})" if nm in row else ''
    T.append(f"| {a} | {cell('paired (24 Sonnet quads)')} | {cell('paired (all 25)')} | {cell('fresh (30)')} |")
T += ['\n## Behaviour on the fresh set (all episodes of the arm)\n', '| arm | episodes | neutron | free scans only | FM called | world ev / reg | wrong | D >= 25 | mean cost | F3 | F4 | F6 | F9 | F10 | FMU |', '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
for a, b in A['T_behaviour'].items():
    c = b['codes']; T.append(f"| {a} | {b['episodes']} | {b['neutron_share']:.2f} | {b['free_scan_only_share']:.2f} | {b['fm_called_share']:.2f} | {b['world_rate_evidence']:.2f} / {b['world_rate_registered']:.2f} | {b['wrong_conclusions']} | {b['decisive_D25']} | {b['mean_cost']} | {c['F3']} | {c['F4']} | {c['F6']} | {c['F9']} | {c['F10']} | {c['FMU']} |")
open(os.path.join(H, 'TABLES_G.md'), 'w').write('\n'.join(T) + '\n')
for i in items: print(i['kind'], '|', i['item'][:100], '|', i['result'], '|', i['value'][:300])
