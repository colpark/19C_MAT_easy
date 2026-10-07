#!/usr/bin/env python3
"""refs.py (stage H3): reference phases from open crystal structures, for phase identification and Vegard constants (skill M1 law class
"independent": every constant carries a source). Needs pymatgen on the host (pip install pymatgen) and network access to COD.

Input: v4/htem/REF_PHASES.json, written by the builder from chemistry knowledge before reading pilot patterns:
  [{"phase": "ZnO wurtzite", "cod_id": 2300112, "elements": ["Zn","O"]}, ...]   (the ids here are placeholders; pick real COD ids)
Output: $HTEM_HOST/refs/<cod_id>.cif (sha256 logged), refs/sticks.json with, per phase, the source, lattice constants, and the
stick pattern (2theta, intensity, hkl) at the D-record wavelength inside the measured 2theta range.
usage: refs.py fetch | sticks
"""
import hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import htem_api as API

OUT = os.path.join(API.HOST, 'refs')
COD = 'https://www.crystallography.net/cod/{}.cif'


def load_list():
    p = os.path.join(HERE, 'REF_PHASES.json')
    if not os.path.exists(p):
        raise SystemExit('write v4/htem/REF_PHASES.json first (phases from chemistry knowledge, COD ids, before reading pilot patterns)')
    return json.load(open(p))


def fetch():
    os.makedirs(OUT, exist_ok=True)
    c = API.Client()
    log = []
    for ph in load_list():
        path = os.path.join(OUT, f"{ph['cod_id']}.cif")
        if not os.path.exists(path):
            try:
                body, _ = c._get(COD.format(int(ph['cod_id'])))  # throttle, budget and retries of the HTEM client
            except API.HTEMError as e:
                raise SystemExit(f"COD {ph['cod_id']}: {e}")
            if not body.lstrip().startswith((b'#', b'data_')):
                open(path + '.bad', 'wb').write(body)
                raise SystemExit(f"COD {ph['cod_id']}: not a CIF (kept .bad)")
            open(path, 'wb').write(body)
        log.append({'phase': ph['phase'], 'cod_id': ph['cod_id'], 'sha256': hashlib.sha256(open(path, 'rb').read()).hexdigest()})
    json.dump(log, open(os.path.join(OUT, 'fetch_log.json'), 'w'), indent=1)
    print(json.dumps(log, indent=1))


def sticks(tt_range=(19.0, 52.0)):
    lam = API.CFG['readers']['xrd']['wavelength_A']
    if not lam:
        raise SystemExit('set readers.xrd.wavelength_A (D record from the descriptor) first')
    from pymatgen.core import Structure
    from pymatgen.analysis.diffraction.xrd import XRDCalculator
    calc = XRDCalculator(wavelength=lam)
    out = []
    for ph in load_list():
        st = Structure.from_file(os.path.join(OUT, f"{ph['cod_id']}.cif"))
        pat = calc.get_pattern(st, two_theta_range=tt_range)
        lat = st.lattice
        out.append({'phase': ph['phase'], 'source': f"COD {ph['cod_id']}", 'formula': st.composition.reduced_formula,
                    'lattice': {'a': lat.a, 'b': lat.b, 'c': lat.c, 'alpha': lat.alpha, 'beta': lat.beta, 'gamma': lat.gamma},
                    'sticks': [[float(t), float(i), [list(h['hkl']) for h in hk]] for t, i, hk in zip(pat.x, pat.y, pat.hkls)]})
    json.dump(out, open(os.path.join(OUT, 'sticks.json'), 'w'), indent=1)
    print(len(out), 'phases written')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    {'fetch': fetch, 'sticks': sticks}.get(cmd, lambda: print(__doc__))()
