#!/usr/bin/env python3
"""pilot_stinville.py (S5, exploratory: the S4b-2 reader failed its held-out real gate, so this table never enters M0). Domains from
IPF_DistordedDIC_X.tif (registered to the DIC grid) at stride 4; per domain (>= DOM_MIN interior-eligible px) the interior mean Exx at
each strain step E1-E4 (0.17, 0.32, 0.61, 1.26 % plastic). Columns: condition, order, unit, sub, value. Unit = domain (spatial)."""
import csv, glob, os, sys
import numpy as np, tifffile
sys.path.insert(0, '/home/aid1/Documents/harbor/v4/trackS/readers'); import stv_reader as R
D = '/home/aid1/Documents/harbor/v4_host/trackS/stinville2022/extracted'
ipf = tifffile.imread(glob.glob(f'{D}/2D*/*/IPF_DistordedDIC_X.tif')[0])[::R.STRIDE, ::R.STRIDE, :3]; lab = R.segment_ipf(ipf)
out = '/home/aid1/Documents/harbor/v4_host/trackS/stinville2022/pilot_stinville.csv'; rows = []
for k, (step, pct) in enumerate((('E1', 0.17), ('E2', 0.32), ('E3', 0.61), ('E4', 1.26))):
    f = tifffile.imread(glob.glob(f'{D}/HRDIC*/*/{step}_718_Exx.tif')[0])[::R.STRIDE, ::R.STRIDE]; f = np.nan_to_num(f)
    m, n = R.domain_mean(f, lab)
    for d in np.where(n >= R.DOM_MIN)[0]: rows.append({'condition': f'{pct}', 'order': k, 'unit': f'domain{d}', 'sub': '', 'value': float(m[d])})
with open(out, 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=['condition', 'order', 'unit', 'sub', 'value']); w.writeheader(); w.writerows(rows)
print(out, len(rows), 'rows;', len({r['unit'] for r in rows}), 'domains')
