#!/usr/bin/env python3
"""validate_sa508.py (S5a, rule I7): sa508_op.py on synthetic curves with known hardness and reduced modulus.
Generator (drawn from the forged-PWHT dev curves for shape and noise only, never from author values): an approach segment at near-zero
load with a random depth offset (0-3000 nm, as the 6000 nm raw curves show), loading P = Pmax ((h - h0)/hmax)^2 to a depth-controlled
hmax 2950-3050 nm, a 0.5-1.0 s hold with 0-4 % load relaxation, power-law unloading P = alpha (h - hf)^m (m 1.2-1.8) down to ~0.05 mN,
and in 30 % of curves a low-load tail of 20-80 s. Pmax, S and hc are solved self-consistently from the true H (2-5 GPa) and Er
(60-230 GPa) with the same Berkovich relations (ideal area function). Noise: load 0.0003-0.0015 mN, depth 0.13-1.4 nm; sampling
0.002-0.004 s.
Gates (frozen with this file): >= 90 % of curves with H within 5 % and Er within 10 % of truth; for pairs 10 % apart in H the ranking
is preserved in >= 95 %. Output validate_sa508.json."""
import json, math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); import sa508_op as R
rng = np.random.default_rng(508)

def synth(H, Er, hmax=None):
    hmax = hmax or rng.uniform(2950, 3050); m = rng.uniform(1.2, 1.8)
    hc = 0.85 * hmax
    for _ in range(100):   # Pmax = H A(hc); S = 2 beta / sqrt(pi) Er sqrt(A); hc = hmax - eps Pmax / S
        A = R.AREA_C0 * hc ** 2; Pmax = H * A * 1e-6; S = 2 * R.BETA / math.sqrt(math.pi) * Er * math.sqrt(A) * 1e-6; hc = hmax - R.EPS * Pmax / S
    hf = hmax - m * Pmax / S; alpha = Pmax / (hmax - hf) ** m
    dt = rng.uniform(0.002, 0.004); off = rng.uniform(0, 3000); nP = rng.uniform(0.0003, 0.0015); nh = rng.uniform(0.13, 1.4)
    t_app = rng.uniform(5, 12); n_app = int(t_app / dt); h_app = np.linspace(off - 30, off, n_app); P_app = np.abs(rng.normal(0.01, 0.005, n_app))
    t_load = rng.uniform(30, 45); n_load = int(t_load / dt); hl = np.linspace(0, hmax, n_load); Pl = Pmax * (hl / hmax) ** 2
    n_hold = int(rng.uniform(0.5, 1.0) / dt); relax = rng.uniform(0, 0.04); Ph = np.linspace(Pmax * (1 + relax), Pmax, n_hold); hh = np.full(n_hold, hmax)
    Pl = Pl * (1 + relax)   # loading ends at the pre-relaxation load; unloading starts from Pmax at hmax
    n_un = int(rng.uniform(8, 12) / dt); hu = np.linspace(hmax, hf + (0.05 / alpha) ** (1 / m), n_un); Pun = alpha * np.clip(hu - hf, 0, None) ** m
    parts_h = [h_app, off + hl, off + hh, off + hu]; parts_P = [P_app, Pl, Ph, Pun]
    if rng.random() < 0.3:
        n_t = int(rng.uniform(20, 80) / dt); parts_h.append(np.full(n_t, off + hu[-1]) + np.cumsum(rng.normal(0, 0.02, n_t))); parts_P.append(np.full(n_t, Pun[-1]))
    h = np.concatenate(parts_h) + rng.normal(0, nh, sum(len(x) for x in parts_h)); P = np.concatenate(parts_P) + rng.normal(0, nP, len(h)); t = np.arange(len(h)) * dt
    return t, h, P

rows = []; rank = []
for k in range(400):
    H = rng.uniform(2, 5); Er = rng.uniform(60, 230)
    r = R.oliver_pharr(*synth(H, Er)); r2 = R.oliver_pharr(*synth(H * 1.1, Er))
    eH = abs(r['H_GPa'] - H) / H if r['ok'] else 1.0; eE = abs(r['Er_GPa'] - Er) / Er if r['ok'] else 1.0
    rows.append({'H': H, 'Er': Er, 'eH': eH, 'eE': eE, 'ok': r['ok']}); rank.append(bool(r['ok'] and r2['ok'] and r2['H_GPa'] > r['H_GPa']))
eH = np.array([x['eH'] for x in rows]); eE = np.array([x['eE'] for x in rows])
res = {'n': len(rows), 'ok': int(sum(x['ok'] for x in rows)), 'H_within_5pct': float(np.mean(eH <= 0.05)), 'Er_within_10pct': float(np.mean(eE <= 0.10)),
       'H_median_err': float(np.median(eH)), 'Er_median_err': float(np.median(eE)), 'rank_10pct': float(np.mean(rank))}
res['gates'] = {'H': res['H_within_5pct'] >= 0.9, 'Er': res['Er_within_10pct'] >= 0.9, 'rank': res['rank_10pct'] >= 0.95}
res['pass'] = all(res['gates'].values())
json.dump(res, open(os.path.join(HERE, 'validate_sa508.json'), 'w'), indent=1); print(json.dumps(res))
