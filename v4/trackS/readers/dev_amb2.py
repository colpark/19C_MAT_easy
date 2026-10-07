#!/usr/bin/env python3
"""dev_amb2.py (S4a-2 dev set only; runs on host A node 2): per-grain features on the four pad cross sections, labelled by position:
pool = grain centroid within POOL_UM of the local surface (the pads are fully remelted near the surface); base = centroid deeper than
BASE_UM (the bottom of the 235 um field). Crops of CROP columns at three positions per pad keep memory modest. Writes dev_amb2.json with
feature distributions and the accuracy of candidate (S3_MAX, KAM_MIN) rules. No held-out file is read."""
import glob, json, os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'readers')); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amb2_reader as R
POOL_UM, BASE_UM, CROP = 50.0, 200.0, 3000
D = os.path.expanduser('~/Documents/harbor/trackS_N2/dev'); out = {'pads': {}, 'grains': []}
for f in sorted(glob.glob(f'{D}/**/*Montaged Map Data.ctf', recursive=True)):
    ph, eul, bc, st = R.read_ctf(f); H, W = ph.shape; name = os.path.basename(f)[:40]; out['pads'][name] = {'shape': [H, W], 'step': st}
    for c0 in (int(W * 0.2), int(W * 0.5) - CROP // 2, int(W * 0.8) - CROP):
        sl = (slice(None), slice(max(0, c0), max(0, c0) + CROP)); p, e = ph[sl], eul[sl]
        lab, F = R.features(p, e, st); idx = p > 0; surf = np.where(idx.any(0), idx.argmax(0), H)
        for g in range(len(F['area_um2'])):
            if F['area_um2'][g] < R.MIN_UM2: continue
            dpt = (F['cy'][g] - surf[int(min(max(F['cx'][g], 0), p.shape[1] - 1))]) * st
            lbl = 'pool' if dpt <= POOL_UM else ('base' if dpt >= BASE_UM else None)
            if lbl: out['grains'].append({'pad': name, 'label': lbl, 'depth_um': float(dpt), **{k: float(F[k][g]) for k in ('area_um2', 'd_um', 'aspect', 'sigma3', 'kam')}})
    print(name, (H, W), len(out['grains']), flush=True)
G = out['grains']
for lbl in ('pool', 'base'):
    s = [g for g in G if g['label'] == lbl]
    out[f'{lbl}_n'] = len(s); out[f'{lbl}_pct'] = {k: np.percentile([g[k] for g in s], [10, 25, 50, 75, 90]).round(3).tolist() for k in ('sigma3', 'kam', 'd_um', 'aspect')}
grid = []
for s3 in (0.02, 0.05, 0.1, 0.15, 0.2, 0.3):
    for km in (0.0, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4):
        pred = [(g['sigma3'] <= s3) and (g['kam'] >= km) for g in G]; truth = [g['label'] == 'pool' for g in G]
        tp = sum(a and b for a, b in zip(pred, truth)); tn = sum((not a) and (not b) for a, b in zip(pred, truth))
        P = sum(truth); N = len(G) - P; grid.append({'s3_max': s3, 'kam_min': km, 'sens': tp / max(P, 1), 'spec': tn / max(N, 1), 'bal_acc': (tp / max(P, 1) + tn / max(N, 1)) / 2})
out['grid'] = sorted(grid, key=lambda r: -r['bal_acc'])[:12]
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dev_amb2.json'), 'w'), indent=1)
print(json.dumps({k: out[k] for k in ('pool_n', 'base_n', 'pool_pct', 'base_pct')}, indent=0)); print(out['grid'][:5])
