#!/usr/bin/env python3
"""amb2_reader.py (Track S pilot S1, reader S4a-2, modality EBSD): melt-pool depth from single-track EBSD cross sections (.ctf).
Definitions written in DESK_amb2022_03.md (round 2) before this code. Pool vs base classification from physics, per grain:
  sigma3   fraction of the grain's boundary (neighbour pairs) that is Sigma-3: 60 deg about <111> within the Brandon tolerance 8.66 deg;
  kam      mean kernel average misorientation (4 neighbours, < 5 deg);
  size     equivalent diameter (um); aspect (PCA) of the grain's pixels.
The annealed base carries annealing twins (sigma3 high); the resolidified pool carries none, has higher KAM and columnar grains.
Thresholds (S3_MAX, KAM_MIN) are set on the dev set (pads, L112 montage, case-1.1 bottom fields) and frozen (S4a2).
Depth: pool grains -> mask closed by CLOSE_UM -> component touching the surface band -> lowest pixel below the local surface.
Censored when the mask reaches the last EDGE_UM of the covered rows. Case 1.1: stitch() places the bottom field under the top field
by normalized cross-correlation of the Euler-1 maps over vertical overlaps of 5-60 % and horizontal shifts of +-40 px.
No model is used; data files are read only."""
import os, sys
import numpy as np
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import stv_reader as SR
GRAIN_DEG, KAM_CUT, BRANDON = 10.0, 5.0, 15.0 / np.sqrt(3)
S3_MAX, KAM_MIN, MIN_UM2, CLOSE_UM, SURF_UM, EDGE_UM, MAJ_UM = 0.10, 0.0, 15.0, 3.0, 5.0, 5.0, 20.0   # MAJ_UM tuned on synthetic dev seeds 100-107   # set on the dev pads (dev_amb2.json): sigma3 alone, balanced accuracy 0.927; KAM adds nothing
def read_ctf(path):
    import pandas as pd
    head = {}; n = 0
    with open(path, errors='replace') as fh:
        for line in fh:
            n += 1
            if line.startswith('Phase\tX'): break
            p = line.rstrip('\n').split('\t')
            if len(p) >= 2: head[p[0].lstrip('﻿')] = p[1]
    W, H, st = int(head['XCells']), int(head['YCells']), float(head['XStep'])
    df = pd.read_csv(path, sep='\t', skiprows=n, header=None, usecols=[0, 5, 6, 7, 9], nrows=W * H, engine='c')
    a = df.to_numpy(float); ph = a[:, 0].reshape(H, W); eul = np.radians(a[:, 1:4]).reshape(H, W, 3); bc = a[:, 4].reshape(H, W)
    return ph, eul, bc, st
def qmul(a, b):
    w1, x1, y1, z1 = np.moveaxis(a, -1, 0); w2, x2, y2, z2 = np.moveaxis(b, -1, 0)
    return np.stack([w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2, w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2], -1)
def conj(q): return q * np.array([1, -1, -1, -1])
def _sigma3_variants():
    out = []
    for ax in ((1, 1, 1), (1, 1, -1), (1, -1, 1), (-1, 1, 1)):
        ax = np.array(ax, float) / np.sqrt(3)
        for ang in (np.pi / 3, -np.pi / 3): out.append(np.r_[np.cos(ang / 2), np.sin(ang / 2) * ax])
    return np.array(out)
S3V = _sigma3_variants()
def sigma3_dev(q1, q2):
    """deviation (deg) of the misorientation q1 -> q2 from the nearest Sigma-3 variant, over the 24 cubic operators."""
    if SR.SYM is None: SR.SYM = SR._cubic_ops()
    d = qmul(conj(q1), q2); best = np.full(d.shape[:-1], 180.0)
    for s in SR.SYM:
        e = qmul(d, np.broadcast_to(s, d.shape))
        dots = np.abs(e @ S3V.T).max(-1); best = np.minimum(best, np.degrees(2 * np.arccos(np.clip(dots, 0, 1))))
    return best
