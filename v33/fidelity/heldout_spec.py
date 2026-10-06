#!/usr/bin/env python3
"""fidelity/heldout_spec.py (v3.2, user decision after Phase 3): the held-out fidelity test sets, chosen and frozen before any F6 read.
External: Nature-family materials papers with an xlsx Source Data file whose sheets are named by figure, taken in the order of the Nature
search pages (search/ncomms.html, search/commsmat.html; query 'source data', materials-science, 2025-2026, relevance), skipping
non-materials topics, deposits without figure-named sheets, papers without a checkable printed number, and papers whose printed number does
not match (log in fidelity/HELDOUT.md). Internal: S039/S098 panels whose plotted values are printed in the papers' own text tables (test
only, never keys).
Each panel: figure image, crop box (px of the published full-size figure PNG), series (figure label -> source), feature rules applied to the
source values (truths computed here, before any read). Reader inputs (colours, legend/inset exclusion boxes, declared tick values,
sub-frame crops) are set after the F6 freeze and before the gate run, logged in fidelity/heldout_inputs.json.
usage: heldout_spec.py -> fidelity/heldout_truth.json (truth rows) and prints counts per set and feature type."""
import sys as _pb_s, os as _pb_o
_pb_d = _pb_o.path.dirname(_pb_o.path.abspath(__file__))
while not _pb_o.path.exists(_pb_o.path.join(_pb_d, 'pbroot.py')) and _pb_o.path.dirname(_pb_d) != _pb_d: _pb_d = _pb_o.path.dirname(_pb_d)
_pb_s.path.insert(0, _pb_d)
from pbroot import ROOT, HOST
import json, os, sys
import numpy as np
EXT = f'{HOST}/fidelity/ext'; OUT = f'{ROOT}/fidelity'
PAPERS = {
 'X1': {'id': 's43246-026-01193-y', 'doi': '10.1038/s43246-026-01193-y', 'journal': 'Communications Materials', 'xlsx': ['43246_2026_1193_MOESM4_ESM.xlsx'],
        'printed_check': 'Fig. 2a [Al] = 51 at.%, [N] = 47 at.% vs sheet Fig. 2a mean over 10-30 nm: 51.0, 47.0'},
 'X2': {'id': 's43246-026-01347-y', 'doi': '10.1038/s43246-026-01347-y', 'journal': 'Communications Materials',
        'xlsx': ['43246_2026_1347_MOESM2_ESM.xlsx', '43246_2026_1347_MOESM3_ESM.xlsx', '43246_2026_1347_MOESM4_ESM.xlsx', '43246_2026_1347_MOESM5_ESM.xlsx'],
        'printed_check': 'Fig. 10c marked point 1.2 m/s at 500 Pa vs sheet Fig. 10(c): p3(1.2 m/s) = 500 Pa'},
 'X3': {'id': 's41467-026-78108-5', 'doi': '10.1038/s41467-026-78108-5', 'journal': 'Nature Communications', 'xlsx': ['41467_2026_78108_MOESM3_ESM.xlsx'],
        'printed_check': 'Fig. 5d S1 = 0.17 mV/kPa, S2 = 0.0023 mV/kPa vs sheet Figure 5 linear fits: 0.170, 0.00234'},
 'X4': {'id': 's41467-026-77568-z', 'doi': '10.1038/s41467-026-77568-z', 'journal': 'Nature Communications', 'xlsx': ['41467_2026_77568_MOESM3_ESM.xlsx'],
        'printed_check': 'Fig. 4d bar label 12 % vs sheet Figure 4 xi_z/xi_y at alpha = 0: 0.1198'},
}
_wb = {}
def sheet(pk, name, xi=0):
    key = (pk, xi, name)
    if key not in _wb:
        import openpyxl
        wb = openpyxl.load_workbook(f"{EXT}/{PAPERS[pk]['id']}/{PAPERS[pk]['xlsx'][xi]}", read_only=True, data_only=True)
        _wb[key] = [list(r) for r in wb[name].iter_rows(values_only=True)]
    return _wb[key]
