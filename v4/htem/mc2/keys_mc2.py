"""keys_mc2.py (v4.5 MC v2; HTEM_MC2_RULES.md sections 1-2): per-library keys, naive procedures and cheap rules of task types L1-L8,
as pure functions on position records built by census_mc2.positions(). Each key function returns a dict with 'decided', 'key',
'naive', 'critical', 'effect' and the per-type extras; None when the library is not eligible. Frozen at MV1."""
import hashlib, math
import numpy as np

GF = math.pi / math.log(2)
B_THK = math.log10(1.25 / 0.75)   # worst-case ratio of two thicknesses each bounded to +/-25 %
LAM = 1.5418
A_ZS, A_ZT = 5.6676, 6.089        # cached COD ZnSe / ZnTe zinc blende (MC5)
DT_REP = 0.069                    # H4 replicate 2theta scatter (deg)


def h(s):
    return int(hashlib.sha256(str(s).encode()).hexdigest(), 16)


# ---------------- common ----------------
def comp_var(P, cation=None):
    """Composition variable x (rules 1): the cation with the largest range over the positions; None for single-cation libraries."""
    comps = [p['comp'] for p in P if p['comp']]
    if not comps: return None, None
    if cation is not None:   # VM-E04: a given (pooled) cation applies even where this library alone has one cation
        return cation, [p['comp'].get(cation, 0.0) if p['comp'] else None for p in P]
    cats = sorted({e for c in comps for e in c})
    if len(cats) < 2: return None, None
    if cation is None:
        cation = max(cats, key=lambda e: (max(c.get(e, 0) for c in comps) - min(c.get(e, 0) for c in comps), -cats.index(e)))
    return cation, [p['comp'].get(cation, 0.0) if p['comp'] else None for p in P]


def comp_step(P, x):
    d = []
    for i, p in enumerate(P):
        if x[i] is None or not p['xy']: continue
        nn = [(math.dist(p['xy'], q['xy']), j) for j, q in enumerate(P) if j != i and q['xy'] and x[j] is not None]
        if nn: d.append(abs(x[i] - x[min(nn)[1]]))
    return float(np.median(d)) if d else None


def neighbour_ok(pick, keyset, x, s):
    """True when the naive pick is outside the key set but within one composition step of a key-set position (not critical)."""
    if x is None or s is None or x[pick] is None: return False
    return any(x[k] is not None and abs(x[pick] - x[k]) <= s for k in keyset)


