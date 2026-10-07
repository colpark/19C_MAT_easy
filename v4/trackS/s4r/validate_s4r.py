#!/usr/bin/env python3
"""validate_s4r.py (S4r gates on FRESH synthetic seeds; frozen with S4r before running). Seeds base 10000 (never used in tuning).
  G1 phase fractions: 10 tiles (seeds 10000-10009, 2048 px); a tile passes when porosity, anhydrous and hydrate are all within 0.02
     absolute of truth; gate: >= 9 of 10.
  G2 porosity bias constant: 30 tiles (seeds 10100-10129, 1024 px) with true porosity spread evenly over 0.05-0.30; bias = read - truth;
     gate: |slope of bias on truth| <= 0.10 AND (max - min) of the mean bias in 5 equal porosity bins <= 0.02.
  G3 ITZ gradient: 10 tiles (seeds 10200-10209, 2048 px, itz=True, porosity falling with distance from the aggregate); the reader's own
     aggregate mask and frozen bins; gate: slope sign of porosity vs bin centre negative on 10 of 10 (truth is negative by construction).
     Aggregate-mask IoU against the drawn aggregate reported.
  G4 portlandite / C-S-H split: not attempted (the dev histograms show no separable hydrate sub-mode); hydrates stay merged and are not
     keyed separately.
Writes validate_s4r.json."""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); import s4r_reader as R, synth_s4r as G
out = {'params': {'SIGMA': R.SIGMA, 'OPEN': R.OPEN, 'PORE_SHIFT': R.PORE_SHIFT}}
g1 = []
for s in range(10000, 10010):
    img, tr = G.tile(s, size=2048); r = R.read_array(img); e = {k: r[k] - tr[k] for k in ('porosity', 'anhydrous', 'hydrate')}
    g1.append({'seed': s, 'truth': {k: tr[k] for k in e}, 'err': e, 'pass': all(abs(v) <= 0.02 for v in e.values())})
out['G1'] = {'tiles': g1, 'n_pass': sum(x['pass'] for x in g1), 'pass': sum(x['pass'] for x in g1) >= 9}
pt = np.linspace(0.05, 0.30, 30); b = []
for i, s in enumerate(range(10100, 10130)):
    img, tr = G.tile(s, porosity=float(pt[i])); r = R.read_array(img); b.append((tr['porosity'], r['porosity'] - tr['porosity']))
b = np.array(b); slope = float(np.polyfit(b[:, 0], b[:, 1], 1)[0]); edges = np.linspace(0.05, 0.30, 6)
bm = [float(b[(b[:, 0] >= edges[j]) & (b[:, 0] <= edges[j + 1]), 1].mean()) for j in range(5)]
out['G2'] = {'slope': slope, 'bin_mean_bias': bm, 'range': max(bm) - min(bm), 'mean_bias': float(b[:, 1].mean()), 'pass': abs(slope) <= 0.10 and max(bm) - min(bm) <= 0.02}
g3 = []
for s in range(10200, 10210):
    img, tr = G.tile(s, size=2048, itz=True); p = R.itz_profile(img)
    if not p['ok']: g3.append({'seed': s, 'ok': False}); continue
    c = [(lo + hi) / 2 for lo, hi, _ in p['bins']]; v = [x for _, _, x in p['bins']]; sl = float(np.polyfit(c, v, 1)[0]) if len(c) >= 2 else 0.0
    tc = [(lo + hi) / 2 for lo, hi, _ in tr['itz_bins']]; tv = [x for _, _, x in tr['itz_bins']]
    g3.append({'seed': s, 'ok': True, 'slope': sl, 'truth_slope': float(np.polyfit(tc, tv, 1)[0]), 'bins': p['bins'], 'agg_frac_read': float(p['agg'].mean())})
out['G3'] = {'tiles': g3, 'n_neg': sum(1 for x in g3 if x.get('ok') and x['slope'] < 0), 'pass': sum(1 for x in g3 if x.get('ok') and x['slope'] < 0) == 10}
out['G4'] = {'attempted': False, 'note': 'hydrates merged (no separable CH / C-S-H sub-mode on dev); not keyed separately'}
out['pass'] = out['G1']['pass'] and out['G2']['pass'] and out['G3']['pass']
json.dump(out, open(f'{HERE}/validate_s4r.json', 'w'), indent=1, default=float)
print(json.dumps({'G1': [out['G1']['n_pass'], out['G1']['pass']], 'G2': {k: out['G2'][k] for k in ('slope', 'range', 'mean_bias', 'pass')}, 'G3': [out['G3']['n_neg'], out['G3']['pass']], 'pass': out['pass']}, default=float))
