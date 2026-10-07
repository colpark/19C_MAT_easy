#!/usr/bin/env python3
"""validate_regions_v3.py (B13, rule I7): synthetic spectra at the counts of a real 6 x 6 binned pixel (deposit: 135-661 counts in the
0.85-2.65 keV window and 16-391 in 5.2-8.9 keV, 10th-90th percentile): validate_eds.py line shapes and curved background scaled to 0.07-0.65
counts per channel, lines of 0, 30, 60, 200 or 800 net counts. Gates: (a) false positives: z >= 5 for an absent line in <= 1 % of spectra;
(b) calibration: for lines of >= 200 counts, SD of (net - true) / se within 0.8-1.25 and |mean| <= 0.3; (c) power at 60 counts reported.
Output validate_regions_v3.json."""
import json, os, sys
import numpy as np
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D); import eds as X, derived as V
rng = np.random.default_rng(31); E = -0.471 + 0.01 * np.arange(2048)
def spec(areas, bgscale):
    bg = bgscale * (40 * np.exp(-E / 3.5) * (E > 0.3) + 5 + 25 * np.exp(-((E - 3.0) / 2.2) ** 2)) / 40
    s = bg.copy()
    for win in X.LINES:
        for n, e in X.LINES[win].items():
            A = areas.get(n, 0.0)
            for b, (a, r) in X.KB.items():
                if b == n: A = areas.get(a, 0.0) * r
            s += A / ((X.fwhm(e) / 2.355) * np.sqrt(2 * np.pi)) * np.exp(-0.5 * ((E - e) / (X.fwhm(e) / 2.355)) ** 2) * 0.01
    return rng.poisson(s)
LN = ['Ni Ka', 'S Ka', 'Al Ka', 'Mg Ka', 'Si Ka']; fp = []; pulls = []; power = []
for k in range(1500):
    true = {n: (rng.choice([0, 0, 30, 60, 200, 800])) for n in LN}; true.update({'Fe Ka': rng.uniform(50, 600), 'Cu Ka': 20, 'Cu La': 5, 'Cr Ka': rng.choice([0, 30])})
    s = spec(true, rng.uniform(0.05, 0.5)); got = {}
    for win in ('low', 'high'): got.update(V.fit_se(E, s, win))
    for n in LN:
        a, se = got[n]; a *= 100; se *= 100; z = a / se if np.isfinite(se) and se > 0 else 0.0
        if true[n] == 0: fp.append(z >= 5)
        elif true[n] >= 200 and np.isfinite(se): pulls.append((a - true[n]) / se)
        if true[n] == 60: power.append(z >= 5)
pulls = np.array(pulls)
res = {'n_spectra': 1500, 'false_pos_rate': float(np.mean(fp)), 'pull_mean': float(pulls.mean()), 'pull_sd': float(pulls.std()), 'power_60': float(np.mean(power))}
res['gates'] = {'false_pos': res['false_pos_rate'] <= 0.01, 'calibration': 0.8 <= res['pull_sd'] <= 1.25 and abs(res['pull_mean']) <= 0.3}
json.dump(res, open(f'{D}/validate_regions_v3.json', 'w'), indent=1); print(res)
