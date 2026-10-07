#!/usr/bin/env python3
"""amb_reader.py (Track S pilot S1, AM Bench 2022 AMB2022-03): melt pool depth and width from EBSD cross sections of single laser
tracks (.ctf exports: native 0.25 um step, orientations and band contrast; the TIFF maps carry borders and no pixel-size tag).
Definitions frozen (S4a) before the reader measures a real single-track map:
  grains     neighbour misorientation < GRAIN_DEG (cubic symmetry, stv_reader._mis) on indexed points (Phase > 0); unindexed points -1.
  surface    per column, the first indexed row (the mount above the track does not index).
  pool       domains with aspect ratio >= A_MIN (PCA of pixel coordinates) and area >= MIN_UM2, closed with a disk of CLOSE_UM, and the
             connected component that touches the surface band (top SURF_UM below the surface) with the largest area.
  depth      the largest value of the lower envelope: per column, local surface to the lowest pool pixel, median-filtered over ENV_UM.
  width      the horizontal extent of pool pixels within SURF_UM of the surface (um).
No model is used. Data files are read only."""
import numpy as np
from scipy import ndimage as ndi
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import stv_reader as SR
GRAIN_DEG, A_MIN, MIN_UM2, CLOSE_UM, SURF_UM, ENV_UM = 10.0, 6.0, 20.0, 2.0, 5.0, 20.0
def read_ctf(path):
    with open(path, errors='replace') as fh:
        head = {}
        for line in fh:
            if line.startswith('Phase\tX'): break
            p = line.rstrip('\n').split('\t')
            if len(p) >= 2: head[p[0].lstrip('﻿')] = p[1]
        W, H, st = int(head['XCells']), int(head['YCells']), float(head['XStep'])
        a = np.loadtxt(fh, usecols=(0, 5, 6, 7, 9), max_rows=W * H)
    ph = a[:, 0].reshape(H, W); eul = np.radians(a[:, 1:4]).reshape(H, W, 3); bc = a[:, 4].reshape(H, W); return ph, eul, bc, st
def grains(ph, eul, deg=None):
    deg = GRAIN_DEG if deg is None else deg
    lab = SR.ang_domains(eul, mis_deg=deg); lab = np.where(ph > 0, lab, -1); return lab
def measure(ph, eul, step, lab=None):
    lab = grains(ph, eul) if lab is None else lab; H, W = lab.shape; idx = ph > 0
    surf = np.where(idx.any(0), idx.argmax(0), H)
    ids = np.unique(lab[lab >= 0]); col = np.zeros(lab.max() + 2, bool); yy, xx = np.mgrid[0:H, 0:W]
    flat = lab.ravel(); order = np.argsort(flat); sl = np.searchsorted(flat[order], ids); el = np.searchsorted(flat[order], ids, side='right')
    for i, a, b in zip(ids, sl, el):
        p = order[a:b]
        if len(p) * step ** 2 < MIN_UM2: continue
        y, x = yy.ravel()[p].astype(float), xx.ravel()[p].astype(float); cv = np.cov(np.vstack([y, x]))
        ev = np.sort(np.linalg.eigvalsh(cv)); col[i] = ev[1] / max(ev[0], 1e-6) >= A_MIN ** 2
    m = np.where(lab >= 0, col[np.clip(lab, 0, None)], False)
    r = max(1, int(round(CLOSE_UM / step))); disk = np.hypot(*np.mgrid[-r:r + 1, -r:r + 1]) <= r
    m = ndi.binary_closing(m, structure=disk) & idx
    cc, n = ndi.label(m)
    if n == 0: return {'depth_um': 0.0, 'width_um': 0.0, 'found': False}
    band = (yy - surf[None, :] >= 0) & (yy - surf[None, :] <= SURF_UM / step)
    touch = np.unique(cc[band & (cc > 0)])
    if not len(touch): return {'depth_um': 0.0, 'width_um': 0.0, 'found': False}
    sz = np.bincount(cc.ravel()); k = touch[np.argmax(sz[touch])]; pool = cc == k
    low = np.array([(np.where(pool[:, c])[0].max() - surf[c]) if pool[:, c].any() else np.nan for c in range(W)], float)
    ok = np.isfinite(low); k = max(1, int(round(ENV_UM / step)))   # lower envelope, median over ENV_UM along x (isolated merged grains)
    env = ndi.median_filter(np.where(ok, low, 0.0), size=k) if ok.any() else low; depth = float(np.nanmax(np.where(ok, env, np.nan))) * step if ok.any() else 0.0
    cols = np.where((pool & band).any(0))[0]; width = (cols.max() - cols.min() + 1) * step if len(cols) else 0.0
    return {'depth_um': float(depth), 'width_um': float(width), 'found': True, 'pool_px': int(pool.sum())}
