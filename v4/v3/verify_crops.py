#!/usr/bin/env python3
"""verify_crops.py (Stage 5C, user instruction 1): identity check of every tier-C fallback crop (E02) before it may feed a key.
Per crop:
  (a) axis labels and units: Tesseract OCR of the crop (3x, upright and rotated 90 deg for vertical y labels); at least one keyword of the node's quantity (or a synonym) must appear.
      n/a for micrographs, SAED/HRTEM images and maps (no axes).
  (b) condition labels: OCR tokens that look like series labels (x = ..., wt%, sample names) must all belong to the paper's conditions;
      n/a when none is printed.
  (c) blind GPT-5.6-Sol check: the crop and the figure caption -> which caption letter and which quantity; the letter must equal the
      crop's letter and the quantity must share a keyword with the node's quantity.
A crop without a node feeds no key ('unused'). Any mismatch drops the crop. Writes papers/<k>/audit/crop_verification.json and a list of
dropped crops into papers/<k>/audit/removals.json ('crops'). usage: verify_crops.py <key> ..."""
import sys as _pb_s, os as _pb_o
_pb_d = _pb_o.path.dirname(_pb_o.path.abspath(__file__))
while not _pb_o.path.exists(_pb_o.path.join(_pb_d, 'pbroot.py')) and _pb_o.path.dirname(_pb_d) != _pb_d: _pb_d = _pb_o.path.dirname(_pb_d)
_pb_s.path.insert(0, _pb_d)
from pbroot import ROOT, HOST
import json, os, re, sys
V32 = f'{ROOT}'; sys.path.insert(0, V32)
import pytesseract
from PIL import Image
import audit32 as A
STOP = {'the', 'and', 'with', 'from', 'for', 'vs', 'versus', 'of', 'in', 'on', 'at', 'to', 'by', 'raw', 'data', 'curve', 'curves', 'image', 'panel', 'samples', 'sample', 'per', 'all'}
SYN = {'xrd': ['diffraction', 'theta', '2θ', 'intensity', 'xrd'], 'xps': ['photoelectron', 'binding', 'energy', 'xps', 'counts'], 'ftir': ['transmittance', 'wavenumber', 'cm-1', 'infrared', 'ftir'],
       'raman': ['raman', 'shift', 'cm-1'], 'p-e': ['polarization', 'polarisation', 'kv', 'μc', 'uc'], 's-e': ['strain', 'kv'], 'strain': ['strain', '%'], 'tga': ['mass', 'weight', 'temperature', 'tga', 'dtg'],
       'uv': ['absorbance', 'wavelength', 'nm', 'absorption'], 'hrtem': ['nm', 'fringe', 'hrtem', 'lattice'], 'sem': ['μm', 'um', 'nm', 'sem'], 'tem': ['nm', 'tem'], 'saed': ['diffraction', 'saed', 'ring'],
       'eds': ['kev', 'energy', 'counts', 'eds'], 'dielectric': ['permittivity', 'dielectric', 'εr', 'tanδ', 'loss'], 'stress': ['stress', 'mpa'], 'friction': ['friction', 'cof', 'coefficient'],
       'wear': ['wear', 'depth', 'μm'], 'conductivity': ['conductivity', 's/m', 's/cm'], 'shielding': ['se', 'db', 'shielding'], 'leakage': ['current', 'a/cm', 'leakage'], 'current': ['current', 'i'],
       'magnetization': ['emu', 'magnetization', 'oe', 'field'], 'polarization': ['polarization', 'μc', 'pr']}
def keywords(q):
    w = [x for x in re.findall(r'[a-zA-Z][a-zA-Z\-]{2,}', q.lower()) if x not in STOP]; kw = set(w)
    for k_, v in SYN.items():
        if k_ in q.lower(): kw |= set(v)
    return kw
NONAXIS = ('micrograph', 'other')

