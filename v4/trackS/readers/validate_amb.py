#!/usr/bin/env python3
"""validate_amb.py (S4a, rule I7): fresh synthetic sections, seeds 200-209 (dev seeds 100-107). Gates frozen with the reader:
depth and width each within +-10 % of truth in >= 9 of 10 sections (skill M2: 9 of 10 within the stated tolerance).
Held-out real evidence (NIST Table 4 depths, optical sections mds2-2718) runs only if both synthetic gates pass. Output validate_amb.json."""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import amb_reader as A, synth_amb as S
from multiprocessing import Pool
def one(seed):
    rng = np.random.default_rng(seed); ph, eul, st, tr = S.section(rng); r = A.measure(ph, eul, st)
    return {'seed': seed, 'truth': tr, 'read': r, 'depth_ratio': r['depth_um'] / tr['depth_um'], 'width_ratio': r['width_um'] / tr['width_um']}
if __name__ == '__main__':
    with Pool(10) as P: rows = P.map(one, range(200, 210))
    dp = sum(abs(r['depth_ratio'] - 1) <= 0.10 for r in rows); wp = sum(abs(r['width_ratio'] - 1) <= 0.10 for r in rows)
    res = {'rows': rows, 'depth_within10': dp, 'width_within10': wp, 'gates': {'depth': dp >= 9, 'width': wp >= 9}}
    json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'validate_amb.json'), 'w'), indent=1, default=float)
    print({k: v for k, v in res.items() if k != 'rows'}); print([(round(r['depth_ratio'], 2), round(r['width_ratio'], 2)) for r in rows])
