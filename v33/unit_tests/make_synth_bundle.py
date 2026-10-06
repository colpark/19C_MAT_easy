#!/usr/bin/env python3
"""make_synth_bundle.py: a synthetic paper bundle papers/_synth for dry runs of generate.py before any freeze (no real cells).
Cells follow laws.py for invented n_H, mu_H, kappa (as in v3.1 make_synthetic), plus a planted grain-size/density pair for T5/T6 and a
planted image set for the T2 image variant. Nodes/bindings copy paper 1's structure; gen_config copies mo21 and adds the planted sets."""
import sys as _pb_s, os as _pb_o
_pb_d = _pb_o.path.dirname(_pb_o.path.abspath(__file__))
while not _pb_o.path.exists(_pb_o.path.join(_pb_d, 'pbroot.py')) and _pb_o.path.dirname(_pb_d) != _pb_d: _pb_d = _pb_o.path.dirname(_pb_d)
_pb_s.path.insert(0, _pb_d)
from pbroot import ROOT, HOST
import json, os, shutil, sys
V32 = f'{ROOT}'; sys.path.insert(0, V32)
import laws as L, provenance as P
D = f'{V32}/papers/_synth'
if os.path.exists(D): shutil.rmtree(D)
os.makedirs(f'{D}/matrix'); os.makedirs(f'{D}/digitized')
S = [0.0, 0.005, 0.01, 0.02, 0.04]; G = [300, 350, 400, 450, 500, 550, 600]
cells, points = [], []
def add(p, x, T, v, rel=0.02):
    u = rel * abs(v); cells.append({'id': f'{p}:x={x}:T={T}', 'panel': p, 'sample_x': x, 'T': T, 'value': v, 'u': u, 'rel_u': rel, 'how': 'marker', 'occluded': False})
    points.append({'panel': p, 'x': x, 'T': T, 'value': v, 'u': u, 'occluded': False})
for i, x in enumerate(S):
    for T in G:
        n = 0.6 + 0.8 * i + 0.002 * (T - 300); mu = 150 - 10 * i - 0.2 * (T - 300); kap = 1.0 + 0.05 * i + 0.0005 * (T - 300)
        rho = L.rho_hall(n, mu); s = -L.spb_S(n, T, 1.2); ke = L.kappa_e(s, rho, T)
        v = {'F4a': n, 'F4b': mu, 'F5a': rho, 'F5b': s, 'F5c': L.pf(s, rho) * (0.6 if x == 0.005 else 1.0), 'F5d': kap, 'F5e': ke * (8 if x == 0 else 1.0),
             'F5f': kap - ke, 'F6a': L.zt(s, rho, kap, T), 'G1': 2.0 + 3.0 * i, 'G2': 0.90 + 0.01 * i}   # G1 grain size grows with x; G2 density flat-ish
        for p, val in v.items(): add(p, x, T, val)
json.dump(cells and None, open(os.devnull, 'w'))
with open(f'{D}/matrix/cells.jsonl', 'w') as f:
    for c in cells: f.write(json.dumps(c) + '\n')
with open(f'{D}/matrix/points.jsonl', 'w') as f:
    for c in points: f.write(json.dumps(c) + '\n')
panels = json.load(open(f'{V32}/papers/mo21/panels.json'))
panels['G1'] = {'quantity': 'grain_size', 'name': 'grain size', 'unit': 'um', 'log': False}; panels['G2'] = {'quantity': 'density', 'name': 'relative density', 'unit': '', 'log': False}
json.dump(panels, open(f'{D}/panels.json', 'w'))
shutil.copy(f'{V32}/papers/mo21/matrix/text_values.jsonl', f'{D}/matrix/')
for p in list(panels):
    json.dump({'status': 'ok', 'legend': {'declared_check': {'ok': True}}, 'series': {str(x): [{}] * 5 for x in S}}, open(f'{D}/digitized/{p}.json', 'w'))
nodes = json.load(open(f'{V32}/papers/mo21/nodes.json'))
nodes += [{'id': 'grain', 'quantity': 'grain_size', 'panel': 'G1', 'level': 'M', 'evidence': {'kind': 'span', 'text': 'synthetic'}},
          {'id': 'dens', 'quantity': 'density', 'panel': 'G2', 'level': 'M', 'evidence': {'kind': 'span', 'text': 'synthetic'}}]
