#!/usr/bin/env python3
"""test_k2.py: offline tests for the round-2 kit fixes (K2). Each fix has at least one test:
  K1 throttle: per-host minimum interval with jitter, one job for slow hosts, skip of verified files, error bodies kept as .bad
  K2 redundant proprietary twins (.osc next to .ang) ignored by R2
  K3 provenance: all-A observables stop keys; desk ratios move to design.separability_ratio_desk_A; parked datasets stop
  K4 widened SEM rule: EBSD maps with a native step count as SEM-instrument data; join.csv carries a modality column
  K5 registry default tier rules by file type
Runs with the kit's own modules on temporary folders; no network beyond 127.0.0.1."""
import csv, http.server, importlib.util, json, os, shutil, socketserver, sys, tempfile, threading, time
HERE = os.path.dirname(os.path.abspath(__file__)); KIT = os.path.dirname(HERE); RES = []
def mod(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(KIT, f'{name}.py')); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def check(label, cond, detail=''):
    RES.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + label + ('' if cond else f'  [{detail}]'), flush=True)
fs, inv, jn, m0 = mod('fetch_s'), mod('inventory_s'), mod('join_s'), mod('m0_s')
tmp = tempfile.mkdtemp()
# ---------------- K1 throttle
fs._HOST_LAST.clear(); t0 = time.monotonic(); fs.throttle('http://a.example/x', 0.3); fs.throttle('http://a.example/y', 0.3); dt_same = time.monotonic() - t0
check('K1 throttle: second request to one host waits >= the delay', dt_same >= 0.3, dt_same)
check('K1 throttle: jitter stays within 0-50 %', dt_same <= 0.3 * 1.5 + 0.1, dt_same)
t0 = time.monotonic(); fs.throttle('http://b.example/x', 0.3); fs.throttle('http://c.example/x', 0.3); check('K1 throttle: different hosts do not wait for each other', time.monotonic() - t0 < 0.15)
fs._HOST_LAST.clear(); fs.SLOW_HOSTS['slow.example'] = 0.2; t0 = time.monotonic(); fs.throttle('http://slow.example/1', 0); fs.throttle('http://slow.example/2', 0)
check('K1 throttle: a slow host gets its minimum interval without --delay', time.monotonic() - t0 >= 0.2)
check('K1 jobs: one job for data.mendeley.com and data.nist.gov', fs.default_jobs({'data.mendeley.com'}) == 1 and fs.default_jobs({'data.nist.gov', 'x.org'}) == 1)
check('K1 jobs: two jobs elsewhere, --jobs wins', fs.default_jobs({'zenodo.org'}) == 2 and fs.default_jobs({'data.nist.gov'}, 3) == 3)
p = os.path.join(tmp, 'ok.bin'); open(p, 'wb').write(b'x' * 100)
check('K1 skip: verified entry with matching size is skipped', fs.already_verified({'verified': True, 'bytes': 100}, p))
check('K1 skip: unverified or wrong size is fetched again', not fs.already_verified({'verified': None, 'bytes': 100}, p) and not fs.already_verified({'verified': True, 'bytes': 99}, p))
eb = os.path.join(tmp, 'curve.csv'); open(eb, 'w').write('{"url":"https://data.mendeley.com/x","error":"{\\"message\\":\\"invalid json response body ... <!DOCTYPE"}"}')
check('K1 error body: a small JSON error where a 1000-byte CSV was expected', fs.looks_like_error_body(eb, 1000))
good = os.path.join(tmp, 'real.csv'); open(good, 'w').write('strain,stress\n0,0\n0.01,200\n')
check('K1 error body: a real small CSV is not an error body', not fs.looks_like_error_body(good, os.path.getsize(good)) and not fs.looks_like_error_body(good, None))
html = os.path.join(tmp, 'img.tif'); open(html, 'w').write('<!DOCTYPE html><html><body>Access denied</body></html>')
check('K1 error body: an HTML page where a TIFF was expected (size unknown)', fs.looks_like_error_body(html, None))
class ErrServer(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body = b'{"url":"x","error":"{\\"message\\":\\"<!DOCTYPE html>\\"}"}'; self.send_response(200); self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), ErrServer); threading.Thread(target=srv.serve_forever, daemon=True).start()
dest = os.path.join(tmp, 'dl', 'HIP-18.csv')
e = fs.download_one({'path': 'HIP-18.csv', 'url': f'http://127.0.0.1:{srv.server_address[1]}/f', 'bytes': 5000, 'digest': None, 'digest_type': None}, dest)
check('K1 error body: download keeps it as .bad, never as data', e['status'] == 'error_body' and os.path.exists(dest + '.bad') and not os.path.exists(dest), e)
srv.shutdown()
# ---------------- K2 redundant twins
root = os.path.join(tmp, 'root'); d = os.path.join(root, 'tw', 'files'); os.makedirs(d)
open(os.path.join(d, 'map.ang'), 'w').write('# XSTEP: 0.7\n# YSTEP: 0.7\n# NCOLS_ODD: 2\n# NROWS: 1\n# GRID: SqrGrid\n0.1 0.2 0.3 0 0 1 0.9 0 1 0.5\n0.1 0.2 0.3 0.7 0 1 0.9 0 1 0.5\n')
open(os.path.join(d, 'map.osc'), 'wb').write(b'\x00' * 64)
inv.scan_dataset(root, 'tw') if hasattr(inv, 'scan_dataset') else None
rows = inv.scan_dataset(root, 'tw'); open(os.path.join(root, 'tw', 'inventory.jsonl'), 'w').write(''.join(json.dumps(r) + '\n' for r in rows))
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()): inv.cmd_readers(root, ['tw'])
rd = json.load(open(os.path.join(root, 'tw', 'readers.json')))
check('K2 twins: .osc next to .ang is redundant', rd['by_ext']['.osc']['status'] == 'redundant', rd['by_ext'].get('.osc'))
check('K2 twins: R2 ignores the redundant file', rd['R2'] != 'fail', rd['R2'])
os.remove(os.path.join(d, 'map.ang')); open(os.path.join(d, 'other.ang'), 'w').write(open(os.path.join(d, 'map.osc'), 'rb').read().decode('latin1')[:0] + '# XSTEP: 0.7\n0.1 0.2 0.3 0 0 1 0.9 0 1 0.5\n')
rows = inv.scan_dataset(root, 'tw'); open(os.path.join(root, 'tw', 'inventory.jsonl'), 'w').write(''.join(json.dumps(r) + '\n' for r in rows))
with contextlib.redirect_stdout(io.StringIO()): inv.cmd_readers(root, ['tw'])
rd = json.load(open(os.path.join(root, 'tw', 'readers.json')))
check('K2 twins: .osc without a same-stem twin stays a failure', rd['by_ext']['.osc']['status'] == 'fail', rd['by_ext'].get('.osc'))
# ---------------- K4 modality
check('K4 modality: ETD image is SE, CBS image is BSE', jn.modality_of({'role': 'sem_image', 'detector': 'ETD'}) == 'SE' and jn.modality_of({'role': 'sem_image', 'detector': 'CBS'}) == 'BSE')
check('K4 modality: rule mode wins, EBSD/EDS/curve roles', jn.modality_of({'role': 'sem_image', 'mode': 'BSE', 'detector': 'ETD'}) == 'BSE' and jn.modality_of({'role': 'ebsd_export'}) == 'EBSD'
      and jn.modality_of({'role': 'eds_map'}) == 'EDS' and jn.modality_of({'role': 'curve'}) == 'curve')
