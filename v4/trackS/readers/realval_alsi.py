#!/usr/bin/env python3
"""realval_alsi.py (S4d held-out real evidence, EXPLORATORY: S4d failed its synthetic constant-bias gate, slope -0.156 > 0.10).
Frozen reader on every 5000x field; per-set mean of the field means against the authors' per-set mean cell size (cell_size_<set>.csv:
author segmentation, A level). Reports Spearman across sets and the per-set ratio (bias) with its CV. Writes realval_alsi.json and the
microstructure pilot table pilot_alsi_cells.csv (condition = set, order = rank of P/v (LED), unit = image (optimistic), value)."""
import csv, glob, json, os, re, sys, warnings
import numpy as np
from scipy.stats import spearmanr
warnings.filterwarnings('ignore')
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); import alsi_reader as R
H = '/home/aid1/Documents/harbor/v4_host/trackS/alsi10mg_luo2024'; RULES = json.load(open('/home/aid1/Documents/harbor/v4/trackS/joinrules/alsi10mg_luo2024.json'))
SETM = RULES['maps']['set']
def one(f):
    import warnings; warnings.filterwarnings('ignore')
    m = re.search(r'_Sample(\d+)-([a-d])\.tif$', f); r = R.measure(f); return {'set': m.group(1), 'field': m.group(2), 'file': os.path.basename(f), **r}
if __name__ == '__main__':
    from multiprocessing import Pool
    files = sorted(glob.glob(f'{H}/extracted/**/*_Sample*-[abcd].tif', recursive=True))
    with Pool(16) as P: rows = P.map(one, files)
    sets = sorted({r['set'] for r in rows}, key=int); per = {}
    for s in sets:
        ours = float(np.mean([r['d_mean_um'] for r in rows if r['set'] == s]))
        auth = np.loadtxt(glob.glob(f'{H}/extracted/Grain-cell morphology/**/AlSi10Mg cell/raw data/cell size/cell_size_{s}.csv', recursive=True)[0], ndmin=1)
        per[s] = {'ours_um': ours, 'authors_um': float(np.mean(auth)), 'ratio': ours / float(np.mean(auth)), 'LED': float(SETM[s]['LED_J_mm']), 'n_fields': sum(r['set'] == s for r in rows)}
    rho = float(spearmanr([per[s]['ours_um'] for s in sets], [per[s]['authors_um'] for s in sets])[0]); rat = np.array([per[s]['ratio'] for s in sets])
    res = {'exploratory': True, 'per_set': per, 'spearman': rho, 'ratio_mean': float(rat.mean()), 'ratio_cv': float(rat.std() / rat.mean()), 'n_fields': len(rows),
           'gates_if_validated': {'spearman_ge_0.9': rho >= 0.9}}
    json.dump(res, open(os.path.join(HERE, 'realval_alsi.json'), 'w'), indent=1)
    order = sorted(sets, key=lambda s: per[s]['LED'])
    with open(f'{H}/pilot_alsi_cells.csv', 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['condition', 'order', 'unit', 'sub', 'value']); w.writeheader()
        for r in rows: w.writerow({'condition': r['set'], 'order': order.index(r['set']), 'unit': f"{r['set']}-{r['field']}", 'sub': '', 'value': r['d_mean_um']})
    print(json.dumps({k: res[k] for k in ('spearman', 'ratio_mean', 'ratio_cv', 'n_fields')}))
    for s in order: print(s, round(per[s]['LED'], 3), round(per[s]['ours_um'], 3), round(per[s]['authors_um'], 3), round(per[s]['ratio'], 2))