num = lambda v: float(v) if isinstance(v, (int, float)) else (float(v) if isinstance(v, str) and v.strip().replace('.', '', 1).replace('-', '', 1).isdigit() else np.nan)
def xy(rows, jx, jy, r0):
    x = np.array([num(r[jx]) if jx < len(r) else np.nan for r in rows[r0:]]); y = np.array([num(r[jy]) if jy < len(r) else np.nan for r in rows[r0:]])
    ok = ~np.isnan(x) & ~np.isnan(y); return x[ok], y[ok]

# ---------------------------------------------------------------- truth rules (on source values only)
def f_y_at_x(s, x0):
    x, y = s; o = np.argsort(x); x, y = x[o], y[o]; return float(np.interp(x0, x, y)) if x[0] <= x0 <= x[-1] else None
def f_plateau(s, a, b):
    x, y = s; m = (x >= a) & (x <= b); return float(y[m].mean()) if m.sum() >= 2 else None
def f_ext(s, kind, a, b, what):
    x, y = s; m = (x >= a) & (x <= b)
    if m.sum() < 2: return None
    i = int(y[m].argmax() if kind == 'max' else y[m].argmin()); return float((x[m] if what == 'x' else y[m])[i])
def f_peak(s, a, b, kind='max'): return f_ext(s, kind, a, b, 'x')
def branches_at(s, x0):
    """loop given as a path: all crossings of x = x0 (linear interpolation along the path) -> sorted y values"""
    x, y = s; out = []
    for i in range(len(x) - 1):
        if (x[i] - x0) * (x[i + 1] - x0) <= 0 and x[i] != x[i + 1]: out.append(y[i] + (x0 - x[i]) / (x[i + 1] - x[i]) * (y[i + 1] - y[i]))
    return sorted(out)
def f_cross_x0_upper(s):
    b = branches_at(s, 0.0); return float(max(b)) if b else None
def f_cross_y0_right(s):
    b = branches_at((s[1], s[0]), 0.0); return float(max(b)) if b else None
def f_branch(s, x0, which):
    b = branches_at(s, x0); return (float(max(b)) if which == 'upper' else float(min(b))) if len(b) >= 2 else None

ROWS = []
def add(set_, pk, fig, panel, box, series, feature, args, truth, note=''):
    if truth is None: return
    ROWS.append({'set': set_, 'paper': pk, 'figure': fig, 'panel': panel, 'box': box, 'series': series, 'feature': feature, 'args': args, 'truth': truth, 'note': note})

