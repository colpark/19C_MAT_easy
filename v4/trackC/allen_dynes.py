#!/usr/bin/env python3
"""Eliashberg moments and Tc from alpha^2F(omega) (JARVIS second route, card CARD_jarvis laws).

  lambda   = 2 int alpha2F(w) / w dw
  omega_log = exp[(2 / lambda) int ln(w) alpha2F(w) / w dw]
  omega_2  = sqrt[(2 / lambda) int w alpha2F(w) dw]
  McMillan-Allen-Dynes: Tc = omega_log / 1.2 exp[-1.04 (1 + lambda) / (lambda - mu* (1 + 0.62 lambda))]
  full Allen-Dynes adds f1 f2 (strong-coupling and shape factors).
Frequencies: the caller passes the unit of w; omega_log is returned in that unit and Tc in K via the
unit factor (meV -> K: 11.604518; cm^-1 -> K: 1.438777; THz -> K: 47.99243).
Only positive frequencies enter (imaginary modes are reported, not integrated).
"""
import numpy as np

TO_K = {'meV': 11.604518, 'cm-1': 1.438777, 'THz': 47.99243, 'K': 1.0}


def _trapz(y, x):
    return float(np.trapezoid(y, x)) if hasattr(np, 'trapezoid') else float(np.trapz(y, x))


def moments(w, a2f):
    w = np.asarray(w, float)
    a2f = np.asarray(a2f, float)
    m = w > 1e-8
    w, a = w[m], a2f[m]
    lam = 2.0 * _trapz(a / w, w)
    if lam <= 0:
        return {'lambda': lam, 'omega_log': float('nan'), 'omega_2': float('nan')}
    wlog = np.exp(2.0 / lam * _trapz(np.log(w) * a / w, w))
    w2 = np.sqrt(2.0 / lam * _trapz(w * a, w))
    return {'lambda': float(lam), 'omega_log': float(wlog), 'omega_2': float(w2)}


def tc_mcmillan_ad(lam, wlog_K, mustar):
    den = lam - mustar * (1 + 0.62 * lam)
    if den <= 0:
        return 0.0
    return float(wlog_K / 1.2 * np.exp(-1.04 * (1 + lam) / den))


def tc_allen_dynes_full(lam, wlog_K, w2_K, mustar):
    L1 = 2.46 * (1 + 3.8 * mustar)
    L2 = 1.82 * (1 + 6.3 * mustar) * (w2_K / wlog_K)
    f1 = (1 + (lam / L1) ** 1.5) ** (1 / 3)
    f2 = 1 + (w2_K / wlog_K - 1) * lam ** 2 / (lam ** 2 + L2 ** 2)
    return f1 * f2 * tc_mcmillan_ad(lam, wlog_K, mustar)


def from_a2f(w, a2f, unit, mustar, full=False):
    m = moments(w, a2f)
    k = TO_K[unit]
    wlog_K = m['omega_log'] * k
    w2_K = m['omega_2'] * k
    tc = (tc_allen_dynes_full(m['lambda'], wlog_K, w2_K, mustar) if full
          else tc_mcmillan_ad(m['lambda'], wlog_K, mustar))
    return {**m, 'omega_log_K': wlog_K, 'omega_2_K': w2_K, 'Tc_K': tc, 'mustar': mustar, 'full': full,
            'n_negative_w': int(np.sum(np.asarray(w) < 0))}
