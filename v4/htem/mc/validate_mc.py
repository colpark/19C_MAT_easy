#!/usr/bin/env python3
"""validate_mc.py (v4.5 MC3, synthetic part; HTEM_MC_RULES section 5 and the prompt's MC3 table): fresh-seed gates for readers S4mc1,
S4mc3, S4mc4, S4mc5 and S4mc6, using the frozen key code in mc_keys.py. Noise levels come from dev data only: config synth.P1 (optical
T/R noise, FPM relative noise), the H4 replicate peak spread and the MC2 dev noise (MC_CENSUS.json noise block, dev groups only).
FRESH_BASE is recorded at the freeze. Writes $HTEM_HOST/validation/mc_synth.json and prints the gate table."""
import json, math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'mc'))
import htem_api as API, mc_keys as K
FRESH_BASE = 0 if os.environ.get('MC_DEV') else 842200; N = 200   # MC_DEV=1: dev seeds for debugging (never the gate)
SP = API.CFG['synth']['P1']; TN, RN = SP['opt_T_noise'], SP['opt_R_noise']; FN = SP['fpm_rel_noise'][1]
NOISE = json.load(open(os.path.join(HERE, 'MC_CENSUS.json')))['noise']
E = np.linspace(1.15, 4.1, 600)


def gate_mc1():
    """Null (s = 0): rejection rate <= alpha + 0.02. Effect size frozen at expected |t| = 3: power >= 0.8."""
    sig = NOISE['sigma_logRs_median']; fp = pw = 0
    for k in range(N):
        r = np.random.default_rng(FRESH_BASE + k)
        x = np.concatenate([r.uniform(0.3, 0.4, 8), r.uniform(0.3, 0.4, 8)]); lib = ['a'] * 8 + ['b'] * 8; off = np.array([0.0] * 8 + [r.normal(0, 0.3)] * 8)
        sxx = sum((x[i] - np.mean([x[j] for j in range(16) if lib[j] == lib[i]])) ** 2 for i in range(16)); s_eff = 3 * sig / math.sqrt(sxx)
        y0 = 2 + off + r.normal(0, sig, 16); y1 = y0 - s_eff * x
        fp += K.mc1_key(x, y0, lib, sig, 'falls')['cls'] != K.CT
        pw += K.mc1_key(x, y1, lib, sig, 'falls')['cls'] == 'consistent'
    return {'false_positive': fp / N, 'power': pw / N, 'pass': fp / N <= 0.07 and pw / N >= 0.8}


def film(r, alpha, d_um, n=2.2, ns=1.52, coherent=True):
    """Thin film on a thick non-absorbing substrate: film reflectance with interference (Airy, no absorption phase), incoherent
    substrate back surface. Returns T, R (noise-free), and the true absorptance."""
    lam = 1239.84198 / E * 1e-3; k = alpha * lam * 1e-4 / (4 * math.pi)   # alpha cm^-1, lam um
    N1 = n + 1j * k; r01 = (1 - N1) / (1 + N1); r12 = (N1 - ns) / (N1 + ns); t01 = 2 / (1 + N1); t12 = 2 * N1 / (N1 + ns)
    delta = 2 * np.pi * N1 * d_um / lam if coherent else 2 * np.pi * N1 * d_um / lam * 0
    ph = np.exp(2j * delta) if coherent else np.exp(-4 * np.pi * k * d_um / lam)
    rf = (r01 + r12 * ph) / (1 + r01 * r12 * ph); tf = t01 * t12 * np.exp(1j * delta) / (1 + r01 * r12 * ph)
    if not coherent:
        att = np.exp(-alpha * d_um * 1e-4); Rf = abs(r01) ** 2 + (1 - abs(r01) ** 2) ** 2 * abs(r12) ** 2 * att ** 2 / (1 - abs(r01 * r12) ** 2 * att ** 2)
        Tf = (1 - abs(r01) ** 2) * (1 - abs(r12) ** 2) * att / (1 - abs(r01 * r12) ** 2 * att ** 2)
    else:
        Rf = np.abs(rf) ** 2; Tf = ns * np.abs(tf) ** 2
    Rb = ((ns - 1) / (ns + 1)) ** 2   # substrate back surface, incoherent
    T = Tf * (1 - Rb) / (1 - Rf * Rb); R = Rf + Tf ** 2 * Rb / (1 - Rf * Rb)   # symmetric-film approximation for the return pass
    return T, R, 1 - T - R


def edge(r):
    eg = r.uniform(1.8, 3.6); a = 2e5 * np.sqrt(np.clip(E - eg, 0, None)) + 2e5 * math.sqrt(0.05) * np.exp((E - eg) / 0.06) * (E < eg)
    return np.minimum(a, 2e6)


