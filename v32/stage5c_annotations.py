#!/usr/bin/env python3
"""stage5c_annotations.py (Stage 5C): annotation entries - numbers printed inside an M panel (HRTEM d-spacing labels, FTIR band-position
labels). Two independent reads, both from the image only:
  (1) Tesseract 5 OCR (crop upscaled 3x; upright and rotated 90 deg for vertical labels); numbers with 2+ significant digits;
  (2) a blind GPT-5.6-Sol read: the crop only (no caption, no node text, no expected values) -> every number printed in the image with
      its unit and the series/condition label nearest to it.
An entry is accepted when the OCR set contains the Sol value (equal after rounding to the printed digits); the condition is taken from Sol
and must be one of the paper's conditions where a condition is named. Disagreement drops the entry (more restrictive wins). Sol never sees
or writes a key: entries are M values read from the image, compared by code. Writes papers/<k>/annotations.json.
usage: stage5c_annotations.py   (panels from papers/<k>/features.json with status 'annotation')"""
import json, os, re, sys
V32 = '/home/aid1/Documents/harbor/v32'; sys.path.insert(0, V32)
import pytesseract
from PIL import Image
import audit32 as A
PROMPT = ('This image is one panel from a figure in a materials-science paper. List every number that is printed as text inside the image '
          '(annotations, labels, values; ignore axis tick labels and scale-bar lengths). For each give the exact printed text, its numeric '
          'value, its unit if printed (else ""), and the series or condition label printed nearest to it (for example "x=0.02"; "" if none). '
          'Answer only with JSON: {"numbers": [{"text": "...", "value": <number>, "unit": "...", "label": "..."}]}')
NUM = re.compile(r'(?<![\d.])(\d+\.\d+|\d{2,})(?![\d.])')

def ocr_numbers(im):
    big = im.resize((im.size[0] * 3, im.size[1] * 3)); txt = ''
    for img in (big, big.rotate(-90, expand=True), big.rotate(90, expand=True)):
        txt += '\n' + pytesseract.image_to_string(img, config='--psm 11')
    return sorted({m.group(1) for m in NUM.finditer(txt.replace(',', '.'))}), txt

def same(sol_text, ocr):
    t = re.sub(r'[^\d.]', '', str(sol_text))
    return bool(t) and any(o == t or (('.' in o) and ('.' in t) and abs(float(o) - float(t)) < 10 ** -len(t.split('.')[1]) / 2 + 1e-12) for o in ocr)

if __name__ == '__main__':
    tot = []
    for k in ['s039', 's098', 't042', 't051', 's048']:
        F = json.load(open(f'{V32}/papers/{k}/features.json')); H = f'/home/aid1/Documents/harbor/v32_host/papers/{k}'
        conds = [str(c) for c in json.load(open(f'{V32}/selection/graphs/{k.upper()}.json'))['conditions'].get('values') or []]
        outp = f'{V32}/papers/{k}/annotations.json'; prev = {e['panel']: e for e in json.load(open(outp))['panels']} if os.path.exists(outp) else {}
        rows, calls = [], []
        for f in F:
            if f['status'] != 'annotation': continue
            im = Image.open(f"{H}/crops/{f['panel']}.jpg").convert('RGB'); ocr, _ = ocr_numbers(im)
            if f['panel'] in prev and prev[f['panel']].get('sol') is not None: sol = prev[f['panel']]['sol']
            else:
                r = A.call(PROMPT, im if max(im.size) <= 1600 else im.resize((im.size[0] // 2, im.size[1] // 2)), f"annot:{k}:{f['panel']}"); calls.append(r)
                sol = (A.parse_json(r.get('reply')) or {}).get('numbers', []) if not r.get('error') else None
            ents = []
            for e in (sol or []):
                lab = str(e.get('label', '')); m = re.search(r'x\s*=\s*([0-9.]+)', lab.replace(' ', ''))
                cond = m.group(1).rstrip('.') if m else None; cond_ok = cond is None or any(cond == c or (cond.replace('.', '', 1).isdigit() and c.replace('.', '', 1).replace('-', '', 1).isdigit() and abs(float(cond) - float(c)) < 1e-9) for c in conds)
                ok = same(e.get('text', e.get('value')), ocr) and cond_ok
                ents.append({'text': e.get('text'), 'value': e.get('value'), 'unit': e.get('unit'), 'label': lab, 'condition': cond, 'ocr_match': same(e.get('text', e.get('value')), ocr),
                             'condition_ok': cond_ok, 'accepted': ok})
            rows.append({'panel': f['panel'], 'node': f['node'], 'roles': f['roles'], 'ocr_numbers': ocr, 'sol': sol, 'entries': ents,
                         'accepted': sum(e['accepted'] for e in ents), 'rejected': sum(not e['accepted'] for e in ents)})
            print(k, f['panel'], 'accepted', rows[-1]['accepted'], 'rejected', rows[-1]['rejected'], '| OCR', ocr[:12])
            for e in ents: print('     ', 'OK ' if e['accepted'] else 'NO ', e['text'], e['unit'], e['label'], '| ocr', e['ocr_match'], 'cond', e['condition_ok'])
        if rows:
            cost = A.cost(calls) + (json.load(open(outp)).get('cost', 0) if prev else 0)
            json.dump({'panels': rows, 'cost': cost, 'model': A.MODEL, 'prompt': PROMPT}, open(outp, 'w'), indent=1, ensure_ascii=False); tot.append(cost)
    print('cost total $%.4f' % sum(tot))
