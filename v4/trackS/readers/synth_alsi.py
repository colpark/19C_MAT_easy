#!/usr/bin/env python3
"""synth_alsi.py (S4d): synthetic 5000x ETD fields of cellular AlSi10Mg at 53.96 nm per pixel, 1024 x 1536 (as the deposit after the
databar crop). Cells: Voronoi, target mean equivalent diameter 0.4-1.6 um; a coarse band (cells x1.6-2.2) along a curved melt-pool
boundary and an elongated zone (stretched x1.5-2.5 along a random direction) cover 20-40 % of the field. Walls: bright Si network,
width 0.10-0.25 um, intensity varying +-30 %, 5 % of wall segments broken. Contrast: cell interiors grey 0.35-0.5, walls 0.75-0.95;
background gradient; blur sigma 0.8-1.3 px; noise sigma 0.05-0.13 on the 0-1 scale (real cell-interior noise 0.06-0.22 after the percentile stretch, measured on
the dark 30 % of each field; one session ~0 after smoothing: 15 % of synthetic fields get noise 0.01 and blur 2 px). Truth: number-mean equivalent diameter of the true cells not
touching the border."""
import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
PX = 0.0539583
def field(rng, d_um=None, H=1024, W=1536):
    d_um = rng.uniform(0.4, 1.6) if d_um is None else d_um; yy, xx = np.mgrid[0:H, 0:W].astype(float)
    # local scale map: coarse band and elongated zone
    cy = rng.uniform(0.2, 0.8) * H; amp = rng.uniform(0.1, 0.3) * H; band = np.abs(yy - cy - amp * np.sin(xx / W * np.pi * rng.uniform(0.5, 2))) < rng.uniform(0.05, 0.12) * H
    scale = np.where(band, rng.uniform(1.6, 2.2), 1.0)
    th = rng.uniform(0, np.pi); u = np.cos(th) * xx + np.sin(th) * yy; v = -np.sin(th) * xx + np.cos(th) * yy
    elong = (np.hypot(xx - rng.uniform(0, W), yy - rng.uniform(0, H)) < rng.uniform(0.15, 0.3) * W) & ~band; st = rng.uniform(1.5, 2.5)
    s_px = d_um / PX; n = int(H * W / (np.pi * (s_px / 2) ** 2) * 1.3)
    pts = np.c_[rng.uniform(0, H, n), rng.uniform(0, W, n)]
    keep = rng.random(n) < 1.0 / np.interp(pts[:, 0], [0, H], [1, 1]) ** 2
    bmask = band[np.clip(pts[:, 0].astype(int), 0, H - 1), np.clip(pts[:, 1].astype(int), 0, W - 1)]
    keep &= ~bmask | (rng.random(n) < 1 / 1.9 ** 2); pts = pts[keep]
    # anisotropic distance in the elongated zone: compress coordinates along u
    Y = np.where(elong, cy + (yy - cy), yy); X = xx
    cu = np.cos(th) * pts[:, 1] + np.sin(th) * pts[:, 0]; cv = -np.sin(th) * pts[:, 1] + np.cos(th) * pts[:, 0]
    q = np.c_[np.where(elong.ravel(), u.ravel() / st, u.ravel()), v.ravel()]; P = np.c_[cu, cv]
    Pe = np.c_[cu / st, cv]; _, l1 = cKDTree(P).query(q[~elong.ravel()] if (~elong).any() else q[:1]); _, l2 = cKDTree(Pe).query(q[elong.ravel()] if elong.any() else q[:1])
    lab = np.empty(H * W, int); lab[~elong.ravel()] = l1 if (~elong).any() else 0
    if elong.any(): lab[elong.ravel()] = l2
    lab = lab.reshape(H, W)
    wall = np.zeros((H, W), bool); wall[:, 1:] |= lab[:, 1:] != lab[:, :-1]; wall[1:] |= lab[1:] != lab[:-1]
    ww = rng.uniform(0.10, 0.25) / PX; it = int(round(ww / 2)) - 1
    if it >= 1: wall = ndi.binary_dilation(wall, iterations=it)   # iterations=0 would dilate until nothing changes (scipy): fixed
    brk = ndi.binary_dilation(rng.random((H, W)) < 0.0005, iterations=3); wall &= ~brk
    img = rng.uniform(0.35, 0.5) + 0.05 * rng.normal(size=1)[0] * np.ones((H, W)); wi = rng.uniform(0.75, 0.95) * (1 + 0.3 * (ndi.gaussian_filter(rng.random((H, W)), 30) - 0.5))
    img = np.where(wall, wi, img) + 0.1 * (xx / W - 0.5) * rng.uniform(-1, 1)
    smooth = rng.random() < 0.15
    img = ndi.gaussian_filter(img, 2.0 if smooth else rng.uniform(0.8, 1.3)) + rng.normal(0, 0.01 if smooth else rng.uniform(0.05, 0.13), (H, W))
    area = np.bincount(lab.ravel()) * PX ** 2; edge = np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])
    ok = area > 0; ok[edge] = False; truth = float((2 * np.sqrt(area[ok] / np.pi)).mean())
    return np.clip(img, 0, 1) * 255, {'d_mean_um': truth, 'target_um': d_um}
