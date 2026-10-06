#!/usr/bin/env python3
"""de_study.py (F6): the colour-separation refusal threshold DE_MIN, set on replicas. S030-like panels (433x337, thin split frame, markers
over lines, 4 crossing curves): series A (S030 CaCl2 legend colour) and series B = A moved by a controlled CIE76 Delta E in a random Lab
direction (in gamut); two further series well apart (S030 orange and purple). For each Delta E level, 8 replicas; reads of A and B
(y_at_x at 30%/70%, x/y at the maximum) pooled. A level passes when >= 95% of reads are within 2u, <= 2% have |z| > 5 and |bias| <= 0.5u.
DE_MIN = the smallest level from which every larger level passes. Writes replicas/de_study.json. usage: de_study.py"""
import sys as _pb_s, os as _pb_o
_pb_d = _pb_o.path.dirname(_pb_o.path.abspath(__file__))
while not _pb_o.path.exists(_pb_o.path.join(_pb_d, 'pbroot.py')) and _pb_o.path.dirname(_pb_d) != _pb_d: _pb_d = _pb_o.path.dirname(_pb_d)
_pb_s.path.insert(0, _pb_d)
from pbroot import ROOT, HOST
import json, math, random, sys
import numpy as np
V32 = f'{ROOT}'; sys.path.insert(0, V32); sys.path.insert(0, f'{V32}/replicas')
import readers as R, feature_replicas as FR
from PIL import Image
import io, tempfile, os

def lab2rgb(L):
    fy = (L[0] + 16) / 116; fx = fy + L[1] / 500; fz = fy - L[2] / 200
    finv = lambda t: t ** 3 if t > 6 / 29 else 3 * (6 / 29) ** 2 * (t - 4 / 29)
    xyz = np.array([finv(fx) * 0.95047, finv(fy), finv(fz) * 1.08883])
    M = np.linalg.inv(np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])); c = M @ xyz
    c = np.where(c <= 0.0031308, 12.92 * c, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055); return c * 255

A = [141, 174, 199]; C = [226, 152, 96]; Dc = [168, 144, 181]
LEVELS = [4, 6, 8, 10, 12, 15, 18, 22, 26, 30]
BASE = {'size': [433, 337], 'frame': [62, 423, 292, 14], 'kind': 'curve', 'n': 4, 'xrange': [0, 350], 'lw': 1.5, 'marker': 3, 'marker_step': 9,
        'marker_line': True, 'frame_w': 1, 'frame_grey': 20, 'frame_split': True, 'tick_w': 1}
if __name__ == '__main__':
    tmp = tempfile.mkdtemp(); res = {}
    for d in LEVELS:
        z_all = []; miss = 0; n = 0
        for k in range(8):
            rng = random.Random(f'de|{d}|{k}')
            for _ in range(200):   # a random Lab direction whose colour stays in gamut
                v = np.array([rng.gauss(0, 1) for _ in range(3)]); v /= np.linalg.norm(v); B = lab2rgb(R.lab(np.array(A, float)) + d * v)
                if (B >= 0).all() and (B <= 255).all(): break
            B = [int(round(x)) for x in B]; de_true = float(np.linalg.norm(R.lab(np.array(A, float)) - R.lab(np.array(B, float))))
            st = dict(BASE, id=f'de{d}', colours=[A, B, C, Dc]); im, truth, pc = FR.render(st, rng)
            buf = io.BytesIO(); im.save(buf, 'JPEG', quality=90); path = f'{tmp}/de.jpg'; open(path, 'wb').write(buf.getvalue())
            pc = dict(pc, de_min=None)
            try: P = R.Panel(path, pc)
            except Exception: miss += sum(1 for f in truth['features'] if f['series'] in ('0', '1')); n += sum(1 for f in truth['features'] if f['series'] in ('0', '1')); continue
            for f in truth['features']:
                if f['series'] not in ('0', '1') or not f.get('visible', True): continue
                n += 1; r = R.read(P, f)
                if r is None: miss += 1
                else: z_all.append((r[0] - f['value']) / r[1])
        z = np.array(z_all); w = float((np.abs(z) <= 2).mean()) if len(z) else 0; g = float((np.abs(z) > 5).mean()) if len(z) else 1; b = float(z.mean()) if len(z) else float('nan')
        ok = w >= 0.95 and g <= 0.02 and abs(b) <= 0.5
        res[d] = {'reads': len(z), 'miss': miss, 'n': n, 'within_2u': w, 'gross_gt5': g, 'bias_u': b, 'pass': bool(ok)}
        print(f'DE {d:3d}: reads {len(z):3d}/{n:3d}  within 2u {w:.0%}  |z|>5 {g:.1%}  bias {b:+.2f}  {"PASS" if ok else "FAIL"}')
    de_min = None
    for d in LEVELS:
        if all(res[e]['pass'] for e in LEVELS if e >= d): de_min = d; break
    print('DE_MIN =', de_min)
    json.dump({'levels': res, 'de_min': de_min, 'base_colour': A}, open(f'{V32}/replicas/de_study.json', 'w'), indent=1)
