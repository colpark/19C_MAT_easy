#!/usr/bin/env python3
"""select_oxides.py (round 2, HR0 section 3): pick O1 and O2 from the frozen census ranking by the pre-registered rule.
Candidates: anion O systems of census/ranking.csv in score order. Pass = (a) every phase of the HR0 list has a measured COD structure
(atom sites, ambient, not theoretical), (b) median probe edge width <= 0.4 eV (>= 6 probes with T, R, thickness), (c) >= half the probes
give an uncensored E04 and its median lies inside the measured range. Probes = census probe_ids (3 per multimodal library), cached.
Tests (b) and (c) run first (local); (a) queries COD (throttled, cached under refs/cod_r2/) only for candidates passing (b) and (c), in
order, until two systems pass. Space groups identify the polymorph (named default table SG below).
Writes $HTEM_HOST/census/OXIDE_PICK.json. usage: select_oxides.py"""
import csv, json, os, re, sys, time, urllib.parse, urllib.request
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import htem_api as API, sample_io as SIO, score_systems as SS
from readers import edge as RE

ORDER = ['O-Sn-Ti-Zn', 'Cr-Mn-O', 'Co-Ni-O-Zn', 'Co-Ni-O', 'Mn-O', 'Ag-O-V', 'Cu-O-Zn']
# (phase, COD formula in Hill order as COD writes it, accepted space-group numbers)
PHASES = {
    'O-Sn-Ti-Zn': [('ZnO wurtzite', 'O Zn', [186]), ('SnO2 rutile', 'O2 Sn', [136]), ('TiO2 anatase', 'O2 Ti', [141]), ('TiO2 rutile', 'O2 Ti', [136]),
                   ('Zn2SnO4 inverse spinel', 'O4 Sn Zn2', [227]), ('Zn2TiO4 inverse spinel', 'O4 Ti Zn2', [227]), ('ZnTiO3 ilmenite', 'O3 Ti Zn', [148])],
    'Cr-Mn-O': [('Cr2O3 corundum', 'Cr2 O3', [167]), ('Mn2O3 bixbyite', 'Mn2 O3', [206]), ('Mn3O4 hausmannite', 'Mn3 O4', [141]),
                ('MnCr2O4 spinel', 'Cr2 Mn O4', [227]), ('beta-MnO2 pyrolusite', 'Mn O2', [136])],
    'Co-Ni-O-Zn': [('NiO rocksalt', 'Ni O', [225]), ('CoO rocksalt', 'Co O', [225]), ('Co3O4 spinel', 'Co3 O4', [227]), ('ZnO wurtzite', 'O Zn', [186]),
                   ('ZnCo2O4 spinel', 'Co2 O4 Zn', [227]), ('NiCo2O4 spinel', 'Co2 Ni O4', [227])],
    'Co-Ni-O': [('NiO rocksalt', 'Ni O', [225]), ('CoO rocksalt', 'Co O', [225]), ('Co3O4 spinel', 'Co3 O4', [227]), ('NiCo2O4 spinel', 'Co2 Ni O4', [227])],
    'Mn-O': [('MnO rocksalt', 'Mn O', [225]), ('Mn3O4 hausmannite', 'Mn3 O4', [141]), ('Mn2O3 bixbyite', 'Mn2 O3', [206]), ('beta-MnO2 pyrolusite', 'Mn O2', [136])],
    'Ag-O-V': [('V2O5', 'O5 V2', [59]), ('VO2 (M1)', 'O2 V', [14]), ('Ag2O', 'Ag2 O', [224]), ('Ag metal', 'Ag', [225]), ('beta-AgVO3', 'Ag O3 V', [8]),
               ('Ag3VO4', 'Ag3 O4 V', [15])],
    'Cu-O-Zn': [('CuO tenorite', 'Cu O', [15]), ('Cu2O cuprite', 'Cu2 O', [224]), ('Cu metal', 'Cu', [225]), ('ZnO wurtzite', 'O Zn', [186])],
}
CODQ = 'https://www.crystallography.net/cod/result?format=json&formula={}'
CODCIF = 'https://www.crystallography.net/cod/{}.cif'
CACHE = os.path.join(API.HOST, 'refs', 'cod_r2'); PAUSE = 2.0; MAX_CIF = 8
UA = {'User-Agent': 'PanelBench-HTEM-round2/1.0 (research; polite, cached)'}


def _get(url, path):
    if os.path.exists(path):
        return open(path, 'rb').read()
    time.sleep(PAUSE)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        b = r.read()
    os.makedirs(os.path.dirname(path), exist_ok=True); open(path, 'wb').write(b); return b


