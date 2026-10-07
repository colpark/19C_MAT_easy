#!/usr/bin/env python3
"""validate_yield_alsi.py (S4e, rule I7): the CrFeNi 0.2 % offset procedure (trackD/yieldproc.py, D1c) in the AlSi10Mg curve regime
(B2: strain from a 24 mm DIC virtual extensometer, so no machine compliance and no seating toe; engineering stress from load / area).
Synthetic curves: E 55-80 GPa, Ramberg-Osgood exponent 4-15 (rounded yielding of AM AlSi10Mg), true 0.2 % offset stress 150-300 MPa,
fracture strain 2-10 %, ~600 points as in the workbooks, DIC strain noise sigma 2e-5 (plus 10 % of curves 1e-4), stress noise 0.5 MPa.
Gates (frozen with this file): >= 90 % of curves within 5 % of the true offset stress; ranking of 10 %-different pairs preserved >= 95 %.
UTS (maximum engineering stress) needs no procedure beyond the maximum. Output validate_yield_alsi.json."""
import json, os, sys
import numpy as np
sys.path.insert(0, '/home/aid1/Documents/harbor/v4/trackD'); import yieldproc as Y
rng = np.random.default_rng(41)
def curve(sy, E, n, ef, noise_e):
    K = sy / 0.002 ** (1 / n); s = np.linspace(0, 3 * sy, 20000); e = s / E + (s / K) ** n; m = e <= ef; e, s = e[m], s[m]
    g = np.linspace(0, e.max(), 600); sg = np.interp(g, e, s); return g + rng.normal(0, noise_e, g.size), sg + rng.normal(0, 0.5, g.size)
rows = []; rank = []
for k in range(300):
    sy = rng.uniform(150, 300); E = rng.uniform(55e3, 80e3); n = rng.uniform(4, 15); ef = rng.uniform(0.02, 0.10); ne = 1e-4 if rng.random() < 0.1 else 2e-5
    e, s = curve(sy, E, n, ef, ne); r = Y.yield_02(s, e); rows.append({'sy': sy, 'got': r['ys'] if r else None, 'err': abs(r['ys'] - sy) / sy if r else 1.0})
    e2, s2 = curve(sy * 1.1, E, n, ef, ne); r2 = Y.yield_02(s2, e2); rank.append(bool(r and r2 and r2['ys'] > r['ys']))
err = np.array([r['err'] for r in rows])
res = {'n': len(rows), 'within_5pct': float(np.mean(err <= 0.05)), 'median_err': float(np.median(err)), 'rank_10pct': float(np.mean(rank))}
res['gates'] = {'within': res['within_5pct'] >= 0.9, 'rank': res['rank_10pct'] >= 0.95}
json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'validate_yield_alsi.json'), 'w'), indent=1); print(res)
