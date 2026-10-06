#!/usr/bin/env python3
"""fidelity/heldout_inputs.py: reader inputs of the held-out panels, set after the F6 freeze and before any held-out read (the kinds of
inputs Stage 5D uses): series colours (sampled at a declared swatch/marker point, guarded by a coarse colour name, or declared black),
other plotted colours in the panel (so the Delta E refusal sees every colour a read series could be confused with), legend/inset/arrow
exclusion boxes, axis kinds (y_none for spectra, x_none for category axes), dual axes (right_series), gradient fills, declared tick
values printed on a shared axis, sub-frame crops, and the bar index of a series among bars of its colour.
Crop-box corrections made here, before any read (logged): X2 4top -> [0, 0, 1000, 381] and 4bottom -> [0, 381, 1000, 821] (the frozen
boxes cut the bottom panel's top frame line and put it inside the top crop; frame rows measured at 15-370 and 391-746).
Source-mapping exclusion made here, before any read (logged): X1 4a series 'AlScN 1.5:1 (215 C, AlN Seed)' and 'AlScN 1:1 (No Seed)': the
sheet names contradict the figure labels (50% CR 215 C, 60% CR NS) under the cycle-ratio reading used by sheet Fig. 4b -> out of scope.
usage: heldout_inputs.py -> fidelity/heldout_inputs.json"""
import sys as _pb_s, os as _pb_o
_pb_d = _pb_o.path.dirname(_pb_o.path.abspath(__file__))
while not _pb_o.path.exists(_pb_o.path.join(_pb_d, 'pbroot.py')) and _pb_o.path.dirname(_pb_d) != _pb_d: _pb_d = _pb_o.path.dirname(_pb_d)
_pb_s.path.insert(0, _pb_d)
from pbroot import ROOT, HOST
import json, sys
import numpy as np
from PIL import Image
OUT = f'{ROOT}/fidelity'; CR = f'{HOST}/fidelity/heldout_crops'; HP = f'{HOST}/papers'
COARSE = {'black': (20, 20, 20), 'gray': (165, 165, 165), 'dgray': (85, 85, 85), 'red': (210, 35, 35), 'blue': (40, 70, 230), 'lblue': (110, 180, 230), 'navy': (35, 55, 130),
          'green': (50, 160, 50), 'lgreen': (160, 200, 120), 'orange': (240, 150, 50), 'purple': (150, 70, 200), 'pink': (240, 140, 150), 'teal': (60, 120, 140),
          'yellow': (245, 205, 40), 'brown': (180, 90, 40), 'salmon': (245, 140, 100), 'slate': (140, 155, 205), 'magenta': (225, 125, 185), 'rose': (228, 75, 95)}
B = (20, 20, 20)
SAMPLE_LOG = []
def sample(img, pt, coarse, r=25):
    """median of the pixels near pt within RGB distance 90 of the coarse colour; the most saturated 30% (darkest 30% if achromatic)."""
    a = np.asarray(img.convert('RGB'), float); x, y = pt; win = a[max(y - r, 0):y + r + 1, max(x - r, 0):x + r + 1].reshape(-1, 3)
    c = np.array(COARSE[coarse], float); px = win[np.linalg.norm(win - c, axis=1) < 90]
    if len(px) < 3:   # not near the point: the coarse colour's pixels anywhere in the panel (logged as 'whole-panel sample')
        allp = a.reshape(-1, 3); px = allp[np.linalg.norm(allp - c, axis=1) < 60]; SAMPLE_LOG.append((pt, coarse, 'whole-panel', len(px)))
        if len(px) < 3: raise SystemExit(f'no {coarse} pixels near {pt} or anywhere')
    sat = px.max(1) - px.min(1)
    key = -px.mean(1) if (c.max() - c.min()) < 30 else sat
    px = px[key >= np.percentile(key, 70)]; return [int(v) for v in np.median(px, 0)]

