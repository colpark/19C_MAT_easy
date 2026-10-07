#!/usr/bin/env python3
"""select_pilot.py (stage H2): library choice for the pilot systems in census/PICK.json, frozen before the sample fetch.
Rule, per system (public multimodal libraries only, i.e. XRD + optical + XRF):
  1. replicate groups first: every member of each recipe group with >= 2 libraries (complete recipes), groups by size (desc), then by
     their smallest library id;
  2. then temperature coverage: for every temperature level not yet covered, ascending, the smallest-id library at that level;
  3. then libraries with electrical data (has_ele > 0), by id;
  4. then the rest by id;
  capped at MAX_LIBS = 12 (first come first kept).
Dev library: random.Random('htem-dev|<system>').choice(selected), used for reader tuning only (never a held-out library).
Writes census/PILOT_LIBS.json {system: {selected, dev, held_out, replicate_groups, temps}}. usage: select_pilot.py"""
import csv, json, os, random, sys
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import htem_api as API
OUT = os.path.join(API.HOST, 'census'); MAX_LIBS = 12

def main():
    pick = json.load(open(f'{OUT}/PICK.json')); rows = list(csv.DictReader(open(f'{OUT}/libraries.csv')))
    res = {}
    for role in ('P1', 'P2'):
        sysk = pick.get(role) if isinstance(pick.get(role), str) else (pick.get(role) or {}).get('system')
        if not sysk: continue
        libs = [r for r in rows if r['system'] == sysk and r['multi'] == '1' and r['data_access'] in ('', 'public', 'None')]
        libs.sort(key=lambda r: int(r['id']))
        groups = defaultdict(list)
        for r in libs:
            if r['complete'] == '1': groups[r['recipe']].append(int(r['id']))
        reps = sorted([g for g in groups.values() if len(g) >= 2], key=lambda g: (-len(g), min(g)))
        sel = []
        def add(i):
            if i not in sel and len(sel) < MAX_LIBS: sel.append(i)
        for g in reps:
            for i in sorted(g): add(i)
        temps = sorted({int(float(r['temp_c'])) for r in libs if r['temp_c'] not in ('', 'None')})
        covered = {int(float(r['temp_c'])) for r in libs if int(r['id']) in sel and r['temp_c'] not in ('', 'None')}
        for t in temps:
            if t not in covered:
                c = [int(r['id']) for r in libs if r['temp_c'] not in ('', 'None') and int(float(r['temp_c'])) == t]
                if c: add(min(c)); covered.add(t)
        for r in libs:
            if int(r['has_ele'] or 0) > 0: add(int(r['id']))
        for r in libs: add(int(r['id']))
        dev = random.Random(f'htem-dev|{sysk}').choice(sel) if sel else None
        res[role] = {'system': sysk, 'selected': sel, 'dev': dev, 'held_out': [i for i in sel if i != dev],
                     'replicate_groups': [g for g in reps], 'temps': temps, 'n_multi_available': len(libs)}
    json.dump(res, open(f'{OUT}/PILOT_LIBS.json', 'w'), indent=1); print(json.dumps(res, indent=1))

if __name__ == '__main__':
    main()
