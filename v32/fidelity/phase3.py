#!/usr/bin/env python3
"""fidelity/phase3.py (Phase 3 gate, a test set: no tuning). Frozen readers (readers.py, F5) on S030 main-text panels; the same features
computed from the authors' Source Data (41467_2026_76588_MOESM4_ESM.xlsx); pass/fail per feature type with the user's gate: in-scope
coverage >= 80%, >= 90% of reads within 2u, |mean error/u| <= 0.5.
Inputs per panel (logged here, the same kinds of inputs 5D uses): legend swatch positions where row grouping is ambiguous; x_none on a
category (bar) axis; legend boxes (excluded from the data area; series colours sampled
from the legend rows, median of the most saturated swatch pixels), legend row -> Source Data column (the printed labels, which follow the
sheet order), printed tick values only if OCR calibration fails. Panels without a legend use the paper's palette sampled from the F3d/F4a
legends (same label -> same colour). Feature positions are fixed by rule before any read (FEATURES below), not chosen from results.
S001 (Zenodo source data does not match the published figures: ROC AUCs differ) and S021 (Source Data for supplementary figures only, no
v0.24 crops) are excluded; S013 has no retrievable Source Data file. usage: phase3.py -> fidelity/phase3_results.json, fidelity/PHASE3.md"""
import json, math, sys
import numpy as np
from PIL import Image
V32 = '/home/aid1/Documents/harbor/v32'; sys.path.insert(0, V32)
import readers as R
SRC = '/home/aid1/Documents/harbor/v32_host/fidelity/src/S030_41467_2026_76588_MOESM4_ESM.xlsx'; CROPS = '/home/aid1/Documents/harbor/v32_host/fidelity/S030/crops'
L7 = ['CaCl2', 'RL800@40%CaCl2', 'RL800@30%CaCl2', 'RL800@25%CaCl2', 'RL800@20%CaCl2', 'RL800@10%CaCl2', 'RL800']
PANELS = {
 'F3d': {'sheet': 'Fig. 3d', 'legends': [[115, 120, 275, 235]], 'rows': L7, 'kind': 'curve',
         'features': [('y_at_x', {'x': 300}), ('y_at_x', {'x': 500}), ('plateau', {'x_from': 720, 'x_to': 790})]},
 'F4a': {'sheet': 'Fig. 4a', 'legends': [[94, 22, 249, 60], [254, 72, 409, 162]], 'rows': L7, 'kind': 'curve', 'swatch': [(104, y) for y in (32, 50)] + [(264, y) for y in (80, 98, 116, 134, 152)],
         'features': [('y_at_x', {'x': 50}), ('y_at_x', {'x': 150}), ('plateau', {'x_from': 300, 'x_to': 350})]},
 'F4c': {'sheet': 'Fig. 4c', 'legends': [[301, 60, 418, 132]], 'rows': ['20°C 20% RH', '20°C 40% RH', '20°C 60% RH', '20°C 80% RH'], 'kind': 'curve',
         'features': [('y_at_x', {'x': 50}), ('y_at_x', {'x': 150}), ('plateau', {'x_from': 300, 'x_to': 350})]},
 'F4e': {'sheet': 'Fig. 4e', 'legends': [[264, 95, 384, 145]], 'rows': ['10°C 60% RH', '20°C 60% RH', '30°C 60% RH'], 'kind': 'curve',
         'features': [('y_at_x', {'x': 50}), ('y_at_x', {'x': 150}), ('plateau', {'x_from': 300, 'x_to': 350})]},
 'F4b': {'sheet': 'Fig. 4b', 'legends': [[280, 80, 425, 190]], 'rows': L7, 'kind': 'curve', 'swatch': [(290, y) for y in (91, 106, 121, 136, 151, 166, 180)], 'features': [('y_at_x', {'x': 25}), ('y_at_x', {'x': 50})]},
 'F4d': {'sheet': 'Fig. 4d', 'legends': [[242, 72, 352, 138]], 'rows': ['20°C 20% RH', '20°C 40% RH', '20°C 60% RH', '20°C 80% RH'], 'kind': 'curve',
         'features': [('y_at_x', {'x': 25}), ('y_at_x', {'x': 50})]},
 'F5a': {'sheet': 'Fig. 5a', 'legends': [[249, 195, 399, 280]], 'swatch': [(264, y) for y in (204, 219, 236, 252, 270)], 'rows': ['RL800', 'RL800@10% CaCl2', 'RL800@20% CaCl2', 'RL800@25% CaCl2', 'CaCl2'], 'kind': 'curve',
         'features': [('x_at_extremum', {'kind': 'min', 'window': [50, 220]}), ('y_at_extremum', {'kind': 'min', 'window': [50, 220]})]},
 'F3c': {'sheet': 'Fig. 3c', 'legends': [], 'palette_from': 'F3d', 'rows': ['RL800@40%CaCl2', 'RL800@30%CaCl2', 'RL800@25%CaCl2', 'RL800@20%CaCl2', 'RL800@10%CaCl2', 'RL800', 'CaCl2'],
         'kind': 'spectrum', 'y_none': True, 'exclude': [[300, 10, 434, 260]], 'features': [('peak_x', {'search': [15, 45], 'half': 1.5})]},
 'F5b': {'sheet': 'Fig. 5b', 'legends': [], 'palette_from': 'F3d', 'rows': ['RL800', 'RL800@10% CaCl2', 'RL800@20% CaCl2', 'RL800@25% CaCl2', 'CaCl2'], 'kind': 'bar', 'x_none': True, 'bar_x': [115, 183, 250, 317, 383],
         'features': [('bar_top', {'index': 0})]},
}
norm = lambda s: str(s).replace(' ', '').replace('CaCl₂', 'CaCl2')

