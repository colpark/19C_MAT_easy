#!/usr/bin/env python3
"""stage5a_inputs.py (Stage 5A, steps 1-2): inputs of a paper bundle, from the v0.24 sources (no model call).
 - license: class and verbatim span from selection/license_pool.json (the paper's own statement).
 - text: MinerU md (v0.24 MinerU 2.7.6 output) and pdftotext -raw of the PDF -> v32_host/papers/<key>/text/.
 - panels: the v0.24 panel store (MinerU figures through the unchanged causalmat detect/ocr/match pipeline) -> crops named F<n><letter>
   (single-panel figures: F<n>, the whole figure image) with sha256 and size; full figure images kept as F<n>_full.
 - contamination: v0.24 items quoting the paper (ids, first 150 characters).
 - native micrographs: pdfimages -all -p; each micrograph panel (provisional graph chart_type 'micrograph') is matched to the native
   bitmaps of its page by normalised cross-correlation (crop vs native resized to the crop, and crop inside native resized to the full
   figure); best NCC >= 0.80 = match; native resolution = native px per crop px. Scale bars that are vector overlays (absent from the
   bitmap) are handled where measurements are made (600 dpi render, Stage 5D).
Writes papers/<key>/inputs.json. usage: stage5a_inputs.py <KEY> ..."""
import glob, hashlib, json, os, re, shutil, subprocess, sys
import numpy as np
from PIL import Image
from skimage.feature import match_template
V32 = '/home/aid1/Documents/harbor/v32'; V024 = '/home/aid1/Documents/harbor/v024'
lic = {r['key']: r for r in json.load(open(f'{V32}/selection/license_pool.json'))}
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()

def store_dir(key):
    for d in (f'{V024}/store/SEM2026/{key}', f'{V024}/oa2/store/OA2/{key}'):
        if os.path.isdir(d): return d
    raise SystemExit(f'{key}: no v0.24 store')

def mineru_md(key, pdf):
    # MinerU rewrites the PDF it stores, so identity is by set: S keys (SEM set) under mineru_out, other keys (oa2) under oa2/mineru_out
    safe = os.path.basename(pdf)[:-4]; d = f'{V024}/mineru_out/{safe}/auto' if key.startswith('S') else f'{V024}/oa2/mineru_out/{safe}/auto'
    return f'{d}/{safe}.md' if os.path.exists(f'{d}/{safe}.md') else None

def ncc(a, b):
    a = a - a.mean(); b = b - b.mean(); d = np.sqrt((a * a).sum() * (b * b).sum()); return float((a * b).sum() / d) if d else 0.0

