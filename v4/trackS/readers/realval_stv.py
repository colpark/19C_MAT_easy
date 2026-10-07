#!/usr/bin/env python3
"""realval_stv.py (S4b-2 held-out real evidence, no model): domains from the raw orientations (Euler_Orientation_Raw.ang, 0.7 um grid,
neighbour misorientation < 5 deg with cubic symmetry; no colours) against the reader's colour segmentation of IPF_Raw_X.tif (the same
EBSD map rendered at 3000 x 2985 px), resampled to the .ang grid by nearest neighbour. Gate (frozen before this run): >= 90 % of .ang domains
of at least 655 px (321 um2, the observable's DOM_MIN) matched at IoU >= 0.7. The best of integer shifts -3..3 px is reported (rendering
offset), chosen on the overall boundary agreement, not on the gate. Output realval_stv.json."""
import json, os, sys
import numpy as np, tifffile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import stv_reader as R
D = '/home/aid1/Documents/harbor/v4_host/trackS/stinville2022/extracted/2D_EBSD_Dataset/2D_EBSD_Dataset'
a = np.loadtxt(f'{D}/Euler_Orientation_Raw.ang', comments='#', usecols=(0, 1, 2, 3, 4, 6))
H, W = 2131, 2142; eul = a[:, :3].reshape(H, W, 3); ci = a[:, 5].reshape(H, W)
ang = R.ang_domains(eul)
ipf = tifffile.imread(f'{D}/IPF_Raw_X.tif')[..., :3]; seg = R.segment_ipf(ipf)
rr = np.clip(np.round(np.arange(H) * ipf.shape[0] / H).astype(int), 0, ipf.shape[0] - 1); cc = np.clip(np.round(np.arange(W) * ipf.shape[1] / W).astype(int), 0, ipf.shape[1] - 1)
best = None
def edges(l): e = np.zeros(l.shape, bool); e[:, 1:] |= l[:, 1:] != l[:, :-1]; e[1:] |= l[1:] != l[:-1]; return e
ea = edges(ang)
for dy in range(-3, 4):
    for dx in range(-3, 4):
        s = seg[np.clip(rr + dy, 0, seg.shape[0] - 1)][:, np.clip(cc + dx, 0, seg.shape[1] - 1)]; agree = float((edges(s) & ea).sum() / max(ea.sum(), 1))
        if best is None or agree > best[0]: best = (agree, dy, dx, s)
agree, dy, dx, s = best; frac, n = R.match(ang, s, 655, 0.7)
res = {'ang_grid': [H, W], 'ang_domains_ge655': n, 'matched_iou07': frac, 'shift_px': [dy, dx], 'boundary_agreement': agree, 'ci_median': float(np.median(ci)),
       'gate': bool(frac >= 0.9), 'ipf_domains': int(seg.max() + 1), 'ang_domains_all': int(ang.max() + 1)}
json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'realval_stv.json'), 'w'), indent=1); print(res)
