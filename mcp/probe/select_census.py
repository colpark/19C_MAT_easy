#!/usr/bin/env python3
"""select_census.py: training crops for the classify_modality probe. MatMech census panels (tiers A/B, with a crop), labelled by the
causalmat panel_modalities rules (caption/definition text -> technique + form; label text is used ONLY to make training labels, never at
tool run time). Label = form, with micrographs and diffraction split by technique. Unambiguous panels only (one technique, a form).
Papers in any PanelBench version are excluded. Up to N per label, fixed seed. Writes census_train.json [{crop, label, doi}]."""
import glob, json, os, random, re, sys
sys.path.insert(0, '/home/aid1/Documents/causalmat/scripts/panels'); from panel_modalities import classify
N = 300; rnd = random.Random(20261001)
H = '/home/aid1/Documents/harbor'
bench = set()
for f in [f'{H}/v022/paper_keys.json', f'{H}/v024/paper_keys.json', f'{H}/v024/oa2/paper_keys.json']:
    bench |= {v['doi'].lower() for v in json.load(open(f)).values()}
def label(techs, form):
    if not form or len(techs) != 1: return None
    t = techs[0]
    if form == 'micrograph': return {'SEM': 'SEM micrograph', 'TEM': 'TEM micrograph', 'AFM/STM': 'AFM/STM image', 'optical microscopy': 'optical micrograph'}.get(t)
    if form == 'diffraction_pattern': return {'XRD': 'XRD pattern', 'TEM': 'electron diffraction'}.get(t)
    if form == 'spatial_map': return 'element map' if t == 'EDS/EDX' else None
    if form == 'orientation_distribution': return 'EBSD map' if t == 'EBSD' else None
    return {'spectrum': 'spectrum', 'xy_curve': 'xy curve', 'schematic': 'schematic', 'photograph': 'photograph', 'simulation_render': 'simulation render'}.get(form)
folders = sorted(glob.glob('/home/aid1/Documents/causalmat/matmech/*/*/panels/match.json')); rnd.shuffle(folders)
by = {}; seen = 0
for mj in folders:
    folder = os.path.dirname(os.path.dirname(mj)); doi = os.path.basename(folder).replace('_', '/').lower()
    if any(b.replace('/', '_') in folder.lower() for b in ()) or doi in bench: continue
    try: m = json.load(open(mj))
    except Exception: continue
    seen += 1
    for f in m.get('figures', []):
        if f['tier'] == 'C': continue
        pre = f.get('caption_preamble') or ''
        for p in f['panels']:
            if not p.get('crop'): continue
            techs, form = classify(f"{p.get('definition') or ''} {pre}".strip())
            lab = label(techs, form)
            if not lab or len(by.get(lab, [])) >= N: continue
            by.setdefault(lab, []).append({'crop': os.path.join(folder, p['crop']), 'label': lab, 'doi': doi})
    if seen % 2000 == 0: print(seen, {k: len(v) for k, v in by.items()}, flush=True)
    if by and all(len(v) >= N for v in by.values()) and len(by) >= 12: break
    if seen > 30000: break
out = [x for v in by.values() for x in v]
json.dump(out, open('/home/aid1/Documents/harbor/mcp/probe/census_train.json', 'w'), indent=0)
print('folders read', seen, '| per label', {k: len(v) for k, v in sorted(by.items())})