def features(ph, eul, step, lab=None):
    """per-grain features. Returns lab and dict of arrays indexed by grain id: area_um2, d_um, aspect, sigma3, kam, cy, cx."""
    q = SR._quat(eul[..., 0], eul[..., 1], eul[..., 2]); idx = ph > 0
    if lab is None: lab = np.where(idx, SR.ang_domains(eul, mis_deg=GRAIN_DEG), -1)
    H, W = lab.shape; G = lab.max() + 1
    mh = SR._mis(q[:, :-1], q[:, 1:]); mv = SR._mis(q[:-1], q[1:])
    k = np.zeros((H, W)); c = np.zeros((H, W))
    for m, sl1, sl2 in ((mh, (slice(None), slice(None, -1)), (slice(None), slice(1, None))), (mv, (slice(None, -1), slice(None)), (slice(1, None), slice(None)))):
        ok = (m < KAM_CUT) & idx[sl1] & idx[sl2]
        k[sl1] += np.where(ok, m, 0); c[sl1] += ok; k[sl2] += np.where(ok, m, 0); c[sl2] += ok
    kam = np.where(c > 0, k / np.maximum(c, 1), np.nan)
    nb = np.zeros(G); n3 = np.zeros(G)
    for sl1, sl2 in (((slice(None), slice(None, -1)), (slice(None), slice(1, None))), ((slice(None, -1), slice(None)), (slice(1, None), slice(None)))):
        a, b = lab[sl1], lab[sl2]; bd = (a != b) & (a >= 0) & (b >= 0)
        if not bd.any(): continue
        dev = sigma3_dev(q[sl1][bd], q[sl2][bd]); is3 = dev <= BRANDON
        for g in (a[bd], b[bd]):
            nb += np.bincount(g, minlength=G); n3 += np.bincount(g, weights=is3.astype(float), minlength=G)
    yy, xx = np.mgrid[0:H, 0:W]; L = lab.ravel(); ok = L >= 0
    area = np.bincount(L[ok], minlength=G) * step ** 2
    kam_g = np.bincount(L[ok], weights=np.nan_to_num(kam.ravel()[ok]), minlength=G) / np.maximum(np.bincount(L[ok], minlength=G), 1)
    cy = np.bincount(L[ok], weights=yy.ravel()[ok], minlength=G) / np.maximum(np.bincount(L[ok], minlength=G), 1)
    cx = np.bincount(L[ok], weights=xx.ravel()[ok], minlength=G) / np.maximum(np.bincount(L[ok], minlength=G), 1)
    syy = np.bincount(L[ok], weights=(yy.ravel()[ok]) ** 2, minlength=G) / np.maximum(np.bincount(L[ok], minlength=G), 1) - cy ** 2
    sxx = np.bincount(L[ok], weights=(xx.ravel()[ok]) ** 2, minlength=G) / np.maximum(np.bincount(L[ok], minlength=G), 1) - cx ** 2
    sxy = np.bincount(L[ok], weights=(xx.ravel()[ok] * yy.ravel()[ok]), minlength=G) / np.maximum(np.bincount(L[ok], minlength=G), 1) - cx * cy
    tr = sxx + syy; det = sxx * syy - sxy ** 2; disc = np.sqrt(np.maximum(tr ** 2 / 4 - det, 0)); l1 = tr / 2 + disc; l2 = np.maximum(tr / 2 - disc, 1e-6)
    return lab, {'area_um2': area, 'd_um': 2 * np.sqrt(area / np.pi), 'aspect': np.sqrt(l1 / l2), 'sigma3': n3 / np.maximum(nb, 1), 'kam': kam_g, 'cy': cy, 'cx': cx, 'kam_map': kam}
def classify(F, s3_max=None, kam_min=None):
    """pool grain: no twins (sigma3 <= S3_MAX) and KAM >= KAM_MIN; grains below MIN_UM2 inherit nothing (handled by closing)."""
    s3_max = S3_MAX if s3_max is None else s3_max; kam_min = KAM_MIN if kam_min is None else kam_min
    return (F['sigma3'] <= s3_max) & (F['kam'] >= kam_min) & (F['area_um2'] >= MIN_UM2)
def depth(ph, lab, pool_g, step):
    idx = ph > 0; H, W = lab.shape; surf = np.where(idx.any(0), idx.argmax(0), H)
    m = np.where(lab >= 0, pool_g[np.clip(lab, 0, None)], False)
    if MAJ_UM:   # spatial majority over a disk of radius MAJ_UM (indexed points only): isolated misclassified grains cannot bridge the mask
        rm = max(1, int(round(MAJ_UM / step))); k = (np.hypot(*np.mgrid[-rm:rm + 1, -rm:rm + 1]) <= rm).astype(float)
        num = ndi.convolve(m.astype(float), k, mode='constant'); den = ndi.convolve(idx.astype(float), k, mode='constant'); m = (num > 0.5 * np.maximum(den, 1)) & idx
    r = max(1, int(round(CLOSE_UM / step))); disk = np.hypot(*np.mgrid[-r:r + 1, -r:r + 1]) <= r
    m = ndi.binary_closing(m, structure=disk) & idx; m = ndi.binary_fill_holes(m) & idx
    cc, n = ndi.label(m); yy = np.arange(H)[:, None]
    band = (yy - surf[None, :] >= 0) & (yy - surf[None, :] <= SURF_UM / step)
    touch = np.unique(cc[band & (cc > 0)])
    if n == 0 or not len(touch): return {'depth_um': 0.0, 'width_um': 0.0, 'found': False, 'censored': False}
    sz = np.bincount(cc.ravel()); k = touch[np.argmax(sz[touch])]; pool = cc == k
    low = np.array([(np.where(pool[:, c])[0].max() - surf[c]) if pool[:, c].any() else -1 for c in range(W)])
    d = float(low.max() * step); bottom = int(np.where(pool.any(1))[0].max())
    cols = np.where((pool & band).any(0))[0]
    return {'depth_um': d, 'width_um': float((cols.max() - cols.min() + 1) * step) if len(cols) else 0.0, 'found': True,
            'censored': bool(bottom >= H - 1 - EDGE_UM / step), 'pool_px': int(pool.sum())}
def stitch(top_eul, top_ph, bot_eul, bot_ph, min_frac=0.05, max_frac=0.6, max_dx=40, min_corr=0.6):
    """vertical offset of the bottom field below the top field; returns (row offset, col shift, corr) or None."""
    A = np.where(top_ph > 0, top_eul[..., 0], np.nan); B = np.where(bot_ph > 0, bot_eul[..., 0], np.nan); H = A.shape[0]; best = None
    for ov in range(int(min_frac * H), int(max_frac * H), 2):
        a = A[H - ov:]; b0 = B[:ov]
        for dx in range(-max_dx, max_dx + 1, 4):
            b = np.roll(b0, dx, axis=1)[:, max_dx:-max_dx]; aa = a[:, max_dx:-max_dx]; ok = np.isfinite(aa) & np.isfinite(b)
            if ok.sum() < 1000: continue
            x, y = aa[ok], b[ok]; cr = float(np.corrcoef(x, y)[0, 1])
            if best is None or cr > best[2]: best = (H - ov, dx, cr)
    return best if best and best[2] >= min_corr else None
