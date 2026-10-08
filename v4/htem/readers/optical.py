"""readers/optical.py: absorption and direct Tauc gap from measured transmission T and reflection R plus thickness (skill M2 derived
observable). Frozen parameters in config.json readers.optical.

alpha = -ln(T / (1 - R)) / d   (single-pass approximation, d in cm). A point is saturated when T < t_min or 1 - R < 1e-3. Ordered by
energy, the reader keeps only the contiguous unsaturated run from the lowest energy up to the first saturated point, so noise-floor
points above the edge never enter the fit.
Tauc (direct): y = (alpha E)^2 against E. y_top is the maximum of y over the unsaturated range. The fit uses the contiguous points below the
y_top index whose y lies in [tauc_lo, tauc_hi] * y_top. Eg = -intercept/slope. Uncertainty: 200 residual bootstrap draws, fixed seed.
censored = True when the edge is not resolved inside the measured range: Eg within edge_margin_ev of the top energy of the spectrum, or
too few points in the window (then Eg is None), or the fit window never reaches alpha_edge_min_cm (default 1e4 cm^-1, the
conventional lower bound of the direct-gap Tauc region), as for a gap above the measured range where only the Urbach tail shows.
"""
import numpy as np

HC = 1239.84198  # eV nm


def _pair(op, t_keys=('uvit', 'nirt'), r_keys=('uvir', 'nirr')):
    """Merge T and R pieces onto the T wavelength grid (R interpolated; only where both exist)."""
    ws, ts, rs = [], [], []
    for tk, rk in zip(t_keys, r_keys):
        if tk in op and rk in op:
            w = op[tk]['wavelength_nm']
            t = op[tk]['response']
            r = np.interp(w, op[rk]['wavelength_nm'], op[rk]['response'], left=np.nan, right=np.nan)
            ok = np.isfinite(r)
            ws.append(w[ok]); ts.append(t[ok]); rs.append(r[ok])
    if not ws:
        return None
    w = np.concatenate(ws); t = np.concatenate(ts); r = np.concatenate(rs)
    o = np.argsort(w)
    w, t, r = w[o], t[o], r[o]
    keep = np.concatenate([[True], np.diff(w) > 0])
    return w[keep], t[keep], r[keep]


def absorption(op, thickness_um, alpha_floor_cm=0.0, t_min=0.02):
    p = _pair(op)
    if p is None or not thickness_um:
        return None
    w, t, r = p
    d_cm = thickness_um * 1e-4
    ok = (t >= t_min) & ((1 - r) > 1e-3)
    with np.errstate(divide='ignore', invalid='ignore'):
        a = -np.log(t / (1 - r)) / d_cm
    ok &= np.isfinite(a)
    E = HC / w
    o = np.argsort(E)
    E, a, ok = E[o], a[o], ok[o]
    bad = np.flatnonzero(~ok)
    run = np.zeros_like(ok)
    run[:bad[0] if bad.size else ok.size] = True
    keep = ok & run
    return {'E': E, 'alpha': np.where(keep, np.maximum(a, alpha_floor_cm), np.nan), 'saturated': ~ok,
            'E_saturation': float(E[bad[0]]) if bad.size else None}