def external():
    # X1 (01193-y) -------------------------------------------------------------------------------------------------------------------
    F = '43246_2026_1193_Fig'; r = sheet('X1', 'Fig. 1')
    for pan, box, c0 in (('1a', [0, 0, 1057, 743], 1), ('1c', [1057, 0, 2000, 743], 7)):
        for lab, j in (('GPCmix', c0 + 1), ('GPCavg', c0 + 2)):
            s = xy(r[3:9], c0, j, 0)
            for xv in s[0]: add('external', 'X1', F + '1', pan, box, lab, 'y_at_x', {'x': float(xv)}, f_y_at_x(s, xv), 'scatter marker (open vs filled, same colour)')
    for pan, sh, box, (a, b) in (('2a', 'Fig. 2a', [0, 0, 1057, 743], (10, 30)), ('2b', 'Fig. 2b', [1057, 0, 2000, 743], (10, 30)),
                                  ('2c', 'Fig. 2c', [0, 743, 1057, 1537], (10, 25)), ('2d', 'Fig. 2d', [1057, 743, 2000, 1537], (8, 26))):
        rr = sheet('X1', sh); hdr = rr[2]
        for lab in ('Al', 'N'):
            j = next(k for k, h in enumerate(hdr) if isinstance(h, str) and h.startswith(lab + ' ')); s = xy(rr, 1, j, 3)
            add('external', 'X1', F + '2', pan, box, lab, 'plateau', {'x_from': a, 'x_to': b}, f_plateau(s, a, b))
            add('external', 'X1', F + '2', pan, box, lab, 'y_at_x', {'x': (a + b) / 2}, f_y_at_x(s, (a + b) / 2))
    rr = sheet('X1', 'Fig. 4a'); labs = rr[1][1:6]
    for k, lab in enumerate(labs, 1):
        s = xy(rr, 0, k, 2); t = f_peak(s, 33, 38.5); add('external', 'X1', F + '4', '4a', [0, 0, 875, 694], lab, 'peak_x', {'window': [t - 1.0, t + 1.0]} if t else {}, t, 'stacked log-offset XRD, Wz 0002')
    rr = sheet('X1', 'Fig. 4b'); labs = rr[1][1:6]
    for k, lab in enumerate(labs, 1):
        s = xy(rr, 0, k, 2); t = f_peak(s, 10, 25); add('external', 'X1', F + '4', '4b', [875, 0, 1750, 694], lab, 'peak_x', {'window': [t - 3.0, t + 3.0]} if t else {}, t, 'overlapping rocking curves')
    rr = sheet('X1', 'Fig. 4d')
    for k, lab, (a, b) in ((1, 'AlScN 0002', (17.5, 18.2)), (2, 'GaN 0002', (16.8, 17.6))):
        s = xy(rr, 0, k, 2); t = f_peak(s, a, b); add('external', 'X1', F + '4', '4d', [875, 694, 1750, 1398], lab, 'peak_x', {'window': [t - 0.3, t + 0.3]} if t else {}, t, 'log counts, noisy')
    rr = sheet('X1', 'Fig. 5c'); s = xy(rr, 0, 1, 2)
    add('external', 'X1', F + '5', '5c', [0, 1200, 1000, 1819], 'Polarization', 'crossing', {'line': 'x=0', 'branch': 'upper'}, f_cross_x0_upper(s), 'P on the right axis')
    add('external', 'X1', F + '5', '5c', [0, 1200, 1000, 1819], 'Polarization', 'crossing', {'line': 'y=0', 'branch': 'right'}, f_cross_y0_right(s), 'P on the right axis')
    rr = sheet('X1', 'Fig. 5b'); s = xy(rr, 0, 3, 2)
    for e in (-2.0, 2.0):
        for w in ('upper', 'lower'): add('external', 'X1', F + '5', '5b', [0, 600, 1000, 1200], 'Relative permittivity', 'y_at_x', {'x': e, 'branch': w}, f_branch(s, e, w))
    # X2 (01347-y) -------------------------------------------------------------------------------------------------------------------
    F = '43246_2026_1347_Fig'
    for pan, sh, box in (('4top', 'Fig. 4 Top', [0, 0, 1000, 410]), ('4bottom', 'Fig. 4 Bottom and Fig. 8', [0, 410, 1000, 821])):
        rr = sheet('X2', sh, 0)
        for lab, j in (('Theory', 1), ('FEM', 2)):
            s = xy(rr, 0, j, 1)
            add('external', 'X2', F + '4', pan, box, lab, 'x_at_extremum', {'kind': 'max', 'window': [800, 1500]}, f_ext(s, 'max', 800, 1500, 'x'))
            add('external', 'X2', F + '4', pan, box, lab, 'y_at_extremum', {'kind': 'max', 'window': [800, 1500]}, f_ext(s, 'max', 800, 1500, 'y'))
            add('external', 'X2', F + '4', pan, box, lab, 'y_at_x', {'x': 600}, f_y_at_x(s, 600))
    rr = sheet('X2', 'Fig. 4 Bottom and Fig. 8', 0)
    for lab, jx, jy in (('Theory-Uniform', 0, 1), ('FEM-Uniform', 0, 2), ('EXP-Uniform', 4, 5)):
        s = xy(rr, jx, jy, 1)
        add('external', 'X2', F + '8', '8b', [0, 440, 1350, 1058], lab, 'x_at_extremum', {'kind': 'max', 'window': [900, 1400]}, f_ext(s, 'max', 900, 1400, 'x'))
        add('external', 'X2', F + '8', '8b', [0, 440, 1350, 1058], lab, 'y_at_extremum', {'kind': 'max', 'window': [900, 1400]}, f_ext(s, 'max', 900, 1400, 'y'))
    rr = sheet('X2', 'Fig. 11(a)', 3)
    for lab, j in (('TL-Vented Supercell', 1), ('TL-Unvented Baseline', 2), ('TL-Bare Macro-pore', 3)):
        s = xy(rr, 0, j, 1)
        for xv in (500, 1500): add('external', 'X2', F + '11', '11a', [0, 0, 1085, 620], lab, 'y_at_x', {'x': xv}, f_y_at_x(s, xv))
    s = xy(rr, 0, 1, 1); add('external', 'X2', F + '11', '11a', [0, 0, 1085, 620], 'TL-Vented Supercell', 'x_at_extremum', {'kind': 'max', 'window': [800, 1100]}, f_ext(s, 'max', 800, 1100, 'x'))
    s = xy(rr, 0, 2, 1); add('external', 'X2', F + '11', '11a', [0, 0, 1085, 620], 'TL-Unvented Baseline', 'x_at_extremum', {'kind': 'max', 'window': [550, 800]}, f_ext(s, 'max', 550, 800, 'x'))
    rr = sheet('X2', 'Fig. 11(b)', 3)
    for lab, j in (('RL-Unvented Baseline', 1), ('RL-Vented Supercell', 3)):
        s = xy(rr, 0, j, 1)
        add('external', 'X2', F + '11', '11b', [0, 610, 1110, 1198], lab, 'x_at_extremum', {'kind': 'max', 'window': [1000, 1250]}, f_ext(s, 'max', 1000, 1250, 'x'))
        add('external', 'X2', F + '11', '11b', [0, 610, 1110, 1198], lab, 'y_at_extremum', {'kind': 'max', 'window': [1000, 1250]}, f_ext(s, 'max', 1000, 1250, 'y'))
    # X3 (78108-5) -------------------------------------------------------------------------------------------------------------------
    F = '41467_2026_78108_Fig'; rr = sheet('X3', 'Figure 3')
    for pan, box, c0, n in (('3a', [0, 0, 629, 493], 0, 5), ('3b', [629, 0, 1286, 493], 11, 5), ('3c', [1286, 0, 2000, 493], 22, 4)):
        for k in range(n):
            lab = rr[2][c0 + 2 * k]; s = xy(rr, c0 + 2 * k, c0 + 2 * k + 1, 3)
            add('external', 'X3', F + '3', pan, box, str(lab), 'x_end', {}, float(s[0].max()))
            add('external', 'X3', F + '3', pan, box, str(lab), 'y_at_extremum', {'kind': 'max', 'window': [0, float(s[0].max())]}, float(s[1].max()))
    for pan, box, c0 in (('3d', [0, 493, 643, 957], 31), ('3e', [643, 493, 1286, 957], 37)):
        for i in range(2, 7):
            lab = rr[i][c0] if i < len(rr) else None
            if lab is None or lab == '--': continue
            add('external', 'X3', F + '3', pan, box, f'Elastic Modulus {lab}', 'bar_top', {'index': i - 2}, num(rr[i][c0 + 1]), 'left axis, pink bars with caps')
            add('external', 'X3', F + '3', pan, box, f'Toughness {lab}', 'bar_top', {'index': i - 2}, num(rr[i][c0 + 3]), 'right axis, blue bars with caps')
    F = '41467_2026_78108_Fig'; rr = sheet('X3', 'Figure 2')
    for k in range(5):
        lab = rr[2][1 + k]; s = xy(rr, 0, 1 + k, 3); t = f_peak(s, 15, 25)
        add('external', 'X3', F + '2', '2b', [0, 371, 651, 910], lab, 'peak_x', {'window': [t - 2.0, t + 2.0]} if t else {}, t, 'stacked XRD')
    for k in range(5):
        lab = rr[2][12 + k]; s = xy(rr, 11, 12 + k, 3); t = f_peak(s, 1130, 1155, 'min')
        add('external', 'X3', F + '2', '2d', [0, 910, 651, 1469], lab, 'peak_x', {'window': [t - 10, t + 10], 'kind': 'min'} if t else {}, t, 'stacked FTIR dip')
    for i in range(2, 7):
        lab = rr[i][7]
        add('external', 'X3', F + '2', '2c', [651, 371, 1350, 882], f'Crystallinity {lab}', 'bar_top', {'index': i - 2}, num(rr[i][8]), 'left axis')
        add('external', 'X3', F + '2', '2c', [651, 371, 1350, 882], f'Crystallite Size {lab}', 'bar_top', {'index': i - 2}, num(rr[i][9]), 'right axis')
        add('external', 'X3', F + '2', '2f', [0, 1469, 658, 2000], f'Ratio {rr[i][59]}', 'bar_top', {'index': i - 2}, num(rr[i][60]), 'gradient-filled bars')
    # X4 (77568-z) -------------------------------------------------------------------------------------------------------------------
    F = '41467_2026_77568_Fig'; rr = sheet('X4', 'Figure 2'); s = xy(rr, 0, 1, 3); s = (s[0] / 1e6, s[1])
    add('external', 'X4', F + '2', '2a', [0, 0, 500, 420], 'Rxy', 'crossing', {'line': 'x=0', 'branch': 'upper'}, f_cross_x0_upper(s))
    add('external', 'X4', F + '2', '2a', [0, 0, 500, 420], 'Rxy', 'crossing', {'line': 'y=0', 'branch': 'right'}, f_cross_y0_right(s), 'x in 1e6 A/cm2')
    rr = sheet('X4', 'Figure 3')
    for pan, box, j in (('3d', [0, 300, 450, 720], 0), ('3f', [900, 300, 1345, 720], 10)):
        s = xy(rr, j, j + 1, 3); s = (s[0] / 1e6, s[1])
        add('external', 'X4', F + '3', pan, box, 'Rxy(J)', 'crossing', {'line': 'x=0', 'branch': 'upper'}, f_cross_x0_upper(s), 'blue J loop; green H loop on the top axis not read')
        add('external', 'X4', F + '3', pan, box, 'Rxy(J)', 'crossing', {'line': 'y=0', 'branch': 'right'}, f_cross_y0_right(s))
    s = xy(rr, 15, 16, 3)
    for a in (90, 270): add('external', 'X4', F + '3', '3i', [900, 750, 1345, 1129], 'Switching ratio', 'y_at_x', {'x': a}, f_y_at_x(s, a), 'markers + fit')
    rr = sheet('X4', 'Figure 4')
    for lab, j in (('+11 mA', 0), ('-11 mA', 2)):
        s = xy(rr, j, j + 1, 3)
        add('external', 'X4', F + '4', '4a', [0, 0, 650, 520], lab, 'crossing', {'line': 'x=0', 'branch': 'upper'}, f_cross_x0_upper(s), 'inset excluded')
        add('external', 'X4', F + '4', '4a', [0, 0, 650, 520], lab, 'crossing', {'line': 'y=0', 'branch': 'right'}, f_cross_y0_right(s))
    for k in range(10):
        lab = rr[2][6 + k]; s = xy(rr, 5, 6 + k, 3); s = (s[0] / 1e6, s[1])
        for jv in (2.5, 3.0): add('external', 'X4', F + '4', '4b', [650, 0, 1345, 520], lab, 'y_at_x', {'x': jv}, f_y_at_x(s, jv), '10 graded green series')
    s = xy(rr, 17, 18, 3); s = (s[0], s[1] * 1e5)
    for h in (-100, 0, 100): add('external', 'X4', F + '4', '4c', [0, 550, 650, 1104], 'chi', 'y_at_x', {'x': h}, f_y_at_x(s, h), 'units 1e-5')
    for i in range(3, 7):
        a = num(rr[i][20]); v = num(rr[i][21])
        if not np.isnan(v): add('external', 'X4', F + '4', '4d', [650, 550, 1345, 1104], f'alpha {a:g}', 'bar_top', {'index': i - 3}, v * 100, 'percent; negative bar at 135 deg; gradient background')

