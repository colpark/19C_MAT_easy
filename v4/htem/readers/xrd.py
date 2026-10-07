"""readers/xrd.py: XRD pattern reader (skill M2 derived observable). Frozen parameters live in config.json readers.xrd.

Steps: our own SNIP background (half width snip_halfwidth_deg, wider than the broadest keyable peak) (the database background column is A level and stays out), robust noise from the MAD of first differences,
peak finding on the smoothed residual at min_snr * noise prominence, then a pseudo-Voigt plus linear baseline fit in a window of
max(window_deg/2, 2.5 x the estimated half-height width) around each peak, FWHM bounded by max_fwhm_deg. A fit that ends at the width
bound is an amorphous hump or background residue: it goes to 'humps', never to 'peaks'. Limit: Bragg peaks with FWHM >= about 0.95 x
max_fwhm_deg (crystallites below about 3 nm at Cu K-alpha) are reported as humps and never keyed. Record this with the freeze. Outputs center (deg 2theta), FWHM (deg), height, area and 1-sigma errors from the fit covariance.

d-spacings need the wavelength, a D record from the descriptor desk check. d_spacing() refuses while it is missing.
"""
import math
import numpy as np
from scipy.optimize import curve_fit
from scipy.signal import find_peaks, peak_widths


def snip(y, iters=40):
    v = np.log(np.log(np.sqrt(np.clip(y, 0, None) + 1) + 1) + 1)
    n = v.size
    for k in range(1, iters + 1):
        a = v.copy()
        lo, hi = k, n - k
        if hi <= lo:
            break
        a[lo:hi] = np.minimum(v[lo:hi], 0.5 * (v[lo - k:hi - k] + v[lo + k:hi + k]))
        v = a
    return (np.exp(np.exp(v) - 1) - 1) ** 2 - 1


def smooth(y, k):
    if k <= 1:
        return y.copy()
    w = np.ones(k) / k
    return np.convolve(np.pad(y, (k // 2, k - 1 - k // 2), mode='edge'), w, mode='valid')


def pvoigt(x, x0, fwhm, h, eta, b0, b1):
    s = fwhm / 2.3548
    g = np.exp(-0.5 * ((x - x0) / s) ** 2)
    l = 1.0 / (1.0 + ((x - x0) / (fwhm / 2)) ** 2)
    return h * (eta * l + (1 - eta) * g) + b0 + b1 * (x - x0)


def noise_sigma(r):
    d = np.diff(r)
    return 1.4826 * np.median(np.abs(d - np.median(d))) / math.sqrt(2) if d.size else 0.0


def read(two_theta, intensity, cfg):
    x = np.asarray(two_theta, float)
    y = np.asarray(intensity, float)
    step = float(np.median(np.diff(x)))
    bg = snip(smooth(y, cfg['smooth_pts']), iters=max(10, int(round(cfg.get('snip_halfwidth_deg', 2.5) / step))))
    r = y - bg
    sig = noise_sigma(r)
    rs = smooth(r, cfg['smooth_pts'])
    if sig <= 0:
        return {'peaks': [], 'noise': 0.0, 'step_deg': step}
    idx, _ = find_peaks(rs, prominence=cfg['min_snr'] * sig, distance=max(1, int(round(0.15 / step))))
    widths = peak_widths(rs, idx, rel_height=0.5)[0] * step if idx.size else []
    fw_max = cfg.get('max_fwhm_deg', 3.0)
    peaks, humps = [], []
    for k_, (i, w0) in enumerate(zip(idx, widths)):
        half = max(cfg['window_deg'] / 2, 2.5 * min(w0, fw_max))
        m = (x > x[i] - half) & (x < x[i] + half)
        if m.sum() < 8:
            continue
        xs, ys = x[m], r[m]
        # H4 (dev evidence, P1): every other detected candidate inside the window is fitted jointly (one pseudo-Voigt each, shared linear
        # baseline), so a weak peak next to a strong one is not pulled onto it and then lost in the dedup step.
        nb = [j for j in range(len(idx)) if j != k_ and abs(x[idx[j]] - x[i]) < half]
        comps = [(i, w0)] + [(idx[j], widths[j]) for j in nb]
        p0, lb, ub = [0.0, 0.0], [-np.inf, -np.inf], [np.inf, np.inf]
        for ii, ww in comps:
            p0 += [x[ii], float(np.clip(ww, 2.5 * step, fw_max * 0.99)), max(rs[ii], sig), 0.5]
            lb += [x[ii] - half, 2 * step, 0, 0]; ub += [x[ii] + half, fw_max, np.inf, 1]
        def model(xx, *q):
            out = q[0] + q[1] * (xx - xx.mean())
            for c in range(len(comps)):
                out = out + pvoigt(xx, q[2 + 4 * c], q[3 + 4 * c], q[4 + 4 * c], q[5 + 4 * c], 0.0, 0.0)
            return out
        try:
            q, covq = curve_fit(model, xs, ys, p0=p0, bounds=(lb, ub), maxfev=8000)
        except (RuntimeError, ValueError):
            continue
        p = np.array([q[2], q[3], q[4], q[5], q[0], q[1]])
        errq = np.sqrt(np.clip(np.diag(covq), 0, None)) if np.all(np.isfinite(covq)) else np.full(len(q), np.nan)
        err = np.array([errq[2], errq[3], errq[4], errq[5], errq[0], errq[1]])
        x0, fw, h, eta = p[:4]
        if not (xs[0] < x0 < xs[-1]) or h < cfg['min_snr'] * sig:
            continue
        if fw >= 0.95 * fw_max:  # at the width bound: an amorphous hump or background residue, not a Bragg peak
            humps.append({'center': float(x0), 'fwhm_at_bound': float(fw), 'height': float(h)})
            continue
        area = h * fw * (eta * math.pi / 2 + (1 - eta) * math.sqrt(math.pi / (4 * math.log(2))))
        peaks.append({'center': float(x0), 'center_err': float(err[0]), 'fwhm': float(fw), 'fwhm_err': float(err[1]),
                      'height': float(h), 'eta': float(eta), 'area': float(area), 'snr': float(h / sig)})
    peaks.sort(key=lambda p: p['center'])
    dedup = []
    for p in peaks:
        if dedup and abs(p['center'] - dedup[-1]['center']) < 0.5 * min(p['fwhm'], dedup[-1]['fwhm']):
            if p['height'] > dedup[-1]['height']:
                dedup[-1] = p
            continue
        dedup.append(p)
    return {'peaks': dedup, 'humps': humps, 'noise': float(sig), 'step_deg': step}


def d_spacing(two_theta_deg, wavelength_A):
    if not wavelength_A:
        raise ValueError('wavelength is a D record: set readers.xrd.wavelength_A from the descriptor desk check first')
    return wavelength_A / (2 * math.sin(math.radians(two_theta_deg) / 2))


def match_phase(peaks, sticks, tol_deg=0.3, top=5):
    """Fraction of the reference's strongest sticks (by intensity) found among the measured peaks within tol, intensity weighted.
    sticks: list of (two_theta, intensity). Returns score in [0, 1] and the matched pairs."""
    ref = sorted(sticks, key=lambda s: -s[1])[:top]
    if not ref:
        return 0.0, []
    wsum, hit, pairs = 0.0, 0.0, []
    centers = np.array([p['center'] for p in peaks]) if peaks else np.array([])
    for tt, inten in ref:
        wsum += inten
        if centers.size:
            j = int(np.argmin(np.abs(centers - tt)))
            if abs(centers[j] - tt) <= tol_deg:
                hit += inten
                pairs.append((tt, float(centers[j])))
    return hit / wsum, pairs