def tauc_direct(E, alpha, cfg, n_boot=200, seed=11, e_top=None):
    e_top = float(np.nanmax(E)) if e_top is None else e_top
    m = np.isfinite(alpha)
    E, a = E[m], alpha[m]
    if E.size < cfg['min_points']:
        return {'Eg': None, 'censored': True, 'reason': 'too few points'}
    y = (a * E) ** 2
    it = int(np.argmax(y))
    ytop = y[it]
    lo, hi = cfg['tauc_lo'] * ytop, cfg['tauc_hi'] * ytop
    j = it
    while j > 0 and y[j - 1] > lo * 0.999:
        j -= 1
    sel = np.arange(j, it + 1)
    sel = sel[(y[sel] >= lo) & (y[sel] <= hi)]
    if sel.size < cfg['min_points']:
        return {'Eg': None, 'censored': True, 'reason': 'edge window too short', 'E_top': float(E[-1])}
    A = np.vstack([E[sel], np.ones(sel.size)]).T
    coef, *_ = np.linalg.lstsq(A, y[sel], rcond=None)
    s, b = coef
    if s <= 0:
        return {'Eg': None, 'censored': True, 'reason': 'non-positive slope'}
    eg = -b / s
    res = y[sel] - A @ coef
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(n_boot):
        yb = A @ coef + rng.choice(res, size=res.size, replace=True)
        cb, *_ = np.linalg.lstsq(A, yb, rcond=None)
        if cb[0] > 0:
            boots.append(-cb[1] / cb[0])
    a_top = float(np.max(a[sel]))
    cens = bool(eg > e_top - cfg['edge_margin_ev'] or a_top < cfg.get('alpha_edge_min_cm', 1e4))
    return {'Eg': float(eg), 'Eg_err': float(np.std(boots)) if boots else None, 'censored': cens, 'n_fit': int(sel.size),
            'E_window': [float(E[sel[0]]), float(E[sel[-1]])], 'E_top': e_top, 'alpha_top_cm': a_top, 'E_last_unsaturated': float(E[-1])}


def edge_model(E, lnA, eg, eu):
    """Direct allowed edge A sqrt(E - Eg) / E above Eg, joined continuously to an Urbach tail below (the synth.py form)."""
    A = np.exp(lnA); above = np.clip(E - eg, 0, None)
    join = A * np.sqrt(eu / 2) / eg
    return np.where(E > eg + eu / 2, A * np.sqrt(above) / E, join * np.exp((E - eg - eu / 2) / eu))


def model_fit(E, alpha, cfg, e_top=None):
    """H4 (second iteration, dev evidence P1): least squares on log(alpha) over the unsaturated range above alpha_fit_floor_cm, free
    A, Eg, Eu. Censored when Eg is within edge_margin_ev of the last unsaturated energy or the fit does not converge."""
    from scipy.optimize import least_squares
    m = np.isfinite(alpha) & (alpha > cfg.get('alpha_fit_floor_cm', 3e3)); E, a = E[m], alpha[m]
    if E.size < cfg['min_points']:
        return {'Eg': None, 'censored': True, 'reason': 'too few points'}
    e_last = float(E.max())
    best = None
    for eg0 in np.linspace(E.min() + 0.1, e_last + 0.3, 12):
        for eu0 in (0.05, 0.2, 0.5):
            p0 = [np.log(max(a.max(), 1e3) * 2), eg0, eu0]
            try:
                r = least_squares(lambda q: np.log(edge_model(E, *q)) - np.log(a), p0, bounds=([5, 0.5, 0.01], [20, 6.0, 1.5]), max_nfev=2000)
            except Exception:
                continue
            if best is None or r.cost < best.cost:
                best = r
    if best is None:
        return {'Eg': None, 'censored': True, 'reason': 'fit failed'}
    lnA, eg, eu = best.x
    cens = bool(eg > e_last - cfg['edge_margin_ev'])
    return {'Eg': float(eg), 'Eu_ev': float(eu), 'A_cm': float(np.exp(lnA)), 'censored': cens, 'E_last_unsaturated': e_last,
            'rms_log': float(np.sqrt(np.mean(best.fun ** 2))), 'n_fit': int(E.size), 'method': 'edge_model'}


def read(op, thickness_um, cfg):
    ab = absorption(op, thickness_um, cfg.get('alpha_floor_cm', 0.0), cfg.get('t_min', 0.02))
    if ab is None:
        return {'Eg': None, 'censored': True, 'reason': 'no T and R pair or no thickness'}
    if cfg.get('method', 'tauc') == 'edge_model':
        return model_fit(ab['E'], ab['alpha'], cfg, e_top=float(np.max(ab['E'])))
    return tauc_direct(ab['E'], ab['alpha'], cfg, e_top=float(np.max(ab['E'])))
