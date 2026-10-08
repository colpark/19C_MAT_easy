"""mc_keys.py (v4.5; HTEM_MC_RULES.md sections 2-4): the frozen key logic of families MC1-MC7, plus readers S4mc1, S4mc3, S4mc4, S4mc5
and S4mc6, as pure functions on arrays. Each key function returns {'cls', 'value', 'panel', 'trust', 'doubt', ...}: cls is the class
string, value the intermediate number, and trust and doubt the classes the trust (trap) and doubt rules give.
CT = 'cannot tell'."""
import hashlib, math
import numpy as np

CT = 'cannot tell'
GF = math.pi / math.log(2)


def h(s):
    return int(hashlib.sha256(str(s).encode()).hexdigest(), 16)


# ---------------- S4mc6: I-V validity (data-intrinsic; MC0) ----------------
def iv_fit(I, V):
    I, V = np.asarray(I, float), np.asarray(V, float); m = np.isfinite(I) & np.isfinite(V); I, V = I[m], V[m]
    out = {'n': int(I.size), 'imax': float(np.max(np.abs(I))) if I.size else 0.0}
    if I.size < 2 or np.ptp(I) == 0:
        out.update(R=None, valid=False, why='degenerate'); return out
    A = np.vstack([I, np.ones(I.size)]).T; (R, V0), *_ = np.linalg.lstsq(A, V, rcond=None); res = V - A @ np.array([R, V0])
    ss = float(np.sum((V - V.mean()) ** 2)); r2 = 1 - float(np.sum(res ** 2)) / ss if ss > 0 else 0.0
    dof = max(I.size - 2, 1); se = math.sqrt(float(np.sum(res ** 2)) / dof / max(float(np.sum((I - I.mean()) ** 2)), 1e-300))
    rms = math.sqrt(float(np.mean(res ** 2))); vmax = float(np.max(np.abs(V))) or 1e-300
    why = [w for w, bad in (('points<4', I.size < 4), ('zero sweep', out['imax'] < 5e-8), ('polarity', R <= 0), ('nonlinear', r2 < 0.999), ('noise', rms > 0.02 * vmax)) if bad]
    out.update(R=float(R), R_err=float(se), r2=float(r2), rms_frac=rms / vmax, valid=not why, why=','.join(why) or None, R_apparent=abs(float(R)))
    return out


def mc6_key(fits):
    """fits: list of 3 iv_fit dicts for A, B, C. Rules section 2 MC6."""
    L = 'ABC'; app = [f.get('R_apparent') if f.get('R') is not None else math.inf for f in fits]
    trust = L[int(np.argmin(app))] if np.isfinite(min(app)) else CT
    doubt = CT if any((f.get('r2') or 0) < 0.999 for f in fits) else trust
    ia = int(np.argmin(app))
    if not fits[ia].get('valid'):
        return {'cls': CT, 'value': GF * app[ia] if np.isfinite(app[ia]) else None, 'panel': L[ia], 'trust': trust, 'doubt': doubt, 'kind': 'invalid apparent-lowest'}
    val = sorted((GF * f['R'], GF * f['R_err'], k) for k, f in enumerate(fits) if f.get('valid'))
    if len(val) >= 2 and val[1][0] - val[0][0] > 3 * math.hypot(val[0][1], val[1][1]) or len(val) == 1:
        k = val[0][2]; return {'cls': L[k], 'value': val[0][0], 'panel': L[k], 'trust': trust, 'doubt': doubt, 'kind': 'decided'}
    return {'cls': CT, 'value': val[0][0] if val else None, 'panel': L[val[0][2]] if val else L[ia], 'trust': trust, 'doubt': doubt, 'kind': 'margin'}


# ---------------- MC2: resistivity ----------------
def mc2_key(rsA, rsB, dA, dB):
    combos = [(rsA * dA * a) / (rsB * dB * b) for a in (0.75, 1.25) for b in (0.75, 1.25)]
    ratio = rsA * dA / (rsB * dB)
    cls = 'A' if all(c < 1 for c in combos) else 'B' if all(c > 1 for c in combos) else CT
    panel = 'thickness' if abs(math.log(dA / dB)) > abs(math.log(rsA / rsB)) else 'Rs'
    trust = 'A' if rsA < rsB else 'B'; doubt = 'B' if rsA < rsB else 'A'
    return {'cls': cls, 'value': ratio, 'panel': panel, 'trust': trust, 'doubt': doubt}