def sg_number(cif):
    m = re.search(r"_space_group_IT_number\s+(\d+)", cif) or re.search(r"_symmetry_Int_Tables_number\s+(\d+)", cif)
    return int(m.group(1)) if m else None


def ambient(cif):
    p = re.search(r"_diffrn_ambient_pressure\s+([\d.]+)", cif) or re.search(r"_cell_measurement_pressure\s+([\d.]+)", cif)
    t = re.search(r"_diffrn_ambient_temperature\s+([\d.]+)", cif) or re.search(r"_cell_measurement_temperature\s+([\d.]+)", cif)
    okp = p is None or abs(float(p.group(1)) - 100) < 1 or float(p.group(1)) < 1   # kPa: 100 (0.1 MPa); some files give 0
    okt = t is None or 273 <= float(t.group(1)) <= 310
    return okp and okt


def has_sites(cif):
    return '_atom_site_fract_x' in cif


def cod_phase(name, formula, sgs, log):
    q = CODQ.format(urllib.parse.quote(formula))
    rows = json.loads(_get(q, os.path.join(CACHE, 'q_' + re.sub(r'\W+', '_', formula) + '.json')) or b'[]')
    cands = sorted(int(r['file']) for r in rows if int(r.get('sg_number') or r.get('sgNumber') or 0) in sgs or not (r.get('sg_number') or r.get('sgNumber')))
    tried = []
    for cid in cands[:MAX_CIF]:
        cif = _get(CODCIF.format(cid), os.path.join(CACHE, f'{cid}.cif')).decode('utf-8', 'replace')
        sg = sg_number(cif); theo = bool(re.search(r"_cod_struct_determination_method\s+theoretical", cif))
        ok = sg in sgs and has_sites(cif) and ambient(cif) and not theo
        tried.append({'cod_id': cid, 'sg': sg, 'sites': has_sites(cif), 'ambient': ambient(cif), 'theoretical': theo, 'ok': ok})
        if ok:
            log.append({'phase': name, 'formula': formula, 'cod_id': cid, 'n_query': len(rows), 'tried': tried}); return cid
    log.append({'phase': name, 'formula': formula, 'cod_id': None, 'n_query': len(rows), 'tried': tried}); return None


def probe_stats(system, c):
    r = {x['system']: x for x in csv.DictReader(open(os.path.join(API.HOST, 'census', 'ranking.csv')))}[system]
    cfg = API.CFG['readers']['optical']; ew, e4, cen, inrange, n = [], [], 0, [], 0
    for lid in r['multi_ids'].split():
        lib = c.cached('library', lid)
        for sid in SS.probe_ids(lib, 3):
            s = c.cached('sample', sid); op = SIO.optical(s) if s else None; d = SIO.thickness_um(s) if s else None
            if not op or not d:
                continue
            res = RE.read(op, d, cfg)
            if res is None:
                continue
            n += 1
            if res['edge_width'] is not None:
                ew.append(res['edge_width'])
            if res['E04'] is not None:
                e4.append(res['E04']); inrange.append(res['run_E'])
            else:
                cen += 1
    med4 = float(np.median(e4)) if e4 else None
    rng = [min(x[0] for x in inrange), max(x[1] for x in inrange)] if inrange else None
    b = n >= 6 and bool(ew) and float(np.median(ew)) <= 0.4
    cc = n > 0 and len(e4) >= n / 2 and med4 is not None and rng is not None and rng[0] < med4 < rng[1]
    return {'n_probes_used': n, 'median_edge_width_eV': float(np.median(ew)) if ew else None, 'n_E04': len(e4), 'n_censored': cen,
            'median_E04_eV': med4, 'measured_range_eV': rng, 'pass_b': bool(b), 'pass_c': bool(cc)}


def main():
    c = API.Client(); out = {'order': ORDER, 'systems': {}, 'picked': []}
    for s in ORDER:
        st = probe_stats(s, c); out['systems'][s] = st
        print(s, json.dumps(st))
    for s in ORDER:
        st = out['systems'][s]
        if not (st['pass_b'] and st['pass_c']):
            continue
        log = []; ids = {ph: cod_phase(ph, f, sg, log) for ph, f, sg in PHASES[s]}
        st['cod'] = log; st['pass_a'] = all(v is not None for v in ids.values()); st['cod_ids'] = ids
        print(s, 'COD', st['pass_a'], ids)
        if st['pass_a']:
            out['picked'].append(s)
        if len(out['picked']) == 2:
            break
    out['O1'], out['O2'] = (out['picked'] + [None, None])[:2]
    json.dump(out, open(os.path.join(API.HOST, 'census', 'OXIDE_PICK.json'), 'w'), indent=1)
    print('O1', out['O1'], 'O2', out['O2'])


if __name__ == '__main__':
    main()