json.dump(nodes, open(f'{D}/nodes.json', 'w'))
shutil.copy(f'{V32}/papers/mo21/law_bindings.json', f'{D}/law_bindings.json')
json.dump({'syn_grain_growth': {'mechanism': 'grain growth with Se content', 'relation': 'boundary mobility rises with x', 'source': 'synthetic', 'prior_rank': 1,
                                'predicts': {'grain(x up)': 'up', 'density(x up)': 'none', 'kappa(x up)': 'up'}},
           'syn_pinning': {'mechanism': 'Se pins boundaries', 'relation': 'Zener pinning', 'source': 'synthetic', 'prior_rank': 2,
                           'predicts': {'grain(x up)': 'down', 'density(x up)': 'none', 'kappa(x up)': 'up'}},
           'syn_none_a': {'mechanism': 'mechanism P', 'relation': 'r1', 'source': 'synthetic', 'prior_rank': 1, 'predicts': {'density(x up)': 'up'}},
           'syn_none_b': {'mechanism': 'mechanism Q', 'relation': 'r2', 'source': 'synthetic', 'prior_rank': 2, 'predicts': {'density(x up)': 'down'}}},
          open(f'{D}/signatures.json', 'w'))
json.dump({'img_set_1': {'0.0': {'intercept': [2.0, 0.1], 'equivalent': [2.2, 0.1]}, '0.01': {'intercept': [5.0, 0.2], 'equivalent': [5.4, 0.25]},
                         '0.04': {'intercept': [14.0, 0.5], 'equivalent': [15.0, 0.6]}}}, open(f'{D}/matrix/image_measurements.json', 'w'))
cfg = open(f'{V32}/papers/mo21/gen_config.py').read()
cfg = cfg.replace("PAPER = 'mo21'", "PAPER = '_synth'").replace("RELEASE_ELIGIBLE = False", "RELEASE_ELIGIBLE = True")
cfg = cfg.replace("SIGNATURE_PAIRS = []", """SIGNATURE_PAIRS = [
    {'id': 'pair_grain', 'mechanisms': ['syn_grain_growth', 'syn_pinning'], 'cause_panels': ['F4a'], 'outcome_panels': ['G1'],
     'comparisons': [{'obs': 'grain(x up)', 'panel': 'G1', 'quantity': 'grain size', 'a': [0.0, 300], 'b': [0.04, 300]},
                     {'obs': 'density(x up)', 'panel': 'G2', 'quantity': 'relative density', 'a': [0.0, 300], 'b': [0.04, 300]},
                     {'obs': 'kappa(x up)', 'panel': 'F5d', 'quantity': 'total thermal conductivity', 'a': [0.0, 300], 'b': [0.04, 300]}],
     'unconstrained': 'the optical band gap', 'authors_choice': 'syn_pinning', 'authors_span': 'synthetic'},
    {'id': 'pair_flat', 'mechanisms': ['syn_none_a', 'syn_none_b'], 'cause_panels': ['F4a'], 'outcome_panels': ['G2'],
     'comparisons': [{'obs': 'density(x up)', 'panel': 'G2', 'quantity': 'relative density', 'a': [0.0, 300], 'b': [0.005, 300]}],
     'unconstrained': 'hardness', 'authors_choice': 'syn_none_a', 'authors_span': 'synthetic'}]""")
cfg = cfg.replace("IMAGE_SETS = []", "IMAGE_SETS = [{'id': 'img_set_1', 'micrographs': {0.0: 'M0', 0.01: 'M1', 0.04: 'M2'}, 'ref_panel': 'G1', 'ref_T': 300}]")
if '--images' in sys.argv:   # image dry run: synthetic crops; the plot-variant T2 needs real digitized frames, so T2_SETS is emptied
    cfg = cfg.replace("T2_SETS = [", "T2_SETS_UNUSED = [") + "\nT2_SETS = []\n"
    import numpy as np
    from PIL import Image
    H = f'{HOST}/papers/_synth/crops'; os.makedirs(H, exist_ok=True)
    for i, p in enumerate(['M0', 'M1', 'M2'] + list(panels) + ['F3a', 'F3b', 'F3c', 'F3d', 'F3e', 'F3f']):
        Image.fromarray((np.random.RandomState(i).rand(200, 260, 3) * 255).astype('uint8')).save(f'{H}/{p}.jpg', quality=90)
cfg = cfg.replace("DESC = {", "DESC = {'M0': 'micrograph', 'M1': 'micrograph', 'M2': 'micrograph', ")
cfg = cfg.replace("DESC = {", "DESC = {'G1': 'grain size versus temperature', 'G2': 'relative density versus temperature', ")
cfg = cfg.replace("Q_PANEL = {", "Q_PANEL = {'grain_size': 'G1', 'density': 'G2', ")
cfg = cfg.replace("UNIT_SHOW = {", "UNIT_SHOW = {'um': 'µm', ").replace("T1_EXAMPLE = {", "T1_EXAMPLE = {'um': '3.5 um', ")
cfg = cfg.replace("QNAME = {", "QNAME = {'grain_size': 'grain size', 'density': 'relative density', ")
open(f'{D}/gen_config.py', 'w').write(cfg)
print('synthetic bundle written:', len(cells), 'cells')
