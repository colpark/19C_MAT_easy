#!/usr/bin/env python3
"""derived.py (v4 Track B rebuild, skill M2 "derived observables"): procedures our code applies to the raw Allende deposit. Each enters the
v4 law library as a derived-observable procedure with frozen parameters (key kind 'derived', from M raw data). The paper never reports these
numbers; the claims it makes about them become T4 audits (claim ladder, v4/notes/20261006_allende_claim_ladder_stitching.md).
  sigmaps(M, W)      Poisson significance of each EDS net map: z = net / sqrt(window total counts) per 6 x 6 bin.
  regions_v2         replaces the median + MAD thresholds Sol rejected (Q1 default 1): sulfide = z_Ni >= 5 and z_S >= 5; Al pocket = z_Al >= 5
                     and not sulfide; silicate = z_Mg >= 5 and z_Si >= 5 and neither; unassigned otherwise. A region needs >= 8 bins.
  fe_l3_features     Fe L-edge region spectrum: constrained fit of a sloped pre-edge background (thick silicate absorbs more at lower
                     energy, ladder note), an edge step and two Gaussians (L3a, L3b 1.2-2.6 eV above); ratio = L3b / L3a amplitude; offset-free.
  l3_l2_separation   parabolic maxima of the background-subtracted spectrum in the L3 and L2 windows (Fe: L2 in onset + 10..18 eV;
                     Ni: L3 onset..+5, L2 onset + 14..22 eV).
  tilt_ratio         whole-frame Mg Ka / Si Ka net counts per tilt (B1 fit); the silicate holds both lines (Mg absent from sulfide and
                     oxide), so the ratio follows the path length of the softer line, not the field's phase mix.
  before_after       per-line count-rate ratio between the 0 deg acquisitions before (01) and after (21) the tilt series.
Validated on synthetic data (validate_derived.py) before any key."""
import numpy as np

def sigmaps(M, W):
    return {k: M[k] / np.sqrt(np.maximum(W[k], 1.0)) for k in M}

def regions_v2(Z, valid):
    sul = valid & (Z['Ni'] >= 5) & (Z['S'] >= 5); alp = valid & (Z['Al'] >= 5) & ~sul
    sil = valid & (Z['Mg'] >= 5) & (Z['Si'] >= 5) & ~sul & ~alp
    return {'sulfide': sul, 'al_pocket': alp, 'silicate': sil}

def bg_subtract(E, s, e0, lo=-9.0, hi=-2.0):
    m = (E >= e0 + lo) & (E <= e0 + hi)
    if m.sum() < 3: return s - s[:3].mean()
    p = np.polyfit(E[m], s[m], 1); return s - np.polyval(p, E)

def _pmax(E, y, lo, hi):
    m = (E >= lo) & (E <= hi); e, v = E[m], y[m]
    if len(e) < 3: return None, None
    i = int(np.argmax(v))
    if 0 < i < len(v) - 1:
        x0, x1, x2 = e[i - 1:i + 2]; y0, y1, y2 = v[i - 1:i + 2]; den = (x0 - x1) * (x0 - x2) * (x1 - x2)
        A = (x2 * (y1 - y0) + x1 * (y0 - y2) + x0 * (y2 - y1)) / den; B = (x2 ** 2 * (y0 - y1) + x1 ** 2 * (y2 - y0) + x0 ** 2 * (y1 - y2)) / den; C = y1 - A * x1 ** 2 - B * x1
        if A < 0: xm = -B / (2 * A); return float(xm), float(A * xm ** 2 + B * xm + C)
    return float(e[i]), float(v[i])

