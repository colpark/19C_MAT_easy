"""readers/fpm.py: sheet resistance from the raw four-point-probe I-V points (skill M2 derived observable).
Rs = geometry_factor * dV/dI from a least-squares line (intercept allowed). resistivity = Rs * thickness (ohm cm when thickness in um is
converted to cm). The geometry factor is a D record (config readers.fpm.geometry_factor, pi/ln2 by default for an infinite thin sheet
with collinear probes); confirm it from the descriptor. linear_r2 flags non-ohmic or noisy contacts. A negative slope (probe leads
swapped) returns |slope| with polarity 'reversed', so the value stays positive and the flag stays visible.
"""
import numpy as np


def read(fp, thickness_um, cfg):
    if fp is None:
        return {'Rs_ohm_sq': None}
    i, v = np.asarray(fp['current_A'], float), np.asarray(fp['voltage_V'], float)
    ok = np.isfinite(i) & np.isfinite(v)
    i, v = i[ok], v[ok]
    if i.size < 2 or np.ptp(i) == 0:
        return {'Rs_ohm_sq': None, 'reason': 'degenerate I'}
    A = np.vstack([i, np.ones(i.size)]).T
    (slope, icpt), *_ = np.linalg.lstsq(A, v, rcond=None)
    pred = A @ np.array([slope, icpt])
    ss = float(np.sum((v - v.mean()) ** 2))
    r2 = 1 - float(np.sum((v - pred) ** 2)) / ss if ss > 0 else 0.0
    if slope == 0:
        return {'Rs_ohm_sq': None, 'reason': 'zero slope'}
    rs = cfg['geometry_factor'] * abs(slope)
    out = {'Rs_ohm_sq': float(rs), 'linear_r2': float(r2), 'n_points': int(i.size), 'polarity': 'normal' if slope > 0 else 'reversed'}
    if thickness_um:
        out['resistivity_ohm_cm'] = float(rs * thickness_um * 1e-4)
    return out
