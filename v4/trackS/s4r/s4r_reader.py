#!/usr/bin/env python3
"""s4r_reader.py (Track S round 3, reader S4r, refodat91): BSE phase and porosity fractions per tile, numpy/scipy only.
Per tile (uint8 BSE, 84.31 nm/px). Per-tile relative classification: gray levels are not comparable across specimens (detector contrast
84.9-89.2 differs by specimen and carbonated tiles saturate), so no absolute threshold is used.
  1. smooth: 3 x 3 median, then Gaussian sigma SIGMA px (pixel noise is ~35 gray levels SD at 3 us dwell).
  2. class model: deterministic 3-class Otsu (exhaustive search for the two thresholds maximising between-class variance) on the
     histogram of all smoothed pixels; every pixel is classed by its smoothed value only. (Draft 1 used a 3-component EM mixture,
     unstable on the broad dev histograms; draft 2 classed raw pixels >= SAT as anhydrous, which on synthetic dev seeds counted noisy
     bright paste (carbonated-like, paste ~180-200) as anhydrous. Both replaced before any fresh-seed gate or held-out read.)
  3. pores: dark class after a binary opening with a (OPEN x OPEN) square (detection limit ~ OPEN px = 0.25 um).
  4. anhydrous (slag + clinker, merged: clinker is not separable from slag on saturated tiles): bright class, opened likewise.
  5. aggregate mask: connected anhydrous-or-hydrate regions that are homogeneous (local SD below HOMOG_SD in a 15 px window) and larger
     than AGG_UM2; excluded from every fraction (design coordinate only, never a key).
  6. fractions over the paste area (tile minus aggregate): porosity, anhydrous, hydrate = 1 - porosity - anhydrous.
Parameters below are tuned on synthetic dev seeds only and frozen in S4r."""
import numpy as np
from scipy import ndimage as ndi
SIGMA = 1.5; OPEN = 3; SAT = 254; AGG_UM2 = 5000.0; HOMOG_SD = 4.0; PX_UM = 0.0843099; PORE_SHIFT = 5.0   # tune_s4r.py on synthetic dev seeds 0-29 (OPEN fixed at 3 px by the round-3 spec)
ITZ_BINS = ((0, 10), (10, 20), (20, 30), (30, 50), (50, 100))   # frozen (S4r-split)

def otsu3(h):
    """Two thresholds (t1 < t2, bin indices) maximising the 3-class between-class variance of histogram h (256 bins)."""
    p = h / max(h.sum(), 1); i = np.arange(len(p)); w = np.cumsum(p); m = np.cumsum(p * i); mt = m[-1]; best = (-1, 0, 0)
    for t1 in range(1, 254):
        w0, m0 = w[t1], m[t1]
        if w0 <= 0: continue
        t2 = np.arange(t1 + 1, 255); w1 = w[t2] - w0; w2 = 1 - w[t2]; ok = (w1 > 0) & (w2 > 0)
        if not ok.any(): continue
        m1 = m[t2] - m0; m2 = mt - m[t2]
        v = np.where(ok, m0 ** 2 / w0 + np.where(ok, m1 ** 2 / np.where(ok, w1, 1), 0) + np.where(ok, m2 ** 2 / np.where(ok, w2, 1), 0), -1)
        j = int(np.argmax(v))
        if v[j] > best[0]: best = (v[j], t1, int(t2[j]))
    return best[1] + 0.5, best[2] + 0.5

def smooth(a):
    return ndi.gaussian_filter(ndi.median_filter(np.asarray(a, dtype=np.float32), 3), SIGMA)

def tile_thresholds(a):
    a = np.asarray(a, dtype=np.float32); sat = a >= SAT; s = smooth(a)
    h, _ = np.histogram(s, bins=256, range=(0, 256)); t1, t2 = otsu3(h.astype(float)); return s, sat, t1 + PORE_SHIFT, t2

def read_array(a):
    a = np.asarray(a, dtype=np.float32); s, sat, t01, t12 = tile_thresholds(a); st = np.ones((OPEN, OPEN), bool)
    pore = ndi.binary_opening(s <= t01, st); anh = ndi.binary_opening(s >= t12, st) & ~pore
    loc_sd = np.sqrt(np.clip(ndi.uniform_filter(s ** 2, 15) - ndi.uniform_filter(s, 15) ** 2, 0, None))
    homog = (loc_sd < HOMOG_SD) & ~pore
    lab, n = ndi.label(homog); agg = np.zeros_like(homog)
    if n:
        sizes = ndi.sum(homog, lab, range(1, n + 1)) * PX_UM ** 2; agg = np.isin(lab, 1 + np.nonzero(sizes > AGG_UM2)[0])
    paste = ~agg; npx = paste.sum()
    if npx < 0.2 * a.size: return {'ok': False, 'why': 'aggregate covers most of the tile'}
    por = float((pore & paste).sum() / npx); an = float((anh & paste).sum() / npx)
    return {'ok': True, 'porosity': por, 'anhydrous': an, 'hydrate': 1 - por - an, 'aggregate_frac': float(agg.mean()), 'sat_frac': float(sat.mean()),
            't_pore': float(t01), 't_anh': float(t12)}

def aggregate_mask(s, pore):
    loc_sd = np.sqrt(np.clip(ndi.uniform_filter(s ** 2, 15) - ndi.uniform_filter(s, 15) ** 2, 0, None)); homog = (loc_sd < HOMOG_SD) & ~pore
    lab, n = ndi.label(homog)
    if not n: return np.zeros_like(homog)
    sizes = ndi.sum(homog, lab, range(1, n + 1)) * PX_UM ** 2; return np.isin(lab, 1 + np.nonzero(sizes > AGG_UM2)[0])

def itz_profile(a):
    """Porosity per frozen distance bin from our aggregate mask (design coordinate, never a key)."""
    a = np.asarray(a, dtype=np.float32); s, sat, t01, t12 = tile_thresholds(a); st = np.ones((OPEN, OPEN), bool)
    pore = ndi.binary_opening(s <= t01, st); agg = aggregate_mask(s, pore)
    if not agg.any(): return {'ok': False, 'why': 'no aggregate'}
    d = ndi.distance_transform_edt(~agg) * PX_UM; out = []
    for lo, hi in ITZ_BINS:
        m = (d >= lo) & (d < hi) & ~agg
        if m.sum() > 1000: out.append((lo, hi, float(pore[m].mean())))
    return {'ok': True, 'bins': out, 'agg': agg}

def classify(a):
    """Per-pixel class map (0 pore, 1 hydrate, 2 anhydrous) without the aggregate mask."""
    s, sat, t01, t12 = tile_thresholds(a); st = np.ones((OPEN, OPEN), bool); out = np.ones(s.shape, np.uint8)
    out[ndi.binary_opening(s >= t12, st)] = 2; out[ndi.binary_opening(s <= t01, st)] = 0; return out

def read(path):
    import tifffile
    return read_array(tifffile.imread(path))
