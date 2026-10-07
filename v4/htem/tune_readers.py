#!/usr/bin/env python3
"""tune_readers.py (stage H4): grid search of reader parameters on synthetic DEV seeds 0-99 only (generator ranges of HTEM_ROLE).
XRD grid: min_snr x smooth_pts x window_deg; optical grid: tauc_lo x tauc_hi. Scores are the gate metrics of validate_readers.py on dev
seeds. Writes $HTEM_HOST/validation/tune_<role>.json (sorted; the chosen setting is copied into config.json readers and frozen).
usage: HTEM_ROLE=P1 tune_readers.py"""
import itertools, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import validate_readers as V
role = os.environ.get('HTEM_ROLE', '?'); seeds = list(range(100)); out = {'role': role, 'xrd': [], 'optical': []}
x0 = dict(V.CFG['readers']['xrd'])
for snr, sm, win in itertools.product([4.0, 6.0, 8.0], [3, 5, 7], [0.8, 1.2, 1.6]):
    V.CFG['readers']['xrd'].update(min_snr=snr, smooth_pts=sm, window_deg=win); g = V.xrd_gate(seeds)
    out['xrd'].append({'min_snr': snr, 'smooth_pts': sm, 'window_deg': win, **{k: g[k] for k in ('pos_within_frac', 'median_fwhm_rel_err', 'amorphous_clean', 'pass')}})
V.CFG['readers']['xrd'].update(x0)
o0 = dict(V.CFG['readers']['optical'])
for lo, hi in itertools.product([0.1, 0.2, 0.3, 0.4, 0.5], [0.6, 0.7, 0.8, 0.9, 1.0]):
    if hi <= lo + 0.15: continue
    V.CFG['readers']['optical'].update(tauc_lo=lo, tauc_hi=hi); g = V.optical_gate(seeds)
    out['optical'].append({'tauc_lo': lo, 'tauc_hi': hi, 'bias_ev': g['bias_ev'], 'bias_sd_ev': g['bias_sd_ev'], 'within': g['within'],
                           'censor': g['censor_flagged_above_range'], 'pass': g['pass']})
V.CFG['readers']['optical'].update(o0)
out['xrd'].sort(key=lambda d: (-d['pos_within_frac'], d['median_fwhm_rel_err'] or 9)); out['optical'].sort(key=lambda d: (d['bias_sd_ev'] or 9))
os.makedirs(os.path.join(os.environ['HTEM_HOST'], 'validation'), exist_ok=True)
json.dump(out, open(os.path.join(os.environ['HTEM_HOST'], 'validation', f'tune_{role}.json'), 'w'), indent=1)
for k in ('xrd', 'optical'):
    print(k); [print('  ', d) for d in out[k][:5]]
