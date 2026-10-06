#!/usr/bin/env python3
"""stage5c_tem_measure.py (Stage 5C recovery): frozen lattice.py (F5) on the real panels whose profile inputs passed the blind Sol check
(papers/<k>/tem_inputs.json). Only styles that passed the TEM replica gate are measured (hrtem_s039g failed: s039 F4g is not measured).
Writes papers/<k>/tem_measurements.json (logged; keys are made in 5D/5E)."""
import sys as _pb_s, os as _pb_o
_pb_d = _pb_o.path.dirname(_pb_o.path.abspath(__file__))
while not _pb_o.path.exists(_pb_o.path.join(_pb_d, 'pbroot.py')) and _pb_o.path.dirname(_pb_d) != _pb_d: _pb_d = _pb_o.path.dirname(_pb_d)
_pb_s.path.insert(0, _pb_d)
from pbroot import ROOT, HOST
import json, sys
V32 = f'{ROOT}'; sys.path.insert(0, V32)
import numpy as np
from PIL import Image
import lattice as LT
STYLE = {('s039', 'F4h'): 'hrtem_s039h', ('s039', 'F4j'): 'saed_s039j', ('s039', 'F4k'): 'saed_s039k', ('t042', 'F3a'): 'hrtem_t042'}
gate = {r['style']: r['pass'] for r in json.load(open(f'{V32}/replicas/tem_check.json'))}
for k in ('s039', 't042'):
    inp = json.load(open(f'{V32}/papers/{k}/tem_inputs.json'))['panels']; out = {}
    for pid, b in inp.items():
        st = STYLE.get((k, pid))
        if b['status'] != 'accepted' or not st or not gate.get(st): out[pid] = {'status': 'not measured', 'why': b['status'] if b['status'] != 'accepted' else f'style {st} not validated'}; print(k, pid, out[pid]); continue
        rgb = np.asarray(Image.open(f'{HOST}/papers/{k}/crops/{pid}.jpg').convert('RGB')); g = rgb.mean(2)
        cal = LT.calibrate(rgb, g, declared=b['bar_label'], where=b['where'])
        if b['kind'] == 'hrtem':
            m = LT.hrtem(g, cal['px_per_unit'], region=(0, 0, g.shape[1], int(0.85 * g.shape[0])), bar_px=cal['bar_px'])
            out[pid] = {'status': 'measured' if m else 'no fringe peak', 'calibration': cal, 'hkl': b['hkl'], 'result': m}
        else:
            m = LT.saed(g, len(b['hkl']), cal['px_per_unit'], bar_px=cal['bar_px'], exclude=[cal['bar_box']])
            st_ = 'refused' if isinstance(m, dict) else ('measured' if m else 'rings not found')
            out[pid] = {'status': st_, 'calibration': cal, 'hkl': b['hkl'], 'result': m if not isinstance(m, list) else [dict(r, hkl=h) for r, h in zip(m, b['hkl'])]}
        print(k, pid, out[pid]['status'], json.dumps(out[pid]['result'], default=float)[:300])
    json.dump(out, open(f'{V32}/papers/{k}/tem_measurements.json', 'w'), indent=1, default=float)
