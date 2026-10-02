#!/usr/bin/env python3
"""combine_labels_v024.py: two-family model labels -> labels_v024.json ({id: [label, note]}) and calibration report.
Claude: labeling/labels_l{1,2,3}_*.json (agents, every panel opened; panel_seen audited). GPT-5.6-Sol: labeling/labels_openai_pool.jsonl
(+ labels_openai_cal.jsonl, identical calibration run reused from v0.23). Rule: sound only if both families say sound; otherwise
the more severe label. Calibration truth (hand labels) is read here only, never by labellers."""
import collections, glob, json
SEV = {'sound': 0, 'weak': 1, 'defective': 2}
A = {x['id']: x for x in json.load(open('labeling/all_items.json'))}
cl, seen_bad = {}, []
for f in sorted(glob.glob('labeling/labels_l[123]_*.json')):
    for i, v in json.load(open(f)).items():
        cl[i] = v['label']
        if set(A[i].get('crops') or {}) - set(v.get('panel_seen') or []): seen_bad.append(i)
gp = {}
for f in ('labeling/labels_openai_cal.jsonl', 'labeling/labels_openai_pool.jsonl'):
    for l in open(f):
        r = json.loads(l)
        if r['label']: gp[r['id']] = r['label']
miss = {'claude': [i for i in A if i not in cl], 'gpt': [i for i in A if i not in gp]}
print('items', len(A), '| missing claude', len(miss['claude']), 'gpt', len(miss['gpt']), '| claude items with a panel not viewed:', len(seen_bad))
out = {}
for i in A:
    if i.startswith('CAL-') or i not in cl or i not in gp: continue
    c, g = cl[i], gp[i]; lab = 'sound' if c == g == 'sound' else max((c, g), key=SEV.get)
    out[i] = [lab, f'two families: Claude={c}, GPT={g}']
json.dump(out, open('labels_v024.json', 'w'), indent=1)
T = json.load(open('/home/aid1/Documents/harbor/v022/.private/calibration_truth.json'))
rep = ['| Calibration vs hand labels | Claude | GPT-5.6-Sol | both families sound |', '|---|---|---|---|']
for L in (1, 2, 3):
    ids = [i for i in T if i.startswith(f'CAL-O{L}') and i in cl and i in gp]
    def st(pred):
        ex = sum(pred(i) == T[i][0] for i in ids); ps = [i for i in ids if pred(i) == 'sound']; hs = [i for i in ids if T[i][0] == 'sound']
        tp = sum(T[i][0] == 'sound' for i in ps)
        return f'{ex}/{len(ids)} exact; precision {tp}/{len(ps)}, recall {tp}/{len(hs)}'
    both = lambda i: 'sound' if cl[i] == gp[i] == 'sound' else 'not'
    rep.append(f'| L{L} ({len(ids)}) | {st(lambda i: cl[i])} | {st(lambda i: gp[i])} | {st(both).split("; ")[1]} |')
pool = [i for i in out]
for L in (1, 2, 3):
    p = [i for i in pool if A[i]['level'] == L]
    agree = sum(cl[i] == gp[i] for i in p); split = sum((cl[i] == 'sound') != (gp[i] == 'sound') for i in p)
    rep.append(f'\nL{L} pool {len(p)}: both sound {sum(out[i][0] == "sound" for i in p)}, exact agreement {agree}, split on sound {split}')
open('LABELS_v024.md', 'w').write('\n'.join(rep)); print('\n'.join(rep))