recs = jn.apply_rules([{'path': 'files/a.ctf', 'ext': '.ctf', 'XStep': '0.25'}], {'rules': [{'name': 'e', 'path_regex': r'\.ctf$', 'role': 'ebsd_export'}]})
check('K4 join: rows carry modality and the native EBSD step', recs[0].get('modality') == 'EBSD' and recs[0].get('XStep') == '0.25', recs)
# ---------------- K3 + K4 through m0
def fake_ds(name, rows, card, conds=('c1', 'c2', 'c3')):
    dd = os.path.join(root, name); os.makedirs(dd, exist_ok=True)
    json.dump({'files': {r['path']: {'status': 'downloaded', 'verified': True, 'bytes': 1} for r in rows}}, open(os.path.join(dd, 'manifest.json'), 'w'))
    json.dump({'R2': 'pass', 'by_ext': {}}, open(os.path.join(dd, 'readers.json'), 'w')); json.dump({}, open(os.path.join(dd, 'inventory_summary.json'), 'w'))
    json.dump({'condition_fields': ['case'], 'conditions': {'case': {c: {} for c in conds}}}, open(os.path.join(dd, 'join_summary.json'), 'w'))
    json.dump({'verdict': 'constant'}, open(os.path.join(dd, 'magleak.json'), 'w'))
    keys = sorted({k for r in rows for k in r})
    with open(os.path.join(dd, 'join.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(rows)
    cards = os.path.join(tmp, 'cards'); os.makedirs(cards, exist_ok=True); json.dump(card, open(os.path.join(cards, f'{name}.json'), 'w'))
reg = os.path.join(tmp, 'reg.json')
json.dump({'datasets': [{'id': n, 'license': 'CC0', 'parts': []} for n in ('ebsdonly', 'allA', 'deskA', 'parked')]}, open(reg, 'w'))
def run_m0(name):
    out = os.path.join(tmp, 'out'); os.makedirs(out, exist_ok=True)
    with contextlib.redirect_stdout(io.StringIO()): m0.main(['--dataset', name, '--root', root, '--registry', reg, '--cards-dir', os.path.join(tmp, 'cards'), '--out-dir', out])
    return json.load(open(os.path.join(out, f'm0_{name}.json')))
ebsd = [{'path': f'files/t{i}.ctf', 'ext': '.ctf', 'role': 'ebsd_export', 'modality': 'EBSD', 'XStep': '0.25', 'case': c} for i, c in enumerate(('c1', 'c2', 'c3'))] + \
       [{'path': f'files/t{i}_Ni.tiff', 'ext': '.tiff', 'role': 'eds_map', 'modality': 'EDS', 'case': c} for i, c in enumerate(('c1', 'c2', 'c3'))]
fake_ds('ebsdonly', ebsd, {'observables': [{'name': 'melt pool depth', 'level': 'M', 'series': True}]})
r = run_m0('ebsdonly')
check('K4 SEM rule: EBSD maps with a native step and EDS maps pass the SEM rule', not any('SEM rule' in x for x in r['stop']), r['stop'])
fake_ds('allA', ebsd, {'observables': [{'name': 'DIC strain', 'level': 'A', 'series': True}, {'name': 'grain size', 'level': 'M'}]})
r = run_m0('allA'); check('K3 provenance: all-A series observables stop keys', any('Provenance' in x for x in r['stop']), r['stop'])
fake_ds('deskA', ebsd, {'observables': [{'name': 'depth', 'level': 'M'}], 'design': {'separability_ratio': 4.48}})
r = run_m0('deskA'); vc = json.load(open(os.path.join(tmp, 'out', 'cards_verified', 'deskA.json')))
check('K3 provenance: an author desk ratio moves to separability_ratio_desk_A', vc['design'].get('separability_ratio_desk_A') == 4.48 and 'separability_ratio' not in vc['design'], vc.get('design'))
fake_ds('parked', ebsd, {'observables': [{'name': 'depth', 'level': 'M'}], 'parked': 'David, 2026-10-07'})
r = run_m0('parked'); check('K3 parked: a parked dataset stops with its reason', any(x.startswith('parked') for x in r['stop']), r['stop'])
# ---------------- K5 registry default
check('K5 default tiers: native exports at 1, maps and HDF5 at 2, patterns and cubes at 3',
      fs.tier_of({}, 'a.ctf') == 1 and fs.tier_of({}, 'README.txt') == 1 and fs.tier_of({'tier': 'auto'}, 'm.tif') == 2 and fs.tier_of({}, 'x.h5oina') == 2
      and fs.tier_of({}, 'p.ebsp') == 3 and fs.tier_of({}, 'c.raw') == 3)
check('K5 default tiers: explicit tier and tier_rules still win', fs.tier_of({'tier': 1}, 'p.ebsp') == 1 and fs.tier_of({'tier_rules': [{'tier': 2, 'names': ['*']}]}, 'a.ctf') == 2)
shutil.rmtree(tmp)
print(f'\n{sum(RES)} passed, {len(RES) - sum(RES)} failed'); sys.exit(0 if all(RES) else 1)
