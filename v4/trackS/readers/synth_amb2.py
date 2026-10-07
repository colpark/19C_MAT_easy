#!/usr/bin/env python3
"""synth_amb2.py (S4a-2): synthetic single-track EBSD cross sections built from the dev statistics (dev_amb2.json: pads only).
Grid 1203 x 903 points at 0.25 um per field (as the deposit). Base: Voronoi grains, lognormal diameter median 7.5 um (dev base 10-90 %:
4.8-14.5 um), random orientations; TWIN_FRAC of base grains carry 1-3 annealing-twin bands 1-4 um wide whose orientation is the parent
times an exact Sigma-3 rotation (60 deg about a <111>); orientation noise 0.09 deg (dev base KAM median 0.094). Mount above a gently
curved surface is unindexed; 2 % random unindexed points. Pool: half-ellipse at the surface, depth D 60-260 um, half width 50-80 um;
columnar grains as angular wedges about the top centre with an arc width of 6-16 um at the fusion boundary (dev pool d median 10 um),
50 % epitaxial (orientation of the base grain they grow from), twin-free; orientation noise 0.17 deg (dev pool KAM median 0.165).
Deep pools: when D exceeds the field, a bottom field is generated with a vertical overlap of 15-35 % (a stitch test) unless
no_bottom=True (a censoring test). Truth: D from the local surface, and whether the covered area contains the whole pool."""
import numpy as np
from scipy.spatial import cKDTree
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import amb2_reader as R, stv_reader as SR
TWIN_FRAC = 0.9   # calibrated to the dev base sigma3 distribution (10th percentile 0.14: ~90 % of base grains carry twin boundaries)
def rand_q(rng, n):
    u = rng.random((n, 3)); return np.c_[np.sqrt(1 - u[:, 0]) * np.sin(2 * np.pi * u[:, 1]), np.sqrt(1 - u[:, 0]) * np.cos(2 * np.pi * u[:, 1]),
                                          np.sqrt(u[:, 0]) * np.sin(2 * np.pi * u[:, 2]), np.sqrt(u[:, 0]) * np.cos(2 * np.pi * u[:, 2])][:, [3, 0, 1, 2]]
def q2eul(q):
    w, x, y, z = np.moveaxis(q, -1, 0); Phi = 2 * np.arctan2(np.hypot(x, y), np.hypot(w, z)); a = np.arctan2(z, w); b = np.arctan2(y, x)
    return np.stack([np.mod(a + b, 2 * np.pi), Phi, np.mod(a - b, 2 * np.pi)], -1)
def noisy(rng, q, deg):
    ax = rng.normal(size=q.shape[:-1] + (3,)); ax /= np.linalg.norm(ax, axis=-1, keepdims=True); ang = np.radians(rng.normal(0, deg, q.shape[:-1]))
    dq = np.concatenate([np.cos(ang / 2)[..., None], np.sin(ang / 2)[..., None] * ax], -1); return R.qmul(q, dq)
def section(rng, step=0.25, Hf=903, W=1203, D=None, no_bottom=False):
    D = rng.uniform(60, 260) if D is None else D; top = rng.uniform(15, 40) / step; hw = rng.uniform(50, 80) / step
    need = top + D / step + 40; ov = int(rng.uniform(0.15, 0.35) * Hf); two = need > Hf and not no_bottom
    H = Hf * 2 - ov if two else Hf; yy, xx = np.mgrid[0:H, 0:W]
    surf = top + 3 / step * np.sin(xx[0] / W * np.pi * rng.uniform(1, 3)); x0 = W / 2 + rng.uniform(-60, 60)
    dmed = 7.5 / step; ng = int(H * W / (np.pi * (dmed / 2) ** 2) * 0.8); pts = np.c_[rng.uniform(0, H, ng), rng.uniform(0, W, ng)]
    _, base = cKDTree(pts).query(np.c_[yy.ravel(), xx.ravel()]); base = base.reshape(H, W); q = rand_q(rng, ng)[base]
    S3 = R.S3V
    for g in rng.choice(ng, int(TWIN_FRAC * ng), replace=False):
        m = base == g
        if m.sum() < 80: continue
        th = rng.uniform(0, np.pi); u = np.cos(th) * yy + np.sin(th) * xx; c0 = u[m].mean(); w = rng.uniform(1, 4) / step
        for off in rng.uniform(-0.3, 0.3, rng.integers(1, 4)) * np.sqrt(m.sum()):
            band = m & (np.abs(u - c0 - off) < w / 2)
            if band.any(): q[band] = R.qmul(q[band][:1], S3[rng.integers(0, 8)][None])[0]
    rel = yy - surf[None, :]; b = D / step; pool = (rel >= 0) & (((xx - x0) / hw) ** 2 + (rel / b) ** 2 <= 1)
    ang = np.degrees(np.arctan2(rel, xx - x0)); edges = []; a = 0.0
    while a < 180:
        r_px = np.hypot(hw * np.cos(np.radians(a)), b * np.sin(np.radians(a))); a += np.degrees(rng.uniform(6, 16) / step / max(r_px, 1)); edges.append(a)
    wid = np.searchsorted(np.array(edges), ang)
    for k in np.unique(wid[pool]):
        m = pool & (wid == k)
        if rng.random() < 0.5:
            iy, ix = np.where(m); far = np.argmax(((ix - x0) / hw) ** 2 + (rel[iy, ix] / b) ** 2); oq = q[iy[far], ix[far]]
        else: oq = rand_q(rng, 1)[0]
        q[m] = oq
    q = noisy(rng, q, 0.09); q[pool] = noisy(rng, q[pool], np.sqrt(0.17 ** 2 - 0.09 ** 2))
    eul = q2eul(q); ph = np.ones((H, W)); ph[yy < surf[None, :]] = 0; ph[rng.random((H, W)) < 0.02] = 0
    truth = {'depth_um': float(D), 'covered': bool(two or need <= Hf)}
    if two:
        return {'top': (ph[:Hf], eul[:Hf]), 'bottom': (ph[Hf - ov:], eul[Hf - ov:]), 'overlap_rows': ov, 'step': step, 'truth': truth}
    return {'top': (ph, eul), 'bottom': None, 'step': step, 'truth': truth}