# ---------------- S4mc1 / MC1: trend vs replicate scatter ----------------
def mc1_key(xs, ys, libs, sigma_rep, claim):
    """xs: fractions, ys: log10 Rs, libs: library label per point, claim 'falls'|'rises'. Fixed-effects common slope."""
    xs, ys = np.asarray(xs, float), np.asarray(ys, float); labs = sorted(set(libs))
    xc = np.array([x - np.mean([xs[j] for j in range(len(xs)) if libs[j] == libs[i]]) for i, x in enumerate(xs)])
    yc = np.array([y - np.mean([ys[j] for j in range(len(ys)) if libs[j] == libs[i]]) for i, y in enumerate(ys)])
    sxx = float(np.sum(xc ** 2))
    if sxx <= 0: return None
    s = float(np.sum(xc * yc) / sxx); se = sigma_rep / math.sqrt(sxx); t = s / se if se > 0 else 0.0
    want = -1 if claim == 'falls' else 1
    cls = CT if abs(t) <= 1.96 else ('consistent' if np.sign(s) == want else 'contradicted')
    sp = float(np.polyfit(xs, ys, 1)[0]); trust = 'consistent' if np.sign(sp) == want else 'contradicted'
    return {'cls': cls, 'value': s, 'se': se, 't': t, 'panel': 'scatter', 'trust': trust, 'doubt': CT, 'pooled_slope': sp}


# ---------------- S4mc3 / MC3: energy balance ----------------
def balance(E, T, R):
    """A = 1 - T - R on the pair grid (eV ascending) and the transparent-region SD (points with T > 0.9 max T, >= 10 points)."""
    E, T, R = map(lambda a: np.asarray(a, float), (E, T, R)); A = 1 - T - R
    tr = T > 0.9 * np.nanmax(T)
    sd = float(np.nanstd(A[tr])) if tr.sum() >= 10 else None
    return A, sd, tr


def mc3_key(E, T, R, e0, sig_rep):
    A, sd, _ = balance(E, T, R)
    if sd is None: return None
    k = int(np.argmin(np.abs(np.asarray(E) - e0))); a = float(A[k]); sig = math.hypot(sd, sig_rep)
    cls = 'absorbs' if a > max(3 * sig, 0.05) else 'does not absorb' if a < 1.5 * sig else CT
    t = float(T[k]); trust = 'absorbs' if -math.log(max(t, 1e-9)) > 0.22 else 'does not absorb'
    panel = 'R' if (cls == 'does not absorb' and t < 0.8) else 'T'
    return {'cls': cls, 'value': a, 'sigma': sig, 'panel': panel, 'trust': trust, 'doubt': 'does not absorb', 'T': t, 'R': float(R[k])}


def mc3_energies(E, T, R):
    """Candidate energies (rules MC3): local R maxima where T < 0.9 x median T of the run; first E with T < 0.5 and < 0.2."""
    E, T, R = map(lambda a: np.asarray(a, float), (E, T, R)); med = float(np.nanmedian(T)); out = []
    for i in range(1, len(E) - 1):
        if R[i] > R[i - 1] and R[i] >= R[i + 1] and T[i] < 0.9 * med: out.append(('Rmax', float(E[i])))
    for thr in (0.5, 0.2):
        k = np.flatnonzero(T < thr)
        if k.size: out.append((f'T<{thr}', float(E[k[0]])))
    return out


# ---------------- S4mc4 / MC4: antiphase detector ----------------
def mc4_windows(E, T, k_smooth=9):
    """Extrema of T after a k_smooth-point moving average (S4mc4 reader parameter, tuned on dev seeds: raw noise wiggles otherwise count
    as the neighbouring maxima and collapse the window)."""
    E, T = np.asarray(E, float), np.asarray(T, float); out = []
    if k_smooth > 1 and T.size > k_smooth:
        Ts = np.convolve(T, np.ones(k_smooth) / k_smooth, mode='same'); h_ = k_smooth // 2; Ts[:h_], Ts[-h_:] = T[:h_], T[-h_:]; T = Ts
    mins = [i for i in range(2, len(T) - 2) if T[i] < T[i - 1] and T[i] <= T[i + 1] and T[i] <= T[i - 2] and T[i] <= T[i + 2]]
    maxs = [i for i in range(1, len(T) - 1) if T[i] > T[i - 1] and T[i] >= T[i + 1]]
    for i in mins:
        lo = max([m for m in maxs if m < i], default=0); hi = min([m for m in maxs if m > i], default=len(E) - 1)
        hw = max(0.15, abs(E[i] - E[lo]), abs(E[hi] - E[i]))
        e1, e2 = max(E[0], E[i] - hw), min(E[-1], E[i] + hw); out.append((float(E[i]), float(e1), float(e2)))
    return out