def sheet_series(name):
    import openpyxl
    ws = openpyxl.load_workbook(SRC, read_only=True, data_only=True)[name]; rows = list(ws.iter_rows(values_only=True)); hdr = rows[0]
    f = lambda v: float(v) if isinstance(v, (int, float)) or (isinstance(v, str) and v.replace('.', '', 1).replace('-', '', 1).isdigit()) else np.nan
    out = {}
    if name == 'Fig. 5b':
        for j, h in enumerate(hdr): out[norm(h)] = np.array([f(r[j]) for r in rows[2:] if j < len(r)])
        return out
    for j in range(0, len(hdr), 2):
        if hdr[j] is None: continue
        x = np.array([f(r[j]) if j < len(r) else np.nan for r in rows[2:]]); y = np.array([f(r[j + 1]) if j + 1 < len(r) else np.nan for r in rows[2:]])
        if np.isnan(x).all():   # Fig. 3d: temperature column empty -> not usable without x
            out[norm(hdr[j])] = None; continue
        ok = ~np.isnan(x) & ~np.isnan(y); out[norm(hdr[j])] = (x[ok], y[ok])
    return out

def legend_colours(rgb, box, n):
    """n legend rows top to bottom: median colour of the most saturated swatch pixels in each row (left 40% of the box)."""
    x0, y0, x1, y1 = box; sub = rgb[y0:y1, x0:x0 + int(0.4 * (x1 - x0))].astype(float); sat = sub.max(2) - sub.min(2)
    rows = np.nonzero((sat > 45).sum(1) >= 2)[0]
    if not len(rows): return []
    groups = [[rows[0]]]
    for r in rows[1:]:
        (groups[-1].append(r) if r - groups[-1][-1] <= 2 else groups.append([r]))
    out = []
    for g in groups:
        px = sub[g[0]:g[-1] + 1].reshape(-1, 3); s = px.max(1) - px.min(1); px = px[s >= np.percentile(s, 75)]
        out.append([int(v) for v in np.median(px, 0)])
    return out

def truth(feat, args, xy):
    x, y = xy; o = np.argsort(x); x, y = x[o], y[o]
    if feat == 'y_at_x': return float(np.interp(args['x'], x, y)) if x[0] <= args['x'] <= x[-1] else None
    if feat == 'plateau': m = (x >= args['x_from']) & (x <= args['x_to']); return float(y[m].mean()) if m.sum() >= 3 else None
    if feat in ('x_at_extremum', 'y_at_extremum'):
        m = (x >= args['window'][0]) & (x <= args['window'][1]); i = int((y[m].argmin() if args['kind'] == 'min' else y[m].argmax()))
        return float(x[m][i] if feat == 'x_at_extremum' else y[m][i])
    if feat == 'peak_x':
        m = (x >= args['search'][0]) & (x <= args['search'][1]); return float(x[m][int(y[m].argmax())])