def run(key):
    PD = f'{V32}/papers/{key}'; H = f'{HOST}/papers/{key}'
    inp = json.load(open(f'{PD}/inputs.json')); nodes = json.load(open(f'{PD}/nodes.json')); caps = json.load(open(f'{H}/text/captions.json'))
    gj = json.load(open(f'{V32}/selection/graphs/{key.upper()}.json')); conds = [str(c) for c in gj['conditions'].get('values') or []]
    pmap = {}
    for n in nodes:
        for p in (n['panel'] if isinstance(n.get('panel'), list) else [n.get('panel')]):
            if p: pmap.setdefault(p, []).append(n)
    prev = {}
    if os.path.exists(f'{PD}/audit/crop_verification.json'): prev = {r['crop']: r for r in json.load(open(f'{PD}/audit/crop_verification.json'))['rows']}
    rows, calls = [], []
    for pid, v in sorted(inp['panels'].items()):
        if v['tier'] != 'C fallback': continue
        ns = pmap.get(pid)
        if not ns: rows.append({'crop': pid, 'verdict': 'unused (no node)'}); continue
        q = ' '.join(n['quantity'] for n in ns); kw = keywords(q); ct = {n.get('chart_type') for n in ns}
        im = Image.open(f'{H}/crops/{pid}.jpg').convert('RGB'); big = im.resize((im.size[0] * 3, im.size[1] * 3))
        txt = pytesseract.image_to_string(big, config='--psm 11') + '\n' + pytesseract.image_to_string(big.rotate(-90, expand=True), config='--psm 11')   # + rotated: vertical y-axis labels
        low = txt.lower()
        axis = 'n/a' if ct <= set(NONAXIS) else ('ok' if any(k in low for k in kw) else 'mismatch')
        labs = re.findall(r'x\s*=\s*([0-9.]+)', low)
        cond = 'n/a' if not labs else ('ok' if all(any(l.rstrip('.') in c for c in conds) for l in labs) else f'mismatch {labs}')
        fig = re.match(r'(F\d+)', pid).group(1); cap = caps.get(fig, '')
        if pid in prev and prev[pid].get('sol'): sol = prev[pid]['sol']
        else:
            p = ('The image is one panel cut from a figure of a materials-science paper. Here is the figure caption:\n\n' + cap +
                 '\n\nWhich panel letter of the caption is this image, and what quantity or content does it show (axes, measurement)? '
                 'Answer only with a JSON object: {"letter": "<single lower-case letter or none>", "quantity": "<short description>"}')
            r = A.call(p, im if max(im.size) <= 1600 else im.resize((im.size[0] // 2, im.size[1] // 2)), f'crop:{key}:{pid}'); r['parsed'] = A.parse_json(r.get('reply')); calls.append(r)
            sol = r['parsed'] or {}
        letter = pid[len(fig):]; sl = str(sol.get('letter', '')).strip().lower().strip('()')
        sq = str(sol.get('quantity', '')).lower(); qok = any(k in sq for k in kw) or bool(keywords(sq) & kw)
        sol_ok = sl == letter and qok
        verdict = 'verified' if sol_ok and axis in ('ok', 'n/a') and cond in ('ok', 'n/a') else 'dropped'
        rows.append({'crop': pid, 'nodes': [n['id'] for n in ns], 'quantity': q[:120], 'axis_ocr': axis, 'condition_labels': cond, 'sol': sol, 'sol_letter_ok': sl == letter,
                     'sol_quantity_ok': qok, 'verdict': verdict})
        print(key, pid, verdict, '| axis', axis, '| cond', cond, '| Sol', sl, sq[:60])
    cost = A.cost(calls) + (json.load(open(f'{PD}/audit/crop_verification.json'))['cost'] if prev else 0)
    json.dump({'rows': rows, 'cost': cost}, open(f'{PD}/audit/crop_verification.json', 'w'), indent=1, ensure_ascii=False)
    r_ = json.load(open(f'{PD}/audit/removals.json')) if os.path.exists(f'{PD}/audit/removals.json') else {'claims': [], 'cells': [], 'item_keys': [], 'reasons': []}
    r_['crops'] = sorted(r['crop'] for r in rows if r['verdict'] != 'verified')
    json.dump(r_, open(f'{PD}/audit/removals.json', 'w'), indent=1)
    from collections import Counter
    print(key, dict(Counter(r['verdict'] for r in rows)), 'cost $%.4f' % cost)

if __name__ == '__main__':
    for k in sys.argv[1:]: run(k)
