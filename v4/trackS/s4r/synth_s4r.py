#!/usr/bin/env python3
"""synth_s4r.py (S4r): synthetic BSE tiles of CEM III/B paste with known phase fractions, ranges from the refodat91 DEV tiles only
(dev_stats.json and the dev histograms, 2026-10-07):
  levels: pore 5-40; hydrate paste 85-200 (uncarbonated ~95, carbonated 150-200); anhydrous (slag) = paste + 50-90, clipped at 255 as on the
  carbonated dev tiles; clinker specks = paste + 110-160 (clipped); paste texture: Gaussian random field, SD 6-14, correlation 3-8 px.
  pixel noise SD 30-50 (dev 31-59); blur Gaussian sigma 1.0-1.4 px (dev edge fits 1.1-1.34); 84.31 nm px.
  anhydrous grains: angular polygons, equivalent diameter lognormal (median 6 um, log-SD 0.6), up to the target fraction; clinker specks
  0.5-2 um, 0-10 % of the anhydrous area. pores: blobs lognormal (median 1.1 um, log-SD 0.8; dev pore EQD median 1.05-1.17 um) plus 0-3
  cracks 2-4 px wide, up to the target porosity. Truth = the drawn masks (pore over all; anhydrous over non-pore), before blur and noise.
  ITZ mode: a homogeneous aggregate block on the left (gray = paste + 20-40, no texture) and porosity decreasing with distance from it.
API: tile(seed, size=1024, porosity=None, anhydrous=None, itz=False) -> (image uint8, truth dict)."""
import numpy as np
from scipy import ndimage as ndi
PX_UM = 0.0843099

def _poly(rng, shape, cy, cx, r):
    n = rng.integers(5, 9); ang = np.sort(rng.uniform(0, 2 * np.pi, n)); rad = r * rng.uniform(0.6, 1.3, n)
    ys, xs = cy + rad * np.sin(ang), cx + rad * np.cos(ang)
    y0, y1 = int(max(ys.min(), 0)), int(min(ys.max() + 1, shape[0])); x0, x1 = int(max(xs.min(), 0)), int(min(xs.max() + 1, shape[1]))
    if y1 <= y0 or x1 <= x0: return None
    yy, xx = np.mgrid[y0:y1, x0:x1]; inside = np.ones(yy.shape, bool)
    for k in range(n):
        ax, ay, bx, by = xs[k], ys[k], xs[(k + 1) % n], ys[(k + 1) % n]
        inside &= ((bx - ax) * (yy - ay) - (by - ay) * (xx - ax)) >= 0
    return (slice(y0, y1), slice(x0, x1)), inside

def tile(seed, size=1024, porosity=None, anhydrous=None, itz=False):
    rng = np.random.default_rng(seed); sh = (size, size)
    por_t = porosity if porosity is not None else rng.uniform(0.05, 0.30); anh_t = anhydrous if anhydrous is not None else rng.uniform(0.05, 0.45)
    agg = np.zeros(sh, bool)
    if itz: agg[:, :int(size * rng.uniform(0.2, 0.3))] = True
    anh = np.zeros(sh, bool); paste_area = (~agg).sum()
    while (anh & ~agg).sum() < anh_t * paste_area:
        r = np.exp(rng.normal(np.log(6.0 / PX_UM / 2), 0.6)); p = _poly(rng, sh, rng.uniform(0, size), rng.uniform(0, size), r)
        if p: anh[p[0]] |= p[1]
    anh &= ~agg; clk = np.zeros(sh, bool); target_clk = rng.uniform(0, 0.10) * anh.sum()
    while clk.sum() < target_clk:
        cy, cx = np.nonzero(anh); i = rng.integers(len(cy)); r = rng.uniform(0.25, 1.0) / PX_UM
        yy, xx = np.ogrid[:size, :size]; clk |= ((yy - cy[i]) ** 2 + (xx - cx[i]) ** 2 <= r * r) & anh
    pore = np.zeros(sh, bool); dist = ndi.distance_transform_edt(~agg) * PX_UM if itz else None
    for _ in range(rng.integers(0, 4)):
        y0, x0 = rng.uniform(0, size, 2); th = rng.uniform(0, np.pi); L = rng.uniform(0.3, 1.0) * size; w = rng.integers(2, 5)
        t = np.linspace(0, L, int(L)); ys = (y0 + t * np.sin(th)).astype(int); xs = (x0 + t * np.cos(th)).astype(int); ok = (ys >= 0) & (ys < size) & (xs >= 0) & (xs < size)
        cr = np.zeros(sh, bool); cr[ys[ok], xs[ok]] = True; pore |= ndi.binary_dilation(cr, iterations=w // 2) & ~agg
        if (pore & ~anh).sum() > 0.3 * por_t * paste_area: break
    tries = 0
    while (pore & ~agg).sum() < por_t * paste_area and tries < 200000:
        tries += 1; r = np.exp(rng.normal(np.log(1.1 / PX_UM / 2), 0.8)); cy, cx = rng.uniform(0, size, 2)
        if itz:   # acceptance falls with distance from the aggregate: porosity gradient
            d = max(cx - agg[0].sum(), 0) * PX_UM
            if rng.random() > np.exp(-d / 25.0) * 0.8 + 0.2: continue
        yy, xx = np.ogrid[:size, :size]; blob = ((yy - cy) ** 2 + (xx - cx) ** 2 <= r * r) & ~agg
        pore |= blob
    anh &= ~pore; clk &= ~pore
    pl, pa = rng.uniform(5, 40), rng.uniform(85, 200); sl = pa + rng.uniform(50, 90); cl = pa + rng.uniform(110, 160)
    tex = ndi.gaussian_filter(rng.normal(0, 1, sh), rng.uniform(3, 8)); tex = tex / tex.std() * rng.uniform(6, 14)
    img = np.full(sh, pa) + tex; img[anh] = sl; img[clk] = cl; img[pore] = pl
    if itz: img[agg] = pa + rng.uniform(20, 40)
    img = ndi.gaussian_filter(img, rng.uniform(1.0, 1.4)) + rng.normal(0, rng.uniform(30, 50), sh)
    img = np.clip(np.rint(img), 0, 255).astype(np.uint8)
    paste = ~agg; truth = {'porosity': float((pore & paste).sum() / paste.sum()), 'anhydrous': float((anh & paste).sum() / paste.sum())}
    truth['hydrate'] = 1 - truth['porosity'] - truth['anhydrous']
    if itz:
        x = np.arange(size); dx = (x - agg[0].sum()) * PX_UM; truth['itz_bins'] = []
        for lo, hi in ((0, 10), (10, 20), (20, 30), (30, 50), (50, 100)):
            m = (dx >= lo) & (dx < hi)
            if m.any(): truth['itz_bins'].append((lo, hi, float(pore[:, m].mean())))
    return img, truth
