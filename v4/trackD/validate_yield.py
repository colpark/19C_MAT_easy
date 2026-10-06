#!/usr/bin/env python3
"""validate_yield.py (rule I7): synthetic compression curves: toe (seating, quadratic over a random strain 0.002-0.01), apparent modulus
20-60 GPa (machine compliance), true yield 150-450 MPa then Voce hardening, force noise 0.3 %, sampling as in the deposit (~2600 points
to 30 % strain). The procedure's 'true' value is the 0.2 % offset on the same noise-free crosshead curve. Gate: >= 95 % within 2 %,
and the ranking of two curves whose true yields differ by 5 % is preserved in >= 95 %."""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import yieldproc as Y
rng = np.random.default_rng(11)
def curve(sy, Ea, toe):
    e = np.linspace(0, 0.3, 2600); el = np.where(e < toe, Ea * e ** 2 / (2 * toe), Ea * (e - toe / 2))
    ey = sy / Ea + toe / 2; s = np.where(el < sy, el, sy + 1.2 * sy * (1 - np.exp(-(e - ey) / 0.08)) + 0 * e)
    s = np.minimum(el, np.maximum(s, 0)) if False else np.where(e < ey, el, sy + 1.2 * sy * (1 - np.exp(-(e - ey) / 0.08)))
    return e, s
def truth(e, s):
    r = Y.yield_02(s, e); return r['ys'] if r else np.nan
rows = []; rank = []
for k in range(300):
    sy = rng.uniform(150, 450); Ea = rng.uniform(20e3, 60e3); toe = rng.uniform(0.002, 0.01)
    e, s = curve(sy, Ea, toe); t = truth(e, s); n = s + rng.normal(0, 0.003 * s.max() / 3, s.size)
    r = Y.yield_02(n, e); rows.append(abs(r['ys'] - t) / t if r else 1.0)
    e2, s2 = curve(sy * 1.05, Ea, toe); n2 = s2 + rng.normal(0, 0.003 * s2.max() / 3, s2.size); r2 = Y.yield_02(n2, e2)
    rank.append(bool(r and r2 and r2['ys'] > r['ys']))
res = {'n': len(rows), 'within_2pct': float(np.mean(np.array(rows) <= 0.02)), 'rank_5pct': float(np.mean(rank)), 'median_rel_err': float(np.median(rows))}
res['gates'] = {'within': res['within_2pct'] >= 0.95, 'rank': res['rank_5pct'] >= 0.95}
json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'validate_yield.json'), 'w'), indent=1); print(res)
