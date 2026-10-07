#!/usr/bin/env python3
"""curves_alsi60.py (S4e-60, all 60 sets per David 2026-10-07; same procedures as curves_alsi.py): per specimen (group workbook g = replicate 1-3, set 1-60) the maximum engineering stress (UTS, M level)
and the 0.2 % offset yield on the author DIC strain (yieldproc D1c; A level because the strain is author-computed). Writes
curves_alsi.json and the property pilot table pilot_alsi_uts.csv (condition = set, order = rank of P/v, unit = specimen)."""
import csv, glob, json, os, sys
import numpy as np, openpyxl
sys.path.insert(0, '/home/aid1/Documents/harbor/v4/trackD'); import yieldproc as Y
H = '/home/aid1/Documents/harbor/v4_host/trackS/alsi10mg_luo2024'; RULES = json.load(open('/home/aid1/Documents/harbor/v4/trackS/joinrules/alsi10mg_luo2024.json')); SETM = RULES['maps']['set']
rows = []; SKIP = []   # S4e-b: headers that are not set numbers are skipped and logged
for f in sorted(glob.glob(f'{H}/extracted/Stress-strain curves/**/*group*.xlsx', recursive=True)):
    grp = int(f.split('group')[-1].split('.')[0]); data = list(openpyxl.load_workbook(f, read_only=True, data_only=True).worksheets[0].iter_rows(values_only=True))
    ids = data[0]
    for j in range(0, len(ids), 2):
        try:
            sid = int(float(str(ids[j]).strip().strip('`')))
        except ValueError:
            SKIP.append({'file': os.path.basename(f), 'column': j, 'header': str(ids[j])}); continue
        if sid > 60: continue
        ids_j = sid
        num = lambda x: isinstance(x, (int, float)) and not isinstance(x, bool)   # S4e-c: cells such as 'No data' are skipped
        pts = [(r[j], r[j + 1]) for r in data[2:] if len(r) > j + 1 and num(r[j]) and num(r[j + 1])]
        if not pts:
            SKIP.append({'file': os.path.basename(f), 'column': j, 'header': str(ids[j]), 'why': 'no numeric data'}); continue
        e = np.array([p_[0] for p_ in pts], float); s = np.array([p_[1] for p_ in pts], float)
        if len(s) < 20: continue
        y = Y.yield_02(s, e); rows.append({'set': str(ids_j), 'replicate': grp, 'uts_MPa': float(s.max()), 'yield_MPa_A': y['ys'] if y else None, 'E_app_GPa': y['E_app'] / 1000 if y else None, 'n_points': len(s)})
json.dump({'specimens': rows, 'skipped_headers': SKIP}, open(f'{H}/curves_alsi60.json', 'w'), indent=1); print('skipped headers', SKIP)
order = sorted(SETM, key=lambda s: (float(SETM[s]['VED_J_mm3']), int(s)))   # 60 sets: ordered by VED (S2j-alsi-60)
with open(f'{H}/pilot_alsi60_uts.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=['condition', 'order', 'unit', 'sub', 'value']); w.writeheader()
    for r in rows: w.writerow({'condition': r['set'], 'order': order.index(r['set']), 'unit': f"{r['set']}-g{r['replicate']}", 'sub': '', 'value': r['uts_MPa']})
pt = list(openpyxl.load_workbook(f'{H}/files/AlSi10Mg PSP feature table.xlsx', read_only=True, data_only=True).worksheets[0].iter_rows(values_only=True))
auth = {str(int(r[0])): {'uts': r[38], 'ys': r[40]} for r in pt[4:] if isinstance(r[0], (int, float)) and 1 <= r[0] <= 60}
out = []
for s in order:
    v = [r for r in rows if r['set'] == s]
    out.append({'set': s, 'n': len(v), 'uts_ours': float(np.mean([r['uts_MPa'] for r in v])), 'uts_auth': auth[s]['uts'], 'ys_ours_A': float(np.mean([r['yield_MPa_A'] for r in v if r['yield_MPa_A']])) if any(r['yield_MPa_A'] for r in v) else None, 'ys_auth': auth[s]['ys']})
json.dump(out, open(f'{H}/curves_alsi60_vs_authors.json', 'w'), indent=1)
from scipy.stats import spearmanr
u = np.array([[o['uts_ours'], o['uts_auth']] for o in out]); yv = np.array([[o['ys_ours_A'], o['ys_auth']] for o in out if o['ys_ours_A']])
print('specimens', len(rows), '| UTS ours/authors mean ratio', round(float(np.mean(u[:, 0] / u[:, 1])), 3), 'max |diff|', round(float(np.max(np.abs(u[:, 0] - u[:, 1]))), 1), '| yield ours/authors ratio', round(float(np.mean(yv[:, 0] / yv[:, 1])), 3), 'spearman', round(float(spearmanr(yv[:, 0], yv[:, 1])[0]), 3))
