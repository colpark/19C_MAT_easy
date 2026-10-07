#!/usr/bin/env python3
"""wavelength_check.py (H3, reference-standard route for the XRD wavelength D record; frozen before reading the library).
Library 10106 (the only multimodal O-Zn library; never a pilot library). Every sample's pattern goes through readers/xrd.py with the
config parameters; peaks are matched to the ZnO wurtzite sticks (COD 2300112 at the D-record wavelength, refs/sticks.json, strongest 5)
within 0.5 deg. Per reflection the median measured 2theta over samples; hexagonal a and c by least squares on 1/d^2 = 4/3 (h^2+hk+k^2)/a^2
+ l^2/c^2. Pass: |a/a_COD - 1| <= 0.01 and |c/c_COD - 1| <= 0.01 (film strain is usually < 1 %; another anode, e.g. Co K-alpha, would be
~16 % off). Also reported: the wavelength implied per reflection by the COD lattice. Writes $HTEM_HOST/refs/wavelength_check.json."""
import json, math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import htem_api as API, sample_io as SIO
from readers import xrd as X
LIB = 10106; TOL = 0.5; LAM = API.CFG['readers']['xrd']['wavelength_A']

def main():
    st = [p for p in json.load(open(os.path.join(API.HOST, 'refs', 'sticks.json'))) if p['phase'] == 'ZnO wurtzite'][0]
    ref = sorted(st['sticks'], key=lambda s: -s[1])[:5]; aC, cC = st['lattice']['a'], st['lattice']['c']
    c = API.Client(); samples = c.samples_of(LIB); hits = {i: [] for i in range(len(ref))}; n = 0
    for s in samples:
        x = SIO.xrd(s)
        if not x: continue
        n += 1; pk = X.read(x['two_theta'], x['intensity'], API.CFG['readers']['xrd'])['peaks']
        cen = np.array([p['center'] for p in pk])
        for i, (tt, _, hkls) in enumerate(ref):
            if cen.size and np.min(np.abs(cen - tt)) <= TOL: hits[i].append(float(cen[np.argmin(np.abs(cen - tt))]))
    rows = []
    for i, (tt, inten, hkls) in enumerate(ref):
        if len(hits[i]) >= 3:
            h, k, l = hkls[0][0], hkls[0][1], hkls[0][-1]; m = float(np.median(hits[i])); d = X.d_spacing(m, LAM)
            dC = 1 / math.sqrt(4 / 3 * (h * h + h * k + k * k) / aC ** 2 + l * l / cC ** 2)
            rows.append({'hkl': [h, k, l], 'stick_2theta': tt, 'median_2theta': m, 'n': len(hits[i]), 'd': d, 'lambda_implied': 2 * dC * math.sin(math.radians(m) / 2)})
    out = {'library': LIB, 'samples_read': n, 'wavelength_A': LAM, 'reflections': rows}
    A = [[4 / 3 * (r['hkl'][0] ** 2 + r['hkl'][0] * r['hkl'][1] + r['hkl'][1] ** 2), r['hkl'][2] ** 2] for r in rows]; b = [1 / r['d'] ** 2 for r in rows]
    if len(rows) >= 2 and np.linalg.matrix_rank(np.array(A)) == 2:
        sol, *_ = np.linalg.lstsq(np.array(A), np.array(b), rcond=None); a, cc = 1 / math.sqrt(sol[0]), 1 / math.sqrt(sol[1])
        out.update({'a': a, 'c': cc, 'a_COD': aC, 'c_COD': cC, 'a_dev': a / aC - 1, 'c_dev': cc / cC - 1,
                    'pass': abs(a / aC - 1) <= 0.01 and abs(cc / cC - 1) <= 0.01})
    else:
        out.update({'pass': False, 'why': 'fewer than two independent reflections matched'})
    json.dump(out, open(os.path.join(API.HOST, 'refs', 'wavelength_check.json'), 'w'), indent=1); print(json.dumps(out, indent=1))

if __name__ == '__main__':
    main()
