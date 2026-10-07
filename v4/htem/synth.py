"""synth.py: synthetic HTEM-like measurements with known truth, for reader validation (skill M2: dev seeds tune, fresh seeds gate).
Dev seeds: 0 to 99. Fresh seeds: 1000 and up. Shapes follow the cached real data (801-point XRD over 19 to 52 deg, 800-point optical
spectra over 300 to 1099 nm, 5-point I-V). Replace the defaults with dev statistics measured on the pilot libraries before the freeze.
"""
import numpy as np

XRD_GRID = np.linspace(19.0, 52.0, 801)
OPT_GRID = np.linspace(300.0, 1099.0, 800)
HC = 1239.84198


def pv(x, x0, fw, h, eta):
    s = fw / 2.3548
    return h * (eta / (1 + ((x - x0) / (fw / 2)) ** 2) + (1 - eta) * np.exp(-0.5 * ((x - x0) / s) ** 2))


def xrd_pattern(seed, n_peaks=None, amorphous=False, broad=False):
    rng = np.random.default_rng(seed)
    x = XRD_GRID
    base = 8000 + 3000 * rng.random()
    bg = base * (1 + 0.4 * np.exp(-(x - 19) / 12)) + 1500 * rng.random() * np.exp(-0.5 * ((x - 30) / 4) ** 2)
    if amorphous:
        bg += base * 0.5 * np.exp(-0.5 * ((x - 32) / 3.5) ** 2)
    n = 0 if amorphous else (n_peaks or int(rng.integers(2, 6 if not broad else 4)))
    sep, fw = (4.0, (0.8, 2.0)) if broad else (1.2, (0.15, 0.6))
    peaks = []
    for _ in range(n):
        while True:
            c = float(rng.uniform(22.0, 49.0))
            if all(abs(c - p['center']) > sep for p in peaks):
                break
        peaks.append({'center': c, 'fwhm': float(rng.uniform(*fw)), 'height': float(base * rng.uniform(0.4, 6.0)),
                      'eta': float(rng.uniform(0.2, 0.8))})
    y = bg.copy()
    for p in peaks:
        y += pv(x, p['center'], p['fwhm'], p['height'], p['eta'])
    y = rng.poisson(np.clip(y, 0, None)).astype(float)
    return x, y, peaks


def optical_spectra(seed, eg=None, thickness_um=None, fringes=True):
    """Direct-gap film: alpha(E) = A sqrt(E - Eg) / E above the gap plus an Urbach tail below. Incoherent film on a substrate with
    constant R0 and optional thickness fringes. Returns wavelength grid, T, R, truth."""
    rng = np.random.default_rng(seed)
    eg = float(eg if eg is not None else rng.uniform(1.6, 3.6))
    d_um = float(thickness_um if thickness_um is not None else rng.uniform(0.15, 0.6))
    w = OPT_GRID
    E = HC / w
    A = rng.uniform(1.5e5, 6e5)
    eu = rng.uniform(0.03, 0.08)
    above = np.clip(E - eg, 0, None)
    a_edge = A * np.sqrt(above) / E
    a_tail = A * np.sqrt(eu / 2) / eg * np.exp((E - eg) / eu)
    alpha = np.where(E > eg, np.maximum(a_edge, A * np.sqrt(eu / 2) / eg), a_tail)
    n_f = 2.0 + 0.1 * rng.random()
    R = np.full_like(w, ((n_f - 1) / (n_f + 1)) ** 2) + 0.02 * rng.random()
    if fringes:
        R = R + 0.05 * np.cos(4 * np.pi * n_f * d_um * 1e3 / w) * np.exp(-alpha * d_um * 1e-4)
    R = np.clip(R, 0.01, 0.6)
    ad = alpha * d_um * 1e-4
    T = (1 - R) ** 2 * np.exp(-ad) / (1 - R ** 2 * np.exp(-2 * ad))
    T = np.clip(T + rng.normal(0, 0.002, T.size), 0, 1)
    R = np.clip(R + rng.normal(0, 0.002, R.size), 0, 1)
    op = {'uvit': {'wavelength_nm': w, 'response': T}, 'uvir': {'wavelength_nm': w, 'response': R}}
    return op, {'Eg': eg, 'thickness_um': d_um}


def iv_points(seed, rs=None, gf=4.532):
    rng = np.random.default_rng(seed)
    rs = float(rs if rs is not None else 10 ** rng.uniform(1, 6))
    i = np.linspace(-1e-4, 1e-4, 5)
    v = (rs / gf) * i + rng.normal(0, abs(rs / gf) * 1e-4 * 0.002, i.size)
    return {'current_A': i, 'voltage_V': v}, {'Rs': rs}