def internal():
    T1 = {'T25': (8108, 2.89, 117.15), 'T20@M5': (7015, 4.10, 110.33), 'T15@M10': (5755, 5.01, 86.42), 'T10@M15': (4032, 2.40, 77.61), 'T5@M20': (2449, 2.37, 61.60)}
    for i, (lab, (fold, strain, strength)) in enumerate(T1.items()):
        add('internal', 'S098', 'crops/F5b', 'F5b', None, lab, 'bar_top', {'index': i}, fold, 'Table 1 folding number')
        add('internal', 'S098', 'crops/F5c', 'F5c', None, lab, 'x_end', {}, strain, 'Table 1 tensile strain (mean of repeats)')
        add('internal', 'S098', 'crops/F5c', 'F5c', None, lab, 'y_at_extremum', {'kind': 'max', 'window': [0, 6]}, strength, 'Table 1 tensile strength (mean of repeats)')
    for i, (lab, v) in enumerate((('T20@M5', 2.81e5), ('T15@M10', 4.76e5), ('T10@M15', 7.43e5), ('T5@M20', 1.09e6), ('M25', 1.23e6))):
        add('internal', 'S098', 'crops/F6a', 'F6a', None, lab, 'bar_top', {'index': i + 1}, v, 'Table 2 conductivity (exponents of the last two from pdftotext)')
    for li, (t, a, r) in enumerate(((25.55, 18.74, 6.81), (50.18, 35.87, 14.31), (76.00, 58.12, 17.88), (100.85, 73.16, 27.69))):
        for lab, v in (('SE_Total', t), ('SE_A', a), ('SE_R', r)): add('internal', 'S098', 'crops/F7h', 'F7h', None, lab, 'bar_top', {'index': li}, v, 'Table 3, hatched bars')
    T4 = {'0.00': (58.47, 4.48, 79.02), '0.01': (57.51, 3.59, 65.42), '0.02': (57.26, 3.05, 62.01), '0.04': (52.52, 2.59, 42.15), '0.06': (51.81, 1.39, 39.01), '0.08': (51.43, 1.27, 20.95)}
    for x, (ms, mr, hc) in T4.items():
        add('internal', 'S039', 'crops/F16', 'F16', None, f'x={x}', 'plateau', {'x_from': 15000, 'x_to': 20000}, ms, 'Table 4 Ms (6 stacked subplots)')
        add('internal', 'S039', 'crops/F16', 'F16', None, f'x={x}', 'crossing', {'line': 'x=0', 'branch': 'upper'}, mr, 'Table 4 Mr')
        add('internal', 'S039', 'crops/F16', 'F16', None, f'x={x}', 'crossing', {'line': 'y=0', 'branch': 'right'}, hc, 'Table 4 Hc (G)')
    for i, (x, d) in enumerate((('0.00', 16.267), ('0.01', 14.375), ('0.02', 13.869), ('0.04', 13.320), ('0.06', 12.691), ('0.08', 11.325))):
        add('internal', 'S039', 'crops/F8', 'F8', None, 'D_DS', 'y_at_x', {'x': i}, d, 'Table 1 D_DS; 4 y axes, categorical x')

if __name__ == '__main__':
    external(); internal()
    for r in ROWS:
        for k, v in list(r['args'].items()):
            if isinstance(v, (np.floating,)): r['args'][k] = float(v)
    json.dump(ROWS, open(f'{OUT}/heldout_truth.json', 'w'), indent=1, default=float)
    from collections import Counter
    FT = lambda f: {'x_at_extremum': 'extremum', 'y_at_extremum': 'extremum'}.get(f, f)
    print(Counter((r['set'], FT(r['feature'])) for r in ROWS))
    print('panels', Counter(r['set'] for r in {(r['set'], r['paper'], r['panel']): r for r in ROWS}.values()))
