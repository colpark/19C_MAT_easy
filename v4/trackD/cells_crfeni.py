#!/usr/bin/env python3
"""cells_crfeni.py (v4 Track D, skill M2 evidence): cells for CrFeNi (Mendeley 10.17632/7d826s3mhf.1, CC BY 4.0) from the raw workbooks
and our grain-size reader. No author-derived number enters a cell.
  compression (every workbook): engineering stress F / (pi D^2 / 4), crosshead strain d / L0 (gauge length from the header);
    ys = 0.2 % offset yield (yieldproc D1; procedure-defined on crosshead strain); s10 = stress at crosshead strain 0.10 on the loading branch (D5b: unloading
    segments excluded; None when loading stops earlier).
  tension: the deposit records crosshead displacement without a gauge length and the extensometer in volts without a calibration, so
    tension strain and tension yield are D gaps (logged). uts = F_max / (thickness x width) for specimens that fractured: name contains
    'Bruch' and the force maximum precedes the end of the record (x at F_max < 0.99 x_max). Test temperature from the folder and the
    workbook header (V4-E11), never from the 373 K file names.
  grain size: grainsize.py (D3) means per condition from grains_crfeni.json (methods I and II); 1573 K excluded (JPG, scale bar unverified).
Writes trackD/cells_crfeni.jsonl (values) and v4_host/trackD/crfeni_curves.npz (curves for rendering; host only)."""
import glob, json, os, re, sys
import numpy as np, openpyxl
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import yieldproc as Y
D = os.path.dirname(os.path.abspath(__file__)); R = '/home/aid1/Documents/harbor/v4_host/trackD/crfeni'
def rows_of(p): return list(openpyxl.load_workbook(p, read_only=True, data_only=True).worksheets[0].iter_rows(values_only=True))
def cond_of(fn): m = re.match(r'CrFeNi_([\d.]+mm_\d+K_\d+min)_', fn); return m[1]
def main():
    cells = []; curves = {}
    for p in sorted(glob.glob(f'{R}/CrFeNi_Compression_Tests/*/*.xlsx')):
        rr = rows_of(p); h = {r[0]: r[1] for r in rr[:5]}; d = np.array([r[:3] for r in rr[7:] if r[0] is not None and r[1] is not None and r[2] is not None], float)
        fn = os.path.basename(p); T = int(p.split('/')[-2][:-1]); spec = int(re.search(r'_(\d+)\.(?:XLS|xls)', fn)[1])
        s, e = Y.stress_strain(d[:, 1], d[:, 2], float(h['Diameter']), float(h['Gage length'])); r = Y.yield_02(s, e)
        top = int(np.argmax(e)); el, sl = e[:top + 1], s[:top + 1]; el = np.maximum.accumulate(el)   # D5b: loading branch only (unloaded tests)
        s10 = float(np.interp(0.10, el, sl)) if el.max() >= 0.10 else None
        key = f'C|{cond_of(fn)}|{T}|{spec}'; curves[key] = np.vstack([e[::4], s[::4]])
        base = {'entity': cond_of(fn), 'test': 'compression', 'T_K': T, 'specimen': spec, 'file': fn, 'header': h.get('Name'), 'level': 'M'}
        if r: cells.append(dict(base, quantity='ys', value=r['ys'], unit='MPa', procedure='yieldproc D1 (0.2 % offset, crosshead strain)'))
        if s10: cells.append(dict(base, quantity='s10', value=s10, unit='MPa', procedure='stress at crosshead strain 0.10'))
    for p in sorted(glob.glob(f'{R}/CrFeNi_Tensile_Tests/*/*.xlsx')):
        rr = rows_of(p); h = {str(r[0]): r[1] for r in rr[:3]}; th = h.get('Thickness', h.get('Probendicke')); w = h.get('Width', h.get('Probenbreite')); name = str(h.get('Name', h.get('Probenbezeichnung')))
        d = np.array([r[:4] for r in rr[5:] if r[1] is not None and r[3] is not None], float); F, x = d[:, 1], d[:, 3]; i = int(F.argmax())
        fn = os.path.basename(p); T = int(p.split('/')[-2][:-1]); spec = int(re.search(r'_(\d+)\.(?:XLS|xls)', fn)[1]); s = F / (th * w)
        curves[f'T|{cond_of(fn)}|{T}|{spec}'] = np.vstack([x[::4], s[::4]])
        frac = 'Bruch' in name and x[i] < 0.99 * x.max()
        base = {'entity': cond_of(fn), 'test': 'tension', 'T_K': T, 'specimen': spec, 'file': fn, 'header': name, 'level': 'M', 'fractured': bool(frac)}
        cells.append(dict(base, quantity='smax', value=float(s.max()), unit='MPa', procedure='F_max / (thickness x width)'))
        if frac: cells.append(dict(base, quantity='uts', value=float(s.max()), unit='MPa', procedure='F_max / (thickness x width), fractured specimens'))
    g = json.load(open(f'{D}/grains_crfeni.json'))['conditions']
    for c, v in g.items():
        for m in ('I', 'II'):
            cells.append({'entity': c, 'test': 'micrograph', 'T_K': None, 'specimen': None, 'quantity': f'grain_{m}', 'value': v[f'{m}_um'], 'u': v[f'{m}_se'], 'n': v['n'], 'unit': 'um', 'level': 'M',
                          'procedure': f'grainsize D3 method {m} (mean over images; u = SE)'})
    with open(f'{D}/cells_crfeni.jsonl', 'w') as f:
        for c in cells: f.write(json.dumps(c) + '\n')
    np.savez_compressed('/home/aid1/Documents/harbor/v4_host/trackD/crfeni_curves.npz', **{k.replace('|', '__'): v for k, v in curves.items()})
    from collections import Counter
    print(len(cells), Counter((c['test'], c['quantity']) for c in cells))
if __name__ == '__main__':
    main()
