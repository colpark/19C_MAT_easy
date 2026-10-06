#!/usr/bin/env python3
"""validate_derived.py (v4 Track B rebuild, rule I7): synthetic checks of derived.py.
  Fe L3: synthetic spectra with an edge step, L3a / L3b Gaussian peaks 1.6-2.2 eV apart with known intensity ratio (0.2-2.0), a sloped
         pre-edge background (thick silicate), an energy offset (-4..+2 eV), noise 1 % of peak; gate: ratio within 15 % on >= 90 % of 60,
         and the ordering L3b > L3a recovered whenever the true ratio >= 1.2 or <= 0.8.
  L3-L2: Fe (12.9 eV) and Ni (17.3 eV) synthetic splittings with offsets; gate: within 0.4 eV on >= 90 %.
  regions_v2: synthetic Poisson maps with known sulfide / Al / silicate patches; gate: >= 90 % of patch bins assigned correctly, <= 2 % of
         background bins assigned to any region.
Output validate_derived.json."""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import derived as V
rng = np.random.default_rng(23); res = {}
E = np.concatenate([np.arange(693, 703, 0.5), np.arange(703, 712, 0.2), np.arange(712, 733, 0.5)])
g = lambda x, m, w: np.exp(-0.5 * ((x - m) / w) ** 2)
rows = []
for k in range(60):
    off = rng.uniform(-4, 2); r = rng.uniform(0.2, 2.0); d = rng.uniform(1.6, 2.2); a0 = 707.5 + off
    s = 0.6 - 0.01 * (E - 693) + 0.25 / (1 + np.exp(-(E - (a0 - 0.5)) / 0.3)) + 1.0 * g(E, a0, 0.45) + r * g(E, a0 + d, 0.5) + 0.35 * g(E, a0 + 12.9, 0.8)
    s = s + rng.normal(0, 0.01 * max(1, r), len(E))
    e0 = a0 - 0.6   # onset from the frozen stxm.onset analogue (steepest rise sits just below L3a)
    f = V.fe_l3_features(E, s, e0)
    rows.append({'true': r, 'got': f['ratio'] if f else None})
ok = [x['got'] is not None and abs(x['got'] - x['true']) / x['true'] <= 0.15 for x in rows]
order = [x['got'] is not None and ((x['got'] > 1) == (x['true'] > 1)) for x in rows if x['true'] >= 1.2 or x['true'] <= 0.8]
res['fe_l3'] = {'within_15pct': float(np.mean(ok)), 'order_ok': float(np.mean(order)), 'gate': bool(np.mean(ok) >= 0.9 and np.mean(order) == 1.0)}
rows2 = []
for el, sep, lo, hi in (('Fe', 12.9, 693, 733), ('Ni', 17.3, 840, 872)):
    Ee = np.arange(lo, hi, 0.4)
    for k in range(20):
        off = rng.uniform(-4, 2); p3 = (707.5 if el == 'Fe' else 852.5) + off
        s = 0.5 + 1.0 * g(Ee, p3, 0.5) + 0.4 * g(Ee, p3 + sep, 0.7) + 0.2 / (1 + np.exp(-(Ee - p3 + 0.5) / 0.3)) + rng.normal(0, 0.01, len(Ee))
        got = V.l3_l2_separation(Ee, s, p3 - 0.6, el); rows2.append(abs(got - sep) <= 0.4 if got else False)
res['l3l2'] = {'within_0.4eV': float(np.mean(rows2)), 'gate': bool(np.mean(rows2) >= 0.9)}
H = 50; valid = np.ones((H, H), bool); truth = np.zeros((H, H), int)
truth[5:15, 5:15] = 1; truth[25:35, 30:42] = 2; truth[18:48, 2:28] = np.where(truth[18:48, 2:28] == 0, 3, truth[18:48, 2:28])
lam = {'Ni': np.where(truth == 1, 400, 2), 'S': np.where(truth == 1, 600, 3), 'Al': np.where(truth == 2, 300, 4), 'Mg': np.where(truth == 3, 900, 5), 'Si': np.where(truth == 3, 2000, 10)}
bgw = {k: 200.0 for k in lam}
M = {k: rng.poisson(lam[k] + bgw[k]) - bgw[k] for k in lam}; W = {k: M[k] + bgw[k] for k in lam}
R = V.regions_v2(V.sigmaps(M, W), valid); lab = {'sulfide': 1, 'al_pocket': 2, 'silicate': 3}
acc = np.mean([R[n][truth == v].mean() for n, v in lab.items()]); fp = np.mean([R[n][truth == 0].mean() for n in lab])
res['regions'] = {'patch_correct': float(acc), 'background_assigned': float(fp), 'gate': bool(acc >= 0.9 and fp <= 0.02)}
json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'validate_derived.json'), 'w'), indent=1); print(res)
