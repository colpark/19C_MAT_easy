#!/usr/bin/env python3
"""readers.py sub-frame crop: two replicas stacked vertically into one image read the same through pc['crop'] as standalone."""
import sys as _pb_s, os as _pb_o
_pb_d = _pb_o.path.dirname(_pb_o.path.abspath(__file__))
while not _pb_o.path.exists(_pb_o.path.join(_pb_d, 'pbroot.py')) and _pb_o.path.dirname(_pb_d) != _pb_d: _pb_d = _pb_o.path.dirname(_pb_d)
_pb_s.path.insert(0, _pb_d)
from pbroot import ROOT, HOST
import json, os, sys, tempfile
import numpy as np
from PIL import Image
sys.path.insert(0, f'{ROOT}'); import readers as R
O = f'{HOST}/feature_replicas'; T = f'{ROOT}/replicas/feature_truth'
a, b = 't042_curve_r0', 't042_curve_r1'
ia, ib = Image.open(f'{O}/{a}/panel.jpg'), Image.open(f'{O}/{b}/panel.jpg')
W = max(ia.size[0], ib.size[0]); im = Image.new('RGB', (W, ia.size[1] + ib.size[1]), 'white'); im.paste(ia, (0, 0)); im.paste(ib, (0, ia.size[1]))
tmp = tempfile.mkdtemp(); p = f'{tmp}/stack.png'; im.save(p)
fails = 0
for name, box in ((a, [0, 0, ia.size[0], ia.size[1]]), (b, [0, ia.size[1], ib.size[0], ia.size[1] + ib.size[1]])):
    t = json.load(open(f'{T}/{name}.json')); solo = R.Panel(f'{O}/{name}/panel.jpg', t['pc']); pc = dict(t['pc'], crop=box); cr = R.Panel(p, pc)
    for ft in t['truth']['features']:
        r1, r2 = R.read(solo, ft), R.read(cr, ft)
        same = (r1 is None and r2 is None) or (r1 is not None and r2 is not None and abs(r1[0] - r2[0]) <= 1e-9 + 0.05 * r1[1])
        fails += not same
print('crop test:', 'PASS' if fails == 0 else f'FAIL ({fails})')
sys.exit(1 if fails else 0)
