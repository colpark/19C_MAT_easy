"""synth.py: synthetic HTEM-like measurements with known truth, for reader validation (skill M2: dev seeds tune, fresh seeds gate).
Dev seeds: 0 to 99. Fresh seeds: 1000 and up. Shapes follow the cached real data (801-point XRD over 19 to 52 deg, 800-point optical
spectra over 300 to 1099 nm, 5-point I-V). Replace the defaults with dev statistics measured on the pilot libraries before the freeze.
"""
import json, os
import numpy as np
# H4: generator ranges from the dev library of the active role (config.json synth.<HTEM_ROLE>, written from dev/dev_stats_<role>.json);
# without HTEM_ROLE the kit defaults below apply (kit tests).
_CFG = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')))
P = _CFG.get('synth', {}).get(os.environ.get('HTEM_ROLE', ''), {})
def _r(key, default):
    return tuple(P.get(key, default))

XRD_GRID = np.linspace(19.0, 52.0, 801)
OPT_GRID = np.linspace(300.0, 1099.0, 800)
HC = 1239.84198


def pv(x, x0, fw, h, eta):
    s = fw / 2.3548
    return h * (eta / (1 + ((x - x0) / (fw / 2)) ** 2) + (1 - eta) * np.exp(-0.5 * ((x - x0) / s) ** 2))


def xrd_pattern(seed, n_peaks=None, amorphous=False, broad=False):
    rng = np.random.default_rng(seed)
    x = XRD_GRID
    b0, b1 = _r('xrd_base', (8000, 11000)); base = b0 + (b1 - b0) * rng.random(); cv = rng.uniform(*_r('xrd_curv', (1.3, 1.5))) - 1
    bg = base * (1 + cv * np.exp(-(x - 19) / 12)) + 1500 * rng.random() * np.exp(-0.5 * ((x - 30) / 4) ** 2)
    if amorphous:
        bg += base * 0.5 * np.exp(-0.5 * ((x - 32) / 3.5) ** 2)
    np0, np1 = _r('xrd_npeaks', (2, 5)); n = 0 if amorphous else (n_peaks or int(rng.integers(np0, (np1 + 1) if not broad else 4)))
    sep, fw = (4.0, (0.8, 2.0)) if broad else (1.2, _r('xrd_fwhm', (0.15, 0.6)))
    peaks = []
    for _ in range(n):
        while True:
            c = float(rng.uniform(22.0, 49.0))
            if all(abs(c - p['center']) > sep for p in peaks):
                break
        h0, h1 = _r('xrd_height', (0.4, 6.0))
        peaks.append({'center': c, 'fwhm': float(rng.uniform(*fw)), 'height': float(base * np.exp(rng.uniform(np.log(h0), np.log(h1)))),
                      'eta': float(rng.uniform(0.2, 0.8))})
    y = bg.copy()
    for p in peaks:
        y += pv(x, p['center'], p['fwhm'], p['height'], p['eta'])
    nm = rng.uniform(*_r('xrd_noise_ratio', (1.0, 1.0)))   # super-Poisson noise (area-detector integration): ratio of SD to sqrt(counts)
    y = np.clip(y, 0, None); y = y + rng.normal(0, 1, y.size) * np.sqrt(y) * nm
    return x, y, peaks


def optical_spectra(seed, eg=None, thickness_um=None, fringes=True):
    """Direct-gap film: alpha(E) = A sqrt(E - Eg) / E above the gap plus an Urbach tail below. Incoherent film on a substrate with
    constant R0 and optional thickness fringes. Returns wavelength grid, T, R, truth."""
    rng = np.random.default_rng(seed)
    eg = float(eg if eg is not None else rng.uniform(*_r('opt_eg', (1.6, 3.6))))
    d_um = float(thickness_um if thickness_um is not None else rng.uniform(*_r('opt_thick_um', (0.15, 0.6))))
    w = OPT_GRID
    E = HC / w
    A = np.exp(rng.uniform(*np.log(_r('opt_A', (1.5e5, 6e5)))))
    eu = rng.uniform(*_r('opt_Eu', (0.03, 0.08)))
    above = np.clip(E - eg, 0, None)
    a_edge = A * np.sqrt(above) / E
    a_tail = A * np.sqrt(eu / 2) / eg * np.exp((E - eg) / eu)
    alpha = np.where(E > eg, np.maximum(a_edge, A * np.sqrt(eu / 2) / eg), a_tail)
    n_f = 2.0 + 0.1 * rng.random()
    R = np.full_like(w, rng.uniform(*_r('opt_R', (((n_f - 1) / (n_f + 1)) ** 2, ((n_f - 1) / (n_f + 1)) ** 2 + 0.02))))
    if fringes:
        R = R + 0.05 * np.cos(4 * np.pi * n_f * d_um * 1e3 / w) * np.exp(-alpha * d_um * 1e-4)
    R = np.clip(R, 0.01, 0.6)
    ad = alpha * d_um * 1e-4
    T = (1 - R) ** 2 * np.exp(-ad) / (1 - R ** 2 * np.exp(-2 * ad))
    tn, rn = P.get('opt_T_noise', 0.002), P.get('opt_R_noise', 0.002)
    T = np.clip(T + rng.normal(0, tn, T.size), 0, 1)
    R = np.clip(R + rng.normal(0, rn, R.size), 0, 1)
    op = {'uvit': {'wavelength_nm': w, 'response': T}, 'uvir': {'wavelength_nm': w, 'response': R}}
    return op, {'Eg': eg, 'thickness_um': d_um}


def iv_points(seed, rs=None, gf=4.532):
    rng = np.random.default_rng(seed)
    r0, r1 = _r('fpm_Rs', (10, 1e6)); rs = float(rs if rs is not None else 10 ** rng.uniform(np.log10(r0), np.log10(r1)))
    i = np.linspace(-1e-4, 1e-4, 5); rel = rng.uniform(*_r('fpm_rel_noise', (0.002 / 2, 0.002 / 2)))
    v = (rs / gf) * i + rng.normal(0, abs(rs / gf) * 2e-4 * rel, i.size)
    return {'current_A': i, 'voltage_V': v}, {'Rs': rs}