def minset_decided(n_valid, keyset):
    return n_valid >= 10 and 1 <= len(keyset) <= max(1, n_valid // 4)


def centre_pick(P, idx):
    xy = [P[i]['xy'] for i in idx if P[i]['xy']]
    if not xy: return None
    c = np.mean(xy, axis=0)
    return min((i for i in idx if P[i]['xy']), key=lambda i: math.dist(P[i]['xy'], c))


def _rs(p):
    f = p['iv']
    return (GF * f['R'], GF * f['R_err']) if f and f.get('valid') else (None, None)


def _rs_app(p):
    f = p['iv']
    return GF * abs(f['R']) if f and f.get('R') not in (None, 0) else None


# ---------------- L1 best conductor ----------------
def l1(P):
    x_cat, x = comp_var(P); s = comp_step(P, x) if x else None
    val = [i for i, p in enumerate(P) if _rs(p)[0] and p['d']]
    app = [i for i, p in enumerate(P) if _rs_app(p)]
    if len(app) < 10: return None
    lo = {i: max(_rs(P[i])[0] - 2 * _rs(P[i])[1], 0) * 0.75 * P[i]['d'] for i in val}
    hi = {i: (_rs(P[i])[0] + 2 * _rs(P[i])[1]) * 1.25 * P[i]['d'] for i in val}
    keyset = sorted(i for i in val if lo[i] <= min(hi.values())) if val else []
    dec = minset_decided(len(val), keyset)
    naive = min(app, key=lambda i: _rs_app(P[i]))
    crit = dec and naive not in keyset and not neighbour_ok(naive, keyset, x, s)
    rho_min = min(hi.values()) if val else None
    rho_n = _rs_app(P[naive]) * P[naive]['d'] if P[naive]['d'] else None   # naive pick's apparent rho (central)
    cheap = {'naive Rs argmin': naive}
    dd = [i for i in app if P[i]['d']]
    if dd: cheap['thickest'] = max(dd, key=lambda i: P[i]['d']); cheap['thinnest'] = min(dd, key=lambda i: P[i]['d'])
    if x:
        xx = [i for i in app if x[i] is not None]
        if xx: cheap['lowest x'] = min(xx, key=lambda i: x[i]); cheap['highest x'] = max(xx, key=lambda i: x[i])
    cheap['panel centre'] = centre_pick(P, app)
    sc = lambda k: k is not None and (k in keyset or neighbour_ok(k, keyset, x, s))
    return {'decided': dec, 'key': keyset, 'naive': naive, 'critical': bool(crit), 'n_valid': len(val), 'x_cat': x_cat, 'step': s,
            'key_x': [x[i] for i in keyset] if x else None,
            'effect': (rho_n / min(_rs(P[i])[0] * P[i]['d'] for i in keyset)) if (crit and rho_n and keyset) else None,
            'cheap': {k: sc(v) for k, v in cheap.items()}, 'oracle': sc(keyset[0]) if keyset else False,
            'naive_invalid': naive not in val}


# ---------------- L3 most transparent at E ----------------
def _at(p, E):
    if not p.get('opt'): return None
    e, t, r = p['opt']
    if E - 0.05 < e[0] or E + 0.05 > e[-1]: return None
    g = np.linspace(E - 0.05, E + 0.05, 5)
    return float(np.mean(np.interp(g, e, t))), float(np.mean(np.interp(g, e, r))), float(np.nanmax(t))


def l3(P, E, sig_A):
    x_cat, x = comp_var(P); s = comp_step(P, x) if x else None
    vals = {i: _at(p, E) for i, p in enumerate(P)}; cov = [i for i, v in vals.items() if v]
    if len(cov) < 10: return None
    val = [i for i in cov if vals[i][2] <= 1.05]
    A = {i: 1 - vals[i][0] - vals[i][1] for i in val}
    keyset = sorted(i for i in val if A[i] <= min(A.values()) + 2 * sig_A) if val else []
    dec = minset_decided(len(val), keyset)
    naive = max(cov, key=lambda i: vals[i][0])
    crit = dec and naive not in keyset and not neighbour_ok(naive, keyset, x, s)
    cheap = {'naive T argmax': naive, 'R argmin': min(cov, key=lambda i: vals[i][1])}
    dd = [i for i in cov if P[i]['d']]
    if dd: cheap['thinnest'] = min(dd, key=lambda i: P[i]['d'])
    if x:
        xx = [i for i in cov if x[i] is not None]
        if xx: cheap['lowest x'] = min(xx, key=lambda i: x[i]); cheap['highest x'] = max(xx, key=lambda i: x[i])
    cheap['panel centre'] = centre_pick(P, cov)
    sc = lambda k: k is not None and (k in keyset or neighbour_ok(k, keyset, x, s))
    an = (1 - vals[naive][0] - vals[naive][1]) if naive in vals and vals[naive] else None
    return {'decided': dec, 'key': keyset, 'naive': naive, 'critical': bool(crit), 'n_valid': len(val), 'x_cat': x_cat, 'step': s,
            'key_x': [x[i] for i in keyset] if x else None, 'effect': (an - min(A.values())) if crit and an is not None else None,
            'cheap': {k: sc(v) for k, v in cheap.items()}, 'oracle': sc(keyset[0]) if keyset else False,
            'naive_impossible': naive not in val}


# ---------------- L2 resistivity trend ----------------
def l2(P, sig_logrs):
    x_cat, x = comp_var(P)
    if not x: return None
    val = [i for i, p in enumerate(P) if _rs(p)[0] and p['d'] and x[i] is not None]
    if len(val) < 10: return None
    xv = np.array([x[i] for i in val]); rng = float(np.ptp(xv))
    if rng < 0.10: return None
    y = np.array([math.log10(_rs(P[i])[0] * P[i]['d']) for i in val])
    si = np.array([_rs(P[i])[1] / (_rs(P[i])[0] * math.log(10)) for i in val]); w = 1 / (si ** 2 + sig_logrs ** 2)
    X = np.vstack([xv, np.ones_like(xv)]).T; W = np.diag(w)
    cov = np.linalg.inv(X.T @ W @ X); b = cov @ X.T @ W @ y; res = y - X @ b
    chi = float(res @ W @ res) / max(len(val) - 2, 1); se = math.sqrt(cov[0, 0] * max(chi, 1.0))
    tol = 2 * se + B_THK / rng
    app = [i for i, p in enumerate(P) if _rs_app(p) and x[i] is not None]
    bn = float(np.polyfit([x[i] for i in app], [math.log10(_rs_app(P[i])) for i in app], 1)[0])
    bd = float(np.polyfit(xv, [math.log10(P[i]['d']) for i in val], 1)[0])
    key = float(b[0]); ok = lambda v: abs(v - key) <= tol
    return {'decided': True, 'key': key, 'tol': tol, 'se': se, 'naive': bn, 'critical': not ok(bn), 'n_valid': len(val), 'x_cat': x_cat,
            'x_range': rng, 'effect': bn - key if not ok(bn) else None,
            'cheap': {'naive slope': ok(bn), 'zero': ok(0.0), 'minus thickness slope': ok(-bd)}, 'oracle': True}


# ---------------- L4 lattice constant at x0 ----------------
def two_theta(a, hkl=(1, 1, 1)):
    d = a / math.sqrt(sum(i * i for i in hkl)); return 2 * math.degrees(math.asin(LAM / (2 * d)))


def l4(P, lid, peaks_of):
    xs, As = [], []
    for i, p in enumerate(P):
        if not p['an'] or not ('Se' in p['an'] or 'Te' in p['an']): continue
        xse = p['an'].get('Se', 0.0); pk = peaks_of(i)
        if not pk: continue
        tv = two_theta(xse * A_ZS + (1 - xse) * A_ZT); c = min(pk, key=lambda q: abs(q['center'] - tv))
        if abs(c['center'] - tv) > 1.0: continue
        d = LAM / (2 * math.sin(math.radians(c['center']) / 2)); xs.append(xse); As.append(math.sqrt(3) * d)
    if len(xs) < 10: return None
    xs, As = np.array(xs), np.array(As); s = None
    xP = [p['an'].get('Se', 0.0) if p['an'] else None for p in P]; s = comp_step(P, xP) or 0.02
    grid = [g for g in (0.2, 0.35, 0.5, 0.65, 0.8) if xs.min() + s <= g <= xs.max() - s]
    grid = sorted(grid, key=lambda g: h(f'mv2-x0|{lid}|{g}'))[:2]
    if not grid: return None
    X = np.vstack([xs, np.ones_like(xs)]).T; b, res, *_ = np.linalg.lstsq(X, As, rcond=None); r = As - X @ b
    s2 = float(r @ r) / max(len(xs) - 2, 1); cov = s2 * np.linalg.inv(X.T @ X); out = []
    for x0 in grid:
        key = float(b[0] * x0 + b[1]); se = math.sqrt(float(np.array([x0, 1]) @ cov @ np.array([x0, 1])))
        tt = two_theta(key); da = key * abs(1 / math.tan(math.radians(tt / 2))) * math.radians(DT_REP / 2)
        tol = math.hypot(2 * se, da); nv = x0 * A_ZS + (1 - x0) * A_ZT
        out.append({'x0': x0, 'decided': True, 'key': key, 'tol': tol, 'naive': nv, 'critical': abs(nv - key) > tol, 'n_valid': len(xs),
                    'effect': abs(nv - key), 'cheap': {'Vegard': abs(nv - key) <= tol}, 'oracle': True})
    return out


# ---------------- L5 temperature at matched composition ----------------
def l5(Ph, Pc, cation):
    _, xh = comp_var(Ph, cation) if cation else (None, None); _, xc = comp_var(Pc, cation) if cation else (None, None)
    vh = [i for i, p in enumerate(Ph) if _rs(p)[0] and p['d']]; vc = [i for i, p in enumerate(Pc) if _rs(p)[0] and p['d']]
    if len(vh) < 10 or len(vc) < 10: return None
    rho = lambda P, i: _rs(P[i])[0] * P[i]['d']
    if cation and (xh is None or xc is None): return None   # VM-E04: a library without XRF composition cannot be matched
    if cation:
        s = max(comp_step(Ph, xh) or 0, comp_step(Pc, xc) or 0)
        cand = sorted((abs(xh[i] - xc[j]), i, j) for i in vh if xh[i] is not None for j in vc if xc[j] is not None)
        uh, uc, pairs = set(), set(), []
        for d, i, j in cand:
            if d > s: break
            if i in uh or j in uc: continue
            uh.add(i); uc.add(j); pairs.append((i, j))
        if len(pairs) < 5: return None
        lr = np.array([math.log10(rho(Ph, i) / rho(Pc, j)) for i, j in pairs])
        L = float(np.median(lr)); se = 1.2533 * float(np.std(lr, ddof=1)) / math.sqrt(len(lr)); npair = len(pairs)
    else:
        a = np.array([math.log10(rho(Ph, i)) for i in vh]); b = np.array([math.log10(rho(Pc, j)) for j in vc])
        L = float(np.median(a) - np.median(b)); se = 1.2533 * math.hypot(np.std(a, ddof=1) / math.sqrt(a.size), np.std(b, ddof=1) / math.sqrt(b.size)); npair = None
    thr = B_THK + 2 * se
    key = 'lower' if L < -thr else 'higher' if L > thr else 'no decided difference'
    ah = [_rs_app(p) for p in Ph if _rs_app(p)]; ac = [_rs_app(p) for p in Pc if _rs_app(p)]
    Ln = math.log10(np.median(ah) / np.median(ac))
    naive = 'lower' if Ln < -B_THK else 'higher' if Ln > B_THK else 'no decided difference'
    return {'decided': True, 'key': key, 'L': L, 'se': se, 'naive': naive, 'Ln': Ln, 'critical': naive != key, 'n_pairs': npair,
            'effect': L - Ln if naive != key else None,
            'cheap': {'naive verdict': naive == key, 'always lower': key == 'lower', 'always no decided difference': key == 'no decided difference'},
            'oracle': True}


# ---------------- L6 single-phase range ----------------
def l6(P, peaks_of, sticks, match_phase):
    x_cat, x = comp_var(P)
    if not x: return None
    phases = list(sticks); per = []
    for i, p in enumerate(P):
        pk = peaks_of(i)
        if x[i] is None or pk is None: continue
        sc = {ph: match_phase(pk, sticks[ph], tol_deg=0.3, top=5) for ph in phases}; per.append((i, pk, sc))
    if len(per) < 10: return None
    main = max(phases, key=lambda ph: float(np.median([sc[ph][0] for _, _, sc in per])))
    mtt = [t for t, _ in sticks[main]]; flag = {}
    for i, pk, sc in per:
        top = max((q['height'] for q in pk), default=0); f = False
        for ph in phases:
            if ph == main or sc[ph][0] < 0.5: continue
            for st, meas in sc[ph][1]:
                q = min(pk, key=lambda q: abs(q['center'] - meas))
                if min(abs(meas - t) for t in mtt) > 0.3 and q['height'] >= 0.05 * top and q['snr'] >= 6: f = True
        flag[i] = f
    xs = sorted((x[i], flag[i]) for i in flag); v = [a for a, _ in xs]; f = [b for _, b in xs]; nf = sum(f)
    s = comp_step(P, x) or 0.02; lo, hi = v[0], v[-1]
    if not nf:
        return {'decided': True, 'key': None, 'naive': None, 'critical': False, 'n_valid': len(per), 'n_flagged': 0, 'x_cat': x_cat, 'main': main,
                'effect': None, 'cheap': {'no boundary': True, 'midpoint': False}, 'oracle': True}
    best = None   # cut k between v[k-1] and v[k]; side high: left unflagged, right flagged; side low: the reverse (rules: <= 1 exception)
    for k in range(1, len(v)):
        for side in ('high', 'low'):
            err = sum(f[:k]) + (len(v) - k - sum(f[k:])) if side == 'high' else (k - sum(f[:k])) + sum(f[k:])
            if best is None or err < best[0]: best = (err, k, side)
    err, k, side = best
    if err > 1:
        return {'decided': False, 'key': None, 'critical': False, 'n_valid': len(per), 'n_flagged': nf, 'main': main, 'cheap': {}, 'oracle': False}
    key = (v[k - 1] + v[k]) / 2; tol = max(s, (v[k] - v[k - 1]) / 2); naive = hi if side == 'high' else lo
    crit = nf >= 2 and abs(naive - key) > tol
    return {'decided': True, 'key': key, 'tol': tol, 'side': side, 'naive': naive, 'critical': crit, 'n_valid': len(per), 'n_flagged': nf,
            'x_cat': x_cat, 'main': main, 'effect': abs(naive - key) if crit else None,
            'cheap': {'no boundary': abs(naive - key) <= tol, 'midpoint': abs((lo + hi) / 2 - key) <= tol}, 'oracle': True}


# ---------------- L7 / L8 audits ----------------
def l7(P):
    iv = [p for p in P if p['iv'] is not None]
    if len(iv) < 10: return None
    key = sum(1 for p in iv if p['iv'].get('valid')); naive = len(iv); ok = lambda v: abs(v - key) <= 1
    return {'decided': True, 'key': key, 'naive': naive, 'critical': naive - key >= 2, 'n_valid': len(iv), 'effect': naive - key if naive - key >= 2 else None,
            'why': [p['iv'].get('why') for p in iv if not p['iv'].get('valid')],
            'cheap': {'all (naive)': ok(naive), 'zero': ok(0), 'all minus 2': ok(naive - 2)}, 'oracle': True}


def l8(P, sig_A, band=(1.8, 3.0)):
    op = [p for p in P if p.get('opt')]
    if len(op) < 10: return None
    bad = 0; hiT = 0
    for p in op:
        e, t, r = p['opt']; over = float(np.nanmax(t)) > 1.05; hiT += over
        m = (e >= band[0]) & (e <= band[1]) & np.isfinite(t) & np.isfinite(r)
        bal = m.sum() >= 10 and float(np.median(t[m] + r[m] - 1)) > 3 * sig_A
        bad += over or bal
    ok = lambda v: abs(v - bad) <= 1
    return {'decided': True, 'key': bad, 'naive': 0, 'critical': bad >= 2, 'n_valid': len(op), 'effect': bad if bad >= 2 else None, 'n_T_over': hiT,
            'cheap': {'zero (naive)': ok(0), 'T>1.05 only': ok(hiT), 'all': ok(len(op))}, 'oracle': True}
