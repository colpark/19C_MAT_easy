#!/usr/bin/env python3
"""build_matrix.py: digitized points -> matrix/cells.jsonl (sample x T x measurement), code only.
Grid T = 300..600 K step 50. A cell takes the marker within 6 K of the grid T if one exists (off by > 1 K: u gains
|slope| x |dT| in quadrature); otherwise linear interpolation
(in log10 for log axes) between the nearest measured neighbours on each side, each within 30 K. No extrapolation: a grid T
outside a series' measured range has no cell. Reading uncertainty u: the marker's own u, or for an interpolated cell the
larger of the two neighbours' u. Also writes matrix/points.jsonl (every digitized marker, for T2/T4 and QA)."""
import sys as _pb_s, os as _pb_o
_pb_d = _pb_o.path.dirname(_pb_o.path.abspath(__file__))
while not _pb_o.path.exists(_pb_o.path.join(_pb_d, 'pbroot.py')) and _pb_o.path.dirname(_pb_d) != _pb_d: _pb_d = _pb_o.path.dirname(_pb_d)
_pb_s.path.insert(0, _pb_d)
from pbroot import ROOT, HOST
import json, os, math
import sys
V3 = f'{ROOT}'
# v3.2: paper-driven. papers/<paper>/profile.json 'matrix' gives the grid along the x axis and the windows; papers/<paper>/panels.json
# gives the measurement per panel (quantity, name, unit, axis label, log).
PAPER = sys.argv[1] if len(sys.argv) > 1 else 'mo21'; PD = f'{V3}/papers/{PAPER}'
MX = json.load(open(f'{PD}/profile.json'))['matrix']; GRID = MX['grid']
PANELS = json.load(open(f'{PD}/panels.json'))

def cell(pts, T, log):
    near = [p for p in pts if abs(p['x'] - T) <= MX['marker_window']]
    if near:
        p = min(near, key=lambda q: abs(q['x'] - T)); u = p['u']; dT = p['x'] - T
        if abs(dT) > MX['slope_term_above']:   # marker off the grid T: add |slope| x |dT| (slope from the nearest other marker) in quadrature
            q = min((q for q in pts if q is not p), key=lambda q: abs(q['x'] - p['x']))
            u = math.hypot(u, abs((q['y'] - p['y']) / (q['x'] - p['x'])) * abs(dT))
        return {'value': p['y'], 'u': u, 'how': 'marker', 'from_T': [round(p['x'], 1)], 'occluded': p.get('occluded', False)}
    L = [p for p in pts if T - MX['interp_max_gap'] <= p['x'] < T]; R = [p for p in pts if T < p['x'] <= T + MX['interp_max_gap']]
    if not L or not R: return None
    a = max(L, key=lambda q: q['x']); b = min(R, key=lambda q: q['x'])
    w = (T - a['x']) / (b['x'] - a['x'])
    if log: v = 10 ** ((1 - w) * math.log10(a['y']) + w * math.log10(b['y']))
    else: v = (1 - w) * a['y'] + w * b['y']
    return {'value': v, 'u': max(a['u'], b['u']), 'how': 'interpolated', 'from_T': [round(a['x'], 1), round(b['x'], 1)],
            'occluded': a.get('occluded', False) or b.get('occluded', False)}

if __name__ == '__main__':
    os.makedirs(f'{PD}/matrix', exist_ok=True); cells, points = [], []
    for panel, meta in PANELS.items():
        d = json.load(open(f'{PD}/digitized/{panel}.json'))
        for xv, pts in d['series'].items():
            for p in pts: points.append({'panel': panel, 'x': float(xv), 'T': p['x'], 'value': p['y'], 'u': p['u'], 'occluded': p.get('occluded', False)})
            for T in GRID:
                c = cell(pts, T, meta['log'])
                if c is None: continue
                cells.append({'id': f'{panel}:x={float(xv)}:T={T}', 'panel': panel, 'sample_x': float(xv), 'T': T, 'quantity': meta['quantity'],
                              'name': meta['name'], 'unit': meta['unit'], 'source': 'digitized', **c, 'rel_u': c['u'] / abs(c['value']) if c['value'] else None})
    cells.sort(key=lambda c: (c['panel'], c['sample_x'], c['T'])); points.sort(key=lambda p: (p['panel'], p['x'], p['T']))   # canonical order
    with open(f'{PD}/matrix/cells.jsonl', 'w') as f:
        for c in cells: f.write(json.dumps(c) + '\n')
    with open(f'{PD}/matrix/points.jsonl', 'w') as f:
        for p in points: f.write(json.dumps(p) + '\n')
    json.dump(PANELS, open(f'{PD}/matrix/panels.json', 'w'), indent=1)   # copy for downstream readers
    import collections
    print(len(cells), 'cells,', len(points), 'points'); print(collections.Counter(c['panel'] for c in cells))
    print('interpolated', sum(c['how'] == 'interpolated' for c in cells), '| occluded-derived', sum(c['occluded'] for c in cells))
