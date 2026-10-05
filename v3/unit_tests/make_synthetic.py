#!/usr/bin/env python3
"""synthetic matrix for dry runs of generate.py before the freeze: invented n_H, mu_H, kappa per (x, T); the other
quantities follow laws.py, then fixed offsets break a few relations (to exercise routing). Nothing here comes from the paper."""
import json, os, sys, shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import laws as L
out = sys.argv[1]; os.makedirs(f'{out}/matrix', exist_ok=True); os.makedirs(f'{out}/digitized', exist_ok=True)
V3 = '/home/aid1/Documents/harbor/v3'
S = [0.0, 0.005, 0.01, 0.02, 0.04]; G = [300, 350, 400, 450, 500, 550, 600]
cells, points = [], []
for i, x in enumerate(S):
    for T in G:
        n = 0.6 + 0.8 * i + 0.002 * (T - 300); mu = 150 - 10 * i - 0.2 * (T - 300); kap = 1.0 + 0.05 * i + 0.0005 * (T - 300)
        rho = L.rho_hall(n, mu); s = -L.spb_S(n, T); ke = L.kappa_e(s, rho, T)
        v = {'F4a': n, 'F4b': mu, 'F5a': rho, 'F5b': s, 'F5c': L.pf(s, rho) * (0.5 if x == 0.005 else 1.0), 'F5d': kap, 'F5e': ke,
             'F5f': kap - ke, 'F6a': L.zt(s, rho, kap, T)}
        for p, val in v.items():
            u = 0.02 * abs(val)
            cells.append({'id': f'{p}:x={x}:T={T}', 'panel': p, 'sample_x': x, 'T': T, 'value': val, 'u': u, 'rel_u': 0.02, 'how': 'marker', 'occluded': False})
            points.append({'panel': p, 'x': x, 'T': T, 'value': val, 'u': u, 'occluded': False})
for p in ['F4a', 'F4b', 'F5a', 'F5b', 'F5c', 'F5d', 'F5e', 'F5f', 'F6a']:
    json.dump({'legend': {'clean': True, 'mapping_source': 'own legend'}, 'series': {str(x): [{}] * 5 for x in S}}, open(f'{out}/digitized/{p}.json', 'w'))
with open(f'{out}/matrix/cells.jsonl', 'w') as f:
    for c in cells: f.write(json.dumps(c) + '\n')
with open(f'{out}/matrix/points.jsonl', 'w') as f:
    for c in points: f.write(json.dumps(c) + '\n')
shutil.copy(f'{V3}/matrix/panels.json', f'{out}/matrix/'); shutil.copy(f'{V3}/matrix/text_values.jsonl', f'{out}/matrix/')
print(len(cells), 'synthetic cells in', out)
