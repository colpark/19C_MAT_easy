#!/usr/bin/env python3
"""dev_stats.py (stage H4): statistics of ONE dev library (census/PILOT_LIBS.json 'dev' of the given role) for the synthetic generator.
Never reads a held-out library. Measures:
  XRD      background level (median counts), background curvature (SNIP background at 19-22 deg over 49-52 deg), noise ratio (MAD of first
           differences of the background-subtracted residual over sqrt(2 x counts): 1 = Poisson), peak FWHM percentiles and peak heights over
           background (kit reader at config parameters), number of peaks per pattern.
  Optical  R level (median R over 500-1000 nm), T and R noise (MAD of first differences), absorption scale A and Urbach energy from the
           film's alpha(E) (alpha d = -ln[T/(1-R)] with the database thickness; Eg-independent fits of A sqrt(E-Eg)/E above and the
           exponential tail below a provisional Tauc gap); thickness range (database thickness, A level: generator range only).
  FPM      I-V noise relative to the linear fit, Rs range.
Writes $HTEM_HOST/dev/dev_stats_<role>.json. usage: dev_stats.py P1|P2"""
import json, math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import htem_api as API, sample_io as SIO
from readers import xrd as RX
HC = 1239.84198

def mad_diff(y):
    d = np.diff(y); return float(1.4826 * np.median(np.abs(d - np.median(d))) / math.sqrt(2))

def main(role):
    pl = json.load(open(os.path.join(API.HOST, 'census', 'PILOT_LIBS.json')))[role]; dev = pl['dev']
    c = API.Client(); samples = c.samples_of(dev)          # cached: no request for a fetched library
    X = {'bg': [], 'curv': [], 'noise_ratio': [], 'fwhm': [], 'h_over_bg': [], 'npeaks': []}
    O = {'R': [], 'T_noise': [], 'R_noise': [], 'A': [], 'Eu': [], 'thick_um': []}; F = {'rel_noise': [], 'Rs': []}
    cfg = API.CFG['readers']['xrd']
    for s in samples:
        x = SIO.xrd(s)
        if x:
            tt, y = x['two_theta'], x['intensity']; r = RX.read(tt, y, cfg)
            bg = RX.snip(RX.smooth(y, cfg['smooth_pts']), iters=max(10, int(round(cfg.get('snip_halfwidth_deg', 2.5) / r['step_deg']))))
            X['bg'].append(float(np.median(bg))); X['curv'].append(float(np.median(bg[tt < 22]) / max(np.median(bg[tt > 49]), 1)))
            X['noise_ratio'].append(mad_diff(y - bg) / max(math.sqrt(np.median(np.clip(y, 1, None))), 1e-9))
            X['npeaks'].append(len(r['peaks']))
            for p in r['peaks']:
                X['fwhm'].append(p['fwhm']); X['h_over_bg'].append(p['height'] / max(float(np.interp(p['center'], tt, bg)), 1))
        o = SIO.optical(s); d = SIO.thickness_um(s)
        if o and 'uvit' in o and 'uvir' in o:
            w, T = o['uvit']['wavelength_nm'], o['uvit']['response']; R = np.interp(w, o['uvir']['wavelength_nm'], o['uvir']['response']); m = (w >= 500) & (w <= 1000)
            if m.any(): O['R'].append(float(np.median(R[m])))
            O['T_noise'].append(mad_diff(T)); O['R_noise'].append(mad_diff(R))
            if d and d > 0:
                O['thick_um'].append(float(d)); E = HC / w; ok = (T > 0.005) & (R < 0.95) & (T < 0.999 * (1 - R))
                if ok.sum() > 20:
                    a = -np.log(T[ok] / (1 - R[ok])) / (d * 1e-4); Ek = E[ok]; o_ = np.argsort(Ek); Ek, a = Ek[o_], a[o_]
                    y = (a * Ek) ** 2; hi = y > 0.5 * y.max()
                    if hi.sum() > 5:
                        p = np.polyfit(Ek[hi], y[hi], 1); eg = -p[1] / p[0] if p[0] > 0 else None
                        if eg and Ek.min() < eg < Ek.max():
                            ab = Ek > eg + 0.1
                            if ab.sum() > 5: O['A'].append(float(np.median(a[ab] * Ek[ab] / np.sqrt(Ek[ab] - eg))))
                            tl = (Ek < eg - 0.05) & (Ek > eg - 0.4) & (a > 1e3)
                            if tl.sum() > 5:
                                q = np.polyfit(Ek[tl], np.log(a[tl]), 1)
                                if q[0] > 0: O['Eu'].append(float(1 / q[0]))
        f = SIO.fpm(s)
        if f:
            i, v = f['current_A'], f['voltage_V']; p = np.polyfit(i, v, 1); res = v - np.polyval(p, i)
            if abs(p[0]) > 0: F['rel_noise'].append(float(np.std(res) / (abs(p[0]) * np.ptp(i)))); F['Rs'].append(float(abs(p[0]) * API.CFG['readers']['fpm']['geometry_factor']))
    pct = lambda L: [round(float(v), 5) for v in np.percentile(L, [5, 25, 50, 75, 95])] if L else None
    out = {'role': role, 'system': pl['system'], 'dev_library': dev, 'samples': len(samples),
           'xrd': {k: pct(v) for k, v in X.items()}, 'optical': {k: pct(v) for k, v in O.items()}, 'fpm': {k: pct(v) for k, v in F.items()},
           'n': {'xrd': len(X['bg']), 'peaks': len(X['fwhm']), 'optical': len(O['R']), 'A_fits': len(O['A']), 'Eu_fits': len(O['Eu']), 'fpm': len(F['Rs'])}}
    os.makedirs(os.path.join(API.HOST, 'dev'), exist_ok=True)
    json.dump(out, open(os.path.join(API.HOST, 'dev', f'dev_stats_{role}.json'), 'w'), indent=1); print(json.dumps(out, indent=1))

if __name__ == '__main__':
    main(sys.argv[1])
