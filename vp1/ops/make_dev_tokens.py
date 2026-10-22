"""vP.1 development tokens for an authoring round (VP1-2), node A2: fresh k = 99 tokens on round G's development worlds, in round G's order
per session (R 2011 then 2012 with v6-active-fm; H 4011 then 4012 with v7h-fm; T 30101 then 30104 with v7t-fm), one pair per session
FAMi, batch vp1-2-dev-TAG-FAMi. No analysis reads these episodes.
  MCENV_STATE=~/vp1_state python ops/make_dev_tokens.py TAG OUT.json      -> {"R1": [t1, t2], ...}"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mcenv import admin_vp1 as AV  # noqa: E402

DEV = {'R': ((2011, 2012), 'v6-active-fm'), 'H': ((4011, 4012), 'v7h-fm'), 'T': ((30101, 30104), 'v7t-fm')}
tag, out = sys.argv[1], sys.argv[2]
if os.path.exists(out): raise SystemExit(f'{out} exists')
res = {}
for i in range(1, 6):
    for fam, (ws, arm) in DEV.items():
        res[f'{fam}{i}'] = AV._register([dict(world=w, arm=arm, k=99, model=f'dev-{tag}', batch=f'vp1-2-dev-{tag}-{fam}{i}') for w in ws])
json.dump(res, open(out, 'w'), indent=1)
print(len(res), 'sessions')
