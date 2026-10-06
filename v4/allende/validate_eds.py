#!/usr/bin/env python3
"""validate_eds.py (v4 Track B, rule I7): synthetic spectra with known line areas (Poisson counts at the real acquisition level of a 4 x 4
binned pixel), energy axis of the deposit (10 eV channels), lines with the eds.py shapes plus a bremsstrahlung-like background with curvature.
Gates (frozen with eds.py): Al Ka recovered within 25 % (or 3 sigma Poisson) when Al net >= 200 counts next to Mg and Si 10x larger;
false Al (true 0) below 3 sigma of the background in >= 95 % of spectra; Fe Ka and Ni Ka within 15 %. Output validate_eds.json."""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import eds as X
rng = np.random.default_rng(7); E = -0.471 + 0.01 * np.arange(2048)
def spec(areas):
    bg = 40 * np.exp(-E / 3.5) * (E > 0.3) + 5
    s = bg.copy()
    for win in X.LINES:
        for n, e in X.LINES[win].items():
            A = areas.get(n, 0.0)
            for b, (a, r) in X.KB.items():
                if b == n: A = areas.get(a, 0.0) * r
            s += A / ((X.fwhm(e) / 2.355) * np.sqrt(2 * np.pi)) * np.exp(-0.5 * ((E - e) / (X.fwhm(e) / 2.355)) ** 2) * 0.01
    return rng.poisson(s), s
rows = []
for k in range(300):
    al = rng.choice([0, 200, 400, 800, 1600]); mg = rng.uniform(2000, 6000); si = rng.uniform(4000, 9000); fe = rng.uniform(500, 3000); ni = rng.choice([0, 300, 1500]); sx = rng.choice([0, 400, 2000])
    true = {'Al Ka': al, 'Mg Ka': mg, 'Si Ka': si, 'Fe Ka': fe, 'Ni Ka': ni, 'S Ka': sx, 'Cu Ka': 150, 'Cu La': 40}
    s, _ = spec(true); got = {}
    for win in X.WIN: got.update(X.fit_spectrum(E, s, win)[0])
    got = {n: v * 100 for n, v in got.items()}   # channel width 0.01 keV -> counts
    rows.append({'true': true, 'got': got})
def rel(n, cut): return [abs(r['got'][n] - r['true'][n]) / r['true'][n] for r in rows if r['true'][n] >= cut]
al = rel('Al Ka', 200); fe = rel('Fe Ka', 1); ni = rel('Ni Ka', 300)
zero_al = [r['got']['Al Ka'] for r in rows if r['true']['Al Ka'] == 0]
res = {'n': len(rows), 'Al_within_25pct': float(np.mean([x <= 0.25 for x in al])), 'Fe_within_15pct': float(np.mean([x <= 0.15 for x in fe])),
       'Ni_within_15pct': float(np.mean([x <= 0.15 for x in ni])), 'Al_false_positive_p95': float(np.percentile(zero_al, 95))}
res['gates'] = {'Al': res['Al_within_25pct'] >= 0.9, 'Fe': res['Fe_within_15pct'] >= 0.9, 'Ni': res['Ni_within_15pct'] >= 0.9, 'Al_false': res['Al_false_positive_p95'] < 100}
json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'validate_eds.json'), 'w'), indent=1); print(res)
