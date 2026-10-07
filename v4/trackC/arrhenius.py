#!/usr/bin/env python3
"""Arrhenius fit (card L3, L4): ln D = ln D0 - Ea / (k_B T); two free parameters (PanelBench M4 T7: <= 2).

fit(T, D, D_se) -> Ea (eV), ln D0, bootstrap spread over the per-temperature D uncertainties (log-normal
resampling with sigma_ln = D_se / D), and predict(T*) with a bootstrap band.
"""
import numpy as np

KB_EV = 8.617333262e-5  # eV/K (CODATA 2018)


def _lin(T, D, w=None):
    """Least squares of ln D on 1/T; w = 1 / var(ln D) per point (revision R3: inverse-variance weights)."""
    x = 1.0 / np.asarray(T, float)
    y = np.log(np.asarray(D, float))
    sw = np.ones_like(x) if w is None else np.sqrt(np.asarray(w, float))
    A = np.vstack([x, np.ones_like(x)]).T * sw[:, None]
    (m, c), *_ = np.linalg.lstsq(A, y * sw, rcond=None)
    return -m * KB_EV, c


def fit(T, D, D_se=None, n_boot=2000, seed=11):
    T = np.asarray(T, float)
    D = np.asarray(D, float)
    if np.any(D <= 0):
        raise ValueError('non-positive D')
    w = None
    if D_se is not None:
        s_ln = np.clip(np.asarray(D_se, float) / D, 1e-3, 5.0)
        w = 1.0 / s_ln ** 2
    Ea, lnD0 = _lin(T, D, w)
    out = {'Ea_eV': float(Ea), 'lnD0': float(lnD0), 'T': T.tolist(), 'D': D.tolist(), 'n_boot': n_boot}
    if D_se is not None:
        s = np.clip(np.asarray(D_se, float) / D, 1e-6, 5.0)
        rng = np.random.default_rng(seed)
        bs = np.array([_lin(T, D * np.exp(rng.normal(0, s)), w) for _ in range(n_boot)])
        out['Ea_boot'] = bs[:, 0]
        out['lnD0_boot'] = bs[:, 1]
        out['Ea_sd'] = float(np.std(bs[:, 0], ddof=1))
    return out


def predict(f, Tstar):
    """Return D(T*) point estimate and, when bootstrapped, its 16-84 % band (cm^2/s)."""
    Tstar = float(Tstar)
    D = float(np.exp(f['lnD0'] - f['Ea_eV'] / (KB_EV * Tstar)))
    r = {'T': Tstar, 'D': D}
    if 'Ea_boot' in f:
        d = np.exp(f['lnD0_boot'] - f['Ea_boot'] / (KB_EV * Tstar))
        r['D_lo'], r['D_hi'] = (float(x) for x in np.percentile(d, [16, 84]))
        r['log10_sd'] = float(np.std(np.log10(d), ddof=1))
    return r
