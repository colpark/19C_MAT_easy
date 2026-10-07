#!/usr/bin/env python3
"""yieldproc.py (v4 Track D, skill M2 derived observable): 0.2 % offset yield stress from a raw force / crosshead-displacement curve.
Crosshead strain includes machine compliance and a seating toe, so the elastic line is the steepest secant: a least-squares line over
every window of W = 25 consecutive points on the loading branch (up to the stress maximum; D1c); the window of maximum slope gives E' and
its strain intercept e0. Yield = first point where stress < E' (e - e0 - 0.002) after the elastic window (linear interpolation). With an
apparent modulus E' below the material E, 0.2 % of crosshead strain is a larger plastic strain than 0.2 % of specimen strain: the value is a
procedure-defined yield (ranked and fitted across conditions, never compared with the authors' numbers as equal quantities).
Validated on synthetic curves in the real compliance regime (validate_yield2.py, D1c) before use on real files (rule I7)."""
import numpy as np
W = 25
def stress_strain(F, d, D, L):
    A = np.pi * (D / 2) ** 2; return F / A, d / L      # MPa (N / mm^2), crosshead engineering strain
def yield_02(s, e):
    """D1c: the elastic window search runs over the whole loading branch (up to the stress maximum, so unloading segments are excluded);
    D1 capped it at 0.9 x the stress at 5 % strain, which cut off the elastic line of compliant rigs (yield beyond 5 % crosshead strain)."""
    s = np.asarray(s, float); e = np.asarray(e, float); top = int(np.argmax(s)); sl = []
    for i in range(0, top - W):
        x = e[i:i + W]; y = s[i:i + W]
        sl.append(np.polyfit(x, y, 1)[0] if np.ptp(x) > 0 else -np.inf)
    if not sl: return None
    sl = np.array(sl); i0 = int(np.argmax(sl)); a = i0; b = i0
    while a > 0 and sl[a - 1] >= 0.95 * sl[i0]: a -= 1          # D1c: refit over the contiguous windows within 5 % of the steepest
    while b < len(sl) - 1 and sl[b + 1] >= 0.95 * sl[i0]: b += 1  # (the maximum of noisy window slopes is biased high)
    m, c = np.polyfit(e[a:b + W], s[a:b + W], 1); e0 = -c / m; g = s - m * (e - e0 - 0.002)
    for j in range(b + W, top - W + 1):
        if g[j] < 0 and g[j - 1] >= 0 and g[j:j + W].max() < 0:   # D1c: the crossing must persist for W points (noise on gradual curves)
            t = g[j - 1] / (g[j - 1] - g[j]); return {'ys': float(s[j - 1] + t * (s[j] - s[j - 1])), 'E_app': float(m), 'e0': float(e0)}
    return None
