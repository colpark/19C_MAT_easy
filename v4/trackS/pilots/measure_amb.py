#!/usr/bin/env python3
"""measure_amb.py (S4a held-out step and S5 pilot table, frozen reader amb_reader.py): melt-pool depth of every single-track .ctf
(the top field; 'bottom' fields are not stitched), joined to its laser case by the frozen join rules (S2j-amb). A track is censored when
the pool reaches the last SURF_UM of the map (the field is shallower than the pool). Writes v4_host/trackS/amb2022_03/pilot_amb.csv
(condition, order, unit, sub, value) and amb_depths.json (every track, with censoring and the reader output)."""
import csv, glob, json, os, re, sys
import numpy as np
sys.path.insert(0, '/home/aid1/Documents/harbor/v4/trackS/readers'); import amb_reader as A
H = '/home/aid1/Documents/harbor/v4_host/trackS/amb2022_03'; R = json.load(open('/home/aid1/Documents/harbor/v4/trackS/joinrules/amb2022_03.json'))
TM = R['maps']['track']; ORDER = R['order']['case']
from multiprocessing import Pool
def one(p):
    b = os.path.basename(p); m = re.search(r'Map Data \d+[_-](L?-?\d{2,3})( bottom)?\.ctf$', b)
    if not m or m.group(2): return None
    tr = m.group(1); meta = TM.get(tr) or TM.get('L' + tr)
    ph, eul, bc, st = A.read_ctf(p); r = A.measure(ph, eul, st)
    lab_h = ph.shape[0] * st; surf_top = float(np.argmax((ph > 0).any(1)) * st)
    cens = bool(r['found'] and r['depth_um'] + surf_top >= lab_h - A.SURF_UM)
    return {'file': b, 'track': tr, 'case': meta['case'], 'rep': meta['rep'], 'E_J_mm2': meta['E_J_mm2'], 'step_um': st, 'grid': list(ph.shape), **r, 'censored': cens,
            'indexed_frac': float((ph > 0).mean())}
if __name__ == '__main__':
    files = sorted(glob.glob(f'{H}/files/**/*Site*Map Data*.ctf', recursive=True))
    with Pool(6) as P: rows = [r for r in P.map(one, files) if r]
    json.dump(rows, open(f'{H}/amb_depths.json', 'w'), indent=1)
    with open(f'{H}/pilot_amb.csv', 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['condition', 'order', 'unit', 'sub', 'value']); w.writeheader()
        for r in rows:
            if r['found'] and not r['censored']: w.writerow({'condition': r['case'], 'order': ORDER.index(r['case']), 'unit': r['track'], 'sub': '', 'value': r['depth_um']})
    for r in sorted(rows, key=lambda r: (ORDER.index(r['case']), r['rep'])): print(r['case'], r['rep'], r['track'], round(r['depth_um'], 1), round(r['width_um'], 1), 'censored' if r['censored'] else '', 'not found' if not r['found'] else '')
