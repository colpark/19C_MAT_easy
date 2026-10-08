#!/usr/bin/env python3
"""splits_mc.py (v4.5 MC1; HTEM_MC_RULES section 9 and section 4): freeze split membership before the census. Inputs: census/libraries.csv
(multimodal libraries, multi == 1). Per library: system, split (dev | test | train), dev reason. Families: train MC1 MC2 MC3 MC5; held out MC4
MC6 MC7. Writes v4/htem/MC_SPLITS.json (sorted, deterministic)."""
import csv, hashlib, json, os, random, sys
from collections import defaultdict
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, HERE)
import htem_api as API
rows = [r for r in csv.DictReader(open(os.path.join(API.HOST, 'census', 'libraries.csv'))) if r.get('multi') == '1']
by_sys = defaultdict(list); groups = defaultdict(list)
for r in rows:
    by_sys[r['system']].append(int(r['id']))
    if r.get('recipe'): groups[(r['system'], r['recipe'])].append(int(r['id']))
dev = {}
for s, ids in by_sys.items():
    if len(ids) >= 3: dev[random.Random(f'htem-dev|{s}').choice(sorted(ids))] = 'dev library (htem-dev rule, systems with >= 3 libraries)'
    rg = [(hashlib.sha256((s + k[1]).encode()).hexdigest(), sorted(v)) for k, v in groups.items() if k[0] == s and len(v) >= 2]
    if len(rg) >= 2:
        for i in min(rg)[1]: dev.setdefault(i, 'dev replicate group')
libs = {}
for s, ids in sorted(by_sys.items()):
    for i in sorted(ids):
        sp = 'dev' if i in dev else ('test' if int(hashlib.sha256(f'mc-split|{i}'.encode()).hexdigest(), 16) % 5 == 0 else 'train')
        libs[str(i)] = {'system': s, 'split': sp, **({'dev_reason': dev[i]} if i in dev else {})}
out = {'rule': 'HTEM_MC_RULES.md section 9 (library split by sha256 mc-split|id mod 5 == 0), section 4 (dev)', 'families': {'train': ['MC1', 'MC2', 'MC3', 'MC5'], 'held_out': ['MC4', 'MC6', 'MC7']},
       'pair_rule': 'a pair is test if either member library is test; dev libraries never yield items', 'system_split': 'decided after the census by the frozen rule (fewest MC2 facts), recorded here then',
       'counts': {k: sum(1 for v in libs.values() if v['split'] == k) for k in ('train', 'test', 'dev')}, 'libraries': libs}
json.dump(out, open(os.path.join(HERE, 'MC_SPLITS.json'), 'w'), indent=1, sort_keys=True)
print(out['counts'], 'systems', len(by_sys))