if __name__ == '__main__':
    res, palette, log = [], {}, {}
    order = ['F3d', 'F4a', 'F4c', 'F4e', 'F4b', 'F4d', 'F5a', 'F3c', 'F5b']
    for pid in order:
        P = PANELS[pid]; rgb = np.asarray(Image.open(f'{CROPS}/{pid}.jpg').convert('RGB')); src = sheet_series(P['sheet'])
        if P.get('bar_x'):   # bar colour: most saturated pixels near the top of the declared bar centre column (gradient-filled bars)
            cols = []
            for bx in P['bar_x']:
                col = rgb[:, bx - 3:bx + 4].astype(float); sat = col.max(2) - col.min(2); rows_ = np.nonzero((sat > 40).sum(1) >= 4)[0]
                px = col[rows_[:20]].reshape(-1, 3); s_ = px.max(1) - px.min(1); px = px[s_ >= np.percentile(s_, 70)]; cols.append([int(v) for v in np.median(px, 0)])
        elif P.get('swatch'):   # declared swatch positions (builder input, as in 5D): median of the most saturated pixels in a 26x7 box
            cols = []
            for (sx, sy) in P['swatch']:
                px = rgb[sy - 3:sy + 4, sx - 4:sx + 22].reshape(-1, 3).astype(float); sat = px.max(1) - px.min(1); px = px[sat >= np.percentile(sat, 80)]
                cols.append([int(v) for v in np.median(px, 0)])
        elif P['legends']:
            cols = [c for b in P['legends'] for c in legend_colours(rgb, b, 0)]
        else: cols = [palette.get(norm(r)) for r in P['rows']]
        if len(cols) != len(P['rows']):
            log[pid] = f'legend rows found {len(cols)} != {len(P["rows"])}: panel not read'; print(pid, log[pid])
            for r in P['rows']:
                for feat, args in P['features']: res.append({'panel': pid, 'series': r, 'feature': feat, 'args': args, 'truth': 1.0, 'status': 'legend rows'})
            continue
        for r, c in zip(P['rows'], cols): palette.setdefault(norm(r), c)
        pc = {'series': [{'label': r, 'value': norm(r), 'colour': c} for r, c in zip(P['rows'], cols)], 'exclude_boxes': P['legends'] + P.get('exclude', []), 'y_none': P.get('y_none', False), 'x_none': P.get('x_none', False)}
        try: Pn = R.Panel(f'{CROPS}/{pid}.jpg', pc); cal = {k: v for k, v in Pn.cal.items() if k != 'dark'}
        except Exception as e:   # every in-scope feature of the panel counts as a miss (a refusal included)
            log[pid] = f'calibration failed ({e})'; print(pid, log[pid])
            for r in P['rows']:
                s_ = src.get(norm(r))
                for feat, args in P['features']:
                    tv = (float(np.nanmean(s_)) if P['kind'] == 'bar' else truth(feat, args, s_)) if s_ is not None else None
                    res.append({'panel': pid, 'series': r, 'feature': feat, 'args': args, 'truth': tv, 'status': ('refused' if isinstance(e, R.Refused) else 'calibration failed') if tv is not None else 'no source value (out of scope)'})
            continue
        log[pid] = {'colours': dict(zip(P['rows'], cols)), 'calibration': str(cal)}
        for r in P['rows']:
            s = src.get(norm(r))
            for feat, args in P['features']:
                if P['kind'] == 'bar':
                    tv = float(np.nanmean(s)) if s is not None else None; ra = dict(args)
                elif s is None: tv = None; ra = dict(args)
                elif feat == 'peak_x':
                    tv = truth(feat, args, s); ra = {'window': [tv - args['half'], tv + args['half']]} if tv is not None else None
                else: tv = truth(feat, args, s); ra = dict(args)
                if tv is None: res.append({'panel': pid, 'series': r, 'feature': feat, 'args': args, 'truth': None, 'status': 'no source value (out of scope)'}); continue
                try: rd = R.read(Pn, {'type': feat, 'series': norm(r), 'args': ra})
                except Exception as e: rd = None
                row = {'panel': pid, 'series': r, 'feature': feat, 'args': ra, 'truth': tv}
                if rd is None: row['status'] = 'miss'
                else: row.update(read=rd[0], u=rd[1], z=(rd[0] - tv) / rd[1] if rd[1] > 0 else float('inf'), status='read')
                res.append(row)
        print(pid, 'read', sum(1 for x in res if x['panel'] == pid and x['status'] == 'read'), 'of', sum(1 for x in res if x['panel'] == pid and x['truth'] is not None))
    # per feature type
    FT = {'y_at_x': 'y_at_x', 'plateau': 'plateau', 'x_at_extremum': 'extremum', 'y_at_extremum': 'extremum', 'peak_x': 'peak_x', 'bar_top': 'bar_top'}
    summ = {}
    for ft in ['peak_x', 'y_at_x', 'plateau', 'extremum', 'crossing', 'bar_top', 'x_end']:
        rows = [x for x in res if FT.get(x['feature']) == ft and x['truth'] is not None]
        if not rows: summ[ft] = {'n': 0, 'verdict': 'replica-only (no source-data test case)'}; continue
        z = np.array([x['z'] for x in rows if x['status'] == 'read']); cov = len(z) / len(rows)
        w = float((np.abs(z) <= 2).mean()) if len(z) else 0.0; b = float(z.mean()) if len(z) else float('nan')
        ok = cov >= 0.8 and w >= 0.9 and abs(b) <= 0.5
        summ[ft] = {'n': len(rows), 'read': len(z), 'coverage': cov, 'within_2u': w, 'bias_u': b, 'median_abs_z': float(np.median(np.abs(z))) if len(z) else None, 'verdict': 'PASS' if ok else 'FAIL'}
    json.dump({'results': res, 'summary': summ, 'log': log}, open(f'{V32}/fidelity/' + (sys.argv[1] if len(sys.argv) > 1 else 'phase3_results.json'), 'w'), indent=1, default=float, ensure_ascii=False)
    for k, v in summ.items(): print(k, v)
