#!/usr/bin/env python3
"""yieldproc.py (v4 Track D, skill M2 derived observable): 0.2 % offset yield stress from a raw force / crosshead-displacement curve.
Crosshead strain includes machine compliance and a seating toe, so the elastic line is the steepest secant: a least-squares line over
every window of W = 25 consecutive points with stress below 0.9 x the stress at 5 % strain; the window of maximum slope gives E' and its
strain intercept e0. Yield = first point where stress < E' (e - e0 - 0.002) after the elastic window (linear interpolation). With an
apparent modulus E' below the material E, 0.2 % of crosshead strain is a larger plastic strain than 0.2 % of specimen strain: the value is a
procedure-defined yield (ranked and fitted across conditions, never compared with the authors' numbers as equal quantities).
Validated on synthetic curves (validate_yield.py) before use on real files (rule I7)."""
import numpy as np
W = 25
def stress_strain(F, d, D, L):
    A = np.pi * (D / 2) ** 2; return F / A, d / L      # MPa (N / mm^2), crosshead engineering strain
def yield_02(s, e):
    s = np.asarray(s, float); e = np.asarray(e, float); k5 = np.searchsorted(e, 0.05) if e.max() > 0.05 else len(e) - 1
    cap = 0.9 * s[k5]; best = None
    for i in range(0, k5 - W):
        if s[i + W - 1] > cap: break
        x = e[i:i + W]; y = s[i:i + W]
        if np.ptp(x) <= 0: continue
        m, c = np.polyfit(x, y, 1)
        if best is None or m > best[0]: best = (m, c, i)
    if best is None: return None
    m, c, i0 = best; e0 = -c / m; g = s - m * (e - e0 - 0.002)
    for j in range(i0 + W, len(s)):
        if g[j] < 0 and g[j - 1] >= 0:
            t = g[j - 1] / (g[j - 1] - g[j]); return {'ys': float(s[j - 1] + t * (s[j] - s[j - 1])), 'E_app': float(m), 'e0': float(e0)}
    return None
