#!/usr/bin/env python3
"""stage5c_tem_inputs.py (Stage 5C recovery): profile inputs for lattice.py on the real HRTEM/SAED panels, each with evidence and a blind
GPT-5.6-Sol check from the image only (rule 3): scale-bar label text, the half of the panel holding the bar, and (SAED) the number of
indexed rings / hkl labels printed. Builder entries were read off the panel by eye; Sol answers without seeing them; any disagreement drops
the panel (more restrictive wins). OCR of the bar label (lattice.calibrate) is logged as a third read. Writes papers/<k>/tem_inputs.json."""
import json, os, sys
V32 = '/home/aid1/Documents/harbor/v32'; sys.path.insert(0, V32)
import numpy as np
from PIL import Image
import audit32 as A, lattice as LT
BUILDER = {
 's039': {'F4h': {'kind': 'hrtem', 'bar_label': '10 nm', 'where': 'left', 'hkl': ['(111)'], 'condition_evidence': 'caption: HRTEM (g-i) for x = 0.00, 0.04, 0.08'},
          'F4j': {'kind': 'saed', 'bar_label': '5 1/nm', 'where': 'left', 'hkl': ['(220)', '(311)', '(400)', '(422)', '(511)', '(440)'], 'condition_evidence': 'caption: SAED (j-l) for x = 0.00, 0.04, 0.08'},
          'F4k': {'kind': 'saed', 'bar_label': '5 1/nm', 'where': 'left', 'hkl': ['(220)', '(311)', '(400)', '(422)', '(511)', '(440)'], 'condition_evidence': 'caption: SAED (j-l) for x = 0.00, 0.04, 0.08'}},
 't042': {'F3a': {'kind': 'hrtem', 'bar_label': '5 nm', 'where': 'right', 'hkl': ['(222)']}, 'F3b': {'kind': 'hrtem', 'bar_label': '5 nm', 'where': 'right', 'hkl': ['(220)']}},
}
PROMPT = ('This is one panel of a figure from a materials-science paper (an electron micrograph or an electron diffraction pattern). Answer only '
          'with JSON: {"scale_bar_label": "<the text of the scale bar label exactly as printed, e.g. 5 nm>", "scale_bar_side": "left|right", '
          '"hkl_labels": ["<every Miller-index label printed in the image, e.g. (220)>"]}')
norm = lambda s: str(s).replace(' ', '').replace('nm-1', '1/nm').replace('nm⁻¹', '1/nm').lower()
if __name__ == '__main__':
    for k, panels in BUILDER.items():
        H = f'/home/aid1/Documents/harbor/v32_host/papers/{k}/crops'; outp = f'{V32}/papers/{k}/tem_inputs.json'
        prev = json.load(open(outp))['panels'] if os.path.exists(outp) else {}; rows, calls = {}, []
        for pid, b in panels.items():
            im = Image.open(f'{H}/{pid}.jpg').convert('RGB')
            if pid in prev and prev[pid].get('sol'): sol = prev[pid]['sol']
            else:
                r = A.call(PROMPT, im, f'tem_inputs:{k}:{pid}'); calls.append(r); sol = A.parse_json(r.get('reply')) or {}
            rgb = np.asarray(im); cal = LT.calibrate(rgb, rgb.mean(2), declared=b['bar_label'], where=b['where'])
            ok_lab = norm(sol.get('scale_bar_label')) == norm(b['bar_label']); ok_side = str(sol.get('scale_bar_side', '')).lower() == b['where']
            ok_hkl = sorted(norm(h) for h in sol.get('hkl_labels', [])) == sorted(norm(h) for h in b['hkl'])
            agree = ok_lab and ok_side and ok_hkl
            rows[pid] = dict(b, sol=sol, sol_label_ok=ok_lab, sol_side_ok=ok_side, sol_hkl_ok=ok_hkl, ocr_label_agrees=cal and cal.get('ocr_agrees'),
                             bar_px=cal and cal['bar_px'], bar_box=cal and cal['bar_box'], status='accepted' if agree and cal else 'dropped')
            print(k, pid, rows[pid]['status'], '| Sol', sol, '| bar px', cal and round(cal['bar_px'], 1), 'OCR agrees', cal and cal.get('ocr_agrees'))
        cost = A.cost(calls) + (json.load(open(outp)).get('cost', 0) if os.path.exists(outp) else 0)
        json.dump({'panels': rows, 'cost': cost, 'prompt': PROMPT, 'model': A.MODEL}, open(outp, 'w'), indent=1, ensure_ascii=False)
