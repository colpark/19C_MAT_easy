#!/usr/bin/env python3
"""C0.4 MANIFEST_trackC.json: every fetched file with size, md5, sha256, the expected md5 from the record
metadata (Materials Cloud files API, figshare computed_md5), its record, license span and fetch host.
usage: manifest.py RAW_DIR META_DIR OUT.json
"""
import hashlib, json, os, sys, glob


def hashes(p):
    m, s = hashlib.md5(), hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 24), b''):
            m.update(b)
            s.update(b)
    return m.hexdigest(), s.hexdigest()


def expected(meta):
    exp = {}
    for f in glob.glob(os.path.join(meta, '*.record.json')):
        d = json.load(open(f))
        doi = d['links'].get('self_doi', '').split('materialscloud:')[-1]
        lic = [r.get('id') for r in d['metadata'].get('rights', [])]
        for k, v in d['files'].get('entries', {}).items():
            exp[(doi, k)] = {'md5': v['checksum'].split(':')[-1], 'size': v['size'], 'record': d['id'],
                             'doi': 'materialscloud:' + doi, 'license': lic}
    for f in glob.glob(os.path.join(meta, 'figshare_*.json')):
        d = json.load(open(f))
        for x in d['files']:
            exp[('figshare_%s' % d['id'], x['name'])] = {'md5': x['computed_md5'], 'size': x['size'],
                                                         'record': 'figshare:%s' % d['id'],
                                                         'license': [d['license']['name']]}
    return exp


def main():
    raw, meta, out = sys.argv[1:4]
    exp = expected(meta)
    rows = []
    for p in sorted(glob.glob(os.path.join(raw, '*', '*'))):
        if p.endswith(('.part', '.bad')) or os.path.isdir(p):
            continue
        d, k = p.split('/')[-2], p.split('/')[-1]
        md5, sha = hashes(p)
        e = exp.get((d, k)) or exp.get(('figshare_21370572' if d.startswith('figshare') else d, k))
        rows.append({'path': f'{d}/{k}', 'size': os.path.getsize(p), 'md5': md5, 'sha256': sha,
                     'expected_md5': e and e['md5'], 'md5_ok': (e is None) or (e['md5'] == md5),
                     'record': e and e['record'], 'license': e and e['license']})
    bad = [r['path'] for r in rows if not r['md5_ok']]
    json.dump({'files': rows, 'n': len(rows), 'md5_failures': bad}, open(out, 'w'), indent=1)
    print(len(rows), 'files; md5 failures:', bad)


if __name__ == '__main__':
    main()
