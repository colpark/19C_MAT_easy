#!/usr/bin/env python3
"""qa.py: digitizer QA without text values (plan rule 4). (1) Hall identity: r = |1 - n_H e mu_H rho| per (sample, T) where all
three cells exist; pass if median r <= 10%. (2) F4c cross-check: its 300 K points must match F4a (n_H) and F4b (mu_H) at 300 K
within reading uncertainty (2u combined). (3) Text values beside digitized values, printed for the report only: nothing is tuned.
Writes matrix/qa.json."""
import sys as _pb_s, os as _pb_o
_pb_d = _pb_o.path.dirname(_pb_o.path.abspath(__file__))
while not _pb_o.path.exists(_pb_o.path.join(_pb_d, 'pbroot.py')) and _pb_o.path.dirname(_pb_d) != _pb_d: _pb_d = _pb_o.path.dirname(_pb_d)
_pb_s.path.insert(0, _pb_d)
from pbroot import ROOT, HOST
import json, statistics, sys
V3 = f'{ROOT}/papers/mo21'
C = {(c['panel'], c['sample_x'], c['T']): c for c in map(json.loads, open(f'{V3}/matrix/cells.jsonl'))}
K = 1e6 / (1e25 * 1.602176634e-19 * 1e-4)   # rho[uOhm m] * n[1e19 cm^-3] * mu[cm^2/Vs] / K = 1
out = {'hall': []}
for (p, x, T), c in sorted(C.items()):
    if p != 'F5a': continue
    n, mu = C.get(('F4a', x, T)), C.get(('F4b', x, T))
    if not (n and mu): continue
    prod = c['value'] * n['value'] * mu['value'] / K
    ru = (c['rel_u'] ** 2 + n['rel_u'] ** 2 + mu['rel_u'] ** 2) ** 0.5
    out['hall'].append({'x': x, 'T': T, 'rho': c['value'], 'n_H': n['value'], 'mu_H': mu['value'], 'product': prod, 'r': abs(1 - prod), 'rel_u_combined': ru})
rs = [h['r'] for h in out['hall']]
out['hall_median_r'] = statistics.median(rs); out['hall_max_r'] = max(rs); out['hall_n'] = len(rs)
out['hall_pass'] = out['hall_median_r'] <= 0.10
print(f"Hall identity: n={len(rs)}, median r={out['hall_median_r']:.3f}, max r={out['hall_max_r']:.3f} -> {'PASS' if out['hall_pass'] else 'FAIL'}")
for h in out['hall']: print(f"  x={h['x']:<6} T={h['T']} rho={h['rho']:7.2f} n={h['n_H']:6.3f} mu={h['mu_H']:6.1f} product={h['product']:.3f} (comb. rel u {h['rel_u_combined']:.3f})")
# F4c (QA only): own calibration. The bottom axis is a 3 px band, so ticks are scanned from the band's top row. Majors (run >= 6)
# carry the printed labels 1 and 10 (left to right); the log minor ticks (2..9 x decade) verify the fit. y: linear fit to the OCR labels.
# Points: 'This work' red stars (relaxed red mask; thin ellipse dashes fail the size test; the legend star sits right of x=310 and below y=190).
sys.argv = ['qa']; sys.path.insert(0, f'{ROOT}')
import numpy as np, digitize as D
D.load_profile('mo21')
from PIL import Image
from scipy import ndimage as ndi
rgb = np.asarray(Image.open(f'{D.HOST}/crops/F4c.jpg').convert('RGB')); gray = rgb.mean(2); dark = gray < 150
ax = D.find_axes(gray); row = ax['x_row']
while dark[row - 1, ax['x_left'] + 40:ax['x_left'] + 300].mean() > 0.9: row -= 1
def run_up(c):
    k = 0
    while dark[row - 1 - k, c] and k < 15: k += 1
    return k
cols = [(c, run_up(c)) for c in range(ax['x_left'] + 3, ax['x_right'] - 6) if 2 <= run_up(c) <= 14]
groups = []
for c, k in cols:
    if groups and c - groups[-1][-1][0] <= 1: groups[-1].append((c, k))
    else: groups.append([(c, k)])
ticks = [(float(np.mean([c for c, _ in g])), max(k for _, k in g)) for g in groups]
maj = sorted(t for t, r in ticks if r >= 6)[:2]
a, b, r = D.fit(maj, [1, 10], True); mc = D.minor_check(ticks, a, b)
fx = lambda p: 10 ** (a * p + b)
yl = json.load(open(f'{V3}/digitized/F4c.json'))['y_labels_ocr']
ya, yb_ = np.polyfit([p for p, _ in yl], [v for _, v in yl], 1); yres = float(np.abs(np.polyval([ya, yb_], [p for p, _ in yl]) - [v for _, v in yl]).max() / abs(ya))
m = D.color_class_relaxed(rgb)['red']; m[:ax['y_top'] + 3] = False; m[row - 2:] = False; m[:, :ax['y_col'] + 3] = False
lab, n = ndi.label(m); stars = []
for i in range(1, n + 1):   # stars: area >= 12, both sides >= 4 px (ellipse dashes are 1-2 px thin)
    yy, xx = np.nonzero(lab == i)
    if len(yy) < 12 or min(np.ptp(yy), np.ptp(xx)) + 1 < 4 or (xx.mean() > 310 and yy.mean() > 190): continue
    size = max(np.ptp(yy), np.ptp(xx)) + 1; upx = float(np.hypot(size / 2, r))
    nx = fx(xx.mean()); stars.append({'n_H': float(nx), 'mu_H': float(np.polyval([ya, yb_], yy.mean())),
                                      'u_n': float(nx * (10 ** (abs(a) * upx) - 1)), 'u_mu': float(abs(ya) * np.hypot(size / 2, yres))})
out['F4c'] = {'x_cal': {'majors_px': maj, 'resid_px': r, 'minor_check_px': mc}, 'y_cal_resid_px': yres, 'stars': stars, 'match': []}
print(f"F4c: x majors {maj}, minor-tick check {mc} px; y label resid {yres:.2f} px; {len(stars)} stars")
for x in (0.0, 0.005, 0.01, 0.02, 0.04):
    n, mu = C.get(('F4a', x, 300)), C.get(('F4b', x, 300))
    if not (n and mu): print(f'  x={x}: F4a/F4b 300 K cell missing ({bool(n)}, {bool(mu)})'); continue
    best = min(stars, key=lambda s: abs(np.log10(s['n_H'] / n['value'])) + abs(s['mu_H'] - mu['value']) / mu['value']) if stars else None
    ok = best and abs(best['n_H'] - n['value']) <= 2 * np.hypot(best['u_n'], n['u']) and abs(best['mu_H'] - mu['value']) <= 2 * np.hypot(best['u_mu'], mu['u'])
    out['F4c']['match'].append({'x': x, 'F4a_n': n['value'], 'F4b_mu': mu['value'], 'star': best, 'within_2u': bool(ok)})
    print(f"  x={x}: F4a/F4b n={n['value']:.2f}+-{n['u']:.2f} mu={mu['value']:.1f}+-{mu['u']:.1f} | nearest F4c star n={best['n_H']:.2f}+-{best['u_n']:.2f} mu={best['mu_H']:.1f}+-{best['u_mu']:.1f} -> {'match' if ok else 'MISMATCH'}")
json.dump(out, open(f'{V3}/matrix/qa.json', 'w'), indent=1)
