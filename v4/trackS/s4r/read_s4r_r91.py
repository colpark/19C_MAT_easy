#!/usr/bin/env python3
"""read_s4r_r91.py (S4r on refodat91 real tiles): the frozen reader on every tile, dev and held-out flagged (split_refodat91.json).
Writes <out>/s4r_r91_tiles.csv (specimen, w_c, carbonation, block, tile, porosity, anhydrous, hydrate, aggregate_frac, sat_frac, t_pore,
t_anh) and prints the sha256 of the held-out rows (determinism check across hosts). usage: read_s4r_r91.py <refodat91 root> <out dir>"""
import csv, hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); import s4r_reader as R
root, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
S = json.load(open(f'{HERE}/split_refodat91.json'))['split']
MAP = {'21C': (0.40, 'carbonated'), '21H': (0.40, 'uncarbonated'), '25C': (0.60, 'carbonated'), '25H': (0.60, 'uncarbonated')}
rows = []
for sp in sorted(S):
    for blk in ('dev', 'held_out'):
        for t in S[sp][blk]:
            r = R.read(f'{root}/{t}')
            rows.append({'specimen': sp, 'w_c': MAP[sp][0], 'carbonation': MAP[sp][1], 'block': blk, 'tile': os.path.basename(t),
                         **{k: (f'{r[k]:.6f}' if isinstance(r.get(k), float) else r.get(k)) for k in ('porosity', 'anhydrous', 'hydrate', 'aggregate_frac', 'sat_frac', 't_pore', 't_anh')}})
F = ['specimen', 'w_c', 'carbonation', 'block', 'tile', 'porosity', 'anhydrous', 'hydrate', 'aggregate_frac', 'sat_frac', 't_pore', 't_anh']
with open(f'{out}/s4r_r91_tiles.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=F); w.writeheader(); [w.writerow(r) for r in rows]
h = hashlib.sha256(''.join(','.join(str(r[k]) for k in F) + '\n' for r in rows if r['block'] == 'held_out').encode()).hexdigest()
print('held-out rows', sum(r['block'] == 'held_out' for r in rows), 'sha256', h)
