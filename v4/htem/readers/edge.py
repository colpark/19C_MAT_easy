"""readers/edge.py (round 2, HR1; rules in HTEM_ROUND2_RULES.md sections 1.1-1.4): E04, the Urbach energy E_U and the edge width from the
contiguous unsaturated absorption run of readers/optical.absorption(). Readers S4ho2 (E04) and S4hu (E_U); edge width is a selection
statistic only.

E04: lowest energy where alpha first reaches 1e4 cm^-1 (upward scan), confirmed by the next point (or the run ending at saturation),
interpolated linearly in log10 alpha. Censored: never reached in the run, within 0.1 eV of E_saturation, or fewer than 6 run points.
E_U: 1 / slope of ln(alpha d) vs E over run points with 1e3 <= alpha <= 1e4 cm^-1; >= 5 points, slope > 0, R^2 >= 0.95.
Bounded-input rule (thickness is level A): every value is recomputed with d x 0.75 and d x 1.25; the result carries the shifts.
Edge width: span over which ln(alpha d) rises from 10 % to 90 % of its range along the run (first upward crossings).
"""
import numpy as np
from readers import optical as RO

A04 = 1e4; A03 = 1e3; SAT_MARGIN = 0.1; MIN_RUN = 6; THICK_SCALES = (0.75, 1.25)


def _run(ab):
    m = np.isfinite(ab['alpha'])
    return ab['E'][m], ab['alpha'][m]


def absorption_incoherent(op, thickness_um, t_min=0.01):
    """Exact inversion of the incoherent film model T = (1-R)^2 x / (1 - R^2 x^2), x = exp(-alpha d), with the same pairing, saturation
    and contiguous-run rule as optical.absorption(). The single-pass form -ln(T/(1-R))/d has an apparent floor ln(1+R)/d (about 1e4
    cm^-1 for 0.1 um films), which sits on the E04 threshold (VH-E11)."""
    p = RO._pair(op)
    if p is None or not thickness_um:
        return None
    w, t, r = p
    d_cm = thickness_um * 1e-4
    ok = (t >= t_min) & ((1 - r) > 1e-3)
    with np.errstate(divide='ignore', invalid='ignore'):
        q = (1 - r) ** 2
        x = np.where(r > 1e-6, (-q + np.sqrt(q ** 2 + 4 * t ** 2 * r ** 2)) / (2 * t * r ** 2), t / np.maximum(q, 1e-12))
        a = -np.log(x) / d_cm
    ok &= np.isfinite(a) & (x > 0)
    E = RO.HC / w
    o = np.argsort(E)
    E, a, ok = E[o], a[o], ok[o]
    bad = np.flatnonzero(~ok)
    run = np.zeros_like(ok)
    run[:bad[0] if bad.size else ok.size] = True
    keep = ok & run
    return {'E': E, 'alpha': np.where(keep, a, np.nan), 'saturated': ~ok, 'E_saturation': float(E[bad[0]]) if bad.size else None}


def absorb(op, d_um, cfg):
    if cfg.get('edge_inversion', 'incoherent') == 'incoherent':
        return absorption_incoherent(op, d_um, cfg.get('t_min', 0.01))
    return RO.absorption(op, d_um, cfg.get('alpha_floor_cm', 0.0), cfg.get('t_min', 0.01))


def e04_from(ab):
    E, a = _run(ab)
    if E.size < MIN_RUN:
        return {'E04': None, 'censored': True, 'why': 'run < 6 points'}
    la = np.log10(np.maximum(a, 1e-30)); t = np.log10(A04); esat = ab.get('E_saturation')
    for i in range(1, E.size):
        if la[i] >= t and la[i - 1] < t and (i + 1 >= E.size or la[i + 1] >= t):
            e = float(E[i - 1] + (t - la[i - 1]) * (E[i] - E[i - 1]) / (la[i] - la[i - 1]))
            if esat is not None and esat - e < SAT_MARGIN:
                return {'E04': e, 'censored': True, 'why': 'within 0.1 eV of saturation'}
            return {'E04': e, 'censored': False, 'why': None}
    if la[0] >= t:
        return {'E04': None, 'censored': True, 'why': 'alpha >= 1e4 at the run start'}
    return {'E04': None, 'censored': True, 'why': 'alpha never reaches 1e4 in the run'}


def eu_from(ab, d_um):
    E, a = _run(ab)
    m = (a >= A03) & (a <= A04)
    if m.sum() < 5:
        return {'E_U': None, 'E_U_why': 'window < 5 points'}
    x, y = E[m], np.log(a[m] * d_um * 1e-4)
    s, c = np.polyfit(x, y, 1); r2 = 1 - np.sum((y - (s * x + c)) ** 2) / max(np.sum((y - y.mean()) ** 2), 1e-30)
    if s <= 0 or r2 < 0.95:
        return {'E_U': None, 'E_U_why': f'slope {s:.3g} r2 {r2:.3f}'}
    return {'E_U': float(1 / s), 'r2': float(r2), 'n': int(m.sum()), 'E_U_why': None}


def edge_width(ab, d_um):
    E, a = _run(ab)
    if E.size < MIN_RUN:
        return None
    a = np.where(a > 0, a, np.nan)
    y = np.log(a * d_um * 1e-4)
    if not np.isfinite(y).any():
        return None
    lo, hi = np.nanmin(y), np.nanmax(y)
    if not np.isfinite(hi - lo) or hi <= lo:
        return None
    def first_up(f):
        t = lo + f * (hi - lo); k = np.flatnonzero(np.nan_to_num(y, nan=-np.inf) >= t)
        return None if not k.size else float(E[k[0]])
    e1, e9 = first_up(0.1), first_up(0.9)
    return None if e1 is None or e9 is None else e9 - e1


def read(op, d_um, cfg):
    """Full record for one sample: E04 and E_U at d and at d x 0.75, d x 1.25; edge width at d. None without T, R or thickness."""
    if not op or not d_um:
        return None
    out = {}
    for k, sc in (('nom', 1.0), ('lo', THICK_SCALES[0]), ('hi', THICK_SCALES[1])):
        ab = absorb(op, d_um * sc, cfg)
        if ab is None:
            return None
        out[k] = {**e04_from(ab), **eu_from(ab, d_um * sc)}
        if k == 'nom':
            out['edge_width'] = edge_width(ab, d_um); E, _ = _run(ab)
            out['run_E'] = [float(E.min()), float(E.max())] if E.size else None
    n = out['nom']
    sh = [abs(out[k]['E04'] - n['E04']) if (n['E04'] is not None and out[k]['E04'] is not None and not out[k]['censored']) else None for k in ('lo', 'hi')]
    out['E04'] = n['E04'] if not n['censored'] else None; out['E04_censored'] = n['censored']; out['E04_why'] = n['why']
    out['E04_dthick'] = None if out['E04'] is None or None in sh else max(sh)
    su = [abs(out[k]['E_U'] - n['E_U']) / n['E_U'] if (out[k]['E_U'] and n['E_U']) else None for k in ('lo', 'hi')]
    out['E_U'] = n['E_U']; out['E_U_dthick_rel'] = None if n['E_U'] is None or None in su else max(su)
    return out
