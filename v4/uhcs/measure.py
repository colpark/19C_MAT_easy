#!/usr/bin/env python3
"""measure.py (v4 Track C, skill M2 micrographs): two independent particle-size measurements on UHCS SEM micrographs.
  crop_image   drop the bottom data bar (it prints the sample label and the scale bar): the image ends at the first row of the bottom block of
               rows whose dark fraction (< 30) exceeds 0.6.
  method S     segmentation: background flattened (subtract a Gaussian of sigma 25 px), global Otsu threshold, holes filled, objects smaller
               than AMIN_PX dropped, border-touching objects dropped; per particle equivalent-circle diameter (ECD).
               Statistic: number-mean ECD of particles with ECD >= DMIN_PX pixels, in um.
  method I     linear intercept on an independently binarized image (Li global threshold on the flattened image; method S uses Otsu):
               horizontal test lines every 6 px; particle chords that do not touch the image edge, >= DMIN_PX; d_I = (4/pi) x mean chord, in
               um, which estimates the size-weighted mean section diameter sum(D^2)/sum(D) (random lines hit particles in proportion to D).
               Method I (synthetic iteration 2): Sauvola thresholding followed matrix texture (66 % ordering); the 1.5 sphere factor was the
               3D rule while the truth is the section diameter.
Both methods use the database scale (um per px) only where the scale check agrees (scale_check.json). Parameters are frozen with this file;
they were set on synthetic images (synth_validate.py) before any real micrograph was measured for keys."""
import numpy as np
from scipy import ndimage as ndi
from skimage import filters, measure, morphology
AMIN_PX = 12; DMIN_PX = 4.0; SIGMA_BG = 25; LINE_STEP = 6; SAUV_W = 51; SAUV_K = 0.2

def crop_image(a):
    """rows above the data bar: scanning up from the bottom, the bar ends where three consecutive rows have dark fraction (< 30) below 0.3."""
    dark = (a < 30).mean(1); r = a.shape[0]; i = r - 1
    while i >= 2 and not (dark[i] < 0.3 and dark[i - 1] < 0.3 and dark[i - 2] < 0.3): i -= 1
    return a[:i + 1]

def flatten(a):
    a = a.astype(float); return a - ndi.gaussian_filter(a, SIGMA_BG)

def method_s(a, um_per_px):
    f = flatten(a); t = filters.threshold_otsu(f); m = f > t
    m = ndi.binary_fill_holes(m); m = morphology.remove_small_objects(m, max_size=AMIN_PX - 1)
    lab = measure.label(m); props = measure.regionprops(lab)
    H, W = m.shape; d = []
    for p in props:
        r0, c0, r1, c1 = p.bbox
        if r0 == 0 or c0 == 0 or r1 == H or c1 == W: continue
        e = p.equivalent_diameter_area
        if e >= DMIN_PX: d.append(e)
    d = np.array(d)
    return {'n': int(len(d)), 'mean_um': float(d.mean() * um_per_px) if len(d) else None, 'median_um': float(np.median(d) * um_per_px) if len(d) else None,
            'area_fraction': float(m.mean())}

def method_i(a, um_per_px):
    f = flatten(a); t = filters.threshold_li(f); m = f > t
    m = morphology.remove_small_objects(m, max_size=AMIN_PX - 1); ch = []
    for r in range(0, m.shape[0], LINE_STEP):
        row = m[r]; i = 0
        while i < len(row):
            if row[i]:
                j = i
                while j + 1 < len(row) and row[j + 1]: j += 1
                if i > 0 and j < len(row) - 1 and (j - i + 1) >= DMIN_PX: ch.append(j - i + 1)
                i = j + 1
            else: i += 1
    ch = np.array(ch)
    return {'n_chords': int(len(ch)), 'mean_chord_um': float(ch.mean() * um_per_px) if len(ch) else None,
            'd_um': float(4 / np.pi * ch.mean() * um_per_px) if len(ch) else None}   # section diameters: E[chord | hit] = (pi/4) D -> estimates sum(D^2)/sum(D)
