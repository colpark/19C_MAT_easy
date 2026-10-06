#!/usr/bin/env python3
"""m0_crfeni.py (v4 Track D rank 1, skill M0 + rule M0 separability pilot): CrFeNi (Mendeley 10.17632/7d826s3mhf.1, CC BY 4.0).
Checks: (1) sample IDs: file name vs workbook header (anneal T in C, time, test temperature); (2) yield stress per specimen (yieldproc D1);
(3) separability: between-condition differences vs within-condition spread (pairs separated when |diff| > 2 combined SE, and one-way
ANOVA); (4) Hall-Petch plausibility against the authors' grain sizes from the deposit file names (A level: screen only, never a key).
Output trackD/m0_crfeni.json."""
import glob, json, os, re, sys
import numpy as np, openpyxl
from scipy import stats
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import yieldproc as Y
R = '/home/aid1/Documents/harbor/v4_host/trackD/crfeni'
def load(p):
    ws = openpyxl.load_workbook(p, read_only=True, data_only=True).worksheets[0]; rows = list(ws.iter_rows(values_only=True))
    h = {r[0]: r[1] for r in rows[:5]}; data = np.array([r[:3] for r in rows[7:] if r[0] is not None and r[1] is not None], float)
    return h, data
out = {'specimens': [], 'id_mismatch': []}
for kind in ('Compression', 'Tensile'):
    for p in sorted(glob.glob(f'{R}/CrFeNi_{kind}_Tests/*/*.xlsx')):
        folder = p.split('/')[-2]; fn = os.path.basename(p); m = re.match(r'CrFeNi_([\d.]+)mm_(\d+)K_(\d+)min_(\d+)K_(\d+)', fn)
        h, d = load(p); name = str(h.get('Name'))
        hm = re.search(r'(\d+)°C_(\d+)min', name); hT = re.search(r'_(RT|-?\d+°?C?|\d+K)_', name)
        rec = {'kind': kind, 'file': fn, 'folder': folder, 'cond': f'{m[1]}mm_{m[2]}K_{m[3]}min', 'test_T_file': int(m[4]), 'test_T_folder': int(folder[:-1]), 'header': name}
        if m[4] != folder[:-1]: out['id_mismatch'].append({'file': fn, 'why': f'folder {folder} vs file name {m[4]}K'})
        if hm and (int(hm[1]) + 273 != int(m[2]) or int(hm[2]) != int(m[3])): out['id_mismatch'].append({'file': fn, 'why': f'header {hm[0]} vs file {m[2]}K {m[3]}min'})
        if kind == 'Compression':
            s, e = Y.stress_strain(d[:, 1], d[:, 2], float(h['Diameter']), float(h['Gage length'])); r = Y.yield_02(s, e)
        else:
            rec['header_fields'] = {k: h[k] for k in list(h)[:5]}; r = None
        rec['ys'] = r['ys'] if r else None; rec['E_app'] = r['E_app'] if r else None; out['specimens'].append(rec)
C = [x for x in out['specimens'] if x['kind'] == 'Compression' and x['test_T_file'] == 293 and x['ys']]
conds = sorted({x['cond'] for x in C}); g = {c: [x['ys'] for x in C if x['cond'] == c] for c in conds}
summ = {c: {'n': len(v), 'mean': float(np.mean(v)), 'sd': float(np.std(v, ddof=1)) if len(v) > 1 else None} for c, v in g.items()}
pairs = []; cs = sorted(conds, key=lambda c: summ[c]['mean'])
for i in range(len(cs)):
    for j in range(i + 1, len(cs)):
        a, b = summ[cs[i]], summ[cs[j]]; se = np.sqrt(a['sd'] ** 2 / a['n'] + b['sd'] ** 2 / b['n']); pairs.append({'a': cs[i], 'b': cs[j], 'diff': b['mean'] - a['mean'], 'se': float(se), 'sep': bool(b['mean'] - a['mean'] > 2 * se)})
adj = [p for p in pairs if cs.index(p['b']) == cs.index(p['a']) + 1]
F = stats.f_oneway(*g.values())
dA = {}
for c in conds:
    fs = glob.glob(f"{R}/CrFeNi_{c}/*d=*"); vals = sorted({int(re.search(r'd=(\d+)', f)[1]) for f in fs}); dA[c] = vals
hp = [(dA[c][0], summ[c]['mean']) for c in conds if len(dA[c]) == 1]
if len(hp) >= 3:
    x = np.array([1 / np.sqrt(d) for d, _ in hp]); y = np.array([s for _, s in hp]); k, s0 = np.polyfit(x, y, 1); rr = stats.pearsonr(x, y)
    hpres = {'points': hp, 'k_MPa_um05': float(k), 'sigma0': float(s0), 'r': float(rr[0]), 'p': float(rr[1])}
else: hpres = None
out['293K_compression'] = {'summary': summ, 'pairs_separated': sum(p['sep'] for p in pairs), 'pairs': len(pairs), 'adjacent': adj, 'anova_F': float(F.statistic), 'anova_p': float(F.pvalue),
                           'authors_d_um (A, screen only)': dA, 'hall_petch_vs_author_d': hpres}
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'm0_crfeni.json'), 'w'), indent=1, default=str)
print(json.dumps({k: out['293K_compression'][k] for k in ('summary', 'pairs_separated', 'pairs', 'anova_p', 'authors_d_um (A, screen only)', 'hall_petch_vs_author_d')}, indent=0, default=str))
print('adjacent', [(p['a'], p['b'], round(p['diff'], 1), round(p['se'], 1), p['sep']) for p in adj]); print('id_mismatch', out['id_mismatch'])
