#!/usr/bin/env python3
"""tune_s4r.py (S4r): grid search of the reader parameters SIGMA, OPEN and PORE_SHIFT on synthetic DEV seeds 0-29 only (fresh seeds
10000+ are reserved for the frozen gates). Score: mean of the worst absolute error over porosity, anhydrous and hydrate per tile; ties go
to the smoother setting. Writes tune_s4r.json; the chosen values are then written into s4r_reader.py and frozen (S4r)."""
import itertools, json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); import s4r_reader as R, synth_s4r as G
tiles = [G.tile(s) for s in range(30)]
res = []
for sig, op, ps in itertools.product([1.5, 2.0, 3.0, 4.0], [1, 3, 5], [-20, -10, -5, 0, 5, 10]):
    R.SIGMA, R.OPEN, R.PORE_SHIFT = sig, op, ps; err = []
    for img, tr in tiles:
        r = R.read_array(img)
        err.append(max(abs(r[k] - tr[k]) for k in ('porosity', 'anhydrous', 'hydrate')) if r['ok'] else 1.0)
    res.append({'SIGMA': sig, 'OPEN': op, 'PORE_SHIFT': ps, 'mean_worst_err': float(np.mean(err)), 'within_0.02': float(np.mean(np.array(err) <= 0.02))})
res.sort(key=lambda d: (d['mean_worst_err'], -d['SIGMA']))
json.dump({'dev_seeds': list(range(30)), 'grid': res}, open(f'{HERE}/tune_s4r.json', 'w'), indent=1)
for d in res[:8]: print(d)
