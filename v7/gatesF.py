"""V7-F5: every pre-registered gate and expectation of v7 (PREREG.md), V7-X8, V7-X10, V7-P (PREREG_P.md) and V7-F, each reported as
met or not met (gates: passed or failed), with the number it rests on. Never relaxed (I5). Inputs: analyzeF.py's output (both keys),
analyze7.py's output on Sonnet at k = 1 (the pre-registered V7-5 code; gate T item 3 and gate H item 2 compute over the compounds
Sonnet runs at k = 1, V7-X8), T/baselines_T.json, P/runs/audit, F/sllm/run. Key per source: the v7 gates and expectations and V7-P use
their registered keys (V7-X4; B1 truth-only); V7-F uses the evidence key first. Both are printed where both exist.
  python v7/gatesF.py ANALYSIS_F.json ANALYZE7.json OUT.json OUT.md"""
import glob, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
A = json.load(open(sys.argv[1])); A7 = json.load(open(sys.argv[2])); OUT, MD = sys.argv[3], sys.argv[4]
items = []


def add(source, name, met, value, kind='expectation', note=''):
    items.append(dict(source=source, item=name, kind=kind,
                      result=(('passed' if met else 'failed') if kind == 'gate' else ('met' if met else 'not met')) if met is not None else 'not computable',
                      value=value, note=note))


def L(fam, arm, key='registered'): return (A[fam]['ladder_matched_k1']['arms'].get(arm) or {}).get(key)
def C(fam, name, key='reg'): return A[fam]['contrasts'][key].get(name)
def B(fam, arm): return A[fam]['behaviour'].get(arm) or {}
def W(fam, arm): return A[fam]['world_level_k1_matched'].get(arm) or {}


T7, H7 = A7['T'], A7['H']
# ---------------------------------------------------------------- v7 main: expectations (registered key, Sonnet k = 1)
r = T7['rate']; add('v7', 'T: noprior resolves at most 0.10 of quads', r['v7t-noprior'] <= 0.10, f"noprior {r['v7t-noprior']}")
ds = T7['arms']['v7t-noprior']['shortcut_signatures']['downhill_share_of_determinate_L_to_H']
add('v7', 'T: in noprior, at least half of determinate L to H verdicts are SUPPORTED', None if ds is None else ds >= 0.5,
    f"{ds} of {T7['arms']['v7t-noprior']['shortcut_signatures']['L_to_H_determinate']} determinate L to H")
add('v7', 'T: fm resolves 0.25 to 0.45 of quads', 0.25 <= r['v7t-fm'] <= 0.45, f"fm {r['v7t-fm']}")
tr = A7.get('T_vs_R_paired')
if tr: add('v7', 'T: on the paired set T fm falls below B1 R fm by 0.1 to 0.3', 0.1 <= -tr['mean_T_fm_minus_R_fm'] <= 0.3,
           f"T fm {tr['mean_T_fm']} vs R fm {tr['mean_R_fm']} (T minus R {tr['mean_T_fm_minus_R_fm']}, n {tr['n']})", note=tr['note'] + '; T at k = 1')
h = H7['rate']; add('v7', 'H: noprior resolves at most 0.15 of pairs', h['v7h-noprior'] <= 0.15, f"noprior {h['v7h-noprior']}")
bt = H7['by_type']
add('v7', 'H: fm gains at least 0.2 on type E', bt['E']['gap'] >= 0.2, f"type E gap {bt['E']['gap']} (n {bt['E']['n']})")
add('v7', 'H: type M resolves at least 0.2 below type E (fm)', bt['E']['fm'] - bt['M']['fm'] >= 0.2, f"fm E {bt['E']['fm']}, M {bt['M']['fm']}")
# ---------------------------------------------------------------- v7 main: gates
add('v7', 'Gate T item 1: kit D passes; selection rows pass on all 30 fresh and at least 26 paired', False, 'paired 25 of 30 (306, 314, 315, 320, 323)', 'gate', 'reported FAILED at V7-X10, not relaxed')
bl = json.load(open(os.path.join(HERE, 'T', 'baselines_T.json')))
blr = {k: v['quads_resolved'] for k, v in bl['rules'].items() if k != 'oracle rule'}
add('v7', 'Gate T item 2: the offline baselines resolve 0 quads', all(x == 0 for x in blr.values()),
    json.dumps(blr) + f"; positive control (oracle rule) {bl['rules']['oracle rule']['quads_resolved']} of {bl['n_quads']}", 'gate')
add('v7', 'Gate T item 3: fm minus noprior quad resolution above zero, 95 % interval above zero (24 compounds, k = 1)', bool(T7['ci95'] and T7['ci95'][0] > 0),
    f"gap {T7['gap']}, CI {T7['ci95']}, sign test {T7['sign_test']}", 'gate', 'k = 1 and 24 compounds lower the power (V7-X8)')
add('v7', 'Gate H item 1: Gate H-supply passed', False, '15 E, 8 M against 16 E, 5 M', 'gate', 'FAILED, waived by David (V7-X6), not relaxed')
add('v7', 'Gate H item 2: fm minus noprior pair resolution above zero, 95 % interval above zero (23 compounds, k = 1)', bool(H7['ci95'] and H7['ci95'][0] > 0),
    f"gap {H7['gap']}, CI {H7['ci95']}, sign test {H7['sign_test']}", 'gate')
