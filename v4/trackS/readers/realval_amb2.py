#!/usr/bin/env python3
"""realval_amb2.py (S4a-2 held-out real evidence; frozen before running): the 21 single-track top fields (+ the case-1.1 bottom
fields, stitched) against NIST Table 4 optical depths (second instrument; A-level author values, n = 6 per case). Gate (round-2 prompt):
>= 5 of 7 cases with our mean depth within max(10 %, 2 NIST SD) AND Spearman >= 0.9 between our case means and the Table 4 means.
Censored tracks are excluded from case means and listed. I4 disclosure: Table 4 means were seen when S4a failed (round 1).
Writes realval_amb2.json and the pilot table pilot_amb2.csv (condition, order, unit, sub, value) for separability_s.py."""
import csv, glob, json, os, re, sys
import numpy as np
from scipy.stats import spearmanr
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); import amb2_reader as R, measure_amb2 as M
D = sys.argv[1] if len(sys.argv) > 1 else '/home/aid1/Documents/harbor/v4_host/trackS/amb2022_03/files'
RULES = json.load(open(sys.argv[2] if len(sys.argv) > 2 else '/home/aid1/Documents/harbor/v4/trackS/joinrules/amb2022_03.json')); TM = RULES['maps']['track']; ORDER = RULES['order']['case']
NIST = {'0': (139.7, 1.9), '1.1': (227.2, 3.2), '1.2': (102.4, 1.1), '2.1': (109.7, 1.7), '2.2': (176.5, 2.6), '3.1': (166.1, 2.0), '3.2': (116.9, 1.2)}
def one(path):
    b = os.path.basename(path); m = re.search(r'Map Data \d+[_-](L?-?\d{2,3})\.ctf$', b)
    if not m: return None
    tr = m.group(1); meta = TM.get(tr) or TM.get('L' + tr); ph, eul, bc, st = R.read_ctf(path); bottom = None
    bf = glob.glob(os.path.join(os.path.dirname(path), f'*{tr} bottom.ctf')) or glob.glob(os.path.join(D, '**', f'*{tr} bottom.ctf'), recursive=True)
    if bf:
        pb, eb, _, _ = R.read_ctf(bf[0]); bottom = (pb, eb)
    r = M.measure_track((ph, eul), bottom, st)
    return {'track': tr, 'case': meta['case'], 'rep': meta['rep'], 'file': b, 'bottom': bool(bf), **{k: r[k] for k in ('depth_um', 'width_um', 'censored', 'stitched', 'found', 'stitch')}}
if __name__ == '__main__':
    from multiprocessing import Pool
    files = sorted(glob.glob(os.path.join(D, '**', '*Site*Map Data*.ctf'), recursive=True)); files = [f for f in files if 'bottom' not in f]
    with Pool(8) as P: rows = [r for r in P.map(one, files) if r]
    per = {}
    for c, (m, sd) in NIST.items():
        v = [r['depth_um'] for r in rows if r['case'] == c and r['found'] and not r['censored']]
        mm = float(np.mean(v)) if v else None
        per[c] = {'n': len(v), 'ours_mean': mm, 'ours_sd': float(np.std(v, ddof=1)) if len(v) > 1 else None, 'nist': m, 'nist_sd': sd, 'tol': max(0.1 * m, 2 * sd),
                  'within': bool(mm is not None and abs(mm - m) <= max(0.1 * m, 2 * sd))}
    have = [c for c in per if per[c]['ours_mean'] is not None]
    rho = float(spearmanr([per[c]['ours_mean'] for c in have], [per[c]['nist'] for c in have])[0]) if len(have) >= 3 else None
    res = {'tracks': rows, 'per_case': per, 'cases_within': sum(per[c]['within'] for c in per), 'spearman': rho, 'censored': [r['track'] for r in rows if r['censored']]}
    res['gates'] = {'depth': res['cases_within'] >= 5, 'order': rho is not None and rho >= 0.9}
    json.dump(res, open(os.path.join(HERE, 'realval_amb2.json'), 'w'), indent=1, default=float)
    with open(os.path.join(HERE, 'pilot_amb2.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['condition', 'order', 'unit', 'sub', 'value']); w.writeheader()
        for r in rows:
            if r['found'] and not r['censored']: w.writerow({'condition': r['case'], 'order': ORDER.index(r['case']), 'unit': r['track'], 'sub': '', 'value': r['depth_um']})
    print(json.dumps({k: res[k] for k in ('cases_within', 'spearman', 'censored', 'gates')}))
    for c, v in per.items(): print(c, v)
    for r in sorted(rows, key=lambda r: (r['case'], r['rep'])): print(r['case'], r['rep'], r['track'], round(r['depth_um'], 1), round(r['width_um'], 1), 'censored' if r['censored'] else '', 'stitched' if r['stitched'] else '')
