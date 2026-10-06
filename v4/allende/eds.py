#!/usr/bin/env python3
"""eds.py (v4 Track B, skill M2 raw data): element net-count maps from the Bruker EDS spectrum images of the Allende grain.
Per (binned) pixel, non-negative least squares of fixed-shape Gaussian lines plus a linear background over each fit window:
  FWHM(E) = sqrt(0.0504^2 + 0.002434 E) keV (Fano law, FWHM 130 eV at Mn Ka), K-alpha / K-beta and L lines at tabulated energies.
  window LOW 0.85-2.65 keV: Ni La 0.851, Cu La 0.930, Na Ka 1.041, Mg Ka 1.254, Al Ka 1.487, Si Ka 1.740, Si Kb 1.836, S Ka 2.307, S Kb 2.464
  window HIGH 5.2-8.9 keV: Cr Ka 5.415, Fe Ka 6.404, Fe Kb 7.058, Ni Ka 7.478, Cu Ka 8.048, Ni Kb 8.265
Energy axis from the file (offset, scale); a constant energy shift is fitted once on the sum spectrum (grid +-20 eV) and logged (D gap if
the shift exceeds 20 eV). Cu (200-mesh Cu grid) is a system peak: fitted, never a key. No k-factors are in the deposit: net counts and
count ratios only, never compositions (logged D gap).
Validated on synthetic spectra (validate_eds.py) before use on the real maps (rule I7)."""
import numpy as np
from scipy.optimize import nnls
LINES = {'low': {'Ni La': 0.851, 'Cu La': 0.930, 'Na Ka': 1.041, 'Mg Ka': 1.254, 'Al Ka': 1.487, 'Si Ka': 1.740, 'Si Kb': 1.836, 'S Ka': 2.307, 'S Kb': 2.464},
         'high': {'Cr Ka': 5.415, 'Fe Ka': 6.404, 'Fe Kb': 7.058, 'Ni Ka': 7.478, 'Cu Ka': 8.048, 'Ni Kb': 8.265}}
WIN = {'low': (0.85, 2.65), 'high': (5.2, 8.9)}
KB = {'Si Kb': ('Si Ka', 0.03), 'S Kb': ('S Ka', 0.07), 'Fe Kb': ('Fe Ka', 0.13), 'Ni Kb': ('Ni Ka', 0.13)}   # K-beta tied to K-alpha (ratio)

def fwhm(E): return np.sqrt(0.0504 ** 2 + 0.002434 * E)

def design(E, win):
    """columns: one per element line group (K-beta folded into its K-alpha by the tabulated ratio), plus linear background (1, E)."""
    names = [n for n in LINES[win] if n not in KB]; cols = []
    for n in names:
        g = lambda e: np.exp(-0.5 * ((E - e) / (fwhm(e) / 2.355)) ** 2)
        col = g(LINES[win][n])
        for b, (a, r) in KB.items():
            if a == n and b in LINES[win]: col = col + r * g(LINES[win][b])
        cols.append(col)
    return names, np.column_stack(cols + [np.ones_like(E), E - E.mean()])

def fit_spectrum(E, s, win):
    lo, hi = WIN[win]; m = (E >= lo) & (E <= hi); names, X = design(E[m], win)
    # linear background may be negative in slope: split into +/- columns for NNLS
    X2 = np.column_stack([X, -X[:, -1]]); coef, res = nnls(X2, s[m].astype(float))
    area = {n: float(coef[i] * (fwhm(LINES[win][n]) / 2.355) * np.sqrt(2 * np.pi)) for i, n in enumerate(names)}   # net counts (channels = 1 per dE unit handled by caller)
    return area, res

def fit_shift(E, s):
    best = None
    for sh in np.arange(-0.02, 0.0201, 0.002):
        r = sum(fit_spectrum(E + sh, s, w)[1] for w in WIN)
        if best is None or r < best[1]: best = (float(sh), r)
    return best[0]

def maps(a, E, binning=4):
    """a: (H, W, C) counts. Returns {line: (H/b, W/b) net counts per binned pixel (in channel units)}."""
    H, W, C = a.shape; h, w = H // binning, W // binning
    b = a[:h * binning, :w * binning].reshape(h, binning, w, binning, C).sum((1, 3)).astype(float)
    out = {}
    for i in range(h):
        for j in range(w):
            for win in WIN:
                area, _ = fit_spectrum(E, b[i, j], win)
                for n, v in area.items(): out.setdefault(n, np.zeros((h, w)))[i, j] = v
    return out
