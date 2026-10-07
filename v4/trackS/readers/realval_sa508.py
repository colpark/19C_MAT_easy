#!/usr/bin/env python3
"""realval_sa508.py (S5a held-out real evidence): sa508_op.py on every raw indent of the three SA508 records against the authors'
per-array 'Avg. HARDNESS' in each 'Hardness Profile.csv' (author instrument output computed with their calibrated area function: level
A, validation only, never a key; its bias is reported). Arrays are matched by set number = traverse position (file '<cond>-NN-<row>-<zone>'
-> 'Set NN'); the zone label in the file name must equal the profile's Region.
Gates (frozen with this file, before the comparison): Spearman rho between our array-mean H and the authors' >= 0.90 over all arrays;
the per-array ratio ours/authors has CV <= 0.05 (constant bias); >= 95 % of indents read ok. The mean ratio is reported as the bias of
the ideal area function against the authors' calibration (no correction is applied to keys).
Writes realval_sa508.json and v4_host/trackS/sa508_ebw/hardness_arrays.csv (condition, position, zone, n, H mean, SD, authors' H)."""
import csv, glob, json, os, re, sys
import numpy as np
from scipy.stats import spearmanr
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); import sa508_op as R
F = '/home/aid1/Documents/harbor/v4_host/trackS/sa508_ebw/files'
REC = {'j2f2dxmd5m': 'forged_PWHT', '58xvm8wt92': 'PMHIP_PWHT', 'x8x628h3gs': 'PMHIP_SQNT'}
rx = re.compile(r'-(\d{2})-([BT][12])-((?:[RL]-)?(?:BM|HAZ)|FZ)\.csv$')
arrays = {}; n_ok = n_all = 0; fails = []
for rec, cond in REC.items():
    prof = glob.glob(f'{F}/{rec}/*/*Nanoindentation Data/*Profile.csv')[0]
    auth = {}
    with open(prof, encoding='utf-8-sig') as fh:
        for row in csv.DictReader(fh):
            m = re.match(r'Set (\d+)', row['Test'] or '')
            if m: auth[int(m.group(1))] = (float(row['Avg. HARDNESS']), (row.get('Region') or row.get('Position') or '').strip(), float(row['Avg. ELASTIC MODULUS']))
    for f in sorted(glob.glob(f'{F}/{rec}/*/*Nanoindentation Data/*.csv')):
        m = rx.search(f)
        if not m: continue
        pos, rowid, zone = int(m.group(1)), m.group(2), m.group(3); r = R.read(f); n_all += 1
        if not r['ok']: fails.append((os.path.basename(f), r.get('why'))); continue
        n_ok += 1; arrays.setdefault((cond, pos, zone), []).append(r)
out = []; ours = []; theirs = []; zone_mismatch = []
for (cond, pos, zone), rs in sorted(arrays.items()):
    out.append({'condition': cond, 'position': pos, 'zone': zone, 'n': len(rs), 'H_GPa': float(np.mean([x['H_GPa'] for x in rs])),
                'H_sd': float(np.std([x['H_GPa'] for x in rs], ddof=1)) if len(rs) > 1 else float('nan'), 'Er_GPa': float(np.mean([x['Er_GPa'] for x in rs]))})
# attach authors' values
for o in out:
    rec = [k for k, v in REC.items() if v == o['condition']][0]
    prof = glob.glob(f'{F}/{rec}/*/*Nanoindentation Data/*Profile.csv')[0]
    with open(prof, encoding='utf-8-sig') as fh:
        for row in csv.DictReader(fh):
            if (row['Test'] or '').strip() == f"Set {o['position']}":
                o['authors_H_GPa'] = float(row['Avg. HARDNESS']); o['authors_E_GPa'] = float(row['Avg. ELASTIC MODULUS']); o['authors_region'] = (row.get('Region') or row.get('Position') or '').strip()
    if o.get('authors_region') and o['authors_region'] != o['zone']: zone_mismatch.append((o['condition'], o['position'], o['zone'], o['authors_region']))
pairs = [o for o in out if 'authors_H_GPa' in o]
x = np.array([o['H_GPa'] for o in pairs]); y = np.array([o['authors_H_GPa'] for o in pairs]); rat = x / y
res = {'indents': n_all, 'indents_ok': n_ok, 'ok_frac': n_ok / max(n_all, 1), 'failures': fails[:20], 'arrays': len(out), 'arrays_with_authors': len(pairs),
       'spearman': float(spearmanr(x, y)[0]), 'ratio_mean': float(rat.mean()), 'ratio_cv': float(rat.std() / rat.mean()),
       'ratio_by_condition': {c: float(np.mean([o['H_GPa'] / o['authors_H_GPa'] for o in pairs if o['condition'] == c])) for c in REC.values()},
       'zone_mismatches': zone_mismatch}
res['gates'] = {'spearman_ge_0.90': res['spearman'] >= 0.90, 'ratio_cv_le_0.05': res['ratio_cv'] <= 0.05, 'ok_ge_0.95': res['ok_frac'] >= 0.95}
res['pass'] = all(res['gates'].values())
json.dump(res, open(os.path.join(HERE, 'realval_sa508.json'), 'w'), indent=1)
with open('/home/aid1/Documents/harbor/v4_host/trackS/sa508_ebw/hardness_arrays.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=['condition', 'position', 'zone', 'n', 'H_GPa', 'H_sd', 'Er_GPa', 'authors_H_GPa', 'authors_E_GPa', 'authors_region'])
    w.writeheader(); [w.writerow({k: o.get(k) for k in w.fieldnames}) for o in out]
print(json.dumps({k: v for k, v in res.items() if k not in ('failures',)}, indent=0))
