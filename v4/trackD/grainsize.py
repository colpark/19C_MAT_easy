#!/usr/bin/env python3
"""grainsize.py (v4 Track D, skill M2 micrographs: two methods): mean intercept length of all contrast boundaries (grain and annealing-twin
boundaries) in BSE channeling-contrast micrographs of CrFeNi. Twin boundaries are not separated (no orientation data), and boundaries
between grains of near-equal gray are invisible to any method, so the quantity is procedure-defined: a constant multiple of the true
boundary intercept (synthetic bias ~1.4), compared across conditions and fitted, never equated with the authors' numbers.
Preprocessing (both methods): crop the FEI databar (ResolutionY); scale to [0, 1] by the 0.5/99.5 percentiles; fill pores (pixels below
0.8 x the 1st percentile of a 9-px median image, dilated 3 px) with the median image; raw pixel noise sig = robust sigma of the median-3
residual / 0.5; total-variation denoising (Chambolle) with weight TVW x sig (grains are piecewise constant, so TV keeps the edges).
Method I (edges): Canny (Gaussian CS px, thresholds CHI and CHI / 2, absolute contrast units) on the TV image; intercepts = edge runs
crossed by horizontal and vertical test lines every STEP px. Mean intercept = line length / crossings.
Method II (regions): watershed on the Sobel gradient of the TV image, markers from h-minima (h = HMIN); regions < 20 px absorbed by
their nearest neighbour; mean intercept = line length / label changes along the same test lines.
Parameters chosen on synthetic dev images (seed 101) for a size-independent bias, then frozen and validated on fresh synthetic images
(validate_grainsize.py, seed 5) before any real image is measured (rule I7). The real images were used only for their noise level."""
import numpy as np
from scipy import ndimage as ndi
from skimage import feature, filters, morphology, segmentation, restoration
STEP, TVW, CS, CHI, HMIN = 16, 3.0, 1.5, 0.10, 0.01
def prep(a, res_y=None):
    a = np.asarray(a, float)
    if res_y: a = a[:res_y]
    lo, hi = np.percentile(a, [0.5, 99.5]); a = np.clip((a - lo) / max(hi - lo, 1e-9), 0, 1)
    m9 = ndi.median_filter(a, 9); pore = ndi.binary_dilation(a < np.percentile(m9, 1) * 0.8, morphology.disk(3)); a = np.where(pore, m9, a)
    d = a - ndi.median_filter(a, 3); sig = 1.4826 * np.median(np.abs(d - np.median(d))) / 0.5
    return restoration.denoise_tv_chambolle(a, weight=TVW * sig), float(sig), float(pore.mean())
def edge_intercept(img):
    e = feature.canny(img, sigma=CS, low_threshold=0.5 * CHI, high_threshold=CHI); n = 0; L = 0
    for r in range(STEP // 2, e.shape[0], STEP): n += int((np.diff(e[r].astype(np.int8)) == 1).sum()); L += e.shape[1]
    for c in range(STEP // 2, e.shape[1], STEP): n += int((np.diff(e[:, c].astype(np.int8)) == 1).sum()); L += e.shape[0]
    return L / max(n, 1), n
def label_intercept(lab):
    n = 0; L = 0
    for r in range(STEP // 2, lab.shape[0], STEP): n += int((np.diff(lab[r]) != 0).sum()); L += lab.shape[1]
    for c in range(STEP // 2, lab.shape[1], STEP): n += int((np.diff(lab[:, c]) != 0).sum()); L += lab.shape[0]
    return L / max(n, 1), n
def segment(img):
    g = filters.sobel(img); mk, _ = ndi.label(morphology.h_minima(g, HMIN)); lab = segmentation.watershed(g, mk)
    small = np.bincount(lab.ravel())[lab] < 20
    if small.any():
        idx = ndi.distance_transform_edt(small, return_distances=False, return_indices=True); lab = lab[tuple(idx)]
    return lab
def measure(a, res_y=None):
    img, sig, pf = prep(a, res_y); m1, n1 = edge_intercept(img); m2, n2 = label_intercept(segment(img))
    return {'I_px': float(m1), 'n_I': int(n1), 'II_px': float(m2), 'n_II': int(n2), 'noise': sig, 'pore_frac': pf}
