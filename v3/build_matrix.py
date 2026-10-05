#!/usr/bin/env python3
"""build_matrix.py: digitized points -> matrix/cells.jsonl (sample x T x measurement), code only.
Grid T = 300..600 K step 50. A cell takes the marker within 6 K of the grid T if one exists (off by > 1 K: u gains
|slope| x |dT| in quadrature); otherwise linear interpolation
(in log10 for log axes) between the nearest measured neighbours on each side, each within 30 K. No extrapolation: a grid T
outside a series' measured range has no cell. Reading uncertainty u: the marker's own u, or for an interpolated cell the
larger of the two neighbours' u. Also writes matrix/points.jsonl (every digitized marker, for T2/T4 and QA)."""
import json, os, math
V3 = '/home/aid1/Documents/harbor/v3'
GRID = [300, 350, 400, 450, 500, 550, 600]
# measurement per panel; unit strings are the canonical answer units. 'axis_label' is what the panel prints.
PANELS = {
    'F4a': {'quantity': 'n_H', 'name': 'Hall carrier concentration', 'unit': '1e19 cm^-3', 'axis_label': 'n_H (10^19 cm^-3)', 'log': True},
    'F4b': {'quantity': 'mu_H', 'name': 'Hall mobility', 'unit': 'cm^2 V^-1 s^-1', 'log': True,
            'axis_label': 'mu_H (10^19 cm^-3)', 'note': 'axis label prints the carrier-concentration unit (figure typo); caption and text say Hall mobility; unit taken as cm^2 V^-1 s^-1'},
    'F5a': {'quantity': 'rho', 'name': 'electrical resistivity', 'unit': 'uOhm m', 'axis_label': 'rho (uOhm m)', 'log': True},
    'F5b': {'quantity': 'S', 'name': 'Seebeck coefficient', 'unit': 'uV K^-1', 'axis_label': 'S (uV K^-1)', 'log': False},
    'F5c': {'quantity': 'PF', 'name': 'power factor', 'unit': 'uW cm^-1 K^-2', 'axis_label': 'PF (uW cm^-1 K^-2)', 'log': False},
    'F5d': {'quantity': 'kappa', 'name': 'total thermal conductivity', 'unit': 'W m^-1 K^-1', 'axis_label': 'kappa (W m^-1 K^-1)', 'log': False},
    'F5e': {'quantity': 'kappa_e', 'name': 'electronic thermal conductivity', 'unit': 'W m^-1 K^-1', 'axis_label': 'kappa_e (W m^-1 K^-1)', 'log': False},
    'F5f': {'quantity': 'kappa_Lb', 'name': 'lattice plus bipolar thermal conductivity', 'unit': 'W m^-1 K^-1', 'axis_label': 'kappa_L+kappa_b (W m^-1 K^-1)', 'log': False,
            'note': 'axis label kappa_L+kappa_b followed (caption says lattice thermal conductivity)'},
    'F6a': {'quantity': 'ZT', 'name': 'figure of merit ZT', 'unit': '', 'axis_label': 'ZT', 'log': False},
}

def cell(pts, T, log):
    near = [p for p in pts if abs(p['x'] - T) <= 6]
    if near:
        p = min(near, key=lambda q: abs(q['x'] - T)); u = p['u']; dT = p['x'] - T
        if abs(dT) > 1:   # marker off the grid T: add |slope| x |dT| (slope from the nearest other marker) in quadrature
            q = min((q for q in pts if q is not p), key=lambda q: abs(q['x'] - p['x']))
            u = math.hypot(u, abs((q['y'] - p['y']) / (q['x'] - p['x'])) * abs(dT))
        return {'value': p['y'], 'u': u, 'how': 'marker', 'from_T': [round(p['x'], 1)], 'occluded': p.get('occluded', False)}
    L = [p for p in pts if T - 30 <= p['x'] < T]; R = [p for p in pts if T < p['x'] <= T + 30]
    if not L or not R: return None
    a = max(L, key=lambda q: q['x']); b = min(R, key=lambda q: q['x'])
    w = (T - a['x']) / (b['x'] - a['x'])
    if log: v = 10 ** ((1 - w) * math.log10(a['y']) + w * math.log10(b['y']))
    else: v = (1 - w) * a['y'] + w * b['y']
    return {'value': v, 'u': max(a['u'], b['u']), 'how': 'interpolated', 'from_T': [round(a['x'], 1), round(b['x'], 1)],
            'occluded': a.get('occluded', False) or b.get('occluded', False)}

if __name__ == '__main__':
    os.makedirs(f'{V3}/matrix', exist_ok=True); cells, points = [], []
    for panel, meta in PANELS.items():
        d = json.load(open(f'{V3}/digitized/{panel}.json'))
        for xv, pts in d['series'].items():
            for p in pts: points.append({'panel': panel, 'x': float(xv), 'T': p['x'], 'value': p['y'], 'u': p['u'], 'occluded': p.get('occluded', False)})
            for T in GRID:
                c = cell(pts, T, meta['log'])
                if c is None: continue
                cells.append({'id': f'{panel}:x={float(xv)}:T={T}', 'panel': panel, 'sample_x': float(xv), 'T': T, 'quantity': meta['quantity'],
                              'name': meta['name'], 'unit': meta['unit'], 'source': 'digitized', **c, 'rel_u': c['u'] / abs(c['value']) if c['value'] else None})
    with open(f'{V3}/matrix/cells.jsonl', 'w') as f:
        for c in cells: f.write(json.dumps(c) + '\n')
    with open(f'{V3}/matrix/points.jsonl', 'w') as f:
        for p in points: f.write(json.dumps(p) + '\n')
    json.dump(PANELS, open(f'{V3}/matrix/panels.json', 'w'), indent=1)
    import collections
    print(len(cells), 'cells,', len(points), 'points'); print(collections.Counter(c['panel'] for c in cells))
    print('interpolated', sum(c['how'] == 'interpolated' for c in cells), '| occluded-derived', sum(c['occluded'] for c in cells))
