#!/usr/bin/env python3
"""carry_labels.py: after the r1-NAT/r1-OCR store rebuild, item ids were renumbered. Carry the round-1 labels (both families) to the new
ids when an item is identical in content: paper, level, question, key, panels, caption spans and crop files. Everything else is new and
goes to round-2 labelling. Writes labeling2/carried.json {new_id: {claude, gpt, old_id}} and labeling2/new_pool_ids.json."""
import json, os
old = json.load(open('open_items_mineru_r1.before_nat.json'))['items']; new = json.load(open('open_items_mineru_r1.json'))['items']
F = json.load(open('r2_flags_v024.json'))
sig = lambda i: json.dumps([i['paper'], i['level'], i.get('question'), i.get('key'), sorted(i['panels']), i.get('captions'), i.get('crops')], sort_keys=True, ensure_ascii=False)
o = {sig(i): i['id'] for i in old}
cl = {}; [cl.update({k: v['label'] for k, v in json.load(open(f'labeling/{f}')).items()}) for f in os.listdir('labeling') if f.startswith('labels_l')]
gp = {json.loads(l)['id']: json.loads(l)['label'] for l in open('labeling/labels_openai_pool.jsonl')}
pool = [i for i in new if not F[i['id']]['removed_by'] and i.get('type') != 'trend']
os.makedirs('labeling2', exist_ok=True); carried, fresh = {}, []
for i in pool:
    oid = o.get(sig(i))
    if oid and oid in cl and oid in gp: carried[i['id']] = {'claude': cl[oid], 'gpt': gp[oid], 'old_id': oid}
    else: fresh.append(i['id'])
json.dump(carried, open('labeling2/carried.json', 'w'), indent=1); json.dump(fresh, open('labeling2/new_pool_ids.json', 'w'))
print('pool', len(pool), '| carried', len(carried), '| new to label', len(fresh), '| old labelled pool items not found again', len(set(cl) & {v for v in o.values()} - {c['old_id'] for c in carried.values()} - {x for x in cl if x.startswith('CAL')}))
