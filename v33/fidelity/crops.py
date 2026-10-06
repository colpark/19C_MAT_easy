#!/usr/bin/env python3
"""fidelity/crops.py (Phase 3): v0.24 crops of the fidelity papers, same procedure as stage5a_inputs.py (store crops; tier-C detector
fallback), no natives, no graphs. Host files only (v32_host/fidelity/<key>/crops); writes fidelity/<key>_panels.json (ids, sha256, tier).
usage: crops.py S001 S021 S030"""
import sys as _pb_s, os as _pb_o
_pb_d = _pb_o.path.dirname(_pb_o.path.abspath(__file__))
while not _pb_o.path.exists(_pb_o.path.join(_pb_d, 'pbroot.py')) and _pb_o.path.dirname(_pb_d) != _pb_d: _pb_d = _pb_o.path.dirname(_pb_d)
_pb_s.path.insert(0, _pb_d)
from pbroot import ROOT, HOST
import hashlib, json, os, shutil, sys
from PIL import Image
V024 = '/home/aid1/Documents/harbor/v024'; OUT = f'{ROOT}/fidelity'
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
for key in sys.argv[1:]:
    sd = f'{V024}/store/SEM2026/{key}'; H = f'{HOST}/fidelity/{key}/crops'; os.makedirs(H, exist_ok=True)
    m = json.load(open(f'{sd}/panels/match.json')); panels = {}
    for f in m['figures']:
        n = f.get('figure_number')
        if n is None: continue
        full = f'{sd}/{f["file"]}'; shutil.copy(full, f'{H}/F{n}_full.jpg')
        for p in f['panels']:
            pid = f'F{n}' if p['label'] == 'single' or not p.get('crop') else f'F{n}{p["label"].lower()}'
            src = full if not p.get('crop') else f'{sd}/panels/crops/{os.path.basename(p["crop"])}'
            if not os.path.exists(src): continue
            shutil.copy(src, f'{H}/{pid}.jpg'); panels[pid] = {'sha256': sha(src), 'size': Image.open(src).size, 'tier': f.get('tier')}
    det = {f['file']: f for f in json.load(open(f'{sd}/panels/panels.json'))['figures']}
    for f in m['figures']:
        n = f.get('figure_number')
        if n is None or any(k.startswith(f'F{n}') and (k == f'F{n}' or k[len(f'F{n}'):].isalpha()) for k in panels): continue
        d = det.get(f['file']); best = {}
        if not d: continue
        for x in d['detections']:
            if x['label'] == 'single' or not x['label'].isalpha(): continue
            L = x['label'].lower()
            if L not in best or x['score'] > best[L]['score']: best[L] = x
        im = Image.open(f'{H}/F{n}_full.jpg')
        for L, x in sorted(best.items()):
            pid = f'F{n}{L}'; x0, y0, x1, y1 = x['bbox']; im.crop((x0, y0, x1, y1)).convert('RGB').save(f'{H}/{pid}.jpg', quality=95)
            panels[pid] = {'sha256': sha(f'{H}/{pid}.jpg'), 'size': [x1 - x0, y1 - y0], 'tier': 'C fallback'}
    json.dump(panels, open(f'{OUT}/{key}_panels.json', 'w'), indent=1); print(key, len(panels), 'panels', sorted(panels))
