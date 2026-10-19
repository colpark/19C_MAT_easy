"""V7-2 step 3: offline baselines on every T quad, with oracle values (the true polymorph of each sample, DFT energies). A quad is resolved
by a rule only if its verdict equals the key in all four cells. Each must resolve 0 quads (Gate T, item 2).
  constant REFUTED      always REFUTED
  post only             SUPPORTED iff the post sample's polymorph is the formula's lowest (DFT)
  pre only              SUPPORTED iff the pre sample's polymorph is not the lowest
  downhill              SUPPORTED iff the two samples hold different polymorphs (a change means downhill; no energy used)
  oracle rule           SUPPORTED iff E(post) < E(pre) (DFT; the graph rule with exact values): must resolve every quad
  python v7/T/baselines_T.py"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
CELLS = {1: ('H', 'L', 'SUPPORTED'), 2: ('L', 'L', 'REFUTED'), 3: ('H', 'H', 'REFUTED'), 4: ('L', 'H', 'REFUTED')}
W = [w for w in json.load(open(os.path.join(HERE, 'WORLDS_T.json')))['worlds'] if w.get('slot', 'take') == 'take']
rules = {
    'constant REFUTED': lambda pre, post, E, low: 'REFUTED',
    'post only': lambda pre, post, E, low: 'SUPPORTED' if post == low else 'REFUTED',
    'pre only': lambda pre, post, E, low: 'SUPPORTED' if pre != low else 'REFUTED',
    'downhill': lambda pre, post, E, low: 'SUPPORTED' if pre != post else 'REFUTED',
    'oracle rule': lambda pre, post, E, low: 'SUPPORTED' if E[post] < E[pre] else 'REFUTED'}
out = {r: dict(quads_resolved=0, worlds_correct=0, failed_cells={}) for r in rules}
for w in W:
    nm = w['names_by_id']; E = {nm[i]: w['dft'][nm[i]]['e_form'] for i in w['polymorph_ids']}
    low = min(E, key=E.get); ph = {'L': nm[w['L']], 'H': nm[w['H']]}
    assert ph['L'] == low, (w['formula'], 'L is not the lowest')
    for r, f in rules.items():
        ok = {c: f(ph[a], ph[b], E, low) == key for c, (a, b, key) in CELLS.items()}
        out[r]['worlds_correct'] += sum(ok.values())
        out[r]['quads_resolved'] += all(ok.values())
        for c, v in ok.items():
            if not v: out[r]['failed_cells'][str(c)] = out[r]['failed_cells'].get(str(c), 0) + 1
res = dict(n_quads=len(W), rules=out, passes=all(out[r]['quads_resolved'] == 0 for r in rules if r != 'oracle rule') and out['oracle rule']['quads_resolved'] == len(W))
json.dump(res, open(os.path.join(HERE, 'baselines_T.json'), 'w'), indent=1)
for r, v in out.items(): print(r, v)
print('baselines pass' if res['passes'] else 'BASELINES FAIL')
