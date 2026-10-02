"""TEM chain: lattice spacings from the FFT of a real-space crop, ring or spot radii of a diffraction pattern."""
import numpy as np
from skimage import feature
from common import cand


def fft_spacings(gray, valid, scale, panel, n=5):
    if not scale or scale.get('recip'):
        return []
    upp, unit = 1.0 / scale['px_per_unit'], scale['unit']
    ys, xs = np.nonzero(valid)
    if len(ys) == 0:
        return []
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    side = min(y1 - y0, x1 - x0)
    if side < 32:
        return []
    cy, cx = (y0 + y1) // 2, (x0 + x1) // 2
    sub = gray[cy - side // 2: cy + side // 2, cx - side // 2: cx + side // 2].astype(float)
    sub = (sub - sub.mean()) * np.outer(np.hanning(sub.shape[0]), np.hanning(sub.shape[1]))
    N = 1 << int(np.ceil(np.log2(2 * sub.shape[0])))   # zero padding for finer radial resolution
    F = np.log1p(np.abs(np.fft.fftshift(np.fft.fft2(sub, s=(N, N)))))
    c = np.array(F.shape) // 2
    yy, xx = np.indices(F.shape)
    r = np.hypot(yy - c[0], xx - c[1])
    F[r < 3 * N / sub.shape[0]] = 0
    pk = feature.peak_local_max(F, min_distance=4, num_peaks=4 * n, exclude_border=False)
    out, seen = [], []
    for (py, px) in pk:
        rad = np.hypot(py - c[0], px - c[1])
        if rad < 3 * N / sub.shape[0]:
            continue
        d_px = F.shape[0] / rad
        if any(abs(d_px - s) / s < 0.03 for s in seen):
            continue
        seen.append(d_px)
        out.append(cand(d_px * upp, unit, 'tem', f'FFT lattice spacing (rank {len(seen)})', 1.0 / len(seen), panel))
        if len(seen) >= n:
            break
    return out


def saed_rings(gray, valid, scale, panel, n=6):
    """Radial profile around the brightest blob; with a reciprocal scale bar radii become d-spacings."""
    g = np.where(valid, gray.astype(float), 0)
    from scipy import ndimage as ndi
    cy, cx = np.unravel_index(np.argmax(ndi.gaussian_filter(g, 3)), g.shape)
    yy, xx = np.indices(g.shape)
    r = np.hypot(yy - cy, xx - cx).astype(int)
    prof = np.bincount(r.ravel(), g.ravel()) / np.maximum(np.bincount(r.ravel()), 1)
    if len(prof) < 20:
        return []
    pk = feature.peak_local_max(prof[5:], min_distance=3, num_peaks=n, exclude_border=False).ravel() + 5
    out = []
    for k, rad in enumerate(sorted(pk), 1):
        if scale and scale.get('recip'):
            q = rad / scale['px_per_unit']  # in 1/unit
            unit = scale['unit'].replace('1/', '')
            if q > 0:
                out.append(cand(1.0 / q, unit, 'tem', f'SAED ring {k} d-spacing', 0.6, panel))
        elif scale:
            # real-space scale bar on a diffraction panel is unusual: report radius only as a length-free candidate is useless
            continue
    return out
