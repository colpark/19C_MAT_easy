#!/usr/bin/env python3
"""test_kit.py: offline tests for the Track S kit (no network). Run: python3 v4/trackS/tests/test_kit.py

Builds synthetic deposits in a temporary HARBOR (FEI, Zeiss, TESCAN and ImageJ tagged TIFFs, a JPEG, an .ang, a CSV and a zip),
mocks the Dryad, NIST PDR, Zenodo, DataCite and refodat responses, serves a file with HTTP Range from a local server, and checks
plan, download with resume and checksum, extract, scan, readers, join, magnification leak, separability and m0.
"""
import hashlib
import http.server
import importlib.util
import io
import json
import os
import random
import shutil
import socketserver
import sys
import tempfile
import threading
import zipfile
from contextlib import redirect_stdout

import numpy as np
import tifffile

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASSED, FAILED = [], []


def mod(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(KIT, f'{name}.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def check(label, cond, detail=''):
    (PASSED if cond else FAILED).append(label)
    print(('PASS ' if cond else 'FAIL ') + label + (f'  [{detail}]' if detail and not cond else ''), flush=True)


def quiet(fn, *a, **k):
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            fn(*a, **k)
    except SystemExit as e:
        return buf.getvalue(), e.code
    return buf.getvalue(), 0


# ---------------------------------------------------------------- fixtures
def fei_text(px_m, hfw_m, kv=20000, det='CBS'):
    return f'[User]\nDate=10/06/2026\n[Beam]\nHV={kv}\n[Scan]\nPixelWidth={px_m}\nPixelHeight={px_m}\nHorFieldsize={hfw_m}\nDwelltime=3e-06\n[Detectors]\nName={det}\nMode=Z-contrast\n[System]\nSystemType=Versa 3D\n'


def zeiss_text(px_nm, mag='10.00 K X'):
    return f'\r\n0\r\nAP_IMAGE_PIXEL_SIZE\r\nImage Pixel Size = {px_nm} nm\r\nAP_MAG\r\nMag = {mag}\r\nAP_ACTUALKV\r\nEHT = 15.00 kV\r\nDP_DETECTOR_CHANNEL\r\nDetector = SE2\r\n'


def img(path, tags=None, **kw):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = (np.random.default_rng(0).random((64, 64)) * 4095).astype('uint16')
    tifffile.imwrite(path, data, extratags=tags or [], **kw)


def build_fixtures(root):
    # dataset fix_const: FEI tags, one pixel size, three categorical conditions, plus EBSD, CSV, JPEG and a zip of TIFFs
    d = os.path.join(root, 'fix_const', 'files')
    for c in 'ABC':
        for i in range(4):
            img(os.path.join(d, f'cond_{c}', f'img_{i:02d}.tif'), [(34682, 's', 0, fei_text(3.345e-8, 1.37e-4), True)])
    with open(os.path.join(d, 'map.ang'), 'w') as fh:
        fh.write('# XSTEP: 0.8\n# YSTEP: 0.8\n# NCOLS_ODD: 3\n# NROWS: 2\n# GRID: SqrGrid\n')
        for y in range(2):
            for x in range(3):
                fh.write(f'0.1 0.2 0.3 {x * 0.8} {y * 0.8} 1200 0.9 0 1 0.5\n')
    with open(os.path.join(d, 'curves.csv'), 'w') as fh:
        fh.write('strain,stress\n0,0\n0.01,200\n')
    from PIL import Image
    Image.new('L', (32, 32)).save(os.path.join(d, 'photo.jpg'))
    zpath = os.path.join(d, 'tiles.zip')
    tmp = tempfile.mkdtemp()
    for i in range(2):
        img(os.path.join(tmp, f'cond_A/tile_{i}.tif'), [(34682, 's', 0, fei_text(3.345e-8, 1.37e-4), True)])
    with zipfile.ZipFile(zpath, 'w') as z:
        for i in range(2):
            z.write(os.path.join(tmp, f'cond_A/tile_{i}.tif'), f'cond_A/tile_{i}.tif')
    shutil.rmtree(tmp)
    # dataset fix_leak: Zeiss tags, pixel size shrinks as anneal time grows (the UHCSDB trap)
    d = os.path.join(root, 'fix_leak', 'files')
    for t, px in ((1, 50.0), (2, 50.0), (4, 25.0), (8, 12.5)):
        for i in range(5):
            img(os.path.join(d, f't_{t}h', f'img_{i}.tif'), [(34118, 's', 0, zeiss_text(px), True)])
    # dataset fix_indep: TESCAN and ImageJ tags, two pixel sizes spread evenly over the conditions
    d = os.path.join(root, 'fix_indep', 'files')
    for t in (1, 2, 4, 8):
        for i, px in enumerate((33.45, 66.9, 33.45, 66.9)):
            if i % 2:
                img(os.path.join(d, f't_{t}h', f'img_{i}.tif'), resolution=(1 / (px / 1000), 1 / (px / 1000)), imagej=True, metadata={'unit': 'um'})
            else:
                img(os.path.join(d, f't_{t}h', f'img_{i}.tif'), [(50431, 's', 0, f'[MAIN]\nPixelSizeX={px * 1e-9}\nHV=20000\n', True)])
    # dataset fix_noscale: plain TIFFs without any scale
    d = os.path.join(root, 'fix_noscale', 'files')
    for t in (1, 2):
        img(os.path.join(d, f't_{t}h', 'img.tif'))


RULES = {
    'fix_const': {'rules': [{'name': 'sem', 'path_regex': r'cond_(?P<cond>[A-C])/.*\.tif$', 'role': 'sem_image'},
                            {'name': 'ebsd', 'path_regex': r'\.ang$', 'role': 'ebsd_map'},
                            {'name': 'curves', 'path_regex': r'\.csv$', 'role': 'curve'},
                            {'name': 'photo', 'path_regex': r'\.jpg$', 'role': 'other'}],
                  'condition_fields': ['cond'], 'unit_field': None, 'unit_type': 'field'},
    'fix_leak': {'rules': [{'name': 'sem', 'path_regex': r't_(?P<time_h>\d+)h/.*\.tif$', 'role': 'sem_image'}],
                 'condition_fields': ['time_h'], 'unit_field': None},
    'fix_indep': {'rules': [{'name': 'sem', 'path_regex': r't_(?P<time_h>\d+)h/.*\.tif$', 'role': 'sem_image'}],
                  'condition_fields': ['time_h'], 'unit_field': None},
    'fix_noscale': {'rules': [{'name': 'sem', 'path_regex': r't_(?P<time_h>\d+)h/.*\.tif$', 'role': 'sem_image'}],
                    'condition_fields': ['time_h'], 'unit_field': None},
}


# ---------------------------------------------------------------- HTTP mocks for the resolvers
def mock_responses():
    sha_readme = 'ab' * 32
    landing = ('<html><head><script type="application/ld+json">' + json.dumps({'@context': 'x', 'components': [
        {'@type': ['nrdp:DataFile'], 'filepath': 'Traces/L-03/a b.tif', 'size': 123,
         'downloadURL': 'https://data.nist.gov/od/ds/mds2-9999/Traces/L-03/a%20b.tif'},
        {'@type': ['nrdp:ChecksumFile'], 'filepath': 'Traces/L-03/a b.tif.sha256',
         'downloadURL': 'https://data.nist.gov/od/ds/mds2-9999/Traces/L-03/a%20b.tif.sha256'}]}) + '</script>'
        '<script id="serverApp-state" type="application/json">' + json.dumps({'k': {'components': [
            {'filepath': 'Pads/P1/c.csv', 'size': 7, 'downloadURL': 'https://data.nist.gov/od/ds/mds2-9999/Pads/P1/c.csv',
             'checksum': {'hash': 'cd' * 32, 'algorithm': {'tag': 'sha256'}}}]}}).replace('"', '&q;') + '</script></head></html>')
    return {
        'https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.test': {'_links': {'stash:version': {'href': '/api/v2/versions/999'}}, 'license': 'CC0'},
        'https://datadryad.org/api/v2/versions/999/files': {'_embedded': {'stash:files': [
            {'path': 'README_file.txt', 'size': 10, 'digest': 'aa' * 32, 'digestType': 'sha-256', '_links': {'stash:download': {'href': '/api/v2/files/1/download'}}},
            {'path': 'HRDIC_Results_Full_Fields.zip', 'size': 20, 'digest': 'bb' * 32, 'digestType': 'sha-256', '_links': {'stash:download': {'href': '/api/v2/files/2/download'}}}]},
            '_links': {'next': {'href': '/api/v2/versions/999/files?page=2'}}},
        'https://datadryad.org/api/v2/versions/999/files?page=2': {'_embedded': {'stash:files': [
            {'path': '3D_EBSD_Dataset_Slices1to176_h5.zip', 'size': 30, 'digest': 'cc' * 32, 'digestType': 'sha-256', '_links': {'stash:download': {'href': '/api/v2/files/3/download'}}}]}, '_links': {}},
        'https://data.nist.gov/rmm/records?@id=ark:/88434/mds2-9999': {'ResultData': [{'title': 'T', 'version': '1.0', 'components': [
            {'@type': ['nrdp:DataFile'], 'filepath': 'README.txt', 'size': 10, 'downloadURL': 'https://data.nist.gov/od/ds/mds2-9999/README.txt',
             'checksum': {'hash': sha_readme, 'algorithm': {'tag': 'sha256'}}},
            {'@type': ['nrdp:Subcollection'], 'filepath': 'Traces'}, {'@type': ['nrdp:Subcollection'], 'filepath': 'Pads'}]}]},
        'https://data.nist.gov/od/id/mds2-9999': landing,
        'https://zenodo.org/api/records/123': {'files': [{'key': 'x.zip', 'size': 5, 'checksum': 'md5:0123', 'links': {'self': 'https://zenodo.org/api/records/123/files/x.zip/content'}}],
                                               'metadata': {'license': {'id': 'cc-by-4.0'}}},
        'https://api.datacite.org/dois/10.71758/refodat.test': {'data': {'attributes': {'sizes': ['14 file(s)', '7020.67 MB'], 'formats': ['.tif'],
                                                                                          'rightsList': [{'rights': 'CC BY 4.0'}], 'url': 'https://refodat.de/receive/x'}}},
        'https://refodat.de/receive/x': '<html><h1>Security Check</h1>Please wait a moment while we verify your connection... Calculating solution...</html>',
    }


def fake_http_get_factory(table):
    def fake(url, accept=None, timeout=120):
        if url not in table:
            return 404, {}, b'not found'
        v = table[url]
        return 200, {}, (v if isinstance(v, str) else json.dumps(v)).encode()
    return fake


# ---------------------------------------------------------------- local Range server
class RangeHandler(http.server.BaseHTTPRequestHandler):
    payload = b''

    def log_message(self, *a):
        pass

    def do_GET(self):  # noqa: N802
        data = self.payload
        rng = self.headers.get('Range')
        if rng and rng.startswith('bytes='):
            start = int(rng[6:].split('-')[0])
            if start >= len(data):
                self.send_response(416)
                self.end_headers()
                return
            chunk = data[start:]
            self.send_response(206)
            self.send_header('Content-Range', f'bytes {start}-{len(data) - 1}/{len(data)}')
        else:
            chunk = data
            self.send_response(200)
        self.send_header('Content-Length', str(len(chunk)))
        self.end_headers()
        self.wfile.write(chunk)


# ---------------------------------------------------------------- regression tests for the code review findings
class ShortFirst(http.server.BaseHTTPRequestHandler):
    """First plain GET promises the full length but sends half and closes. Range requests get the rest."""
    payload = b''
    hits = []

    def log_message(self, *a):
        pass

    def do_GET(self):  # noqa: N802
        rng = self.headers.get('Range')
        self.hits.append(rng)
        data = self.payload
        if rng:
            start = int(rng[6:].split('-')[0])
            chunk = data[start:]
            self.send_response(206)
            self.send_header('Content-Range', f'bytes {start}-{len(data) - 1}/{len(data)}')
            self.send_header('Content-Length', str(len(chunk)))
            self.end_headers()
            self.wfile.write(chunk)
        else:
            self.send_response(200)
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data[:len(data) // 2])
            self.wfile.flush()
            self.close_connection = True


def regression(fs, tmp, root, rng):
    # 1. short body: resume instead of a corrupt or restarted file
    payload = bytes(rng.getrandbits(8) for _ in range(2 * 1024 * 1024 + 5))
    ShortFirst.payload, ShortFirst.hits = payload, []
    srv = socketserver.TCPServer(('127.0.0.1', 0), ShortFirst)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    fs.time.sleep = lambda s: None  # no waiting in tests
    dest = os.path.join(tmp, 'dl2', 'short.bin')
    e = fs.download_one({'path': 'short.bin', 'url': f'http://127.0.0.1:{srv.server_address[1]}/short.bin', 'bytes': None,
                         'digest': None, 'digest_type': None}, dest)
    check('review 1: a short body resumes with Range and completes', e['status'] == 'downloaded' and open(dest, 'rb').read() == payload
          and any(h for h in ShortFirst.hits if h), (e.get('status'), ShortFirst.hits))
    # 2. a corrupt present copy moves to .bad and downloads again
    open(dest, 'wb').write(b'corrupt')
    e = fs.download_one({'path': 'short.bin', 'url': f'http://127.0.0.1:{srv.server_address[1]}/short.bin', 'bytes': len(payload),
                         'digest': hashlib.sha256(payload).hexdigest(), 'digest_type': 'sha256'}, dest)
    check('review 2: corrupt present copy replaced, kept as .bad', e['verified'] is True and os.path.exists(dest + '.bad'), e.get('status'))
    srv.shutdown()
    # 3 and 11. NIST ark URLs, filepath names, nested subcollections and an empty subcollection
    comps = [{'@type': ['nrdp:Subcollection'], 'filepath': 'Traces'}, {'@type': ['nrdp:Subcollection'], 'filepath': 'Traces/L-03'},
             {'@type': ['nrdp:Subcollection'], 'filepath': 'Pads'},
             {'@type': ['nrdp:DataFile'], 'filepath': 'Traces/L-03/x y + z.tif', 'size': 3,
              'downloadURL': 'https://data.nist.gov/od/ds/ark:/88434/mds2-9998/Traces/L-03/x%20y%20%2B%20z.tif'},
             {'@type': ['nrdp:DataFile'], 'filepath': 'other.tif', 'downloadURL': 'https://data.nist.gov/od/ds/mds2-1111/other.tif'}]
    table = {'https://data.nist.gov/rmm/records?@id=ark:/88434/mds2-9998': {'ResultData': [{'components': comps}]},
             'https://data.nist.gov/od/id/mds2-9998': '<html></html>'}
    fs.http_get = fake_http_get_factory(table)
    files, meta = fs.resolve_nist({'pdr_id': 'mds2-9998'})
    check('review 11: ark form URL resolves to the NERDm filepath', [f['path'] for f in files] == ['Traces/L-03/x y + z.tif'], [f['path'] for f in files])
    check('review 3: nested subcollection counts as covered, empty Pads flagged', meta['incomplete_subcollections'] == ['Pads'], meta['incomplete_subcollections'])
    # 16. Zenodo entries as a list
    fs.http_get = fake_http_get_factory({'https://zenodo.org/api/records/7': {'files': {'entries': [{'key': 'a.zip', 'size': 1, 'checksum': 'md5:ff'}]}, 'metadata': {}}})
    files, _ = fs.resolve_zenodo({'record_id': '7'})
    check('review 16: Zenodo entries list', files and files[0]['path'] == 'a.zip')
    # 14. unfinished browser download stops the manual registration
    src = os.path.join(tmp, 'browser2')
    os.makedirs(src)
    open(os.path.join(src, 'big.7z.crdownload'), 'wb').write(b'x')

    class M:
        dataset, src, move = 'm_ref', os.path.join(tmp, 'browser2'), False
    out, code = quiet(fs.manual, M)
    check('review 14: .crdownload stops manual registration', code not in (0, None), code)


def regression_stats(tmp, root):
    ml, sp = mod('magleak_s'), mod('separability_s')
    # 5. U shaped scale over an ordered field is a leak (Kruskal-Wallis), Spearman alone would pass it
    vals = [str(t) for t in (1, 2, 3) for _ in range(8)]
    scale = [10.0] * 8 + [20.0] * 8 + [10.0] * 8
    r = ml.test_field(vals, scale, 't', order=[1, 2, 3])
    check('review 5: U shaped scale is a leak, numeric order list accepted', r['verdict'] == 'leak' and r['kind'] == 'ordered', r)
    r = ml.test_field(['a', 'b', 'c'] * 4, [33.45] * 12, 'specimen')
    check('review 5: constant categorical scale is independent', r['verdict'] == 'independent', r)
    # 4 and 6. resolution tags never count, and untestable fields give untested
    ds = 'fix_res'
    os.makedirs(os.path.join(root, ds))
    with open(os.path.join(root, ds, 'join.csv'), 'w') as fh:
        fh.write('path,ext,role,rule,t,pixel_size_nm,pixel_size_source\n')
        for i in range(4):
            fh.write(f'a{i}.tif,.tif,sem_image,r,{i},84667,resolution_tag\n')
    rp = os.path.join(tmp, 'rules_res.json')
    json.dump({'dataset': ds, 'rules': [], 'condition_fields': ['t']}, open(rp, 'w'))
    quiet(ml.main, ['--dataset', ds, '--root', root, '--rules', rp])
    check('review 4: resolution tag pixel sizes read as missing', json.load(open(os.path.join(root, ds, 'magleak.json')))['verdict'] == 'missing')
    with open(os.path.join(root, ds, 'join.csv'), 'w') as fh:
        fh.write('path,ext,role,rule,t,pixel_size_nm,pixel_size_source\n')
        fh.write('a.tif,.tif,sem_image,r,,30,fei\nb.tif,.tif,sem_image,r,,60,fei\n')
    quiet(ml.main, ['--dataset', ds, '--root', root, '--rules', rp])
    check('review 6: varying scale with no testable field reads untested', json.load(open(os.path.join(root, ds, 'magleak.json')))['verdict'] == 'untested')
    # 7, 8 and 17. separability rules
    check('review 17: only S4 reader freezes count', sp.frozen('S2j') is False)
    rows = [{'condition': 'a', 'unit': 'u1', 'value': 1, 'order': 1}, {'condition': 'b', 'unit': 'u1', 'value': 2, 'order': ''}]
    try:
        sp.run(rows, 'given')
        ok = False
    except ValueError:
        ok = True
    check('review 8: a missing order value stops instead of switching to mean order', ok)
    rows = [{'condition': 'a', 'unit': f'u{i}', 'value': v} for i, v in enumerate((1.0, 1.2, 0.9))] + \
           [{'condition': 'b', 'unit': 'only', 'sub': str(i), 'value': 3 + 0.01 * i} for i in range(50)]
    r = sp.run(rows, 'mean')
    check('review 7: mixed unit counts run no pooled ANOVA', r['anova_F'] is None and r['anova_basis'].startswith('not run'), r['anova_basis'])


def main():
    tmp = tempfile.mkdtemp(prefix='trackS_test_')
    os.environ['HARBOR'] = tmp
    root = os.path.join(tmp, 'v4_host', 'trackS')
    os.makedirs(root)
    rng = random.Random(1)

    # ---------------- fetch: resolvers with mocks
    fs = mod('fetch_s')
    fs.http_get = fake_http_get_factory(mock_responses())
    reg = {'host_root': 'v4_host/trackS', 'datasets': [
        {'id': 'm_dryad', 'pilot': 'S2', 'license': 'CC0', 'parts': [{'repository': 'dryad', 'doi': '10.5061/dryad.test', 'tier_rules': [
            {'tier': 1, 'names': ['README_file.txt', 'HRDIC_Results_Full_Fields.zip']}, {'tier': 3, 'names': ['*']}]}]},
        {'id': 'm_nist', 'pilot': 'S1', 'license': 'NIST', 'parts': [{'repository': 'nist_pdr', 'pdr_id': 'mds2-9999', 'tier': 1}]},
        {'id': 'm_zen', 'pilot': 'reserve', 'license': 'CC BY', 'parts': [{'repository': 'zenodo', 'record_id': '123', 'tier': 1}]},
        {'id': 'm_ref', 'pilot': 'S3', 'license': 'CC BY', 'expected': {'files': 2, 'bytes_total_approx': 30},
         'parts': [{'repository': 'refodat_manual', 'doi': '10.71758/refodat.test', 'landing': 'https://refodat.de/receive/x', 'tier': 1}]}]}
    regpath = os.path.join(tmp, 'registry.json')
    json.dump(reg, open(regpath, 'w'))
    fs.REGISTRY = regpath
    fs.HARBOR = tmp

    class A:
        tier, dataset = 1, None
    out, code = quiet(fs.plan, A)
    pd = json.load(open(os.path.join(root, 'm_dryad', 'plan.json')))
    tiers = {f['path']: f['tier'] for f in pd['files']}
    check('dryad: pagination resolves 3 files', len(pd['files']) == 3, tiers)
    check('dryad: tier rules (README and HRDIC tier 1, h5 tier 3)', tiers.get('README_file.txt') == 1 and tiers.get('3D_EBSD_Dataset_Slices1to176_h5.zip') == 3, tiers)
    check('dryad: version id and sha256 digests', pd['parts'][0].get('version_id') == 999 and pd['files'][0]['digest_type'] == 'sha256')
    pn = json.load(open(os.path.join(root, 'm_nist', 'plan.json')))
    paths = sorted(f['path'] for f in pn['files'])
    check('nist: landing page fills the subcollections (ld+json and transfer state)', paths == ['mds2-9999/Pads/P1/c.csv', 'mds2-9999/README.txt', 'mds2-9999/Traces/L-03/a b.tif'], paths)
    tif = [f for f in pn['files'] if f['path'].endswith('a b.tif')][0]
    check('nist: .sha256 companion mapped, not listed as data', tif['sha256_companion'].endswith('a%20b.tif.sha256'))
    check('nist: checksum read from transfer state', [f for f in pn['files'] if f['path'].endswith('c.csv')][0]['digest'] == 'cd' * 32)
    check('reserve skipped unless named', not os.path.exists(os.path.join(root, 'm_zen', 'plan.json')))
    A.dataset = ['m_zen']
    quiet(fs.plan, A)
    pz = json.load(open(os.path.join(root, 'm_zen', 'plan.json')))
    check('zenodo: md5 digest and content link', pz['files'][0]['digest_type'] == 'md5' and pz['files'][0]['url'].endswith('/content'))
    pr = json.load(open(os.path.join(root, 'm_ref', 'plan.json')))
    check('refodat: manual with security check detected', pr['parts'][0].get('manual') and pr['parts'][0].get('security_check') is True, pr['parts'][0])

    # ---------------- fetch: download with resume and checksum against a local Range server
    payload = bytes(rng.getrandbits(8) for _ in range(3 * 1024 * 1024 + 17))
    RangeHandler.payload = payload
    srv = socketserver.TCPServer(('127.0.0.1', 0), RangeHandler)
    port = srv.server_address[1]
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    url = f'http://127.0.0.1:{port}/data.bin'
    dest = os.path.join(tmp, 'dl', 'data.bin')
    os.makedirs(os.path.dirname(dest))
    open(dest + '.part', 'wb').write(payload[:1024 * 1024])
    good = hashlib.sha256(payload).hexdigest()
    e = fs.download_one({'path': 'data.bin', 'url': url, 'bytes': len(payload), 'digest': good, 'digest_type': 'sha256'}, dest)
    check('download: resume from .part and verify sha256', e['status'] == 'downloaded' and e['verified'] is True and open(dest, 'rb').read() == payload, e)
    e2 = fs.download_one({'path': 'data.bin', 'url': url, 'bytes': len(payload), 'digest': good, 'digest_type': 'sha256'}, dest)
    check('download: present file rechecked, not refetched', e2['status'] == 'present' and e2['verified'] is True)
    dest2 = os.path.join(tmp, 'dl', 'bad.bin')
    e3 = fs.download_one({'path': 'bad.bin', 'url': url, 'bytes': len(payload), 'digest': '00' * 32, 'digest_type': 'sha256'}, dest2)
    check('download: wrong digest kept as .bad', e3['verified'] is False and os.path.exists(dest2 + '.bad') and not os.path.exists(dest2))
    e4 = fs.download_one({'path': 'nod.bin', 'url': url, 'bytes': None, 'digest': None, 'digest_type': None}, os.path.join(tmp, 'dl', 'nod.bin'))
    check('download: no repository digest gives verified None', e4['verified'] is None and e4['sha256'] == good)
    srv.shutdown()

    # ---------------- redirect to another host drops the bearer token
    seen = {}

    class Echo(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):  # noqa: N802
            seen['auth'] = self.headers.get('Authorization')
            self.send_response(200)
            self.send_header('Content-Length', '2')
            self.end_headers()
            self.wfile.write(b'ok')
    srv_b = socketserver.TCPServer(('127.0.0.1', 0), Echo)
    port_b = srv_b.server_address[1]
    threading.Thread(target=srv_b.serve_forever, daemon=True).start()

    class Redirect(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):  # noqa: N802
            seen['auth_a'] = self.headers.get('Authorization')
            self.send_response(302)
            self.send_header('Location', f'http://127.0.0.1:{port_b}/file')
            self.end_headers()
    srv_a = socketserver.TCPServer(('127.0.0.1', 0), Redirect)
    port_a = srv_a.server_address[1]
    threading.Thread(target=srv_a.serve_forever, daemon=True).start()
    import urllib.request as ur
    req = ur.Request(f'http://localhost:{port_a}/start', headers={'Authorization': 'Bearer SECRET'})
    with fs.OPENER.open(req, timeout=20) as r:
        body = r.read()
    check('redirect: token sent to the first host, dropped on the other host', seen.get('auth_a') == 'Bearer SECRET' and seen.get('auth') is None and body == b'ok', seen)
    srv_a.shutdown()
    srv_b.shutdown()

    # ---------------- manual registration (refodat)
    src = os.path.join(tmp, 'browser')
    os.makedirs(src)
    open(os.path.join(src, 'a.tif'), 'wb').write(b'x' * 10)
    open(os.path.join(src, 'b.7z'), 'wb').write(b'y' * 20)

    class M:
        dataset, src, move = 'm_ref', os.path.join(tmp, 'browser'), False
    out, code = quiet(fs.manual, M)
    man = json.load(open(os.path.join(root, 'm_ref', 'manifest.json')))
    check('manual: count and size checked against the registry', man['manual_check']['count_ok'] and man['manual_check']['size_ok'] and code == 0, man['manual_check'])

    # ---------------- inventory, readers, join, magleak on synthetic deposits
    build_fixtures(root)
    inv = mod('inventory_s')
    ids = ['fix_const', 'fix_leak', 'fix_indep', 'fix_noscale']
    quiet(inv.main, ['extract', '--root', root, '--dataset'] + ids)
    check('extract: zip unpacked with marker', os.path.exists(os.path.join(root, 'fix_const', 'extracted', 'tiles', '.extracted.json')))
    quiet(inv.main, ['scan', '--root', root, '--dataset'] + ids)
    rows = [json.loads(x) for x in open(os.path.join(root, 'fix_const', 'inventory.jsonl'))]
    fei = [r for r in rows if r['path'].endswith('img_00.tif')][0]
    check('scan: FEI pixel size, HFW, kV, detector', abs(fei['pixel_size_nm'] - 33.45) < 1e-6 and abs(fei['hfw_um'] - 137) < 1e-6 and fei['kv'] == 20 and fei['detector'] == 'CBS', fei)
    tile = [r for r in rows if r['in_archive'] and r['path'].endswith('.tif')]
    check('scan: TIFFs inside the extracted zip carry tags', len(tile) == 2 and all(r['pixel_size_source'] == 'fei' for r in tile))
    ang = [r for r in rows if r['ext'] == '.ang'][0]
    check('scan: .ang header parsed', ang.get('XSTEP') == '0.8' and ang.get('GRID') == 'SqrGrid', ang)
    rl = [json.loads(x) for x in open(os.path.join(root, 'fix_leak', 'inventory.jsonl'))]
    z = [r for r in rl if r['path'].startswith('files/t_4h')][0]
    check('scan: Zeiss pixel size and K magnification', z['pixel_size_source'] == 'zeiss' and abs(z['pixel_size_nm'] - 25.0) < 1e-9 and z['magnification'] == 10000, z)
    ri = [json.loads(x) for x in open(os.path.join(root, 'fix_indep', 'inventory.jsonl'))]
    srcs = {r['pixel_size_source'] for r in ri}
    check('scan: TESCAN and ImageJ sources', srcs == {'tescan', 'imagej'}, srcs)
    ij = [r for r in ri if r['pixel_size_source'] == 'imagej'][0]
    check('scan: ImageJ pixel size in nm', abs(ij['pixel_size_nm'] - 66.9) < 1e-3, ij)
    rn = [json.loads(x) for x in open(os.path.join(root, 'fix_noscale', 'inventory.jsonl'))]
    check('scan: no scale gives source none', all(r['pixel_size_source'] == 'none' for r in rn))
    quiet(inv.main, ['readers', '--root', root, '--dataset'] + ids)
    rd = json.load(open(os.path.join(root, 'fix_const', 'readers.json')))
    check('readers: tif, ang, csv, jpg open', all(rd['by_ext'][e]['status'] == 'pass' for e in ('.tif', '.ang', '.csv', '.jpg')), {e: v['status'] for e, v in rd['by_ext'].items()})
    check('readers: R2 verdict pass', rd['R2'] == 'pass', rd['R2'])

    js, ml = mod('join_s'), mod('magleak_s')
    verdicts = {}
    for ds in ids:
        rp = os.path.join(tmp, f'rules_{ds}.json')
        json.dump(dict(RULES[ds], dataset=ds), open(rp, 'w'))
        quiet(js.main, ['--dataset', ds, '--root', root, '--rules', rp])
        quiet(ml.main, ['--dataset', ds, '--root', root, '--rules', rp])
        verdicts[ds] = json.load(open(os.path.join(root, ds, 'magleak.json')))['verdict']
    jsum = json.load(open(os.path.join(root, 'fix_const', 'join_summary.json')))
    check('join: roles and condition levels', jsum['roles'].get('sem_image') == 14 and set(jsum['conditions']['cond']) == {'A', 'B', 'C'}, jsum['roles'])
    check('magleak: constant pixel size passes', verdicts['fix_const'] == 'constant', verdicts)
    check('magleak: pixel size that follows anneal time is a leak', verdicts['fix_leak'] == 'leak', verdicts)
    check('magleak: pixel size spread evenly is independent', verdicts['fix_indep'] == 'independent', verdicts)
    check('magleak: missing scale flagged', verdicts['fix_noscale'] == 'missing', verdicts)

    # ---------------- separability
    sp = mod('separability_s')

    def table(path, spec):
        with open(path, 'w') as fh:
            fh.write('condition,order,unit,sub,value\n')
            for c, o, units, mu, sd, subs in spec:
                for u in range(units):
                    for s in range(subs):
                        fh.write(f'{c},{o},{c}u{u},{s},{rng.gauss(mu, sd)}\n')
    t1 = os.path.join(tmp, 'sep_pass.csv')
    table(t1, [('c1', 1, 3, 10, 1, 1), ('c2', 2, 3, 20, 1, 1), ('c3', 3, 3, 30, 1, 1), ('c4', 4, 3, 40, 1, 1)])
    out, code = quiet(sp.main, ['--table', t1])
    r = json.load(open(t1.replace('.csv', '_separability.json')))
    check('separability: refuses without a frozen reader (deferred)', r['verdict'] == 'deferred', r)
    freeze = os.path.join(tmp, 'FREEZE.md')
    open(freeze, 'w').write('# v4 freeze\n\n## S4a (2026-10-07T10:00:00-05:00)\n\nreason: test\n')
    sp.FREEZE = freeze
    quiet(sp.main, ['--table', t1, '--reader-freeze', 'S4a', '--unit-type', 'specimen'])
    r = json.load(open(t1.replace('.csv', '_separability.json')))
    check('separability: clear series passes, ANOVA reported', r['verdict'] == 'pass' and r['pairs_separated'] == 3 and r['anova_p'] < 1e-3 and not r['optimistic_spatial_units'], r.get('verdict'))
    t2 = os.path.join(tmp, 'sep_fail.csv')
    table(t2, [('c1', 1, 3, 10, 3, 1), ('c2', 2, 3, 10.2, 3, 1), ('c3', 3, 3, 10.4, 3, 1)])
    quiet(sp.main, ['--table', t2, '--reader-freeze', 'S4a'])
    r = json.load(open(t2.replace('.csv', '_separability.json')))
    check('separability: overlapping series fails and keeps one class', r['verdict'] == 'fail' and len(r['classes_for_T2']) == 1, r.get('classes_for_T2'))
    t3 = os.path.join(tmp, 'sep_spatial.csv')
    table(t3, [('a', 1, 1, 5, 1, 20), ('b', 2, 1, 9, 1, 20)])
    quiet(sp.main, ['--table', t3, '--reader-freeze', 'S4a', '--unit-type', 'tile'])
    r = json.load(open(t3.replace('.csv', '_separability.json')))
    check('separability: single unit uses bootstrap and flags optimistic', r['summary']['a']['se_source'].startswith('bootstrap') and r['optimistic_spatial_units'] is True, r['summary']['a'])

    # ---------------- m0 on fix_const
    m0 = mod('m0_s')
    cards = os.path.join(tmp, 'cards')
    os.makedirs(cards)
    card = json.load(open(os.path.join(KIT, 'cards', 'anjaria2025.json')))
    json.dump(card, open(os.path.join(cards, 'fix_const.json'), 'w'))
    reg2 = {'datasets': [{'id': 'fix_const', 'pilot': 'S2', 'license': 'CC0 1.0', 'parts': []}]}
    rp2 = os.path.join(tmp, 'reg2.json')
    json.dump(reg2, open(rp2, 'w'))
    files = {}
    for b, _, ns in os.walk(os.path.join(root, 'fix_const', 'files')):
        for n in ns:
            p = os.path.join(b, n)
            files[os.path.relpath(p, os.path.join(root, 'fix_const', 'files'))] = {'bytes': os.path.getsize(p), 'verified': True, 'status': 'downloaded'}
    json.dump({'files': files}, open(os.path.join(root, 'fix_const', 'manifest.json'), 'w'))
    outdir = os.path.join(tmp, 'm0out')
    os.makedirs(outdir)
    o, code = quiet(m0.main, ['--dataset', 'fix_const', '--root', root, '--registry', rp2, '--cards-dir', cards, '--out-dir', outdir, '--pilot', t1.replace('.csv', '_separability.json')])
    res = json.load(open(os.path.join(outdir, 'm0_fix_const.json')))
    vcard = json.load(open(os.path.join(outdir, 'cards_verified', 'fix_const.json')))
    check('m0: GO with evidence and logged card changes', res['decision'] in ('GO', 'GO WITH CHECKS') and len(res['card_changes']) >= 3, (res['decision'], res['stop'], res['checks']))
    check('m0: verified card fields (R1, R2, R4, sem block, R6 from pilot)', vcard['access']['raw_downloadable'] is True and vcard['readers']['all_formats'] is True
          and vcard['calibration']['absolute_scales'] is True and vcard['sem']['magnification_fixed'] is True and vcard['design']['separability_ratio'] > 2,
          {k: vcard.get(k) for k in ('access', 'readers', 'calibration')})
    check('m0: scorer report attached', 'Requirements:' in res['scorer']['report'] and res['scorer']['requirements']['R6'] == 'pass', res['scorer']['requirements'])

    regression(fs, tmp, root, rng)
    regression_stats(tmp, root)
    z = os.path.join(tmp, 'zeiss_kx.tif')
    img(z, [(34118, 's', 0, zeiss_text(12.5, mag='50.00 KX'), True)])
    zm = inv.tiff_meta(z)
    check('review 13: Zeiss 50.00 KX reads 50000', zm.get('magnification') == 50000, zm.get('magnification'))
    # review 9: m0 without a magnification test and with a spatial pilot only
    os.remove(os.path.join(root, 'fix_const', 'magleak.json'))
    outdir2 = os.path.join(tmp, 'm0out2')
    os.makedirs(outdir2)
    quiet(m0.main, ['--dataset', 'fix_const', '--root', root, '--registry', rp2, '--cards-dir', cards, '--out-dir', outdir2,
                    '--pilot', t3.replace('.csv', '_separability.json')])
    res2 = json.load(open(os.path.join(outdir2, 'm0_fix_const.json')))
    vc2 = json.load(open(os.path.join(outdir2, 'cards_verified', 'fix_const.json')))
    check('review 9: no magleak and a spatial pilot give checks, R6 stays out', res2['decision'] == 'GO WITH CHECKS'
          and any('not run' in c for c in res2['checks']) and any('spatial' in c for c in res2['checks'])
          and vc2['design'].get('separability_ratio') == card['design'].get('separability_ratio') and vc2['design'].get('separability_ratio_spatial'), res2['checks'])
    # review 12: a raw space in a URL is encoded, not an InvalidURL crash
    RangeHandler.payload = b'abc' * 1000
    srv3 = socketserver.TCPServer(('127.0.0.1', 0), RangeHandler)
    threading.Thread(target=srv3.serve_forever, daemon=True).start()
    e5 = fs.download_one({'path': 'sp.bin', 'url': f'http://127.0.0.1:{srv3.server_address[1]}/a b.bin', 'bytes': 3000, 'digest': None, 'digest_type': None},
                         os.path.join(tmp, 'dl3', 'sp.bin'))
    check('review 12: URL with a raw space downloads', e5['status'] == 'downloaded', e5)
    srv3.shutdown()
    print(f'\n{len(PASSED)} passed, {len(FAILED)} failed')
    shutil.rmtree(tmp, ignore_errors=True)
    sys.exit(1 if FAILED else 0)


if __name__ == '__main__':
    main()
