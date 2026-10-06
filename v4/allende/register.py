#!/usr/bin/env python3
"""register.py (v4 Track B): rigid registration (rotation + translation, scale fixed by metadata) of an image onto a reference of a
different pixel size. Both are resampled to the reference grid; rotation searched over -180..180 deg (2 deg, then 0.2 deg around the
best), translation by phase cross-correlation on Hann-apodized, zero-mean images; score = normalised cross-correlation at the best shift.
Used on thickness-like images: STXM mean OD (all energies) and the EDS total-count map (all channels), which both follow projected mass.
Validated on synthetic transforms (validate_register.py) before real use; a registration is accepted only when its score exceeds the
second-best rotation basin by >= 0.05 (unambiguous) and >= 0.5 absolute."""
import numpy as np
from scipy import ndimage as ndi
from skimage.registration import phase_cross_correlation
from skimage.transform import rescale, rotate

def prep(a):
    a = a.astype(float); a = (a - a.mean()) / (a.std() + 1e-9); return a

def resample(img, px_img, px_ref):
    return rescale(img, px_img / px_ref, anti_aliasing=True, preserve_range=True)

def place(img, shape):
    out = np.zeros(shape); h, w = min(shape[0], img.shape[0]), min(shape[1], img.shape[1])
    oy, ox = (shape[0] - h) // 2, (shape[1] - w) // 2; iy, ix = (img.shape[0] - h) // 2, (img.shape[1] - w) // 2
    out[oy:oy + h, ox:ox + w] = img[iy:iy + h, ix:ix + w]; return out

def score(ref, mov):
    win = np.outer(np.hanning(ref.shape[0]), np.hanning(ref.shape[1]))
    sh, _, _ = phase_cross_correlation(ref * win, mov * win, upsample_factor=4)
    m2 = ndi.shift(mov, sh, order=1); valid = ndi.shift(np.ones_like(mov), sh, order=0) > 0.5
    a, b = ref[valid], m2[valid]; ncc = float(np.corrcoef(a, b)[0, 1]) if valid.sum() > 50 else -1.0
    return ncc, sh

def register(ref, px_ref, mov, px_mov):
    """returns dict(angle, shift (rows, cols) in reference pixels, ncc, margin) mapping mov onto ref."""
    R = prep(ref); M = prep(place(resample(mov, px_mov, px_ref), ref.shape))
    coarse = []
    for ang in np.arange(-180, 180, 2.0):
        n, sh = score(R, prep(rotate(M, ang, preserve_range=True))); coarse.append((n, ang, sh))
    coarse.sort(key=lambda x: -x[0]); best = coarse[0]
    second = next((c for c in coarse if min(abs(c[1] - best[1]), 360 - abs(c[1] - best[1])) > 10), (-1, None, None))
    fine = max(((score(R, prep(rotate(M, a, preserve_range=True)))[0], a) for a in np.arange(best[1] - 2, best[1] + 2.01, 0.2)))
    n, sh = score(R, prep(rotate(M, fine[1], preserve_range=True)))
    return {'angle': float(fine[1]), 'shift': [float(x) for x in sh], 'ncc': n, 'second_basin_ncc': float(second[0]), 'margin': float(n - second[0]),
            'accept': bool(n >= 0.5 and n - second[0] >= 0.05)}

def apply(mov, px_mov, px_ref, shape, reg):
    M = place(resample(mov, px_mov, px_ref), shape); M = rotate(M, reg['angle'], preserve_range=True); return ndi.shift(M, reg['shift'], order=1)
