#!/usr/bin/env python3
"""reader2_select.py (v4 Track C, rule I7): choose the particle reader on a development split of the human-annotated UHCS particle set
(NIST 11256/964, CC BY-SA 3.0 US; annotations are I level: validation only, never keys) and test it once on the held-out split.
Split (fixed before any tuning): per condition, images sorted by name; odd positions -> dev, even positions -> test. The duplicate pair
800C-24H-Q-1 / -7 (identical image) is kept together in dev.
Quantity: number-mean ECD of particles with ECD >= DMIN_UM (0.15 um), ignoring particles cut by the edge; the same rule on the masks gives
the truth. Search grid (dev only): pre-smoothing sigma {0, 1, 1.5}; background sigma {15, 25, 40}; threshold {otsu, li, yen}; opening
radius {0, 1, 2}; objective = median |log(reader/truth)| + 0.5 x median |log(reader area fraction / truth area fraction)|.
Acceptance (test split, frozen here): |reader - truth| / truth <= 0.20 on >= 90 % of test images, and the condition medians order the
800 C times (3, 8, 24, 85 h) the same way as the truth medians. Output: reader2_selection.json."""
import glob, itertools, json, os, re
import numpy as np, tifffile
from scipy import ndimage as ndi
from skimage import filters, measure, morphology
X = '/home/aid1/Documents/harbor/v4_host/uhcsdb/nist964/x/particles'; UM = 1 / 26.0; DMIN_UM = 0.15
def ecd_stats(m):
    L = measure.label(m); H, W = m.shape; d = []
    for p in measure.regionprops(L):
        r0, c0, r1, c1 = p.bbox
        if r0 == 0 or c0 == 0 or r1 == H or c1 == W: continue
        e = p.equivalent_diameter_area * UM
        if e >= DMIN_UM: d.append(e)
    return (float(np.mean(d)) if d else float('nan')), float(m.mean())
def reader(a, sm, bg, th, op):
    a = a.astype(float)
    if sm: a = ndi.gaussian_filter(a, sm)
    f = a - ndi.gaussian_filter(a, bg); t = {'otsu': filters.threshold_otsu, 'li': filters.threshold_li, 'yen': filters.threshold_yen}[th](f); m = f > t
    if op: m = morphology.binary_opening(m, morphology.disk(op))
    return ndi.binary_fill_holes(m)
files = sorted(glob.glob(f'{X}/images/*.tif')); cond = lambda f: re.sub(r'-\d+\.tif$', '', os.path.basename(f))
split = {}
for c in sorted({cond(f) for f in files}):
    fs = sorted(f for f in files if cond(f) == c)
    for k, f in enumerate(fs): split[f] = 'dev' if k % 2 == 0 else 'test'
for f in files:
    if os.path.basename(f) in ('800C-24H-Q-1.tif', '800C-24H-Q-7.tif'): split[f] = 'dev'
data = {}
for f in files:
    a = tifffile.imread(f); a = a[..., 0] if a.ndim == 3 else a; lab = tifffile.imread(f.replace('/images/', '/labels/'))
    data[f] = (a, ecd_stats(lab > 0))
grid = list(itertools.product([0, 1, 1.5], [15, 25, 40], ['otsu', 'li', 'yen'], [0, 1, 2])); best = None
for g in grid:
    errs = []
    for f in files:
        if split[f] != 'dev': continue
        a, (tm, tf) = data[f]; rm, rf = ecd_stats(reader(a, *g))
        errs.append((abs(np.log(rm / tm)), abs(np.log(max(rf, 1e-4) / tf))))
    e = np.array(errs); obj = float(np.median(e[:, 0]) + 0.5 * np.median(e[:, 1]))
    if best is None or obj < best[0]: best = (obj, g)
g = best[1]; rows = []
for f in files:
    a, (tm, tf) = data[f]; rm, rf = ecd_stats(reader(a, *g)); rows.append({'file': os.path.basename(f), 'split': split[f], 'cond': cond(f), 'truth': tm, 'reader': rm, 'f_truth': tf, 'f_reader': rf})
test = [r for r in rows if r['split'] == 'test']; ok = [abs(r['reader'] - r['truth']) / r['truth'] <= 0.20 for r in test]
med = lambda key, c: float(np.median([r[key] for r in rows if r['cond'] == c]))
times = ['800C-3H-Q', '800C-8H-Q', '800C-24H-Q', '800C-85H-Q']
order_truth = list(np.argsort([med('truth', c) for c in times])); order_reader = list(np.argsort([med('reader', c) for c in times]))
res = {'best_params': {'smooth_sigma': g[0], 'bg_sigma': g[1], 'threshold': g[2], 'open_radius': g[3]}, 'dev_objective': best[0],
       'test_within_20pct': float(np.mean(ok)), 'n_test': len(test), 'order_truth': [times[i] for i in order_truth], 'order_reader': [times[i] for i in order_reader],
       'accept': bool(np.mean(ok) >= 0.9 and order_truth == order_reader), 'rows': rows}
json.dump(res, open('/home/aid1/Documents/harbor/v4/uhcs/reader2_selection.json', 'w'), indent=1, default=float)
print({k: v for k, v in res.items() if k != 'rows'})
for r in test: print(r['file'].ljust(20), 'truth %.3f reader %.3f  f %.3f/%.3f' % (r['truth'], r['reader'], r['f_truth'], r['f_reader']))