add('v7', 'Gate H item 3: type M reported as its own stratum', True, f"type M n {bt['M']['n']}, gap {bt['M']['gap']}", 'gate')
# ---------------------------------------------------------------- V7-X8 expectations (secondary models)
for fam in ('T', 'H'):
    hs, ss = C(fam, 'haiku-fm vs haiku-noprior'), C(fam, 'sonnet-fm vs sonnet-noprior (k1)')
    sh = C(fam, 'sonnet-fm vs sonnet-noprior (k1)')
    if hs and ss: add('V7-X8', f'{fam}: Haiku shows a positive FM gap, below Sonnet\'s', hs['gap'] > 0 and hs['gap'] < ss['gap'],
                      f"Haiku {hs['gap']} {hs['ci95']} (n {hs['n_compounds']}); Sonnet {ss['gap']} {ss['ci95']} (n {ss['n_compounds']})")
    q = [L(fam, a) for a in ('qwen3-8b-fm', 'qwen3-8b-noprior') if L(fam, a) is not None]
    if q: add('V7-X8', f'{fam}: Qwen3-8B resolves almost nothing', max(q) <= 0.05, f'fm {L(fam, "qwen3-8b-fm")}, noprior {L(fam, "qwen3-8b-noprior")}')
# ---------------------------------------------------------------- V7-X10 expectations
b = B('T', 'sonnet-fm'); add('V7-X10', 'Sonnet fm takes no measurement beyond the free scans in at least 10 % of T episodes', b['free_scan_only_share'] >= 0.10, f"{b['free_scan_only_share']} of {b['episodes']}")
c = C('T', 'V7-P primary: sonnet-fm vs stronger of s-broad, s-neutron (k1)')
add('V7-X10', 'The stronger of S-broad and S-neutron resolves more T quads than Sonnet fm', c['gap'] < 0, f"Sonnet fm {c['a']} vs {c['chosen']} {c['b']} (gap {c['gap']}, CI {c['ci95']})")
# ---------------------------------------------------------------- V7-P gate and expectations (registered key primary)
aud = [json.load(open(f)) for f in glob.glob(os.path.join(HERE, 'P', 'runs', 'audit', '*.json')) if not f.endswith('test.json')]
sl = [json.loads(l) for f in glob.glob(os.path.join(HERE, 'F', 'sllm', 'run', 'episodes*.jsonl')) for l in open(f)]
add('V7-P', 'Gate P-1: isolation (scripts as own client processes from a clean folder; no privileged read; S-plan registers only hypothetical worlds)',
    not any(a['breach'] for a in aud), f"{len(aud)} audited script episodes, {sum(a['breach'] for a in aud)} breaches", 'gate')
for fam in ('B1', 'H'):
    rp = A[fam]['s_replay']
    vals = {a: (v['reg']['replay'], v['reg']['agent']) for a, v in rp.items() if a != 'fm-hint'}
    add('V7-P', f'{fam}: S-replay lands within 0.05 of each agent', all(abs(x - y) <= 0.05 for x, y in vals.values()) if vals else None,
        json.dumps({a: dict(replay=x, agent=y) for a, (x, y) in vals.items()}))
c = C('H', 'V7-P primary: sonnet-fm vs stronger of s-broad, s-neutron (all k)')
add('V7-P', 'H: the stronger fixed recipe exceeds Sonnet fm by at least 0.2', -c['gap'] >= 0.2, f"{c['chosen']} {c['b']} vs Sonnet fm {c['a']} (Sonnet minus recipe {c['gap']}, CI {c['ci95']})")
hb, hn = A['H']['ladder']['s-broad']['registered'], A['H']['ladder']['s-neutron']['registered']
add('V7-P', 'H: S-neutron beats S-broad', hn > hb, f'S-neutron {hn}, S-broad {hb} (k 1-4)')
c = C('B1', 'V7-P primary: sonnet-fm vs stronger of s-broad, s-neutron (all k)')
add('V7-P', 'B1: the stronger fixed recipe lands within 0.1 of Sonnet fm', abs(c['gap']) <= 0.1, f"{c['chosen']} {c['b']} vs Sonnet fm {c['a']} (gap {c['gap']}, CI {c['ci95']})")
for fam in ('B1', 'H'):
    lad = A[fam]['ladder']; sp = lad['s-plan']['registered']; m = max(lad['s-broad']['registered'], lad['s-neutron']['registered'])
    add('V7-P', f'{fam}: S-plan is at least as high as both fixed recipes', sp >= m, f"S-plan {sp}, S-broad {lad['s-broad']['registered']}, S-neutron {lad['s-neutron']['registered']}")
