#!/usr/bin/env python3
"""test_k3.py: offline tests for K3 (V4-E26/27, applied at David's request 2026-10-07).
  K3a join_s.py refuses rules that still carry _todo, and joins once the note is removed
  K3b m0_s.py reports the share of SEM-role files without native pixel metadata and flags it above 5 %
  K3c the round-2 join rules carry no _todo"""
import glob, importlib.util, json, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); KIT = os.path.dirname(HERE); RES = []
def check(label, cond, detail=''):
    RES.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + label + ('' if cond else f'  [{detail}]'), flush=True)
tmp = tempfile.mkdtemp(); ds = 'k3demo'; os.makedirs(f'{tmp}/{ds}')
rows = [{'path': f'files/A/{i}.tif', 'ext': '.tif', 'kind': 'image', 'pixel_size_nm': 5.0, 'pixel_size_source': 'fei'} for i in range(3)]
open(f'{tmp}/{ds}/inventory.jsonl', 'w').write(''.join(json.dumps(r) + '\n' for r in rows))
rules = {'dataset': ds, 'rules': [{'name': 'tiles', 'path_regex': r'files/(?P<s>A)/.*\.tif$', 'role': 'sem_image'}], 'maps': {}, 'condition_fields': ['s'], 'unit_field': 's'}
rp = f'{tmp}/r.json'; json.dump(dict(rules, _todo='fill from the descriptor'), open(rp, 'w'))
p = subprocess.run([sys.executable, '-I', f'{KIT}/join_s.py', '--dataset', ds, '--root', tmp, '--rules', rp], capture_output=True, text=True)
check('K3a: rules with _todo stop the join', p.returncode != 0 and 'K3' in (p.stderr + p.stdout), p.stderr[-200:])
check('K3a: no join.csv written when stopped', not os.path.exists(f'{tmp}/{ds}/join.csv'))
json.dump(rules, open(rp, 'w'))
p = subprocess.run([sys.executable, '-I', f'{KIT}/join_s.py', '--dataset', ds, '--root', tmp, '--rules', rp], capture_output=True, text=True)
check('K3a: confirmed rules join', p.returncode == 0 and os.path.exists(f'{tmp}/{ds}/join.csv'), p.stderr[-200:])
src = open(f'{KIT}/m0_s.py').read()
check('K3b: m0 reports the share without native metadata and flags it above 5 %', 'sem_missing_native_share' in src and 'miss_share > 0.05' in src)
todo = [f for f in glob.glob(f'{KIT}/joinrules/*.json') if json.load(open(f)).get('_todo')]
check('K3c: no round-2 join rules carry _todo', not todo, todo)
print(f'{sum(RES)}/{len(RES)} pass'); sys.exit(0 if all(RES) else 1)
