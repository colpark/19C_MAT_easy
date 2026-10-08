#!/usr/bin/env python3
"""desk_mc.py (v4.5 MC0): data-side desk checks over every cached HTEM sample and library (no network). Writes
$HTEM_HOST/mc/desk_mc.json. Questions: XRD background state (xrd_intensity vs xrd_background), frame-edge steps, Kα2 resolution
(FWHM against the Kα1/Kα2 splitting), optical T/R ranges (absolute vs normalized), substrate per library, bare-substrate records,
FPM raw I-V coverage and current span, xrf_type counts, replicate groups."""
import glob, json, math, os, sys
from collections import Counter, defaultdict
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, HERE)
import htem_api as API, sample_io as SIO, census as CEN
C = API.Client(); out = {}
arr = lambda v: np.asarray(v, float) if isinstance(v, list) and v else None
samples = []
for f in sorted(glob.glob(os.path.join(API.HOST, 'cache', 'sample', '*'))):
    try: s = json.load(open(f))
    except Exception: continue
    if isinstance(s, dict) and 'id' in s: samples.append(s)
out['n_samples_cached'] = len(samples)
# XRD background state
st = Counter(); sub_min = []; ratio = []; steps = Counter(); nstep = 0
for s in samples:
    I, B, A = arr(s.get('xrd_intensity')), arr(s.get('xrd_background')), arr(s.get('xrd_angle'))
    if I is None or A is None: continue
    st['xrd'] += 1
    if B is not None and B.size == I.size:
        st['with_background'] += 1; ratio.append(float(np.median(B) / max(np.median(I), 1e-9)))
        sub_min.append(float(np.percentile(I, 5)))
    d = np.abs(np.diff(I)); thr = 8 * np.median(d) + 1e-9
    for k in np.flatnonzero(d > thr):   # candidate steps: jump with flat neighbours on both sides (not a peak)
        if 3 <= k < d.size - 3 and d[k - 3:k].max() < thr / 3 and d[k + 1:k + 4].max() < thr / 3: steps[round(float(A[k]), 1)] += 1; nstep += 1
out['xrd'] = {'n': st['xrd'], 'n_with_background_array': st['with_background'],
              'median_background_over_intensity': float(np.median(ratio)) if ratio else None,
              'intensity_p5_median': float(np.median(sub_min)) if sub_min else None,
              'step_candidates_total': nstep, 'step_positions_top': steps.most_common(8)}
# Kα2: splitting 2 tanθ Δλ/λ (Δλ 0.00383 Å on 1.5406 Å) against fitted FWHM of strong peaks at 2θ > 40 deg (H4/H10 matrices)
fw = []
for t in ('P1r2', 'P2r2'):
    p = os.path.join(API.HOST, 'matrix', t, 'cells.jsonl')
    if not os.path.exists(p): continue
    for l in open(p):
        c = json.loads(l)
        for pk in (c['derived'].get('xrd_peaks') or []):
            if pk.get('snr', 0) >= 10 and pk.get('fwhm'): fw.append((pk['center'], pk['fwhm']))
split = lambda tt: math.degrees(2 * math.tan(math.radians(tt / 2)) * 0.00383 / 1.5406)
hi = [f for c, f in fw if c > 40]; lo = [f for c, f in fw if c <= 40]
out['ka2'] = {'splitting_deg_at_30': split(30), 'splitting_deg_at_50': split(50), 'n_peaks': len(fw),
              'fwhm_median_2theta_le40': float(np.median(lo)) if lo else None, 'fwhm_median_2theta_gt40': float(np.median(hi)) if hi else None,
              'fwhm_p10_all': float(np.percentile([f for _, f in fw], 10)) if fw else None,
              'resolved': bool(fw) and float(np.percentile([f for _, f in fw], 10)) < split(50) / 2}
# optical
ot = Counter(); tmax = []; rmax = []; tr_sum = []
for s in samples:
    T, R = arr(s.get('opt_uvit_response')), arr(s.get('opt_uvir_response'))
    if T is None or R is None: continue
    ot['n'] += 1; tmax.append(float(np.nanmax(T))); rmax.append(float(np.nanmax(R)))
    if T.size == R.size: tr_sum.append(float(np.nanpercentile(T + R, 95)))
out['optical'] = {'n': ot['n'], 'T_max_median': float(np.median(tmax)) if tmax else None, 'T_max_p99': float(np.percentile(tmax, 99)) if tmax else None,
                  'R_max_median': float(np.median(rmax)) if rmax else None, 'T_plus_R_p95_median': float(np.median(tr_sum)) if tr_sum else None,
                  'n_T_over_1.05': sum(t > 1.05 for t in tmax)}
# libraries
libs = []
for f in sorted(glob.glob(os.path.join(API.HOST, 'cache', 'library', '*'))):
    try: L = json.load(open(f))
    except Exception: continue
    if isinstance(L, dict) and 'id' in L: libs.append(L)
out['libraries'] = {'n_cached': len(libs), 'xrf_type': Counter(str(L.get('xrf_type')) for L in libs).most_common(),
                    'substrate': Counter(str(L.get('deposition_substrate_material')) for L in libs).most_common(10),
                    'elements_empty_or_substrate_only': sum(1 for L in libs if not (L.get('elements') or []))}
# FPM
fp = Counter(); imax = []
for s in samples:
    V, I = arr(s.get('fpm_voltage_volts')), arr(s.get('fpm_current_amps'))
    if V is None or I is None: continue
    fp['n'] += 1; fp[f'points_{V.size}'] += 1; imax.append(float(np.max(np.abs(I))))
out['fpm'] = {'counts': dict(fp), 'abs_current_max_quantiles': [float(x) for x in np.percentile(imax, [1, 50, 99])] if imax else None,
              'distinct_current_spans': Counter(round(x, 6) for x in imax).most_common(6)}
# replicate groups (census libraries.csv: recipe, temp per system)
import csv
rows = list(csv.DictReader(open(os.path.join(API.HOST, 'census', 'libraries.csv'))))
g = defaultdict(set)
for r in rows:
    if r.get('multi') == '1' and r.get('recipe'): g[(r['system'], r['recipe'])].add(r['id'])
rep = Counter(k[0] for k, v in g.items() if len(v) >= 2)
out['replicates'] = {'systems_with_groups': len(rep), 'groups_total': sum(rep.values()), 'top': rep.most_common(15)}
os.makedirs(os.path.join(API.HOST, 'mc'), exist_ok=True)
json.dump(out, open(os.path.join(API.HOST, 'mc', 'desk_mc.json'), 'w'), indent=1, default=str)
print(json.dumps(out, indent=1, default=str)[:5000])
