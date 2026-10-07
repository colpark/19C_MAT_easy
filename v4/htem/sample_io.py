"""sample_io.py: parse cached HTEM library and sample records into plain arrays and dicts. Tolerates both API layouts seen so far:
flat optical fields (opt_uvit_wavelength, opt_uvit_response, ...) and the older nested layout (oo -> uvit -> wavelength, response).

Levels (skill M1, defaults for this database, recorded as "default"):
  D  deposition_* fields, substrate, position, xyz_mm
  M  xrd_angle/xrd_intensity/xrd_background, optical responses, xrf composition, thickness, fpm voltages and currents
  A  opt_direct_bandgap, opt_absorption_coefficient, opt_average_vis_trans, fpm_sheet_resistance, fpm_resistivity, fpm_conductivity,
     peak_count, opt_normalized_transmittance (the database's own processing; validation evidence only, never keys)
"""
import math, re
import numpy as np

A_LEVEL_FIELDS = ('opt_direct_bandgap', 'opt_absorption_coefficient', 'opt_average_vis_trans', 'fpm_sheet_resistance',
                  'fpm_resistivity', 'fpm_conductivity', 'peak_count', 'opt_normalized_transmittance')
ANIONS = ('O', 'N', 'S', 'Se', 'Te', 'F', 'Cl', 'H', 'C', 'P')
OPT_KEYS = ('uvit', 'uvir', 'nirt', 'nirr')


def _arr(v):
    """1-D float array; JSON nulls inside a list become NaN (callers drop non-finite points pairwise)."""
    if v is None or not isinstance(v, (list, tuple, np.ndarray)):
        return None
    try:
        a = np.array([np.nan if x is None else x for x in v], dtype=float)
    except (TypeError, ValueError):
        return None
    return a if a.ndim == 1 and a.size else None


def xrd(s, min_points=50):
    tt, y, bg = _arr(s.get('xrd_angle')), _arr(s.get('xrd_intensity')), _arr(s.get('xrd_background'))
    if tt is None or y is None or tt.size != y.size:
        return None
    if bg is not None and bg.size != y.size:
        bg = None
    ok = np.isfinite(tt) & np.isfinite(y)
    if ok.sum() < min_points:
        return None
    tt, y = tt[ok], y[ok]
    bg = None if bg is None else bg[ok]
    o = np.argsort(tt)
    return {'two_theta': tt[o], 'intensity': y[o], 'background': None if bg is None else bg[o], 'dropped': int((~ok).sum())}


def _raw_optical(s, k):
    w, r = _arr(s.get(f'opt_{k}_wavelength')), _arr(s.get(f'opt_{k}_response'))
    if (w is None or r is None) and isinstance(s.get('oo'), dict) and isinstance(s['oo'].get(k), dict):
        w, r = _arr(s['oo'][k].get('wavelength')), _arr(s['oo'][k].get('response'))
    if w is None or r is None or w.size != r.size:
        return None
    ok = np.isfinite(w) & np.isfinite(r)
    if ok.sum() < 10:
        return None
    o = np.argsort(w[ok])
    return w[ok][o], r[ok][o]


def optical(s):
    """T and R spectra as fractions. Non-finite points are dropped (missing, not saturated). Percent against fraction is decided jointly
    per T/R pair (uvit with uvir, nirt with nirr) from the 95th percentile, so a lone spike or an opaque film cannot flip the scale."""
    raw = {k: _raw_optical(s, k) for k in OPT_KEYS}
    out = {}
    for pair in (('uvit', 'uvir'), ('nirt', 'nirr')):
        have = [raw[k] for k in pair if raw[k] is not None]
        if not have:
            continue
        q = max(float(np.percentile(r, 95)) for _, r in have)
        scale = 0.01 if q > 1.5 else 1.0
        for k in pair:
            if raw[k] is not None:
                out[k] = {'wavelength_nm': raw[k][0], 'response': raw[k][1] * scale, 'scale': scale}
    return out


def _cations_of(formula):
    return [e for e in dict.fromkeys(re.findall(r'[A-Z][a-z]?', str(formula))) if e not in ANIONS]


def composition(s, cations_only=True):
    """Cation fractions from XRF. VH-E03: on real records xrf_concentration aligns with xrf_compounds (oxides, nitrides, bare elements,
    anions measured as elements, repeated entries), not with xrf_elements (which also lists the anion). Rule: if the concentrations align
    with the compounds, each compound credits its single cation (repeats summed, anion-only entries skipped); a compound with two or more
    cations makes the record ambiguous (None). Otherwise the element-aligned layout; otherwise None."""
    el, conc, cp = s.get('xrf_elements'), s.get('xrf_concentration'), s.get('xrf_compounds')
    if isinstance(conc, dict):
        pairs = list(conc.items())
    elif isinstance(cp, list) and isinstance(conc, list) and len(cp) == len(conc) and cp:
        pairs = []
        for f, c in zip(cp, conc):
            cats = _cations_of(f)
            if len(cats) > 1:
                return None
            if cats:
                pairs.append((cats[0], c))
            elif not cations_only:
                pairs.append((str(f), c))
    elif isinstance(el, list) and isinstance(conc, list) and len(el) == len(conc):
        pairs = list(zip(el, conc))
    else:
        return None
    vals = {}
    for e, c in pairs:
        try:
            c = float(c)
        except (TypeError, ValueError):
            continue
        if math.isfinite(c) and (not cations_only or e not in ANIONS):
            vals[str(e)] = vals.get(str(e), 0.0) + max(c, 0.0)
    tot = sum(vals.values())
    return {e: v / tot for e, v in vals.items()} if tot > 0 else None


def fpm(s):
    v, i = _arr(s.get('fpm_voltage_volts')), _arr(s.get('fpm_current_amps'))
    if v is None or i is None or v.size != i.size or v.size < 2:
        return None
    return {'voltage_V': v, 'current_A': i}


def xyz(s):
    v = _arr(s.get('xyz_mm'))
    return None if v is None or v.size < 2 or not np.all(np.isfinite(v[:2])) else [float(v[0]), float(v[1])]


def thickness_um(s):
    t = s.get('thickness')
    try:
        t = float(t)
    except (TypeError, ValueError):
        return None
    return t if math.isfinite(t) and t > 0 else None


def a_level(s):
    return {k: s.get(k) for k in A_LEVEL_FIELDS if s.get(k) is not None}


def summary(s):
    """Which modalities a sample actually carries (not the library has_* counters)."""
    op = optical(s)
    return {'xrd': xrd(s) is not None, 'xrf': composition(s) is not None, 'thickness': thickness_um(s) is not None,
            'opt_T': any(k in op for k in ('uvit', 'nirt')), 'opt_R': any(k in op for k in ('uvir', 'nirr')),
            'fpm': fpm(s) is not None}


def system_key(elements):
    return '-'.join(sorted({str(e) for e in (elements or [])}))


def anion_class(elements):
    es = set(elements or [])
    for a in ('O', 'N', 'S', 'Se', 'Te'):
        if a in es:
            return a
    return 'metal'