def gate_mc3():
    """A = 1 - T - R within 0.01 absolute of the noise-free absorptance at a random in-run energy, on >= 90 % of seeds."""
    ok = 0
    for k in range(N):
        r = np.random.default_rng(FRESH_BASE + 1000 + k); a = edge(r); T, R, A = film(r, a, r.uniform(0.1, 0.6))
        Tn, Rn = T + r.normal(0, TN, E.size), R + r.normal(0, RN, E.size); run = Tn >= 0.01; idx = np.flatnonzero(run)
        i = int(r.choice(idx)); ok += abs((1 - Tn[i] - Rn[i]) - A[i]) <= 0.01
    return {'within_0.01': ok / N, 'pass': ok / N >= 0.9}


def gate_mc4():
    """Class recovered on >= 90 % of seeds per kind: interference only (alpha ~ 0, coherent fringes) -> interference; absorption band
    (Gaussian alpha band with peak alpha*d in 0.5-2, incoherent) -> absorption; mixed (the same band under coherent fringes) -> absorption.
    Bands are drawn decidable (peak absorptance well above the frozen 4 sigma_A threshold); weaker bands are cannot-tell cases by rule."""
    res = {}
    for kind, want in (('interference', 'interference'), ('absorption', 'absorption'), ('mixed', 'absorption')):
        hit = 0
        for k in range(N):
            r = np.random.default_rng(FRESH_BASE + 2000 + k + {'interference': 0, 'absorption': 300, 'mixed': 600}[kind])
            d = r.uniform(0.3, 0.8); e0 = r.uniform(1.6, 2.6)
            band = r.uniform(0.5, 2.0) / (d * 1e-4) * np.exp(-0.5 * ((E - e0) / r.uniform(0.08, 0.2)) ** 2)
            alpha = (band if kind != 'interference' else 0 * E) + 1e-3
            T, R, A = film(r, alpha, d, coherent=(kind != 'absorption'))
            Tn, Rn = T + r.normal(0, TN, E.size), R + r.normal(0, RN, E.size)
            wins = K.mc4_windows(E, Tn); wins = [w for w in wins if 1.3 < w[0] < 3.0]
            if kind != 'interference': wins = [w for w in wins if abs(w[0] - e0) < 0.15] or wins
            if not wins: continue
            w = min(wins, key=lambda w: abs(w[0] - e0)); out = K.mc4_key(E, Tn, Rn, *w, NOISE['sigma_A_median'])
            hit += bool(out) and out['cls'] == want
        res[kind] = hit / N
    return {**res, 'pass': all(v >= 0.9 for v in res.values())}


def gate_mc5():
    """Coverage of the +/-2u band for the residual under the frozen error model: between 0.90 and 0.98."""
    cov = 0; ux = NOISE['u_x_median']
    for k in range(N):
        r = np.random.default_rng(FRESH_BASE + 3000 + k); xt = r.uniform(0.05, 0.95)
        meas = K.two_theta_111(xt * 5.6676 + (1 - xt) * 6.089) + r.normal(0, 0.069); xo = xt + r.normal(0, ux)
        out = K.mc5_key(meas, xo, 0.0, ux, 5.6676, 6.089, None, None, False); cov += out['cls'] == 'within error'
    return {'coverage': cov / N, 'pass': 0.90 <= cov / N <= 0.98}


def gate_mc6():
    """Flags injected nonlinearity, near-zero sweeps and reversed polarity on >= 90 %; false flags on clean curves <= 5 %."""
    res = {}
    for kind in ('clean', 'nonlinear', 'open', 'reversed'):
        fl = 0
        for k in range(N):
            r = np.random.default_rng(FRESH_BASE + 4000 + k + {'clean': 0, 'nonlinear': 300, 'open': 600, 'reversed': 900}[kind])
            I = np.linspace(-1e-6, 1e-6, 5); Rr = 10 ** r.uniform(1, 5); V = Rr * I
            if kind == 'nonlinear': V = V + 0.25 * Rr * 1e-6 * (I / 1e-6) ** 2 * r.choice([-1, 1]) + 0.1 * Rr * 1e-6 * np.abs(I / 1e-6) ** 3
            if kind == 'open': I = I * 1e-3
            if kind == 'reversed': V = -V
            V = V + r.normal(0, FN * np.max(np.abs(V)), V.size)
            fl += not K.iv_fit(I, V)['valid']
        res[kind] = fl / N
    return {**res, 'pass': res['clean'] <= 0.05 and all(res[k] >= 0.9 for k in ('nonlinear', 'open', 'reversed'))}


if __name__ == '__main__':
    out = {'fresh_base': FRESH_BASE, 'n_per_gate': N, 'S4mc1': gate_mc1(), 'S4mc3': gate_mc3(), 'S4mc4': gate_mc4(), 'S4mc5': gate_mc5(), 'S4mc6': gate_mc6()}
    os.makedirs(os.path.join(API.HOST, 'validation'), exist_ok=True)
    json.dump(out, open(os.path.join(API.HOST, 'validation', 'mc_synth.json'), 'w'), indent=1, default=float)
    for k, v in out.items(): print(k, v)
