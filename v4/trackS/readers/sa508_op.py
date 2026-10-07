#!/usr/bin/env python3
"""sa508_op.py (S5a, SA508 reader): Oliver-Pharr hardness and reduced modulus from one raw nanoindentation load-depth curve
(CSV: TIME s, DEPTH nm, LOAD mN; two header lines). Standard instrument equation on the raw readings -> level M. Frozen before it
touched any held-out evidence; parameters are textbook named defaults, not tuned on author values.
Procedure:
  1. contact (S5a-2): fit Kick's law P = k (h - h0)^2 to the loading points between LOAD_LO and LOAD_HI x Pmax (named default 0.02-0.50)
     and take h0 from the fit; depth -> h - h0. (S5a used the first point above 0.001 Pmax, which sits ~3 % of hmax below the surface:
     H read ~8 % high on synthetic curves.)
  2. start of unloading (S5a-2): the last point of the hold, i.e. the last index where the 25-point moving-average depth is within
     max(2 nm, 3 x depth noise) of its maximum; hmax = that smoothed depth, Pu = the load there. (S5a took the single deepest point,
     which can sit before the hold relaxation.)
  3. unloading = points after hmax while the load stays above 2 % of Pu, cut at the first load minimum.
  4. fit P = alpha (h - hf)^m to the unloading points with FIT_LO..FIT_HI x Pu (named default 0.40-0.95; Oliver & Pharr 1992, 2004),
     least squares on load with m in [1.0, 2.5].
  5. S = dP/dh at hmax; hc = hmax - EPS Pu / S (EPS 0.75, Berkovich); A = 24.5 hc^2 (ideal Berkovich area function: the tip
     calibration and frame compliance are not in the deposit, D gap); H = Pu / A; Er = sqrt(pi) S / (2 BETA sqrt(A)), BETA 1.034.
Returns dict with H_GPa, Er_GPa, hmax_nm, Pu_mN, S_mN_nm, hc_nm, m, h0_nm, fit_points, ok (False with 'why' on failure).
usage: sa508_op.py file.csv [...]"""
import json, math, sys
import numpy as np
from scipy.optimize import least_squares
LOAD_LO, LOAD_HI = 0.02, 0.50; FIT_LO, FIT_HI = 0.40, 0.95; EPS = 0.75; BETA = 1.034; AREA_C0 = 24.5

def load_csv(path):
    a = np.genfromtxt(path, delimiter=',', skip_header=2, encoding='utf-8-sig')
    a = a[np.all(np.isfinite(a), axis=1)]
    return a[:, 0], a[:, 1], a[:, 2]

def oliver_pharr(t, h, P):
    out = {'ok': False}
    if len(P) < 50: out['why'] = 'too few points'; return out
    Pmax = float(np.max(P)); ip = int(np.argmax(P))
    lo = np.nonzero((P[:ip + 1] >= LOAD_LO * Pmax) & (P[:ip + 1] <= LOAD_HI * Pmax))[0]
    if len(lo) < 10: out['why'] = 'too few loading points for the contact fit'; return out
    k_, c_ = np.polyfit(h[lo], np.sqrt(np.clip(P[lo], 0, None)), 1)   # sqrt(P) = sqrt(k) (h - h0): linear in h
    if k_ <= 0: out['why'] = 'loading fit failed'; return out
    h0 = float(-c_ / k_); hr = h - h0
    hs = np.convolve(hr, np.ones(25) / 25, mode='same'); top = float(np.max(hs[12:-12])) if len(hs) > 30 else float(np.max(hs))
    noise = float(np.std(np.diff(h[:min(200, ip)])) / np.sqrt(2)) if ip > 20 else 1.0
    near = np.nonzero(hs >= top - max(2.0, 3 * noise))[0]; im = int(near[-1])
    hmax = float(hs[im]); Pu = float(P[im])
    if hmax <= 0 or Pu <= 0: out['why'] = 'no loading'; return out
    seg = np.arange(im, len(P))
    stop = np.argmax(P[seg] < 0.02 * Pu) if np.any(P[seg] < 0.02 * Pu) else len(seg)
    seg = seg[:max(stop, 1)]
    hu, Pu_ = hr[seg], P[seg]
    sel = (Pu_ >= FIT_LO * Pu) & (Pu_ <= FIT_HI * Pu)
    if sel.sum() < 10: out['why'] = f'too few unloading points in the fit window ({int(sel.sum())})'; return out
    x, y = hu[sel], Pu_[sel]
    def res(p):
        a, hf, m = p; return a * np.clip(x - hf, 1e-9, None) ** m - y
    hf0 = float(x.min() - 0.3 * (x.max() - x.min()) - 1.0)
    p0 = [y.max() / max(x.max() - hf0, 1.0) ** 1.5, hf0, 1.5]
    try:
        r = least_squares(res, p0, bounds=([0, -1e6, 1.0], [np.inf, float(x.min()) - 1e-6, 2.5]), max_nfev=20000)
    except Exception as e:
        out['why'] = f'fit failed: {e}'; return out
    a, hf, m = r.x; S = float(a * m * max(hmax - hf, 1e-9) ** (m - 1))
    hc = hmax - EPS * Pu / S; A = AREA_C0 * hc ** 2
    if hc <= 0 or S <= 0: out['why'] = 'non-physical contact depth'; return out
    H = Pu / A * 1e6; Er = math.sqrt(math.pi) * S / (2 * BETA * math.sqrt(A)) * 1e6
    return {'ok': True, 'H_GPa': H, 'Er_GPa': Er, 'hmax_nm': hmax, 'Pu_mN': Pu, 'S_mN_nm': S, 'hc_nm': hc, 'm': float(m), 'hf_nm': float(hf),
            'h0_nm': h0, 'i_unload': im, 'fit_points': int(sel.sum()), 'fit_rms_mN': float(np.sqrt(np.mean(r.fun ** 2)))}

def read(path):
    return oliver_pharr(*load_csv(path))

if __name__ == '__main__':
    for p in sys.argv[1:]:
        print(p, json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in read(p).items()}))