def mc4_key(E, T, R, emin, e1, e2, sig_rep):
    A, sd, _ = balance(E, T, R)
    if sd is None: return None
    E = np.asarray(E, float); m = (E >= e1) & (E <= e2)
    if m.sum() < 7: return None
    x = E[m]; dT = T[m] - np.polyval(np.polyfit(x, T[m], 1), x); dR = R[m] - np.polyval(np.polyfit(x, R[m], 1), x)
    if np.std(dT) == 0 or np.std(dR) == 0: return None
    r = float(np.corrcoef(dT, dR)[0, 1]); Am = A[m]; dA = float(np.nanmax(Am) - np.nanmin(Am)); sig = math.hypot(sd, sig_rep)
    km = int(np.argmin(np.abs(x - emin))); ends = max(Am[0], Am[-1])
    cls = 'interference' if (r < -0.5 and dA < 2 * sig) else 'absorption' if (dA > 4 * sig and Am[km] - ends > 2 * sig) else CT
    return {'cls': cls, 'value': r, 'dA': dA, 'sigma': sig, 'panel': 'R' if cls == 'interference' else 'T', 'trust': 'absorption', 'doubt': 'interference'}


# ---------------- S4mc5 / MC5: Vegard residual ----------------
LAM = 1.5418


def two_theta_111(a):
    return 2 * math.degrees(math.asin(LAM * math.sqrt(3) / (2 * a)))


def mc5_key(meas, x, y, u_x, aZS, aZT, aMS, aMT, extra_match):
    """meas: measured (111) 2θ; x = Se/(Se+Te); y = Mn/(Mn+Zn); aMT None drops cation alloying; extra_match: bool."""
    tv = two_theta_111(x * aZS + (1 - x) * aZT); r = meas - tv
    d = (two_theta_111((x + 0.01) * aZS + (0.99 - x) * aZT) - tv) / 0.01
    u_model = abs(two_theta_111(1.005 * (x * aZS + (1 - x) * aZT)) - tv) / 2
    u = math.sqrt(0.069 ** 2 + (d * u_x) ** 2 + u_model ** 2)
    r_ext = None
    if aMS and aMT:
        a = (1 - y) * (x * aZS + (1 - x) * aZT) + y * (x * aMS + (1 - x) * aMT); r_ext = meas - two_theta_111(a)
    if abs(r) <= 2 * u: cls = 'within error'
    elif extra_match and (r_ext is None or abs(r_ext) > 2 * u): cls = 'second phase'
    elif r_ext is not None and abs(r_ext) <= 2 * u and not extra_match: cls = 'cation alloying'
    else: cls = CT
    trust = 'within error' if abs(r) < 0.3 else 'cation alloying'
    panel = {'cation alloying': 'Mn map', 'second phase': 'XRD'}.get(cls, 'anion map')
    return {'cls': cls, 'value': r, 'u': u, 'r_ext': r_ext, 'panel': panel, 'trust': trust, 'doubt': 'second phase'}


# ---------------- MC7 from MC2 (rules MC7: median substitution, unique necessary panel) ----------------
def mc7_from_mc2(rsA, rsB, dA, dB, rs_med, d_med):
    base = mc2_key(rsA, rsB, dA, dB)['cls']
    if base == CT: return None
    nec = []
    if mc2_key(rs_med, rs_med, dA, dB)['cls'] != base: nec.append('Rs map')
    if mc2_key(rsA, rsB, d_med, d_med)['cls'] != base: nec.append('thickness map')
    # the XRF composition map never enters the MC2 key logic: never necessary
    if len(nec) != 1: return None
    return {'cls': nec[0], 'value': None, 'panel': nec[0], 'trust': 'Rs map', 'doubt': 'thickness map'}
