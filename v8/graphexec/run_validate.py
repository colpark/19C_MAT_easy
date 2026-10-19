"""V6-4 validation of the exemplar trace (V6_SPEC 3): graphexec.validate with both twins, three hold worlds per twin (1013-1015 for A,
1016-1018 for B: displacement +0.10 mm, zero offset +0.005 deg, crystallite size x 1.2; the twin's noise, V6-X4), the non-bypass
evidence of V6-2 (the panel fails the pair; the blind FM planner resolves no pair) and the rendered traces (number lock). Writes
exemplar/validation/result.json (rows), logs/*.json (every intervention log) and VALIDATION.md is written by write_validation.py.
  python v6/graphexec/run_validate.py OUTDIR"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
import graphexec as G
import adapters_mcenv as AD
import run_gold as RG

ROOT6 = os.path.join(HERE, '..')
S0 = RG.SCEN * 10
HOLDS = [('hold_displacement_+0.10mm', 'A', S0 + 3), ('hold_zero_+0.005deg', 'A', S0 + 4), ('hold_size_x1.2', 'A', S0 + 5),
         ('hold_displacement_+0.10mm', 'B', S0 + 6), ('hold_zero_+0.005deg', 'B', S0 + 7), ('hold_size_x1.2', 'B', S0 + 8)]


if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(os.path.join(out, 'logs'), exist_ok=True)
    e = RG.env('v6-4-validate'); g = G.Graph.load(os.path.join(ROOT6, 'spec', 'graph_R.json'))
    twins = {'A': RG.task(e, S0 + 1), 'B': RG.task(e, S0 + 2)}
    holds = [(lab, tw, RG.task(e, w)) for lab, tw, w in HOLDS]
    sel = json.load(open(os.path.join(ROOT6, 'exemplar', 'fastpath', 'targeted.jsonl')).readlines()[-1]) if False else None
    ext = dict(panel_fails=True, blindfm_pairs_resolved=0, source='exemplar/SELECTION.md (bar 2: panel wrong on both twins; bar 5: twins of one formula)')
    rend = {}
    sfx = '' if RG.SCEN == 101 else f'_N{RG.SCEN}'
    for tw, name in (('A', f'gold_A{sfx}'), ('B', f'gold_B{sfx}')):
        p = os.path.join(ROOT6, 'exemplar', 'render', f'{name}.md')
        if os.path.exists(p): rend[name] = (open(p).read(), [json.load(open(os.path.join(ROOT6, 'exemplar', f'{name}.json')))])
    res = G.validate(g, G.Executor(g, AD.ADAPTERS, source='gold'), twins, holds=holds, external=ext, rendered=rend or None)
    for k, lg in res['logs'].items(): json.dump(lg, open(os.path.join(out, 'logs', f'{k}.json'), 'w'), indent=1)
    json.dump(dict(graph_id=res['graph_id'], rows=res['rows'], pass_=res['pass']), open(os.path.join(out, 'result.json'), 'w'), indent=1, default=str)
    json.dump(e.tokens, open(os.path.join(out, 'tokens.json'), 'w'), indent=1)
    print(G.validation_table(res)); print('PASS' if res['pass'] else 'FAIL')
