#!/usr/bin/env python3
"""synth_amb.py: synthetic EBSD cross sections of a single laser track at the deposit's grid (1203 x 903 points, 0.25 um).
Base plate: equiaxed Voronoi grains (mean diameter 20-40 um) with random orientations, 30 % carrying an annealing-twin band (random
orientation). Mount: rows above a gently curved surface (+-3 um) are unindexed. Melt pool: half ellipse at the surface, depth D 30-200 um
(capped by the map), width W 60-220 um; inside, columnar grains as angular wedges about a point on the surface centre line (wedge
1.5-5 deg), each wedge 50 % epitaxial (orientation of the base grain where it meets the boundary) or random; 20 % of wedges split once
along their length (new random orientation). Noise: 2 % unindexed points, orientation noise 0.5 deg. Truth: D and W as generated
(measured from the local surface)."""
import numpy as np
from scipy.spatial import cKDTree
def rand_eul(rng, n): return np.c_[rng.uniform(0, 2 * np.pi, n), np.arccos(rng.uniform(-1, 1, n)), rng.uniform(0, 2 * np.pi, n)]
def section(rng, H=903, W=1203, step=0.25):
    D = rng.uniform(30, 200); Wd = rng.uniform(60, 220); top = rng.uniform(15, 40) / step; yy, xx = np.mgrid[0:H, 0:W]
    surf = top + 3 / step * np.sin(xx[0] / W * np.pi * rng.uniform(1, 3)); x0 = W / 2 + rng.uniform(-60, 60)
    d = rng.uniform(20, 40) / step; ng = int(H * W / (np.pi * (d / 2) ** 2)); pts = np.c_[rng.uniform(0, H, ng), rng.uniform(0, W, ng)]
    _, base = cKDTree(pts).query(np.c_[yy.ravel(), xx.ravel()]); base = base.reshape(H, W); ori = rand_eul(rng, ng); eul = ori[base]
    for g in rng.choice(ng, int(0.3 * ng), replace=False):
        m = base == g
        if m.sum() < 500: continue
        th = rng.uniform(0, np.pi); u = np.cos(th) * yy + np.sin(th) * xx; c0 = u[m].mean(); w = rng.uniform(2, 6) / step
        band = m & (np.abs(u - c0) < w / 2); eul[band] = rand_eul(rng, 1)[0]
    a, b = Wd / 2 / step, D / step; rel_y = (yy - surf[None, :]); pool = (rel_y >= 0) & (((xx - x0) / a) ** 2 + (rel_y / b) ** 2 <= 1)
    ang = np.degrees(np.arctan2(rel_y, xx - x0)); edges = np.cumsum(rng.uniform(1.5, 5, 200)); edges = edges[edges < 180]; wid = np.searchsorted(edges, ang)
    for k in np.unique(wid[pool]):
        m = pool & (wid == k)
        if rng.random() < 0.5:   # epitaxial: copy the base orientation where the wedge meets the boundary
            iy, ix = np.where(m); far = np.argmax(((ix - x0) / a) ** 2 + (rel_y[iy, ix] / b) ** 2); o = ori[base[iy[far], ix[far]]]
        else: o = rand_eul(rng, 1)[0]
        eul[m] = o
        if rng.random() < 0.2:
            r = np.hypot((xx - x0) / a, rel_y / b); cut = rng.uniform(0.3, 0.7); eul[m & (r < cut)] = rand_eul(rng, 1)[0]
    eul = eul + np.radians(rng.normal(0, 0.5, eul.shape)); ph = np.ones((H, W)); ph[yy < surf[None, :]] = 0; ph[rng.random((H, W)) < 0.02] = 0
    return ph, eul, step, {'depth_um': float(min(D, (H - surf.max()) * step)), 'width_um': float(Wd)}
