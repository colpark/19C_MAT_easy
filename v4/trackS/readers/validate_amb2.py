#!/usr/bin/env python3
"""validate_amb2.py (S4a-2, rule I7): fresh synthetic seeds (dev seeds were 100-107). Gates frozen with the reader (S4a2):
  depth      seeds 200-209, depth 60-260 um (deep pools get a stitched bottom field): >= 9 of 10 within 10 %;
  censoring  seeds 300-304, deep pools (230-260 um) with no bottom field: every one flagged censored;
  width      reported only. Output validate_amb2.json."""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import synth_amb2 as S, measure_amb2 as M
from multiprocessing import Pool
def one(seed):
    rng = np.random.default_rng(seed)
    s = S.section(rng) if seed < 300 else S.section(rng, D=rng.uniform(230, 260), no_bottom=True)
    r = M.measure_track(s['top'], s['bottom'], s['step'])
    return {'seed': seed, 'truth': s['truth'], 'bottom': s['bottom'] is not None, **{k: r[k] for k in ('depth_um', 'width_um', 'censored', 'stitched', 'found')},
            'ratio': r['depth_um'] / s['truth']['depth_um']}
if __name__ == '__main__':
    with Pool(10) as P: rows = P.map(one, list(range(200, 210)) + list(range(300, 305)))
    dep = [r for r in rows if r['seed'] < 300]; cen = [r for r in rows if r['seed'] >= 300]
    res = {'rows': rows, 'depth_within10': sum(abs(r['ratio'] - 1) <= 0.10 and not r['censored'] for r in dep), 'censor_flagged': sum(r['censored'] for r in cen), 'censor_n': len(cen)}
    res['gates'] = {'depth': res['depth_within10'] >= 9, 'censoring': res['censor_flagged'] == res['censor_n']}
    json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'validate_amb2.json'), 'w'), indent=1, default=float)
    print(json.dumps({k: v for k, v in res.items() if k != 'rows'})); [print(r['seed'], round(r['truth']['depth_um']), round(r['ratio'], 2), r['censored'], r['bottom'], r['stitched']) for r in rows]