def run(key):
    r = lic[key]; pdf = r['source_file']; PD = f'{V32}/papers/{key.lower()}'; H = f'/home/aid1/Documents/harbor/v32_host/papers/{key.lower()}'
    for d in (PD, f'{H}/text', f'{H}/crops', f'{H}/native'): os.makedirs(d, exist_ok=True)
    out = {'key': key, 'doi': r['doi'], 'license_class': r['license_class'], 'license_span': r['span'], 'pdf': pdf, 'pdf_sha256': sha(pdf)}
    md = mineru_md(key, pdf); out['mineru_md'] = md
    if md: shutil.copy(md, f'{H}/text/{key}.md')
    subprocess.run(['pdftotext', '-raw', pdf, f'{H}/text/{key}_raw.txt'], check=True)
    sd = store_dir(key); m = json.load(open(f'{sd}/panels/match.json')); panels = {}
    for f in m['figures']:
        n = f.get('figure_number')
        if n is None: continue
        full = f'{sd}/{f["file"]}'; shutil.copy(full, f'{H}/crops/F{n}_full.jpg')
        for p in f['panels']:
            pid = f'F{n}' if p['label'] == 'single' or not p.get('crop') else f'F{n}{p["label"].lower()}'
            src = full if not p.get('crop') else f'{sd}/panels/crops/{os.path.basename(p["crop"])}'
            if not os.path.exists(src): continue
            shutil.copy(src, f'{H}/crops/{pid}.jpg'); im = Image.open(src)
            panels[pid] = {'src': src.replace('/home/aid1/', '~/'), 'sha256': sha(src), 'size': im.size, 'figure_file': os.path.basename(full), 'tier': f.get('tier'), 'status': p.get('panel_status')}
    # tier-C figures (detector panel count != caption letters): no store crops. Fallback: the detector's own lettered boxes (panels.json),
    # highest score per letter; 'unverified' when the letter is in neither the caption nor the text letters (e.g. 'T' read for 'l')
    det = {f['file']: f for f in json.load(open(f'{sd}/panels/panels.json'))['figures']}
    for f in m['figures']:
        n = f.get('figure_number')
        if n is None or any(k.startswith(f'F{n}') and (k == f'F{n}' or k[len(f'F{n}'):].isalpha()) for k in panels): continue
        d = det.get(f['file']);
        if not d: continue
        known = set(f.get('letters', {}).get('caption', []) + f.get('letters', {}).get('text', [])); best = {}
        for x in d['detections']:
            if x['label'] == 'single' or not x['label'].isalpha(): continue
            L = x['label'].lower()
            if L not in best or x['score'] > best[L]['score']: best[L] = x
        full = f'{H}/crops/F{n}_full.jpg'; im = Image.open(full)
        for L, x in sorted(best.items()):
            pid = f'F{n}{L}'; x0, y0, x1, y1 = x['bbox']; im.crop((x0, y0, x1, y1)).convert('RGB').save(f'{H}/crops/{pid}.jpg', quality=95)
            panels[pid] = {'src': f"detector box {x['bbox']} of {os.path.basename(f['file'])}", 'sha256': sha(f'{H}/crops/{pid}.jpg'), 'size': [x1 - x0, y1 - y0],
                           'figure_file': os.path.basename(f['file']), 'tier': 'C fallback', 'status': 'detector letter in caption/text' if L in known else 'unverified letter',
                           'detector_score': x['score']}
    out['panels'] = panels
    items = [json.loads(l) for l in open(f'{V024}/panelbench_v024/items.jsonl')]
    out['contamination_v024_items'] = [{'id': i['id'], 'question': (i.get('question') or '')[:150]} for i in items if i.get('paper') == key]
    # native images
    nd = f'{H}/native'
    for f_ in glob.glob(f'{nd}/*'): os.remove(f_)
    subprocess.run(['pdfimages', '-all', '-p', pdf, f'{nd}/img'], check=True)
    natives = sorted(glob.glob(f'{nd}/img-*'))
    gj = json.load(open(f'{V32}/selection/graphs/{key}.json'))
    micro = sorted({p for n in gj['nodes'] if n.get('chart_type') == 'micrograph' and n.get('panel') for p in (n['panel'] if isinstance(n['panel'], list) else [n['panel']])})
    nat = {}
    for pid in micro:
        if pid not in panels: nat[pid] = {'match': None, 'note': 'panel id not in the crop store'}; continue
        c = np.asarray(Image.open(f'{H}/crops/{pid}.jpg').convert('L'), float); fn = re.match(r'F(\d+)', pid).group(1); fig = Image.open(f'{H}/crops/F{fn}_full.jpg')
        best = (0.0, None, None)
        for nf in natives:
            try: N = Image.open(nf).convert('L')
            except Exception: continue
            if min(N.size) < 32: continue
            s1 = ncc(np.asarray(N.resize((c.shape[1], c.shape[0])), float), c)                     # native = the panel
            s2 = 0.0
            if N.size[0] >= c.shape[1] and N.size[1] >= c.shape[0]:
                Nf = np.asarray(N.resize(fig.size), float)                                         # native = the whole figure
                if Nf.shape[0] >= c.shape[0] and Nf.shape[1] >= c.shape[1]: s2 = float(match_template(Nf, c).max())
            s, how = max((s1, 'panel'), (s2, 'figure'))
            if s > best[0]: best = (s, nf, how)
        s, nf, how = best
        if nf and s >= 0.80:
            N = Image.open(nf); scale = N.size[0] / c.shape[1] if how == 'panel' else N.size[0] / fig.size[0]
            nat[pid] = {'match': os.path.basename(nf), 'ncc': round(s, 3), 'as': how, 'native_size': N.size, 'native_px_per_crop_px': round(scale, 2)}
        else: nat[pid] = {'match': None, 'best_ncc': round(s, 3), 'note': 'no native bitmap matches (vector or composite): 600 dpi render in Stage 5D'}
    out['micrographs'] = nat
    json.dump(out, open(f'{PD}/inputs.json', 'w'), indent=1)
    print(f"{key}: {r['license_class']} | md {'yes' if md else 'NO'} | panels {len(panels)} | v0.24 items {len(out['contamination_v024_items'])} | natives {len(natives)} | micrographs matched {sum(1 for v in nat.values() if v.get('match'))}/{len(nat)}")

if __name__ == '__main__':
    for k in sys.argv[1:]: run(k)
