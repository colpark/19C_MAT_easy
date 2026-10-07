#!/usr/bin/env python3
"""alsi_reader.py (Track S pilot S1b, reader S4d, modality SE): mean solidification-cell equivalent diameter on the 5000x ETD fields of
AlSi10Mg (Zenodo 10008435). Steps: crop the FEI databar (Image/ResolutionY), grey = channel mean, resample to PX_NM (every field to one
pixel size: magnification follows the image type), percentile stretch, flatten the background (subtract a Gaussian of BG_UM),
Gaussian SIG_PX, walls = pixels above the local mean + K_WALL x local SD (window WIN_UM) (the Si network is bright), cells = connected
non-wall regions bounded by the skeleton of the wall mask (SKEL), specks below MIN_UM2 removed; cells touching the border are excluded; observable = number-mean equivalent
diameter (um) of the remaining cells. Parameters tuned on synthetic dev seeds only (real fields supply only the noise level);
the dev-estimated bias B0 is frozen with the reader. No model is used; data files are read only."""
import numpy as np
from scipy import ndimage as ndi
PX_NM, BG_UM, SIG_PX, K_WALL, WIN_UM, MIN_UM2, B0, SKEL = 53.9583, 3.0, 0.7, 0.3, 5.0, 0.02, 0.908, True   # tuned on synthetic dev seeds 100-115; B0 = dev median reader/truth
def load_field(path):
    import tifffile
    with tifffile.TiffFile(path) as t: m = t.fei_metadata or {}; a = t.pages[0].asarray()
    ry = int(m.get('Image', {}).get('ResolutionY') or a.shape[0]); px = float(m.get('Scan', {}).get('PixelWidth')) * 1e9
    g = a[:ry].astype(float); g = g.mean(-1) if g.ndim == 3 else g; return g, px
def resample(g, px):
    return g if abs(px - PX_NM) < 1e-3 else ndi.zoom(g, px / PX_NM, order=1)
def cells(g):
    px_um = PX_NM / 1000; lo, hi = np.percentile(g, [0.5, 99.5]); a = np.clip((g - lo) / max(hi - lo, 1e-9), 0, 1)
    a = a - ndi.gaussian_filter(a, BG_UM / px_um); a = ndi.gaussian_filter(a, SIG_PX)
    w = max(3, int(round(WIN_UM / px_um))); mu = ndi.uniform_filter(a, w); sd = np.sqrt(np.maximum(ndi.uniform_filter(a * a, w) - mu * mu, 1e-12))
    wall = a > mu + K_WALL * sd
    if SKEL:   # cells bounded by wall centrelines (wall width does not shrink the cells; cells partition the plane as Voronoi truth does)
        from skimage.morphology import skeletonize, remove_small_objects
        wall = remove_small_objects(wall, max_size=max(2, int(MIN_UM2 / px_um ** 2 / 4)))
        wall = ndi.binary_dilation(skeletonize(wall))
    lab, n = ndi.label(~wall)
    if n == 0: return np.array([]), lab
    area = np.bincount(lab.ravel())[1:] * px_um ** 2
    edge = np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]]); keep = np.ones(n, bool); keep[edge[edge > 0] - 1] = False
    keep &= area >= MIN_UM2; d = 2 * np.sqrt(area[keep] / np.pi); return d, lab
def measure(path_or_array, px=None):
    g, p = (load_field(path_or_array) if isinstance(path_or_array, str) else (path_or_array, px))
    d, _ = cells(resample(g, p)); return {'d_mean_um': float(d.mean()) / B0 if len(d) else float('nan'), 'n_cells': int(len(d)), 'd_raw_mean_um': float(d.mean()) if len(d) else float('nan')}
