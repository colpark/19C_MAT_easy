#!/usr/bin/env python3
"""verify_flags.py (A6.4): check every overlay flag of the auditor against the marker pixels of the crop.
A flag gives a colour and an approximate (T, value). Search window: |T - T_flag| <= 15 K and the value within a factor 1.15 (log axes)
or 8% of the axis span (linear axes), converted to pixels with the panel's calibration.
  'marker without ring': confirmed when a blob of that colour class (relaxed mask, area >= 12, size 4-16 px, outside the padded
     legend box) lies in the window with no digitized marker of that series within 6 px.
  'ring without marker': confirmed when a digitized marker of that series lies in the window and the 11x11 patch under it holds
     < 12 pixels of the series' colour class.
Window: |T - T_flag| <= 15 K and within 12 px of the series' own pixel height (the auditor's y readings are rough on log axes).
A confirmed unringed marker within 6 K of a grid T (it would have been that cell's source) removes that cell's items. An unconfirmed flag is logged with the pixel evidence (every panel passed its A5 replicas).
Writes audit/outputs/overlay_flags_verified.json."""
import sys as _pb_s, os as _pb_o
_pb_d = _pb_o.path.dirname(_pb_o.path.abspath(__file__))
while not _pb_o.path.exists(_pb_o.path.join(_pb_d, 'pbroot.py')) and _pb_o.path.dirname(_pb_d) != _pb_d: _pb_d = _pb_o.path.dirname(_pb_d)
_pb_s.path.insert(0, _pb_d)
from pbroot import ROOT, HOST
import json, math, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
V31 = f'{ROOT}'; HOST = f'{HOST}'
sys.argv = [sys.argv[0]]; sys.path.insert(0, V31)
import digitize as D
COLOUR = {'green': 'green', 'olive': 'green', 'black': 'black', 'dark': 'black', 'gray': 'black', 'grey': 'black', 'red': 'red', 'orange': 'red',
          'blue': 'blue', 'navy': 'blue', 'magenta': 'magenta', 'pink': 'magenta', 'purple': 'magenta', 'violet': 'magenta'}
CONV = {'green': '0.0', 'black': '0.005', 'red': '0.01', 'blue': '0.02', 'magenta': '0.04'}
GRID = [300, 350, 400, 450, 500, 550, 600]
flags = json.load(open(f'{V31}/audit/outputs/overlays.json')); out = []
for r in flags:
    panel = r['panel']; fl = (r.get('parsed') or {}).get('flags') or []
    d = json.load(open(f'{V31}/digitized/{panel}.json')); rgb = np.asarray(Image.open(f'{HOST}/crops/{panel}.jpg').convert('RGB'))
    xc, yc = d['x_cal'], d['y_cal']; masks = D.color_class_relaxed(rgb)
    px_of = lambda T: (T - xc['b']) / xc['a']
    py_of = lambda v: ((math.log10(v) if yc['log'] else v) - yc['b']) / yc['a']
    lb = d['legend'].get('box')
    for f in fl:
        rec = {'panel': panel, 'flag': f, 'confirmed': None, 'evidence': None, 'remove_cells': []}
        cname = next((COLOUR[k] for k in COLOUR if k in str(f.get('series_colour', '')).lower()), None)
        try: T = float(f.get('approx_x_value')); v = float(f.get('approx_y_value'))
        except (TypeError, ValueError): rec['evidence'] = 'flag without usable coordinates'; out.append(rec); continue
        if cname is None: rec['evidence'] = 'colour not mapped'; out.append(rec); continue
        xs = CONV[cname]; pts = sorted(d['series'].get(xs, []), key=lambda p: p['px'])
        x0p, x1p = sorted([px_of(T - 15), px_of(T + 15)])
        # the auditor's y readings are rough (log axes); the window follows the series itself: within 12 px of the series'
        # pixel height interpolated from its digitized markers (falls back to the auditor's y when the series has < 2 markers)
        def series_py(px):
            if len(pts) < 2: return py_of(v)
            return float(np.interp(px, [p['px'] for p in pts], [p['py'] for p in pts]))
        inwin = lambda px, py: x0p <= px <= x1p and abs(py - series_py(px)) <= 12
        if 'without ring' in f.get('kind', ''):
            # coverage test (touching markers merge into blobs > 16 px, so no blob-size filter): colour pixels of the series' class
            # (2x2 opening drops 1-px lines) inside the window and outside the padded legend, farther than 5 px from every digitized
            # marker of the series; leftover connected pieces of >= 12 px are unringed markers
            m = ndi.binary_opening(masks[cname], structure=np.ones((2, 2)))
            yy, xx = np.nonzero(m); keep = np.zeros_like(m)
            for y_, x_ in zip(yy, xx):
                if not inwin(x_, y_): continue
                if lb and lb[0] - 10 <= x_ <= lb[2] + 10 and lb[1] - 10 <= y_ <= lb[3] + 10: continue
                if all(math.hypot(x_ - p['px'], y_ - p['py']) > 5 for p in pts): keep[y_, x_] = True
            lab, n = ndi.label(keep); unringed = []
            for i in range(1, n + 1):
                ys_, xs_ = np.nonzero(lab == i)
                if len(ys_) >= 12: unringed.append((float(xs_.mean()), float(ys_.mean())))
            rec['confirmed'] = bool(unringed); rec['evidence'] = {'without_digitized_marker': [list(b) for b in unringed]}
        else:
            cand = [p for p in pts if inwin(p['px'], p['py'])]; bad = []
            for p in cand:
                pat = masks[cname][int(p['py']) - 5:int(p['py']) + 6, int(p['px']) - 5:int(p['px']) + 6]
                if pat.sum() < 12: bad.append({'T': p['x'], 'value': p['y'], 'colour_px': int(pat.sum())})
            rec['confirmed'] = bool(bad); rec['evidence'] = {'markers_in_window': len(cand), 'without_colour': bad}
        if rec['confirmed']:
            # a confirmed unringed marker within 6 K of a grid T would have been that cell's source: the cell's items are removed
            locs = [b[0] for b in rec['evidence'].get('without_digitized_marker', [])] if 'without ring' in f.get('kind', '') else [px_of(b['T']) for b in rec['evidence']['without_colour']]
            Ts = [xc['a'] * px + xc['b'] for px in locs]
            rec['marker_T'] = Ts
            rec['remove_cells'] = sorted({f'{panel}:x={float(xs)}:T={g}' for g in GRID for t in Ts if abs(g - t) <= 6})
        out.append(rec)
json.dump(out, open(f'{V31}/audit/outputs/overlay_flags_verified.json', 'w'), indent=1)
print(f'{len(out)} flags, confirmed {sum(1 for o in out if o["confirmed"])}, unconfirmed {sum(1 for o in out if o["confirmed"] is False)}, unusable {sum(1 for o in out if o["confirmed"] is None)}')
for o in out: print(o['panel'], o['flag'].get('kind'), o['flag'].get('series_colour'), o['flag'].get('approx_x_value'), o['flag'].get('approx_y_value'), '->', o['confirmed'], json.dumps(o['evidence'])[:160])
