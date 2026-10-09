#!/usr/bin/env python3
"""energy_mc2.py (v4.5 MC v2, rules section 3): the L3 energy E per system from dev libraries only, before the census.
Writes v4/htem/MC2_ENERGY.json."""
import json, os, sys
from collections import defaultdict
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_mc2 as CM
GRID = [round(1.6 + 0.1 * k, 1) for k in range(17)]
dev = defaultdict(list)
for r in CM.ROWS:
    if CM.SPL.get(r['id'], {}).get('split') == 'dev':
        P = CM.positions(r['id'])
        if P: dev[r['system']].append((r['id'], P))
systems = sorted({r['system'] for r in CM.ROWS}); out = {}
for s in systems:
    best = None; used = [lid for lid, _ in dev.get(s, [])]
    for E in GRID:
        sds, ts = [], []
        for _, P in dev.get(s, []):
            tr = []
            for p in P:
                if not p['opt']: continue
                e, t, r = p['opt']
                if E - 0.05 >= e[0] and E + 0.05 <= e[-1]:
                    g = np.linspace(E - 0.05, E + 0.05, 5); tr.append((np.mean(np.interp(g, e, t)), np.mean(np.interp(g, e, r))))
            if len(tr) >= 10: sds.append(float(np.std([b for _, b in tr]))); ts += [a for a, _ in tr]
        if sds and np.median(ts) >= 0.3 and (best is None or np.median(sds) > best[1] + 1e-12): best = (E, float(np.median(sds)))
    out[s] = {'E_eV': best[0] if best else 2.5, 'rule': 'dev max median SD of R' if best else 'default 2.5 eV', 'dev_libraries': used,
              'score': best[1] if best else None}
json.dump(out, open(os.path.join(CM.HERE, 'MC2_ENERGY.json'), 'w'), indent=1, sort_keys=True)
print(sum(v['rule'] != 'default 2.5 eV' for v in out.values()), 'systems from dev,', sum(v['rule'] == 'default 2.5 eV' for v in out.values()), 'default')