def col(img, spec):
    if spec == 'black': return list(B)
    if isinstance(spec, list): return spec   # declared from the panel's dominant colour clusters (colour-bin listing, logged in LOG.md)
    pt, coarse = spec; return sample(img, pt, coarse)

# panel -> inputs. series: truth series label -> (reader value, colour spec, extra); others: colour specs of further plotted series
P = {}
def panel(key, img, **kw): P[key] = dict(img=img, **kw)

def build():
    def ext(pk, pan): return Image.open(f'{CR}/{pk}_{pan}.png')
    # X1 -------------------------------------------------------------------------------------------------------------------------
    for pan in ('1a', '1c'):   # GPCmix (open) and GPCavg (filled): both black -> refusal expected
        panel(f'X1|{pan}', f'{CR}/X1_{pan}.png', series={'GPCmix': ('GPCmix', 'black'), 'GPCavg': ('GPCavg', 'black')}, others=[((811, 574), "blue")], merge_gap=4)
    L2 = {'2a': {'ex': [[357, 38, 700, 268], [800, 168, 1000, 528]], 'Al': (861, 199), 'N': (861, 277), 'O': (861, 428)},
          '2b': {'ex': [[243, 44, 588, 279], [684, 191, 882, 544]], 'Al': (750, 218), 'N': (750, 294), 'O': (750, 444), 'y_ticks': [0, 20, 40, 60, 80, 100]},
          '2c': {'ex': [[337, 44, 697, 279], [814, 140, 1028, 588]], 'Al': (873, 166), 'N': (873, 298), 'O': (873, 497), 'Cl': (873, 365)},
          '2d': {'ex': [[250, 44, 610, 279], [706, 140, 934, 588]], 'Al': (764, 162), 'N': (764, 294), 'O': (764, 494), 'Cl': (764, 360), 'y_ticks': [0, 20, 40, 60, 80, 100]}}
    for pan, d in L2.items():
        im = ext('X1', pan); oth = ['black', (d['O'], 'blue')] + ([(d['Cl'], 'green')] if 'Cl' in d else [])
        panel(f'X1|{pan}', f'{CR}/X1_{pan}.png', series={'Al': ('Al', (d['Al'], 'gray')), 'N': ('N', (d['N'], 'red'))}, others=oth, exclude=d['ex'], **({'y_ticks': d['y_ticks']} if 'y_ticks' in d else {}))
    panel('X1|4a', f'{CR}/X1_4a.png', y_none=True, exclude=[[72, 79, 308, 472]], skip_series=['AlScN  1.5:1 (215° C, AlN Seed)', 'AlScN 1:1 (No Seed)'],
          series={'AlN': ('AlN', [204, 36, 12]), 'AlScN 1.5:1 (AlN Seed)': ('60CR', [60, 132, 204]), 'AlScN 3:1 (AlN Seed)': ('75CR', 'black')},
          others=[[108, 60, 180], [60, 120, 36]])
    panel('X1|4b', f'{CR}/X1_4b.png', y_none=True,
          series={'AlN': ('AlN', [204, 36, 12]), 'AlScN 1.5:1 (AlN Seed)': ('60CR', [60, 132, 204]), 'AlScN 3:1 (AlN Seed)': ('75CR', 'black'),
                  'AlScN 1.5:1 (No Seed)': ('60NS', [60, 120, 36]), 'AlScN  1:1 (215° C, AlN Seed)': ('50CR', [108, 60, 180])})
    panel('X1|4d', f'{CR}/X1_4d.png', y_none=True, series={'GaN 0002': ('GaN', ((300, 150), 'teal')), 'AlScN 0002': ('AlScN', ((475, 250), 'red'))})
    panel('X1|5b', f'{CR}/X1_5b.png', exclude=[[177, 123, 231, 154]], series={'Relative permittivity': ('eps', ((270, 75), 'lblue'))}, others=['black'])
    panel('X1|5c', f'{CR}/X1_5c.png', exclude=[[179, 400, 233, 439], [748, 397, 802, 439]], right_series=['P'],
          series={'Polarization': ('P', ((600, 55), 'red'))}, others=[((500, 330), 'purple')])
    # X2 -------------------------------------------------------------------------------------------------------------------------
    for pan, box in (('4top', [0, 0, 1000, 381]), ('4bottom', [0, 381, 1000, 821])):
        panel(f'X2|{pan}', None, figure='43246_2026_1347_Fig4', box=box, **({'x_ticks': [0, 500, 1000, 1500, 2000]} if pan == '4top' else {}),
              exclude=[[780, 0, 1000, 70]] if pan == '4bottom' else [[790, 0, 1000, 160]],
              series={'Theory': ('Theory', 'black'), 'FEM': ('FEM', ((1100, 30), 'red'))}, others=[], colour_points_in='figure')
    panel('X2|8b', f'{CR}/X2_8b.png', exclude=[[1010, 25, 1300, 135]], series={'Theory-Uniform': ('T', 'black'), 'FEM-Uniform': ('F', ((1045, 87), 'red')), 'EXP-Uniform': ('E', 'black')})
    panel('X2|11a', f'{CR}/X2_11a.png', exclude=[[604, 23, 935, 139], [927, 447, 1012, 516]],
          series={'TL-Vented Supercell': ('V', ((640, 47), 'red')), 'TL-Unvented Baseline': ('U', ((640, 80), 'dgray')), 'TL-Bare Macro-pore': ('B', ((640, 113), 'lblue'))})
    panel('X2|11b', f'{CR}/X2_11b.png', exclude=[[660, 15, 1000, 160]],
          series={'RL-Vented Supercell': ('V', ((700, 37), 'red')), 'RL-Unvented Baseline': ('U', ((700, 70), 'dgray'))}, others=[((700, 103), 'lblue'), ((700, 136), 'red')])
    # X3 -------------------------------------------------------------------------------------------------------------------------
    panel('X3|2b', f'{CR}/X3_2b.png', y_none=True, exclude=[[486, 121, 635, 405]],
          series={'PVA-dry': ('dry', [84, 84, 84]), 'PVA-H2O': ('h2o', [240, 60, 60]), 'PVA-SC': ('sc', [252, 156, 40]),
                  'PVA-gly': ('gly', [12, 108, 228]), 'PVA-gly-SC': ('glysc', [60, 180, 108])})
    panel('X3|2d', f'{CR}/X3_2d.png', y_none=True, exclude=[[120, 50, 240, 360]],
          series={'PVA-dry': ('dry', ((560, 95), 'dgray')), 'PVA-H2O': ('h2o', ((560, 175), 'red')), 'PVA-SC': ('sc', ((560, 240), 'orange')),
                  'PVA-gly': ('gly', ((560, 318), 'blue')), 'PVA-gly-SC': ('glysc', ((560, 410), 'green'))})
    panel('X3|2c', f'{CR}/X3_2c.png', x_none=True, exclude=[[364, 34, 614, 101]], right_series=['size'],
          bars={'Crystallinity': ('cryst', ((95, 150), 'pink')), 'Crystallite Size': ('size', ((150, 150), 'lblue'))})
    panel('X3|2f', f'{CR}/X3_2f.png', x_none=True, gradient_fill=True, bars={'Ratio': ('ratio', ((140, 90), 'pink'))})
    for pan, ex, pts in (('3a', [[130, 35, 450, 165]], [(150, 45), (150, 72), (150, 98), (150, 125), (150, 151)]),
                          ('3b', [[125, 30, 440, 160]], [(150, 42), (150, 68), (150, 94), (150, 120), (150, 146)]),
                          ('3c', [[114, 40, 286, 142]], [(130, 52), (130, 78), (130, 104), (130, 130)])):
        names = {'3a': ['0M', '0.25M', '0.5M', '0.75M', '1M'], '3b': ['0.04', '0.08', '0.12', '0.16', '0.2'], '3c': ['PVA-gly-SC', 'PVA-gly', 'PVA-SC', 'PVA-H2O']}[pan]
        coarse = {'3a': ['salmon', 'yellow', 'lblue', 'green', 'purple'], '3b': ['salmon', 'yellow', 'green', 'lblue', 'purple'], '3c': ['salmon', 'lblue', 'green', 'orange']}[pan]
        panel(f'X3|{pan}', f'{CR}/X3_{pan}.png', exclude=ex, series={n: (n, (p, c)) for n, p, c in zip(names, pts, coarse)})
    for pan, ex in (('3d', [[168, 45, 592, 96]]), ('3e', [[350, 30, 570, 85]])):
        panel(f'X3|{pan}', f'{CR}/X3_{pan}.png', x_none=True, exclude=ex, right_series=['tough'],
              bars={'Elastic Modulus': ('mod', [252, 156, 156]), 'Toughness': ('tough', [132, 204, 252])}, others=[[12, 156, 228]])
    # X4 -------------------------------------------------------------------------------------------------------------------------
    panel('X4|2a', f'{CR}/X4_2a.png', exclude=[[237, 118, 340, 272]], merge_gap=4, series={'Rxy': ('R', ((210, 105), 'lblue'))})
    for pan in ('3d', '3f'):
        panel(f'X4|{pan}', f'{CR}/X4_{pan}.png', merge_gap=4, series={'Rxy(J)': ('R', ((270, 170) if pan == '3d' else (250, 172), 'lblue'))}, others=[((300, 92), 'lgreen')])
    panel('X4|3i', f'{CR}/X4_3i.png', merge_gap=4, series={'Switching ratio': ('S', [36, 108, 132])}, others=[[228, 84, 84]])
    panel('X4|4a', f'{CR}/X4_4a.png', exclude=[[151, 25, 363, 264], [402, 332, 645, 393]], merge_gap=4,
          series={'+11 mA': ('p', ((425, 340), 'lblue')), '-11 mA': ('m', ((425, 380), 'brown'))})
    hx = ['Hx=-200 Oe', 'Hx=-180 Oe', 'Hx=-100 Oe', 'Hx=-40 Oe', 'Hx=-20 Oe', 'Hx=0 Oe', 'Hx=20 Oe', 'Hx=60 Oe', 'Hx=140 Oe', 'Hx=200 Oe']
    ys = [389, 382, 347, 312, 271, 218, 179, 109, 76, 58]
    panel('X4|4b', f'{CR}/X4_4b.png', exclude=[[530, 30, 695, 400]], merge_gap=4,
          series={h: (h, ((518, y), 'lgreen' if i < 6 else 'teal')) for i, (h, y) in enumerate(zip(hx, ys))})
    panel('X4|4c', f'{CR}/X4_4c.png', merge_gap=4, series={'chi': ('chi', ((870 - 650 + 0, 0), 'blue'))} if False else {'chi': ('chi', ((225, 395), 'blue'))},
          others=[((140, 300), 'orange'), 'black'])
    panel('X4|4d', f'{CR}/X4_4d.png', x_none=True, bars={'alpha 0': ('a0', [84, 180, 228]), 'alpha 45': ('a45', [36, 60, 132]), 'alpha 90': ('a90', [228, 60, 36]), 'alpha 135': ('a135', [252, 156, 60])})
    # internal -------------------------------------------------------------------------------------------------------------------
    panel('S098|F5b', f'{HP}/s098/crops/F5b.jpg', x_none=True, bars={'T25': ('T25', ((172, 150), 'salmon')), 'T20@M5': ('T20', ((248, 150), 'teal' if False else 'lgreen')),
          'T15@M10': ('T15', ((324, 200), 'slate')), 'T10@M15': ('T10', ((400, 250), 'magenta')), 'T5@M20': ('T5', ((476, 300), 'lgreen'))}, per_bar_colour=True)
    panel('S098|F6a', f'{HP}/s098/crops/F6a.jpg', x_none=True, per_bar_colour=True,
          bars={'T20@M5': ('T20', [108, 204, 156]), 'T15@M10': ('T15', [132, 156, 204]), 'T10@M15': ('T10', [228, 132, 204]), 'T5@M20': ('T5', [168, 216, 84]), 'M25': ('M25', [252, 228, 48])})
    panel('S098|F5c', f'{HP}/s098/crops/F5c.jpg', exclude=[[95, 20, 280, 150]],
          series={'T25': ('T25', [252, 141, 98]), 'T20@M5': ('T20', [101, 194, 165]), 'T15@M10': ('T15', [141, 160, 203]), 'T10@M15': ('T10', [231, 137, 197]), 'T5@M20': ('T5', [168, 215, 83])})
    panel('S098|F7h', f'{HP}/s098/crops/F7h.jpg', x_none=True, exclude=[[25, 20, 115, 95]],
          bars={'SE_Total': ('T', [60, 84, 108]), 'SE_A': ('A', [84, 160, 130]), 'SE_R': ('R', [228, 132, 108])})
    for i, (x, y0, y1, c) in enumerate((('0.08', 8, 125, 'navy'), ('0.06', 125, 242, 'green'), ('0.04', 242, 357, 'purple'), ('0.02', 357, 473, 'blue'),
                                       ('0.01', 473, 590, 'red'), ('0.00', 590, 760))) if False else []:
        pass
    sub = [('0.08', 8, 125, 'navy'), ('0.06', 125, 242, 'green'), ('0.04', 242, 357, 'purple'), ('0.02', 357, 473, 'blue'), ('0.01', 473, 590, 'red'), ('0.00', 590, 707, 'black')]
    for x, y0, y1, c in sub:
        panel(f'S039|F16|x={x}', f'{HP}/s039/crops/F16.jpg', crop=[0, y0, 539, y1], x_ticks=[-20000, 0, 20000], exclude=[[60, 0, 210, 26]], merge_gap=4,
              series={f'x={x}': (f'x={x}', 'black' if c == 'black' else ((420, (y0 + y1) // 2 - 45), c))}, colour_points_in='full')
    panel('S039|F8', None, unsupported='four y axes on one panel (D_DS on an inner right axis): no reader')

if __name__ == '__main__':
    build(); out = {}
    for key, p in P.items():
        q = {k: v for k, v in p.items() if k not in ('series', 'others', 'bars', 'img')}
        if p.get('unsupported'): out[key] = q; continue
        if p.get('figure'):
            im = Image.open(f"{HOST}/fidelity/ext/s43246-026-01347-y/{p['figure']}_HTML.png").convert('RGB')
            sub_ = im.crop(tuple(p['box'])); q['img'] = f"{CR}/X2_{key.split('|')[1]}_fixed.png"; sub_.save(q['img']); im = sub_
        else:
            q['img'] = p['img']; im = Image.open(p['img']).convert('RGB')
        q['series'] = {}
        src = p.get('series') or p.get('bars')
        for lab, (val, spec) in src.items(): q['series'][lab] = {'value': val, 'colour': col(im, spec)}
        q['others'] = [col(im, s) for s in p.get('others', [])]
        q['kind'] = 'bar' if p.get('bars') else 'curve'
        out[key] = q
    json.dump({'panels': out, 'sample_log': SAMPLE_LOG}, open(f'{OUT}/heldout_inputs.json', 'w'), indent=1)
    import readers as R
    for k, q in out.items():
        if q.get('unsupported'): print(k, 'UNSUPPORTED'); continue
        cols = [v['colour'] for v in q['series'].values()] + q['others']
        L = R.lab(np.array(cols, float)); d = min((float(np.linalg.norm(L[i] - L[j])) for i in range(len(cols)) for j in range(i + 1, len(cols))), default=99)
        print(k, {s: v['colour'] for s, v in q['series'].items()}, 'others', q['others'], 'minDE %.1f' % d)
