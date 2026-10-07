#!/usr/bin/env python3
"""synth_stv.py: synthetic IPF maps and DIC Exx fields at the Stinville working grid (401 nm per pixel), with known truth.
Grains: Voronoi, mean equivalent diameter 62 um (155 px; README grain size), each with an IPF-like colour; 40 % of grains carry 1-2 twin
bands (8-25 px wide) of another colour; per-grain colour gradient up to +-8 levels (orientation spread), colour noise sigma 3 levels,
1 px boundary blur; 8 % of neighbouring grain pairs get near-identical colours (difference 4-10 levels), as in IPF-X maps where different
orientations share a loading-direction colour.
Exx: per grain a base strain ~ mean m (0.6-1.6 %) x U(0.3, 1.0); slip bands as parallel lines at a grain angle, spacing 3-12 um, width
2-4 px, band strain 5-25 x m; DIC smoothing Gaussian 1.2 px (31-px subset at 100 nm, step 3 -> ~1 um); noise sigma 0.1 m.
Truth per domain: the reader's statistic on the clean field (before DIC smoothing and noise), exx_field.clean; band masks are
also returned (sub-resolution at 401 nm, so band area is not recoverable and is not used as truth)."""
import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
def grains(rng, N=1024, d_px=155):
    ng = max(int(N * N / (np.pi * (d_px / 2) ** 2)), 6); pts = rng.uniform(0, N, (ng, 2)); yy, xx = np.mgrid[0:N, 0:N]
    _, lab = cKDTree(pts).query(np.c_[yy.ravel(), xx.ravel()]); lab = lab.reshape(N, N); dom = lab.copy(); nxt = ng; ang = rng.uniform(0, np.pi, ng)
    col = {g: rng.uniform(30, 250, 3) for g in range(ng)}
    nb = set()
    for a, b in ((lab[:, :-1], lab[:, 1:]), (lab[:-1], lab[1:])):
        m = a != b; nb |= set(zip(a[m].tolist(), b[m].tolist()))
    for a, b in list(nb):
        if a < b and rng.random() < 0.08: col[b] = np.clip(col[a] + rng.uniform(4, 10, 3) * rng.choice([-1, 1], 3), 0, 255)
    for g in range(ng):
        if rng.random() < 0.4:
            m = lab == g
            if m.sum() < 2000: continue
            th = rng.uniform(0, np.pi); u = np.cos(th) * yy + np.sin(th) * xx; c0 = u[m].mean()
            for _ in range(rng.integers(1, 3)):
                w = rng.uniform(8, 25); off = rng.uniform(-50, 50); band = m & (np.abs(u - c0 - off) < w / 2)
                if band.sum() > 300: dom[band] = nxt; col[nxt] = rng.uniform(30, 250, 3); ang = np.append(ang, ang[g]); nxt += 1
    # truth domains are connected regions (the reader's definition): a twin band cutting a grain leaves 2-3 parent pieces
    out = np.zeros_like(dom); nxt2 = 0; col2 = {}; ang2 = []
    for d in np.unique(dom):
        cc, k = ndi.label(dom == d)
        for j in range(1, k + 1):
            out[cc == j] = nxt2; col2[nxt2] = col[d]; ang2.append(ang[d] if d < len(ang) else 0.0); nxt2 += 1
    return lab, out, col2, np.array(ang2)
def ipf_map(rng, dom, col):
    N = dom.shape[0]; yy, xx = np.mgrid[0:N, 0:N]; img = np.zeros((N, N, 3))
    gx = {d: rng.uniform(-8, 8, 3) / N for d in col}
    for d in np.unique(dom):
        m = dom == d; img[m] = col[d] + np.outer((xx[m] - N / 2), gx[d])
    img = ndi.uniform_filter(img, size=(2, 2, 1)) + rng.normal(0, 3, img.shape); return np.clip(img, 0, 255).astype(np.uint8)
def exx_field(rng, dom, ang, m):
    N = dom.shape[0]; yy, xx = np.mgrid[0:N, 0:N]; base = np.zeros((N, N)); band = np.zeros((N, N), bool); amp = np.zeros((N, N))
    for d in np.unique(dom):
        msk = dom == d; base[msk] = m * rng.uniform(0.3, 1.0)
        th = ang[d] if d < len(ang) else rng.uniform(0, np.pi); u = np.cos(th) * yy + np.sin(th) * xx
        sp = rng.uniform(3, 12) / 0.401; w = rng.uniform(2, 4); ph = rng.uniform(0, sp)
        if rng.random() < 0.15: continue   # some domains do not slip
        b = msk & (np.mod(u + ph, sp) < w); band |= b; amp[b] = m * rng.uniform(5, 25)
    clean = base + amp; f = ndi.gaussian_filter(clean, 1.2) + rng.normal(0, 0.1 * m, (N, N)); exx_field.clean = clean.astype(np.float32); return f.astype(np.float32), band
def truth_fraction(dom, band):
    n = np.bincount(dom.ravel()); s = np.bincount(dom.ravel(), weights=band.ravel().astype(float)); return s / np.maximum(n, 1), n
