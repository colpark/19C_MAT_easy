#!/usr/bin/env python3
"""dev_stats.py (S4r): statistics of the refodat91 DEV tiles only (split_refodat91.json), for the synthetic generator. Never reads a
held-out tile. Statistics use their own heavily smoothed segmentation (sigma 4 px), not the reader. Per specimen (condition): raw gray-level percentiles, saturation and black fractions, the reader's 3-class model (means, SDs,
weights), pixel noise (SD of the difference between the raw tile and its 3 x 3 median, over hydrate-class pixels), edge blur (Gaussian sigma
fitted to 1-D profiles across anhydrous-grain edges), dark-feature (pore) and bright-grain (anhydrous) equivalent-diameter distributions
(after the 3 px opening), and the class fractions. Writes dev_stats.json."""
import json, os, sys
import numpy as np, tifffile
from scipy import ndimage as ndi
from scipy.optimize import curve_fit
from scipy.special import erf
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); import s4r_reader as R
ROOT = '/home/aid1/Documents/harbor/v4_host/trackS/refodat91'
S = json.load(open(f'{HERE}/split_refodat91.json'))['split']

def edge_sigma(a, anh):
    """Fit erf edges on short profiles normal to anhydrous-grain boundaries (sampled along rows)."""
    sig = []; rng = np.random.default_rng(0); rows = rng.choice(a.shape[0], 120, replace=False)
    for r in rows:
        m = anh[r].astype(int); d = np.nonzero(np.diff(m) != 0)[0]
        for c in d[:4]:
            if c < 12 or c > a.shape[1] - 13: continue
            y = a[r, c - 12:c + 13].astype(float); x = np.arange(-12, 13)
            if m[c + 1] < m[c]: y = y[::-1]
            try:
                p, _ = curve_fit(lambda x, lo, hi, x0, s: lo + (hi - lo) * 0.5 * (1 + erf((x - x0) / (np.sqrt(2) * s))), x, y, p0=[y[:5].mean(), y[-5:].mean(), 0, 1.5], maxfev=2000)
                if 0.3 < p[3] < 8 and p[1] - p[0] > 20: sig.append(p[3])
            except Exception: pass
    return float(np.median(sig)) if sig else None, len(sig)

def eqd(mask):
    lab, n = ndi.label(mask);
    if not n: return []
    return (2 * np.sqrt(ndi.sum(mask, lab, range(1, n + 1)) / np.pi) * R.PX_UM).tolist()

out = {}
for sp, v in S.items():
    P = []; noise = []; blur = []; pd = []; gd = []; fr = []; mods = []
    for t in v['dev']:
        a = tifffile.imread(f'{ROOT}/{t}'); r = R.read_array(a); fr.append([r['porosity'], r['anhydrous'], r['hydrate'], r['aggregate_frac']]); mods.append([r['mu'], r['sd'], r['pi']])
        P.append(np.percentile(a, [1, 5, 25, 50, 75, 95, 99]).tolist())
        # statistics-only segmentation (not the reader): heavy smoothing (sigma 4 px) and the reader's per-tile class model on it
        sm = ndi.gaussian_filter(a.astype(np.float32), 4.0); satm = a >= R.SAT; h, e = np.histogram(sm[~satm], bins=256, range=(0, 256))
        t01, t12 = R.thresholds(*R.gmm3((e[:-1] + e[1:]) / 2, h.astype(float))); cls = np.ones(a.shape, np.uint8); cls[(sm >= t12) | satm] = 2; cls[sm <= t01] = 0
        big = ndi.binary_erosion(cls == 2, np.ones((11, 11), bool)) & ~satm   # interiors of large anhydrous grains, unsaturated
        noise.append(float(np.std(a[big] - ndi.uniform_filter(a.astype(float), 21)[big])) if big.sum() > 2000 else None)
        s, n = edge_sigma(a, cls == 2); blur.append(s)
        pd += eqd(cls == 0); gd += eqd(cls == 2); r['fractions_sigma4'] = [float((cls == 0).mean()), float((cls == 2).mean())]; fr[-1] += r['fractions_sigma4']
    q = lambda L: np.percentile(L, [10, 25, 50, 75, 90]).round(3).tolist() if L else None
    out[sp] = {'gray_pct': np.mean(P, 0).round(1).tolist(), 'sat_frac': float(np.mean([(tifffile.imread(f'{ROOT}/{t}') >= 254).mean() for t in v['dev']])),
               'class_model_mean': np.mean([m[0] for m in mods], 0).round(2).tolist(), 'class_model_sd': np.mean([m[1] for m in mods], 0).round(2).tolist(),
               'class_model_pi': np.mean([m[2] for m in mods], 0).round(3).tolist(), 'noise_sd': float(np.mean([x for x in noise if x])) if any(noise) else None, 'edge_sigma_px': float(np.median([b for b in blur if b])) if any(blur) else None,
               'pore_eqd_um_pct': q(pd), 'grain_eqd_um_pct': q(gd), 'fractions_mean': np.mean(fr, 0).round(4).tolist(), 'fractions_order': ['porosity', 'anhydrous', 'hydrate', 'aggregate', 'porosity_sigma4', 'anhydrous_sigma4']}
json.dump(out, open(f'{HERE}/dev_stats.json', 'w'), indent=1); print(json.dumps(out, indent=1))
