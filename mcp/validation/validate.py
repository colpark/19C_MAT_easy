#!/usr/bin/env python3
"""validate.py (node 2, hub venv): known-answer checks through the hub (the same path the gateway uses). Writes ~/mcp/validation/results.json.
Sections: sem_scale (read_scale_bar px/um, particle_stats mean diameter on myscope renders), sem_optics (FOV vs 127000/M),
plots (axis_calibrate residuals; curve_metrics value_at_x, yield_0p2_offset, peaks on digitized curves and on the true xy),
tem (fft_dspacing / saed_rings on abTEM simulations from the science family, if present), xrd (xrd_phase_match top-1 on noisy simulated
patterns), omnixas (tutorial MSE is reported by the omnixas build), placebo (A2 result == A1 result on the mapped crop).
Flags any tool with relative error above 10% on its own synthetic test. No thresholds gate the build."""
import base64, json, os, sys, urllib.request, numpy as np
V = os.path.expanduser('~/mcp/validation'); R = {}
def call(tool, img=None, args=None, ref=None):
    p = {'tool': tool, 'args': args or {}, 'seed': 0}
    if img is not None: p['image_b64'] = base64.b64encode(img).decode()
    if ref: p['image_ref'] = ref
    r = json.loads(urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8099/call', json.dumps(p).encode(), {'Content-Type': 'application/json'}), timeout=900).read())
    r.pop('images', None); return r
rel = lambda a, b: None if a is None or b in (None, 0) else abs(a - b) / abs(b)
def flag(x): return x is not None and x > 0.10

# --- SEM scale and particle size
T = json.load(open(f'{V}/sem/truth.json')); rows = []
for fn, t in T.items():
    img = open(f'{V}/sem/{fn}', 'rb').read()
    sb = call('read_scale_bar', img); ppu = (sb.get('values') or {}).get('px_per_um')
    ps = call('particle_stats', img, {'source': 'sam'}); d = ((ps.get('values') or {}).get('eqdiam_um') or {}).get('mean')
    rows.append({'image': fn, 'px_per_um_true': t['px_per_um'], 'px_per_um': ppu, 'rel_err_scale': rel(ppu, t['px_per_um']),
                 'diam_true_um': t['feature_size_um'], 'diam_mean_um': d, 'rel_err_diam': rel(d, t['feature_size_um']),
                 'n_particles': (ps.get('values') or {}).get('count'), 'warnings': (sb.get('warnings') or []) + (ps.get('warnings') or [])})
R['sem_scale'] = rows
R['sem_optics'] = []
for m in (1000, 2000, 5000, 10000, 50000):
    fov = (call('sem_optics', args={'magnification': m}).get('values') or {}).get('field_of_view_um')
    R['sem_optics'].append({'magnification': m, 'fov_um': fov, 'expected_um': 127000 / m, 'rel_err': rel(fov, 127000 / m)})

# --- plots
P = json.load(open(f'{V}/plots/truth.json')); rows = []
for name, t in P.items():
    img = open(f'{V}/plots/{name}.png', 'rb').read()
    cal = call('axis_calibrate', img).get('values') or {}
    dig = call('digitize_curve', img).get('values') or {}
    s = (dig.get('series') or [{}]); s = max(s, key=lambda e: e.get('n_points', 0)) if s else {}
    row = {'plot': name, 'kind': t['kind'], 'x_fit': cal.get('x'), 'y_fit': cal.get('y'),
           'x_rel_rms': (cal.get('x') or {}).get('rel_rms_residual'), 'y_rel_rms': (cal.get('y') or {}).get('rel_rms_residual')}
    xy_dig = {'x': s.get('x'), 'y': s.get('y')} if s.get('x') else None
    for src, xy in (('digitized', xy_dig), ('true_xy', {'x': t['x'], 'y': t['y']})):
        if not xy: row[f'{src}_err'] = None; continue
        if t['kind'] in ('linear', 'logy'):
            v = (call('curve_metrics', args={'metric': 'value_at_x', 'xy': xy, 'at': t['at']}).get('values') or {}).get('y'); row[f'{src}_err'] = rel(v, t['y_at'])
        elif t['kind'] == 'stress_strain':
            x = np.asarray(xy['x'], float) / 100.0
            v = (call('curve_metrics', args={'metric': 'yield_0p2_offset', 'xy': {'x': x.tolist(), 'y': xy['y']}}).get('values') or {}).get('yield'); row[f'{src}_err'] = rel(v, t['yield_0p2'])
        else:
            pk = (call('curve_metrics', args={'metric': 'peaks', 'xy': xy}).get('values') or {}).get('peaks') or []
            top = sorted(pk, key=lambda p: -p['prominence'])[:len(t['centers'])]
            err = [min(abs(p['x'] - c) for p in top) / 70.0 for c in t['centers']] if top else None   # relative to the 70 deg axis span
            row[f'{src}_err'] = max(err) if err else None
    rows.append(row)
R['plots'] = rows

# --- TEM (abTEM simulations from the science build: ~/mcp/science/validation/validation.json with known d-spacings and sampling)
tj = os.path.expanduser('~/mcp/science/validation/validation.json')
if os.path.exists(tj):
    TT = json.load(open(tj)); rows = []
    for name, t in TT.items():
        img = open(os.path.join(os.path.dirname(tj), t['png']), 'rb').read(); sim = t['simulation']; known = list(t['known_d_spacings_A'].values())
        if t['args']['mode'] == 'diffraction':
            r = call('saed_rings', img).get('values') or {}; inv = float(np.mean(sim['sampling_invA_per_px']))
            ds = [1.0 / (e['radius_px'] * inv) for e in (r.get('rings') or []) if e['radius_px'] > 0]; tool = 'saed_rings'
        else:
            r = call('fft_dspacing', img).get('values') or {}; spa = float(np.mean(sim['sampling_A_per_px']))
            ds = [p['d_px'] * spa for p in (r.get('peaks') or [])]; tool = 'fft_dspacing'
        strongest = ds[:4]
        err = {str(d0): (min((abs(d - d0) / d0 for d in ds), default=None)) for d0 in known}
        rows.append({'image': t['png'], 'tool': tool, 'known_d_A': known, 'recovered_d_A': [round(d, 3) for d in ds[:8]],
                     'rel_err_per_known_d': err, 'strongest_recovered_match_known': [min(abs(d - d0) / d0 for d0 in known) for d in strongest]})
    R['tem'] = rows
else:
    R['tem'] = 'abTEM validation images not present'

# --- XRD: 10 common phases simulated with pymatgen, broadened (Gaussian FWHM 0.15 deg) + 3% noise -> xrd_phase_match top-1
PH = [('Si', ['Si']), ('Al2O3', ['Al', 'O']), ('ZnO', ['Zn', 'O']), ('NaCl', ['Na', 'Cl']), ('MgO', ['Mg', 'O']), ('CeO2', ['Ce', 'O']),
      ('Cu', ['Cu']), ('TiO2', ['Ti', 'O']), ('Fe3O4', ['Fe', 'O']), ('BaTiO3', ['Ba', 'Ti', 'O'])]
rng = np.random.default_rng(11); rows = []
for f, el in PH:
    sim = call('xrd_simulate', args={'formula': f}).get('values') or {}
    pk = sim.get('peaks') or []; tt = np.asarray([q['two_theta'] for q in pk], float); ii = np.asarray([q['intensity'] for q in pk], float)
    if tt.size == 0: rows.append({'phase': f, 'error': 'no simulated pattern', 'keys': list(sim)[:8]}); continue
    x = np.linspace(10, 90, 3200); y = sum(a * np.exp(-0.5 * ((x - c) / (0.15 / 2.355)) ** 2) for c, a in zip(tt, ii))
    y = y / y.max() + 0.03 * rng.random(x.size)
    m = call('xrd_phase_match', args={'xy': {'x': x.tolist(), 'y': y.tolist()}, 'elements': el}).get('values') or {}
    cands = m.get('top_k') or []
    top1 = (cands[0].get('formula') or cands[0].get('phase') or cands[0].get('name')) if cands else None
    rows.append({'phase': f, 'top1': top1, 'top3': [c.get('formula') or c.get('phase') or c.get('name') for c in cands[:3]], 'method': m.get('method')})
R['xrd'] = rows

# --- placebo: A2 result for a crop == A1 result for its mapped crop
pm = json.load(open(os.path.expanduser('~/mcp/hub/placebo_map.json'))); rows = []
for k, v in list(pm.items())[:5]:
    a2 = call('read_text', ref=v['placebo_sha256']).get('values')
    a1 = call('read_text', open(os.path.expanduser(f"~/mcp/crops/{v['placebo_sha256']}.img"), 'rb').read()).get('values')
    rows.append({'task': v['task'], 'panel': v['panel'], 'equal': a1 == a2})
R['placebo'] = rows
json.dump(R, open(f'{V}/results.json', 'w'), indent=1, default=str)
fl = [('scale', r['image']) for r in R['sem_scale'] if flag(r['rel_err_scale'])] + [('diam', r['image']) for r in R['sem_scale'] if flag(r['rel_err_diam'])]
fl += [('plot', r['plot']) for r in R['plots'] if flag(r.get('digitized_err'))]
print('xrd:', [(r['phase'], r.get('top1')) for r in R['xrd']])
print('flags (>10%):', len(fl), fl[:12]); print('placebo equal:', [r['equal'] for r in R['placebo']])