FMW = {'B1': {'202'}, 'H': {'401', '416', '422'}}
for fam in ('B1', 'H'):
    w = {}
    for a in ('s-broad', 's-neutron', 's-plan'):
        for s, n in (A[fam]['wrong_conclusions_by_compound'].get(a) or {}).items(): w[s] = w.get(s, 0) + n
    tot = sum(w.values()); on = sum(n for s, n in w.items() if s in FMW[fam])
    add('V7-P', f'{fam}: script wrong conclusions concentrate on the FM-wrong compounds ({", ".join(sorted(FMW[fam]))})', (on / tot > 0.5) if tot else None,
        f'{on} of {tot} on those compounds; by compound {json.dumps(w)}')
for fam in ('B1', 'H'):
    pc = A[fam]['per_compound_all_k']; wins = []
    for s, d in pc.items():
        if 'sonnet-fm' not in d or not all(x in d for x in ('s-broad', 's-neutron', 's-plan')): continue
        if all(d['sonnet-fm']['reg'] > d[x]['reg'] for x in ('s-broad', 's-neutron', 's-plan')): wins.append(s)
    add('V7-P', f'{fam}: Sonnet beats every script on at least 3 compounds', len(wins) >= 3, f'{len(wins)} compounds: {wins}')
# ---------------------------------------------------------------- V7-F expectations (evidence key first)
for fam in ('B1', 'H', 'T'):
    progs = sorted(a for a in A[fam]['behaviour'] if a.startswith('sllm-'))
    if not progs: continue
    nn = [a for a in progs if B(fam, a)['neutron_share'] > 0.5]
    ag = W(fam, 'sonnet-fm')
    within = {a: round(W(fam, a)['evidence'] - ag['evidence'], 4) for a in progs}
    add('V7-F', f'{fam}: at most 2 of 5 S-llm programs take the neutron', len(nn) <= 2, f'{len(nn)} take it in most episodes: {nn}; neutron shares ' + json.dumps({a: B(fam, a)["neutron_share"] for a in progs}))
    add('V7-F', f'{fam}: the S-llm programs score within 0.1 of the agent per world', all(abs(v) <= 0.1 for v in within.values()),
        f"agent (Sonnet fm, k 1) {ag['evidence']} per world; program minus agent " + json.dumps(within))
for fam in ('B1', 'H', 'T'):
    w = W(fam, 'fm-hint')
    if not w: continue
    add('V7-F', f'{fam}: fm-hint takes the neutron in at least 80 % of episodes', w['neutron_share'] >= 0.8, f"{w['neutron_share']} of {w['worlds']}")
    add('V7-F', f'{fam}: fm-hint stops after the free scans in under 5 % of episodes', w['free_scan_only_share'] < 0.05, f"{w['free_scan_only_share']}")
    if fam in ('B1', 'H'):
        sn = W(fam, 's-neutron')
        add('V7-F', f'{fam}: fm-hint lands within 0.1 of S-neutron per world', abs(w['evidence'] - sn['evidence']) <= 0.1, f"fm-hint {w['evidence']}, S-neutron {sn['evidence']} (k 1, matched worlds)")
c = C('T', 'sonnet-fm vs s-neutron (k1)', 'ev')
add('V7-F', 'T: S-neutron resolves more quads than Sonnet fm, with an interval above zero', bool(c['ci95'][1] < 0), f"Sonnet fm {c['a']} vs S-neutron {c['b']}; Sonnet minus S-neutron {c['gap']}, CI {c['ci95']}")
hs, ss = C('T', 'haiku-fm vs haiku-noprior', 'ev'), C('T', 'sonnet-fm vs sonnet-noprior (k1)', 'ev')
add('V7-F', 'T: Haiku shows a smaller FM gap than Sonnet', hs['gap'] < ss['gap'], f"Haiku {hs['gap']} (n {hs['n_compounds']}), Sonnet {ss['gap']} (n {ss['n_compounds']}); evidence key")
add('V7-F', 'T: Qwen resolves almost nothing', max(L('T', 'qwen3-8b-fm', 'evidence'), L('T', 'qwen3-8b-noprior', 'evidence')) <= 0.05, f"fm {L('T', 'qwen3-8b-fm', 'evidence')}, noprior {L('T', 'qwen3-8b-noprior', 'evidence')}")
for fam in ('B1', 'H', 'T'):
    rs = A[fam]['recipe_strata_k1'].get('ev')
    if not rs: continue
    arms = {a: v for a, v in rs['arms'].items() if a not in ('s-broad', 's-neutron') and v['solvable'] is not None and v['fails'] is not None}
    viol = {a: v for a, v in arms.items() if not v['fails'] < v['solvable']}
    add('V7-F', f'{fam}: on the recipe-fails stratum every arm resolves less than on the recipe-solvable stratum', not viol,
        f"solvable {len(rs['solvable'])} compounds, fails {len(rs['fails'])}; arms not lower on fails: " + json.dumps(viol))
json.dump(items, open(OUT, 'w'), indent=1)
with open(MD, 'w') as f:
    f.write('| source | kind | item | result | value |\n|---|---|---|---|---|\n')
    for it in items:
        f.write(f"| {it['source']} | {it['kind']} | {it['item']} | **{it['result']}** | {it['value']}{' (' + it['note'] + ')' if it['note'] else ''} |\n")
for it in items: print(it['source'], '|', it['item'][:90], '|', it['result'])
