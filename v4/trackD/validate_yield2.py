#!/usr/bin/env python3
"""validate_yield2.py (D1b, rule I7; replaces the validate_yield.py gate, whose 'truth' was the procedure itself on the noise-free curve,
so it tested noise robustness only, and whose apparent moduli 20-60 GPa missed the real 4-15 GPa of the deposit's rigs: V4-E15).
Synthetic crosshead curves in the real regime: apparent modulus Ea 4-15 GPa, seating toe 0-0.03 strain (saturating exponential), gradual elastic-plastic
transition (Ramberg-Osgood plastic strain (s / K)^n with n 6-15 calibrated so that the true 0.2 % offset stress is sy), sy 80-400 MPa,
force noise 0.3 %, ~2600 points to 0.3 strain. Truth = sy, the 0.2 % offset on the TRUE
elastic line (known slope Ea and toe intercept). Gates: >= 90 % of curves within 5 %; ranking of two curves whose sy differ by 10 % (same
rig parameters) preserved in >= 95 %."""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import yieldproc as Y
rng = np.random.default_rng(23)
def curve(sy, Ea, toe, n, H=0):
    """seating toe: extra strain toe (1 - exp(-s / st)), st = 0.08 sy, so the true elastic line is s = Ea (e - toe) once seated;
    Ramberg-Osgood plastic strain (s / K)^n with (sy / K)^n = 0.002, so sy is the true 0.2 % offset stress."""
    K = sy / 0.002 ** (1 / n); s = np.linspace(0, 3 * sy, 8000); e = s / Ea + (s / K) ** n + toe * (1 - np.exp(-s / (0.08 * sy)))
    m = e <= 0.3; e, s = e[m], s[m]; grid = np.linspace(0, e.max(), 2600); return grid, np.interp(grid, e, s)
rows = []; rank = []
for k in range(300):
    sy = rng.uniform(80, 400); Ea = rng.uniform(4e3, 15e3); toe = rng.choice([0.0, rng.uniform(0.002, 0.03)]); n = rng.uniform(6, 15)
    e, s = curve(sy, Ea, toe, n, 0); nz = s + rng.normal(0, 0.003 * s.max() / 3, s.size)
    r = Y.yield_02(nz, e); rows.append({'sy': sy, 'Ea': Ea, 'toe': float(toe), 'n': n, 'got': r['ys'] if r else None, 'err': abs(r['ys'] - sy) / sy if r else 1.0})
    e2, s2 = curve(sy * 1.1, Ea, toe, n, 0); n2 = s2 + rng.normal(0, 0.003 * s2.max() / 3, s2.size); r2 = Y.yield_02(n2, e2)
    rank.append(bool(r and r2 and r2['ys'] > r['ys']))
err = np.array([r['err'] for r in rows])
res = {'n': len(rows), 'within_5pct': float(np.mean(err <= 0.05)), 'median_err': float(np.median(err)), 'rank_10pct': float(np.mean(rank)),
       'within_5pct_toe': float(np.mean(err[[r['toe'] > 0 for r in rows]] <= 0.05)), 'within_5pct_notoe': float(np.mean(err[[r['toe'] == 0 for r in rows]] <= 0.05)),
       'worst': sorted(rows, key=lambda r: -r['err'])[:5]}
res['gates'] = {'within': res['within_5pct'] >= 0.9, 'rank': res['rank_10pct'] >= 0.95}
json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'validate_yield2.json'), 'w'), indent=1, default=float)
print({k: v for k, v in res.items() if k != 'worst'}); print(res['worst'][:3])
