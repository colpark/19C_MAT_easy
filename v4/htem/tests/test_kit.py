#!/usr/bin/env python3
"""Offline tests for the HTEM kit: a mocked API (no network), synthetic samples, readers, census, scoring, matrix, pilot table, render.
usage: python3 v4/htem/tests/test_kit.py   (prints 'N passed' and exits 1 on any failure)"""
import email.message, io, json, os, shutil, sys, tempfile, urllib.error
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = tempfile.mkdtemp(prefix='htem_test_')
os.environ['HTEM_HOST'] = TMP
sys.path.insert(0, HERE)
import numpy as np
import htem_api as API
import sample_io as SIO
import census as CEN
import score_systems as SC
import synth as SY
import build_matrix as BM
import pilot_table as PT
import render as RD
from readers import xrd as RX, optical as RO, fpm as RF

CFG = API.CFG
PASSED, FAILED = [], []


def test(fn):
    try:
        fn(); PASSED.append(fn.__name__)
    except Exception as e:  # noqa: BLE001
        import traceback; traceback.print_exc(); FAILED.append(fn.__name__)
    return fn


# ---------------------------------------------------------------- fake server
def make_sample(sid, lib_id, pos, frac_zn, seed, eg, thick=0.3, rs=None, layout='flat'):
    x, y, _ = SY.xrd_pattern(seed, n_peaks=3)
    op, _ = SY.optical_spectra(seed, eg=eg, thickness_um=thick)
    s = {'id': sid, 'sample_library_id': lib_id, 'position': pos, 'xyz_mm': [pos % 11 * 4.5, pos // 11 * 4.5, 0.0], 'thickness': thick,
         'xrf_elements': ['Zn', 'Sn'], 'xrf_concentration': [100 * frac_zn, 100 * (1 - frac_zn)],
         'xrd_angle': x.tolist(), 'xrd_intensity': y.tolist(), 'xrd_background': (y * 0.5).tolist(),
         'opt_direct_bandgap': eg + 0.01, 'owner_email': 'someone@example.org'}
    if layout == 'flat':
        for k in ('uvit', 'uvir'):
            s[f'opt_{k}_wavelength'] = op[k]['wavelength_nm'].tolist(); s[f'opt_{k}_response'] = (100 * op[k]['response']).tolist()
    else:
        s['oo'] = {k: {'wavelength': op[k]['wavelength_nm'].tolist(), 'response': op[k]['response'].tolist()} for k in ('uvit', 'uvir')}
    if rs:
        fp, _ = SY.iv_points(seed, rs=rs)
        s['fpm_voltage_volts'] = fp['voltage_V'].tolist(); s['fpm_current_amps'] = fp['current_A'].tolist()
        s['fpm_sheet_resistance'] = rs * 1.03
    return s


LIBS, SAMPLES = [], {}


def build_world():
    recipe = dict(deposition_initial_temp_c=230, deposition_power=[15, 25], deposition_gases=['Argon', 'Oxygen'],
                  deposition_gas_flow_sccm=[6, 4], deposition_growth_pressure_mtorr=12, deposition_sample_time_min=60,
                  deposition_substrate_material='Eagle')
    sid = 1000
    for k, lid in enumerate((9154, 9158, 9779, 10104)):
        rec = dict(recipe)
        if lid == 10104:
            rec['deposition_initial_temp_c'] = 310
        ids = []
        for pos in range(1, 12):
            frac = 0.05 + 0.08 * (pos - 1)
            SAMPLES[sid] = make_sample(sid, lid, pos, frac, seed=10 * lid + pos, eg=2.6 + 0.8 * frac, rs=1e3 * (1 + pos),
                                       layout='flat' if k % 2 == 0 else 'nested')
            ids.append(sid); sid += 1
        LIBS.append({'id': lid, 'elements': ['Zn', 'Sn', 'O'], 'has_xrd': 11, 'has_xrf': 11, 'has_opt': 11, 'has_ele': 11 if lid == 9154 else 0,
                     'quality': 3, 'data_access': 'public', 'sample_ids': ids, 'owner_name': 'X', 'owner_email': 'x@y', **rec})
    LIBS.append({'id': 6707, 'elements': ['Cu', 'Zn', 'N'], 'has_xrd': 44, 'has_xrf': 44, 'has_opt': 0, 'has_ele': 0, 'quality': 3,
                 'data_access': 'public', 'sample_ids': [], **recipe})


class Resp(io.BytesIO):
    def __init__(self, body, ctype='application/json'):
        super().__init__(body); self.headers = {'Content-Type': ctype}
    def __enter__(self): return self
    def __exit__(self, *a): self.close()


CALLS = []


def opener(req, timeout=None):
    url = req.full_url; CALLS.append(url)
    path = url.split('/api/', 1)[1]
    if path.startswith('sample_library/'):
        lid = int(path.split('/')[1]); lib = next(l for l in LIBS if l['id'] == lid)
        return Resp(json.dumps(lib).encode())
    if path.startswith('sample_library'):
        return Resp(json.dumps([{k: v for k, v in l.items() if k not in ('sample_ids', 'data_access')} for l in LIBS]).encode())
    if path.startswith('sample/'):
        sid = int(path.split('/')[1])
        if sid == 99999:
            return Resp(b'<html>error</html>', 'text/html')
        return Resp(json.dumps(SAMPLES[sid]).encode())
    raise AssertionError(url)


def client():
    return API.Client(opener=opener, sleep=lambda s: None)


build_world()
API.Client.__init__.__defaults__ = (CFG, os.path.join(TMP, 'cache'), os.path.join(TMP, 'manifest.jsonl'), opener, lambda s: None,
                                    API.time.monotonic)


# ---------------------------------------------------------------- tests
@test
def api_caches_and_strips_pii():
    c = client(); n0 = len(CALLS)
    lib = c.library(9154); c.library(9154)
    assert len(CALLS) == n0 + 1
    assert 'owner_email' not in lib and 'owner_name' not in lib
    s = c.sample(lib['sample_ids'][0]); assert 'owner_email' not in s
    v = API.verify_manifest(os.path.join(TMP, 'cache'), os.path.join(TMP, 'manifest.jsonl')); assert v['objects'] >= 2 and not v['bad']


@test
def api_error_body_kept_as_bad():
    c = client()
    try:
        c.sample(99999); raise AssertionError('no error')
    except API.HTEMError:
        pass
    assert os.path.exists(os.path.join(TMP, 'cache', 'sample', '99999.bad'))
    assert not os.path.exists(os.path.join(TMP, 'cache', 'sample', '99999.json'))


@test
def api_retry_after_honoured():
    waits = []
    state = {'n': 0}
    def flaky(req, timeout=None):
        state['n'] += 1
        if state['n'] == 1:
            h = email.message.Message(); h['Retry-After'] = '7'
            raise urllib.error.HTTPError(req.full_url, 503, 'busy', h, None)
        return opener(req, timeout)
    d = tempfile.mkdtemp()
    c = API.Client(cache=d, manifest=os.path.join(d, 'm.jsonl'), opener=flaky, sleep=waits.append)
    c.library(9158)
    assert 7.0 in waits and state['n'] == 2


@test
def api_budget():
    d = tempfile.mkdtemp(); cfg = json.loads(json.dumps(CFG)); cfg['throttle']['max_requests'] = 1
    c = API.Client(cfg=cfg, cache=d, manifest=os.path.join(d, 'm.jsonl'), opener=opener, sleep=lambda s: None)
    c.library(9154)
    try:
        c.library(9158); raise AssertionError('budget not enforced')
    except API.HTEMError:
        pass


@test
def sample_io_layouts_and_levels():
    a, b = SAMPLES[1000], SAMPLES[1011]
    for s in (a, b):
        op = SIO.optical(s); assert 'uvit' in op and 'uvir' in op and op['uvit']['response'].max() <= 1.0
    comp = SIO.composition(a); assert abs(sum(comp.values()) - 1) < 1e-9 and abs(comp['Zn'] - 0.05) < 1e-9
    assert 'opt_direct_bandgap' in SIO.a_level(a)
    assert SIO.summary(a) == {'xrd': True, 'xrf': True, 'thickness': True, 'opt_T': True, 'opt_R': True, 'fpm': True}
    assert SIO.anion_class(['Cu', 'Zn', 'N']) == 'N' and SIO.system_key(['Zn', 'O', 'Sn']) == 'O-Sn-Zn'


@test
def census_rows_and_replicates():
    rows = CEN.library_rows(LIBS, 10)
    srows = {r['system']: r for r in CEN.system_rows(rows)}
    zto = srows['O-Sn-Zn']
    assert zto['n_multi'] == 4 and zto['n_rep'] == 3 and zto['n_temps'] == 2 and zto['n_ele'] == 1
    assert srows['Cu-N-Zn']['n_multi'] == 0


@test
def score_refuses_without_prior_and_picks():
    os.makedirs(os.path.join(TMP, 'census'), exist_ok=True)
    CEN.write_csv(os.path.join(TMP, 'census', 'systems.csv'), CEN.system_rows(CEN.library_rows(LIBS, 10)))
    real_prior = os.path.join(HERE, 'PRIOR_SYSTEMS.json')
    had = os.path.exists(real_prior)
    prior = os.path.join(TMP, 'PRIOR_SYSTEMS.json')
    os.environ['HTEM_PRIOR'] = prior
    try:
        assert SC.main([]) == 2
        json.dump([], open(prior, 'w'))
        assert SC.main([]) == 0
        pick = json.load(open(os.path.join(TMP, 'census', 'PICK.json')))
        assert pick['P1']['system'] == 'O-Sn-Zn' and pick['P1']['spread'] > 0.5 and pick['P1']['t_and_r'] == 1.0
    finally:
        os.environ.pop('HTEM_PRIOR', None)
    assert os.path.exists(real_prior) == had, 'test touched the frozen prior file'


@test
def readers_synthetic_gates():
    import validate_readers as VR
    seeds = list(range(5000, 5010))  # test seeds: never the config fresh_seed_base range
    assert VR.CFG['fresh_seed_base'] not in seeds
    assert VR.xrd_gate(seeds)['pass'] and VR.xrd_gate(seeds, broad=True)['pass'] and VR.optical_gate(seeds)['pass'] and VR.fpm_gate(seeds)['pass']


@test
def xrd_d_spacing_needs_wavelength():
    try:
        RX.d_spacing(30.0, None); raise AssertionError('no refusal')
    except ValueError:
        pass
    assert abs(RX.d_spacing(30.0, 1.5406) - 2.97624) < 1e-4


@test
def xrd_phase_match():
    x, y, truth = SY.xrd_pattern(7, n_peaks=4)
    peaks = RX.read(x, y, CFG['readers']['xrd'])['peaks']
    sticks = [(t['center'], t['height']) for t in truth]
    score, pairs = RX.match_phase(peaks, sticks)
    assert score > 0.95 and len(pairs) == 4
    wrong = [(t['center'] + 1.0, t['height']) for t in truth]
    assert RX.match_phase(peaks, wrong)[0] < 0.5


@test
def optical_censors_gap_above_range_and_no_thickness():
    op, t = SY.optical_spectra(3, eg=4.7)
    r = RO.read(op, t['thickness_um'], CFG['readers']['optical']); assert r['censored'] or r['Eg'] is None
    assert RO.read(op, None, CFG['readers']['optical'])['Eg'] is None


@test
def fpm_reader():
    fp, t = SY.iv_points(5, rs=2500.0)
    r = RF.read(fp, 0.3, CFG['readers']['fpm'])
    assert abs(r['Rs_ohm_sq'] / 2500 - 1) < 0.01 and r['linear_r2'] > 0.999 and abs(r['resistivity_ohm_cm'] - 2500 * 0.3e-4) < 1e-3


@test
def matrix_heldout_replicates_and_pilot():
    assert BM.main(['--tag', 'zto', '--freeze', 'S4h-test', '9154', '9158', '9779', '10104']) == 0
    d = os.path.join(TMP, 'matrix', 'zto')
    cells = [json.loads(l) for l in open(os.path.join(d, 'cells.jsonl'))]
    assert len(cells) == 44 and all(c['derived']['freeze'] == 'S4h-test' for c in cells)
    h = json.load(open(os.path.join(d, 'heldout.json')))
    assert h['Eg']['pass'] and abs(h['Rs']['median_ratio'] - 1 / 1.03) < 0.02
    rep = json.load(open(os.path.join(d, 'replicates.json')))
    assert rep['pairs'] >= 22 and rep['median_abs_dEg_eV'] is not None
    assert PT.main(['--tag', 'zto', '--obs', 'Eg', '--cation', 'Zn', '--bin', '0.1', '--temp', '230']) == 0
    rows = list(__import__('csv').DictReader(open(os.path.join(d, 'pilot_Eg_Zn_T230_library.csv'))))
    assert rows and {'condition', 'unit', 'value', 'order'} <= set(rows[0])
    assert all(r['condition'].startswith('T230_') for r in rows) and len(rows) == 33  # the 310 C library never joins the series
    assert all(float(r['order']) < 1.0 for r in rows)
    assert PT.main(['--tag', 'zto', '--obs', 'Eg', '--cation', 'Zn', '--bin', '0.1', '--temp', '225']) == 3
    by_libpair = {}
    for r in rep['rows']:
        by_libpair.setdefault((r['pair'][0].split(':')[0], r['pair'][1].split(':')[0]), []).append(r['pair'])
    assert len(by_libpair) == 3
    for prs in by_libpair.values():
        for k in (0, 1):
            assert len({p[k] for p in prs}) == len(prs), 'replicate pairing must be one to one within a library pair'


@test
def render_is_deterministic_and_has_no_metadata():
    x, y, _ = SY.xrd_pattern(1)
    p1, p2 = os.path.join(TMP, 'r1.png'), os.path.join(TMP, 'r2.png')
    for p in (p1, p2):
        RD.xrd_panel(p, [(x, y), (x, y * 0.7)], gray=True, letters=['A', 'B'], seed=3)
    b1, b2 = open(p1, 'rb').read(), open(p2, 'rb').read()
    assert b1 == b2 and b'Software' not in b1 and b'matplotlib' not in b1.lower()
    RD.library_map(os.path.join(TMP, 'm.png'), [[i % 11, i // 11, 3.2] for i in range(44)], np.arange(44), 'Eg (eV)',
                   annotate=list(range(44)))
    RD.library_map(os.path.join(TMP, 'm2.png'), [[1, 2, 0], None, [3, 4]], [1.0, 2.0, 3.0], 'x', annotate=['a', 'b', 'c'])


@test
def nulls_and_scales_do_not_break_readers():
    s = json.loads(json.dumps(SAMPLES[1000]))
    s['xrd_angle'][5] = None; s['xrd_intensity'][300] = None
    x = SIO.xrd(s); assert x is not None and x['dropped'] == 2
    assert RX.read(x['two_theta'], x['intensity'], CFG['readers']['xrd'])['peaks']
    s['opt_uvit_response'][-1] = None; s['opt_uvir_response'][-1] = None   # 1099 nm, the lowest energy
    r = RO.read(SIO.optical(s), SIO.thickness_um(s), CFG['readers']['optical']); assert r['Eg'] is not None
    f = json.loads(json.dumps(SAMPLES[1011]))   # nested layout, fractions, one UV spike above 1.5
    f['oo']['uvit']['response'][0] = 1.6
    op = SIO.optical(f); assert op['uvit']['scale'] == 1.0
    assert RO.read(op, SIO.thickness_um(f), CFG['readers']['optical'])['Eg'] is not None
    t = json.loads(json.dumps(SAMPLES[1000])); t['xrf_concentration'] = [101.0, -1.0]
    assert min(SIO.composition(t).values()) >= 0
    for k in ('thickness', 'xyz_mm', 'xrf_concentration'):
        u = json.loads(json.dumps(SAMPLES[1000])); u[k] = None
        BM.row_for(LIBS[0], u, 'S4h-test')


@test
def recipe_key_keeps_power_and_flow_pairs():
    a = dict(LIBS[0], deposition_compounds=['Zn', 'Sn'], deposition_power=[15, 25], deposition_gases=['Argon', 'Oxygen'],
             deposition_gas_flow_sccm=[6, 4])
    b = dict(a, deposition_power=[25, 15])
    c = dict(a, deposition_gas_flow_sccm=[4, 6])
    assert CEN.recipe_key(a, 10) != CEN.recipe_key(b, 10) and CEN.recipe_key(a, 10) != CEN.recipe_key(c, 10)
    assert CEN.recipe_key(dict(a, deposition_initial_temp_c=25), 10)[1] == 30
    assert CEN.recipe_key(dict(a, deposition_compounds=['Sn', 'Zn'], deposition_power=[25, 15]), 10) == CEN.recipe_key(a, 10)


@test
def api_404_cached_budget_per_attempt_and_id_check():
    calls = []
    def notfound(req, timeout=None):
        calls.append(1); raise urllib.error.HTTPError(req.full_url, 404, 'nf', email.message.Message(), None)
    d = tempfile.mkdtemp()
    c = API.Client(cache=d, manifest=os.path.join(d, 'm.jsonl'), opener=notfound, sleep=lambda s: None)
    for _ in range(3):
        try:
            c.sample(424242)
        except API.NotFound:
            pass
    assert len(calls) == 1
    cfg = json.loads(json.dumps(CFG)); cfg['throttle']['max_requests'] = 2
    def busy(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 503, 'busy', email.message.Message(), None)
    c2 = API.Client(cfg=cfg, cache=d, manifest=os.path.join(d, 'm.jsonl'), opener=busy, sleep=lambda s: None)
    try:
        c2.library(1)
    except API.HTEMError:
        pass
    assert c2.n_requests == 2
    for body in (b'{}', b'{"id": null, "error": "not found"}', b'<html>x</html>', b'[1,2]'):
        assert API.Client.is_error_body(body, 'application/json', 'dict', key=5)
    assert API.Client.is_error_body(b'{"id": 6}', '', 'dict', key=5)
    assert not API.Client.is_error_body(b'{"position": 3, "xrd_angle": [1]}', '', 'dict', key=5)
    assert not API.Client.is_error_body(b'{"id": 5}', 'text/html', 'dict', key=5)


@test
def fpm_reversed_polarity_positive():
    fp, _ = SY.iv_points(2, rs=800.0)
    fp = {'current_A': fp['current_A'], 'voltage_V': -fp['voltage_V']}
    r = RF.read(fp, None, CFG['readers']['fpm']); assert r['Rs_ohm_sq'] > 0 and r['polarity'] == 'reversed'


@test
def build_matrix_skips_bad_sample():
    lib = dict(LIBS[1], id=7777, sample_ids=LIBS[1]['sample_ids'][:3] + [99999])
    LIBS.append(lib)
    try:
        assert BM.main(['--tag', 'skip', '--freeze', 'S4h-test', '7777']) == 0
        d = os.path.join(TMP, 'matrix', 'skip')
        assert len(open(os.path.join(d, 'cells.jsonl')).readlines()) == 3
        assert json.load(open(os.path.join(d, 'skipped.json')))[0]['sample'] == 99999
    finally:
        LIBS.remove(lib)


@test
def p2_found_beyond_stage_b_top_k():
    ranked = [{'system': 'O-Sn-Zn', 'anion': 'O', 'score': 9}, {'system': 'Ga-O-Zn', 'anion': 'O', 'score': 8},
              {'system': 'Ge-N-Zn', 'anion': 'N', 'score': 3}]
    p1, p2 = SC.pick(ranked); assert p1['system'] == 'O-Sn-Zn' and p2['system'] == 'Ge-N-Zn'
    ranked2 = [{'system': 'Ge-N-Zn', 'anion': 'N', 'score': 12}] + ranked[:2]
    p1, p2 = SC.pick(ranked2, core={'O-Sn-Zn', 'Ga-O-Zn'}); assert p1['system'] == 'O-Sn-Zn' and p2['system'] == 'Ge-N-Zn'
    assert SC.probe_ids({'sample_ids': list(range(10, 54))}, 2) == [10, 53]



@test
def recipe_key_null_flow_vh_e02():
    """VH-E02: a gas listed with a null flow next to a numeric flow, and a null power, must not crash the recipe key."""
    r = {'elements': ['Zn', 'O'], 'deposition_initial_temp_c': 200, 'deposition_compounds': ['ZnO', 'ZnO'], 'deposition_power': [30, None],
         'deposition_gases': ['Ar', 'Ar', 'O2'], 'deposition_gas_flow_sccm': [None, 10.0, 2.0], 'deposition_growth_pressure_mtorr': 5,
         'deposition_sample_time_min': 60, 'deposition_substrate_material': 'EXG'}
    k = CEN.recipe_key(r, 10)
    assert k[0] == 'O-Zn' and k[1] == 200 and k[3][0][0] == 'ar' and k[3][0][1] == 10.0 and k[3][1][1] is None


@test
def composition_compound_aligned_vh_e03():
    """VH-E03: concentrations aligned with xrf_compounds (anion in xrf_elements) must give cation fractions."""
    a = SIO.composition({'xrf_compounds': ['NiO', 'CoO', 'ZnO'], 'xrf_elements': ['Ni', 'O', 'Co', 'Zn'], 'xrf_concentration': [3.737, 46.63, 49.63]})
    assert a and abs(a['Zn'] - 0.4963 / 0.99997) < 1e-3 and set(a) == {'Ni', 'Co', 'Zn'}
    b = SIO.composition({'xrf_compounds': ['Zn', 'Mn', 'Te', 'Se', 'Te'], 'xrf_elements': ['Zn', 'Mn', 'Te', 'Se'], 'xrf_concentration': [30, 20, 25, 15, 10]})
    assert set(b) == {'Zn', 'Mn'} and abs(b['Zn'] - 0.6) < 1e-9
    c = SIO.composition({'xrf_compounds': ['Zn3N2', 'Cu3N'], 'xrf_elements': ['Zn', 'Cu', 'N'], 'xrf_concentration': [40, 60]})
    assert abs(c['Cu'] - 0.6) < 1e-9
    assert SIO.composition({'xrf_compounds': ['ZnSnO3'], 'xrf_elements': ['Zn', 'Sn', 'O'], 'xrf_concentration': [100]}) is None
    assert SIO.composition({'xrf_compounds': ['Zn', 'Sn'], 'xrf_elements': ['Zn', 'Sn'], 'xrf_concentration': [1, 2, 3]}) is None

if __name__ == '__main__':
    print(f'{len(PASSED)} passed, {len(FAILED)} failed', FAILED if FAILED else '')
    shutil.rmtree(TMP, ignore_errors=True)
    sys.exit(1 if FAILED else 0)
