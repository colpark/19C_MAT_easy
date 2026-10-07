#!/usr/bin/env python3
"""validate_alsi.py (S4d, rule I7): fresh synthetic fields, seeds 200-209 (dev 100-115), cell sizes 0.4-1.6 um. Gates (frozen with the
reader): >= 9 of 10 fields with reader/truth within 10 % after dividing by the frozen dev bias B0 (alsi_reader.measure does this), and a
constant bias: |slope of (reader/truth) vs ln(truth)| <= 0.10. Output validate_alsi.json."""
import json, os, sys, warnings
import numpy as np
warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import synth_alsi as S, alsi_reader as R
from multiprocessing import Pool
def one(seed):
    import warnings; warnings.filterwarnings('ignore')
    img, tr = S.field(np.random.default_rng(seed)); r = R.measure(img, R.PX_NM); return {'seed': seed, 'truth_um': tr['d_mean_um'], 'reader_um': r['d_mean_um'], 'ratio': r['d_mean_um'] / tr['d_mean_um']}
if __name__ == '__main__':
    with Pool(10) as P: rows = P.map(one, range(200, 210))
    rat = np.array([r['ratio'] for r in rows]); t = np.log([r['truth_um'] for r in rows])
    res = {'rows': rows, 'within10': int(np.sum(np.abs(rat - 1) <= 0.10)), 'slope': float(np.polyfit(t, rat, 1)[0]), 'median_ratio_after_B0': float(np.median(rat))}
    res['gates'] = {'within': res['within10'] >= 9, 'constant_bias': abs(res['slope']) <= 0.10}
    json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'validate_alsi.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != 'rows'})); [print(r['seed'], round(r['truth_um'], 2), round(r['ratio'], 2)) for r in rows]