def fe_l3_features(E, s, e0):
    """synthetic iteration 2: window maxima failed on overlapping peaks (33 % within 15 %). Fit on [onset - 9, onset + 6] eV: linear
    background + arctan-like step (sigmoid at onset, width 0.3 eV) + two Gaussians L3a (center onset + 0..2.5 eV) and L3b (L3a + 1.2..2.6 eV),
    widths 0.3-0.9 eV; ratio = L3b / L3a amplitude."""
    from scipy.optimize import least_squares
    m = (E >= e0 - 9) & (E <= e0 + 6); x, y = E[m], s[m]
    if len(x) < 10: return None
    g = lambda c, w: np.exp(-0.5 * ((x - c) / w) ** 2)
    def model(p):
        b0, b1, st, a1, ca, wa, a2, d, wb = p
        return b0 + b1 * (x - e0) + st / (1 + np.exp(-(x - e0) / 0.3)) + a1 * g(e0 + ca, wa) + a2 * g(e0 + ca + d, wb)
    span = float(y.max() - y.min()) or 1.0
    best = None
    for ca0 in (0.6, 1.2, 1.8):
        for d0 in (1.5, 2.0):
            p0 = [float(y[:3].mean()), 0.0, 0.1 * span, 0.5 * span, ca0, 0.5, 0.5 * span, d0, 0.5]
            lo = [-np.inf, -np.inf, 0, 0, 0.0, 0.3, 0, 1.2, 0.3]; hi = [np.inf, np.inf, 5 * span, 10 * span, 2.5, 0.9, 10 * span, 2.6, 0.9]
            r = least_squares(lambda p: model(p) - y, p0, bounds=(lo, hi))
            if best is None or r.cost < best.cost: best = r
    b0, b1, st, a1, ca, wa, a2, d, wb = best.x
    return {'L3a_eV': float(e0 + ca), 'L3a': float(a1), 'L3b_eV': float(e0 + ca + d), 'L3b': float(a2), 'ratio': float(a2 / a1) if a1 > 0 else None, 'split_eV': float(d)}

def l3_l2_separation(E, s, e0, el):
    y = bg_subtract(E, s, e0)
    if el == 'Fe': (a, b), (c, d) = (0.0, 6.0), (10.0, 18.0)
    else: (a, b), (c, d) = (0.0, 5.0), (14.0, 22.0)
    e3, _ = _pmax(E, y, e0 + a, e0 + b); e2, _ = _pmax(E, y, e0 + c, e0 + d)
    return None if e3 is None or e2 is None else float(e2 - e3)

def tilt_ratio(area): return area['Mg Ka'] / area['Si Ka']

def before_after(a_before, a_after, rt_before, rt_after):
    return {k: (a_after[k] / rt_after) / (a_before[k] / rt_before) for k in a_before if a_before[k] > 0}

def fit_se(E, s, win):
    """B13 (regions_v3, Q1b repair): net line areas and their standard errors from the fit itself. NNLS as in eds.fit_spectrum; the
    covariance is (A^T W A)^-1 over the active line columns plus the quadratic background, with Poisson weights W = 1 / max(model, 1);
    lines NNLS set to zero get z = 0. Returns {line: (area, se)} in the eds.fit_spectrum area units."""
    from scipy.optimize import nnls
    import eds as X
    lo, hi = X.WIN[win]; m = (E >= lo) & (E <= hi); names, D = X.design(E[m], win); y = s[m].astype(float); nl = len(names)
    D2 = np.column_stack([D, -D[:, -2], -D[:, -1]]); coef, _ = nnls(D2, y); model = D2 @ coef; w = 1.0 / np.maximum(model, 1.0)
    act = [i for i in range(nl) if coef[i] > 0]; cols = act + [nl, nl + 1, nl + 2]; A = D[:, cols]
    cov = np.linalg.pinv(A.T @ (A * w[:, None])); out = {}
    for i, n in enumerate(names):
        g = (X.fwhm(X.LINES[win][n]) / 2.355) * np.sqrt(2 * np.pi)
        out[n] = (float(coef[i] * g), float(np.sqrt(max(cov[cols.index(i), cols.index(i)], 0)) * g)) if i in act else (0.0, float('inf'))
    return out

def zmaps_v3(a, E, binning=6, lines=('Ni Ka', 'S Ka', 'Al Ka', 'Mg Ka', 'Si Ka')):
    """per binned pixel: net area and its fit standard error for each line (both windows). Returns ({line: net}, {line: se})."""
    H, W, C = a.shape; h, w = H // binning, W // binning
    b = a[:h * binning, :w * binning].reshape(h, binning, w, binning, C).sum((1, 3)).astype(float)
    net = {n: np.zeros((h, w)) for n in lines}; se = {n: np.full((h, w), np.inf) for n in lines}
    for i in range(h):
        for j in range(w):
            for win in ('low', 'high'):
                for n, (ar, sd) in fit_se(E, b[i, j], win).items():
                    if n in net: net[n][i, j] = ar; se[n][i, j] = sd
    return net, se

def regions_v3(Z, valid):
    """same rule as regions_v2, on z = fitted net / fit standard error (B13)."""
    return regions_v2(Z, valid)
