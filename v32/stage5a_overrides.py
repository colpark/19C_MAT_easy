#!/usr/bin/env python3
"""stage5a_overrides.py: apply the Sol tag audit restrictively (hard rule 3): a node the builder tagged M and Sol tagged A (or S/D) becomes
A; computed_from = the Sol sources that are node ids, else a processing model by the authors (no law parameter). Evidence keeps the
builder's span and adds the override. usage: stage5a_overrides.py <key> ..."""
import json, sys
V32 = '/home/aid1/Documents/harbor/v32'; sys.path.insert(0, V32)
import provenance as P
for k in sys.argv[1:]:
    PD = f'{V32}/papers/{k}'; nodes = json.load(open(f'{PD}/nodes.json')); ov = json.load(open(f'{PD}/audit/tag_overrides.json')); ids = {n['id'] for n in nodes}; done = []
    for n in nodes:
        o = ov.get(n['id'])
        if not o or n['level'] != 'M': continue
        cf = [c for c in (o.get('computed_from_sol') or []) if c in ids and c != n['id']]
        n['level'] = 'A'; n['computed_from'] = cf
        if not cf: n['params'] = (n.get('params') or []) + [{'name': 'processing of raw readings (Sol tag audit)', 'kind': 'fit', 'by': 'authors', 'fit_on': []}]
        n['evidence']['sol_override'] = o['reason']; done.append(n['id'])
    P.Graph([dict(x, evidence={'kind': x['evidence']['kind'], 'text': x['evidence']['text']}) for x in nodes])
    json.dump(nodes, open(f'{PD}/nodes.json', 'w'), indent=1, ensure_ascii=False); print(k, 'tagged A by the audit:', done)
