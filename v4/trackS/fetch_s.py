#!/usr/bin/env python3
"""fetch_s.py: Track S downloader with manifests (skill M0 inputs check, requirement R1 access).

Commands
  plan   [--tier N] [--dataset ID ...]            resolve every file list from the repository API, print sizes per tier,
                                                    check free disk, write <root>/<id>/plan.json and <root>/_plan_summary.json
  get    [--tier N] [--dataset ID ...] [--yes] [--jobs K]
                                                    download the planned files (resume with HTTP Range, retry with backoff),
                                                    check each file against the repository checksum, write <root>/<id>/manifest.json
  verify [--dataset ID ...]                         recompute sha256 for every manifest entry and compare
  manual --dataset ID --src DIR [--move]            register files a person downloaded in a browser (refodat security check):
                                                    hash them, check count and total size against DataCite, place them under files/
  inputs                                            write <root>/INPUTS_trackS.md (paths, bytes and sha256 of every manifest) for LOG.md

Rules
  * Tier 1 = desk checks and pilot, tier 2 = second route, tier 3 = everything. --tier N fetches tiers <= N.
  * Reserves (pilot "reserve") resolve and download only when named with --dataset.
  * A file that fails its repository checksum stays as <name>.bad and the run reports it. Nothing is silently accepted.
  * get refuses to start when free disk is below 1.1 x the planned bytes, and asks for --yes above 20 GB.
  * No credentials are written anywhere. DRYAD_TOKEN (optional) goes only to datadryad.org as a bearer header.

Environment: HARBOR (default /home/aid1/Documents/harbor). Standard library only (Python 3.9 or newer).
"""
import argparse
import concurrent.futures as cf
import datetime as dt
import fnmatch
import hashlib
import html as htmllib
import http.client
import json
import os
import re
import shutil
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REGISTRY = os.path.join(HERE, 'datasets_s.json')
HARBOR = os.environ.get('HARBOR', '/home/aid1/Documents/harbor')
UA = os.environ.get('FETCH_UA', 'panelbench-v4-trackS/1.0 (research data fetch; github.com/colpark/19C_MAT_easy)')
CHUNK = 8 * 1024 * 1024
BIG = 20 * 10 ** 9
LOCK = threading.Lock()
LAST_PAGES = {}  # pdr_id -> landing HTML, saved next to plan.json for inspection when parsing finds nothing


def now():
    return dt.datetime.now().astimezone().isoformat(timespec='seconds')


def log(*a):
    print(*a, flush=True)


# ---------------------------------------------------------------- HTTP (tests replace http_get)
class _StripAuthOnHostChange(urllib.request.HTTPRedirectHandler):
    """Follow redirects, but never forward the Dryad bearer token to another host (for example a presigned S3 URL)."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is not None and urllib.parse.urlparse(newurl).hostname != urllib.parse.urlparse(req.full_url).hostname:
            for k in list(new.headers):
                if k.lower() == 'authorization':
                    del new.headers[k]
            new.unredirected_hdrs.pop('Authorization', None)
        return new


OPENER = urllib.request.build_opener(_StripAuthOnHostChange())


def _headers(url, extra=None):
    h = {'User-Agent': UA}
    tok = os.environ.get('DRYAD_TOKEN')
    if tok and urllib.parse.urlparse(url).hostname == 'datadryad.org':
        h['Authorization'] = f'Bearer {tok}'
    if extra:
        h.update(extra)
    return h


def http_get(url, accept=None, timeout=120):
    """GET with retry and backoff. Returns (status, headers dict, body bytes)."""
    last = None
    for attempt in range(6):
        req = urllib.request.Request(_safe_url(url), headers=_headers(url, {'Accept': accept} if accept else None))
        try:
            with OPENER.open(req, timeout=timeout) as r:
                return r.status, dict(r.headers), r.read()
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 500, 502, 503, 504):
                wait = _retry_after(e.headers, attempt)
                log(f'  HTTP {e.code} on {url}: waiting {wait} s')
                time.sleep(wait)
                continue
            return e.code, dict(e.headers or {}), e.read() if hasattr(e, 'read') else b''
        except (urllib.error.URLError, TimeoutError, ConnectionError, http.client.HTTPException) as e:
            last = e
            if 'Tunnel connection failed' in str(e) or 'Name or service not known' in str(e) or attempt >= 3:
                break  # proxy refusal or DNS failure: retrying does not help
            time.sleep(min(300, 2 ** attempt * 5))
    raise RuntimeError(f'GET failed: {url}: {last}')


def _retry_after(headers, attempt):
    try:
        return max(1, min(600, int((headers or {}).get('Retry-After'))))
    except (TypeError, ValueError):
        return min(300, 2 ** attempt * 5)


def _safe_url(url):
    """Percent-encode spaces and other unsafe characters, keep existing escapes."""
    return urllib.parse.quote(url, safe=":/?&=%#+,;@!$'()*[]~")


def get_json(url):
    status, _, body = http_get(url, accept='application/json')
    if status != 200:
        raise RuntimeError(f'HTTP {status} for {url}')
    return json.loads(body.decode('utf-8'))


def get_text(url):
    status, _, body = http_get(url, accept='text/html,application/xhtml+xml')
    return status, body.decode('utf-8', 'replace')


# ---------------------------------------------------------------- resolvers -> list of file dicts
# file dict: {path, url, bytes, digest, digest_type, tier, part, note}

def _norm_digest_type(t):
    t = (t or '').lower().replace('-', '')
    return {'sha256': 'sha256', 'md5': 'md5', 'sha1': 'sha1'}.get(t, t or None)


def resolve_dryad(part):
    base = 'https://datadryad.org'
    doi = part['doi']
    ds = get_json(f"{base}/api/v2/datasets/{urllib.parse.quote('doi:' + doi, safe='')}")
    vhref = ds['_links']['stash:version']['href']
    version_id = int(vhref.rstrip('/').rsplit('/', 1)[-1])
    out, url = [], f'{base}{vhref}/files'
    while url:
        j = get_json(url)
        for f in j.get('_embedded', {}).get('stash:files', []):
            out.append({'path': f['path'], 'url': base + f['_links']['stash:download']['href'], 'bytes': f.get('size'),
                        'digest': f.get('digest'), 'digest_type': _norm_digest_type(f.get('digestType'))})
        nxt = (j.get('_links') or {}).get('next')
        url = base + nxt['href'] if nxt else None
    return out, {'version_id': version_id, 'version_href': vhref, 'license': ds.get('license')}


def _nist_rel(url, comp):
    """Path of a file inside its record: NERDm filepath when present, else the URL tail after the record id."""
    fp = comp.get('filepath')
    if isinstance(fp, str) and fp.strip('/') and not fp.startswith('cmps/'):
        return fp.strip('/')
    m = re.search(r'/od/ds/(?:ark:/\d+/)?[^/]+/(.+)$', url)
    return urllib.parse.unquote(m.group(1)) if m else None


def _nist_add(found, comp, pdr_id):
    url = comp.get('downloadURL') or comp.get('contentUrl') or comp.get('url')
    if not isinstance(url, str) or 'data.nist.gov/od/ds/' not in url:
        return
    other = re.findall(r'mds\d+-\d+', url)
    if other and pdr_id not in other:  # a link to another record
        return
    rel = _nist_rel(url, comp)
    if not rel:
        return
    rec = found.setdefault(rel, {'path': rel, 'url': url, 'bytes': None, 'digest': None, 'digest_type': None})
    size = comp.get('size', comp.get('contentSize'))
    if isinstance(size, (int, float)) or (isinstance(size, str) and size.isdigit()):
        rec['bytes'] = int(size)
    ck = comp.get('checksum')
    if isinstance(ck, dict) and ck.get('hash'):
        alg = ck.get('algorithm')
        alg = alg.get('tag') if isinstance(alg, dict) else alg
        rec['digest'], rec['digest_type'] = ck['hash'], _norm_digest_type(alg or 'sha256')


def _walk_json(x, fn):
    if isinstance(x, dict):
        fn(x)
        for v in x.values():
            _walk_json(v, fn)
    elif isinstance(x, list):
        for v in x:
            _walk_json(v, fn)


def embedded_json_blobs(page):
    """JSON objects inside <script> tags, including Angular transfer state (&q; escapes)."""
    blobs = []
    for m in re.finditer(r'<script[^>]*>(.*?)</script>', page, flags=re.S | re.I):
        s = m.group(1).strip()
        if not s or s[0] not in '{[':
            continue
        for cand in (s, s.replace('&q;', '"').replace('&a;', '&').replace('&s;', "'").replace('&l;', '<').replace('&g;', '>'),
                     htmllib.unescape(s)):
            try:
                blobs.append(json.loads(cand))
                break
            except ValueError:
                continue
    return blobs


def resolve_nist(part):
    pdr_id = part['pdr_id']
    found, notes, subcollections = {}, [], set()
    try:
        j = get_json(f'https://data.nist.gov/rmm/records?@id=ark:/88434/{pdr_id}')
        rec = (j.get('ResultData') or [{}])[0]
        for comp in rec.get('components', []):
            types = comp.get('@type', [])
            if 'nrdp:Subcollection' in types:
                subcollections.add(comp.get('filepath'))
            _nist_add(found, comp, pdr_id)
        meta = {'title': rec.get('title'), 'version': rec.get('version'), 'license': rec.get('license'), 'modified': rec.get('modified')}
    except Exception as e:  # noqa: BLE001 (report and continue with the landing page)
        meta = {}
        notes.append(f'RMM API failed: {e}')
    # Files inside subcollections are often missing from the RMM record. The landing page embeds them.
    def uncovered():
        return sorted(sc for sc in subcollections if sc and not any(p.startswith(sc.strip('/') + '/') for p in found))
    if not found or uncovered():
        try:
            status, page = get_text(f'https://data.nist.gov/od/id/{pdr_id}')
        except Exception as e:  # noqa: BLE001
            status, page = None, ''
            notes.append(f'landing page failed: {e}')
        if status == 200:
            LAST_PAGES[pdr_id] = page
            n0 = len(found)
            for blob in embedded_json_blobs(page):
                _walk_json(blob, lambda d: _nist_add(found, d, pdr_id))
            notes.append(f'landing page added {len(found) - n0} files')
        elif status is not None:
            notes.append(f'landing page HTTP {status}')
    if not found:
        raise RuntimeError('no files resolved for ' + pdr_id + ': ' + ' | '.join(notes))
    missing = uncovered()
    if missing:
        notes.append(f'subcollections with no listed files: {missing}. Inspect landing_{pdr_id}.html, extend the resolver, and stop until they resolve.')
    files = []
    for rel, f in sorted(found.items()):
        if rel.endswith('.sha256'):
            continue
        comp = found.get(rel + '.sha256')
        f['sha256_companion'] = comp['url'] if comp else f['url'] + '.sha256'
        files.append(f)
    return files, dict(meta, notes=notes, subcollections=sorted(x for x in subcollections if x), incomplete_subcollections=missing)


def resolve_zenodo(part):
    j = get_json(f"https://zenodo.org/api/records/{part['record_id']}")
    entries = j.get('files')
    if isinstance(entries, dict):
        inner = entries.get('entries') or {}
        entries = list(inner.values()) if isinstance(inner, dict) else list(inner)
    out = []
    for f in entries or []:
        key = f.get('key') or f.get('filename')
        ck = f.get('checksum') or ''
        dtp, dig = (ck.split(':', 1) + [None])[:2] if ':' in ck else (None, None)
        links = f.get('links') or {}
        url = links.get('content') or links.get('self') or links.get('download') or \
            f"https://zenodo.org/records/{part['record_id']}/files/{urllib.parse.quote(key)}?download=1"
        out.append({'path': key, 'url': url, 'bytes': f.get('size') or f.get('filesize'), 'digest': dig, 'digest_type': _norm_digest_type(dtp)})
    md = j.get('metadata', {})
    return out, {'license': (md.get('license') or {}).get('id') if isinstance(md.get('license'), dict) else md.get('license'),
                 'version': md.get('version'), 'doi': j.get('doi')}


def resolve_mendeley(part):
    ds, ver = part['dataset_id'], part['version']
    base = f'https://data.mendeley.com/public-api/datasets/{ds}'
    folders = get_json(f'{base}/folders/{ver}')
    byid = {f['id']: f for f in folders if isinstance(f, dict)}

    def fpath(fid):
        p = []
        while fid in byid:
            p.append(byid[fid]['name'])
            fid = byid[fid].get('parent_id')
        return '/'.join(reversed(p))
    out = []
    for fid in [None] + list(byid):
        q = f'{base}/files?version={ver}&folder_id=' + (fid if fid else 'root')
        for f in get_json(q):
            if not isinstance(f, dict):
                continue
            cd = f.get('content_details') or {}
            url = cd.get('download_url')
            if not url:
                continue
            rel = '/'.join(x for x in (ds, fpath(fid) if fid else '', f.get('filename')) if x)
            dig, dtp = (cd.get('sha256_hash'), 'sha256') if cd.get('sha256_hash') else (cd.get('sha1_hash'), 'sha1') if cd.get('sha1_hash') else (None, None)
            out.append({'path': rel, 'url': url, 'bytes': cd.get('size') or f.get('size'), 'digest': dig, 'digest_type': dtp})
    return out, {'dataset_id': ds, 'version': ver}


def resolve_direct(part):
    req = urllib.request.Request(part['url'], method='HEAD', headers=_headers(part['url']))
    size = None
    try:
        with OPENER.open(req, timeout=60) as r:
            size = int(r.headers.get('Content-Length')) if r.headers.get('Content-Length') else None
    except Exception:  # noqa: BLE001
        pass
    return [{'path': 'direct/' + part['name'], 'url': part['url'], 'bytes': size, 'digest': None, 'digest_type': None}], {}


def resolve_refodat(part):
    """No scripted download: probe the landing page once and read DataCite for the expected count and size."""
    meta = {'manual': True}
    try:
        a = get_json(f"https://api.datacite.org/dois/{part['doi']}")['data']['attributes']
        meta['datacite_sizes'] = a.get('sizes')
        meta['datacite_formats'] = a.get('formats')
        meta['datacite_rights'] = [r.get('rights') for r in a.get('rightsList', [])]
        meta['landing'] = a.get('url')
    except Exception as e:  # noqa: BLE001
        meta['datacite_error'] = str(e)
    try:
        status, page = get_text(part['landing'])
        meta['landing_status'] = status
        meta['security_check'] = bool(re.search(r'security check|verify your connection|calculating solution', page, re.I))
    except Exception as e:  # noqa: BLE001
        meta['landing_error'] = str(e)
    return [], meta


RESOLVERS = {'dryad': resolve_dryad, 'nist_pdr': resolve_nist, 'zenodo': resolve_zenodo, 'mendeley': resolve_mendeley,
             'direct': resolve_direct, 'refodat_manual': resolve_refodat}


def tier_of(part, name):
    if 'tier' in part:
        return part['tier']
    for rule in part.get('tier_rules', []):
        if any(fnmatch.fnmatch(name, pat) for pat in rule['names']):
            return rule['tier']
    return 3


# ---------------------------------------------------------------- registry and plan
def load_registry():
    return json.load(open(REGISTRY))


def root_dir(reg):
    return os.path.join(HARBOR, reg.get('host_root', 'v4_host/trackS'))


def select(reg, ids):
    ds = reg['datasets']
    if ids:
        known = {d['id'] for d in ds}
        bad = [i for i in ids if i not in known]
        if bad:
            sys.exit(f'unknown dataset ids: {bad}. Known: {sorted(known)}')
        return [d for d in ds if d['id'] in ids]
    return [d for d in ds if d.get('pilot') != 'reserve']


def plan(args):
    reg = load_registry()
    root = root_dir(reg)
    os.makedirs(root, exist_ok=True)
    summary = {'created': now(), 'tier_max': args.tier, 'datasets': {}}
    for d in select(reg, args.dataset):
        files, metas = [], []
        for part in d['parts']:
            label = part.get('pdr_id') or part.get('doi') or part.get('record_id') or part.get('dataset_id') or part.get('name')
            min_tier = part.get('tier', min([r['tier'] for r in part.get('tier_rules', [])] or [1]))
            if min_tier > args.tier:
                metas.append({'part': label, 'repository': part['repository'], 'skipped': f'tier {min_tier} > {args.tier}'})
                continue
            try:
                got, meta = RESOLVERS[part['repository']](part)
            except Exception as e:  # noqa: BLE001
                got, meta = [], {'error': str(e)}
            prefix = part['pdr_id'] + '/' if part['repository'] == 'nist_pdr' else ''
            for f in got:
                f['path'] = prefix + f['path']
                f['tier'] = tier_of(part, os.path.basename(f['path']))
                f['part'] = label
            files += got
            metas.append({'part': label, 'repository': part['repository'], **meta})
        sel = [f for f in files if f['tier'] <= args.tier]
        known = [f['bytes'] for f in sel if isinstance(f.get('bytes'), int)]
        unresolved = [m['part'] for m in metas if m.get('error') or m.get('incomplete_subcollections')]
        warnings = []
        names = {os.path.basename(f['path']) for f in files}
        for part in d['parts']:
            for rule in part.get('tier_rules', []):
                for pat in rule['names']:
                    if not any(ch in pat for ch in '*?[') and pat not in names and files:
                        warnings.append(f'tier rule name not found in the deposit: {pat} (renamed in a new version?)')
        exp_v = (d.get('expected') or {}).get('version_id')
        for m in metas:
            if exp_v and m.get('version_id') and m['version_id'] != exp_v:
                warnings.append(f"repository version {m['version_id']} differs from the screened version {exp_v}: check the file list")
        for w in warnings:
            log(f"   WARNING {d['id']}: {w}")
        p = {'dataset': d['id'], 'pilot': d.get('pilot'), 'license': d.get('license'), 'resolved': now(), 'tier_max': args.tier,
             'parts': metas, 'unresolved_parts': unresolved, 'files': files, 'selected': len(sel), 'selected_bytes_known': sum(known),
             'selected_bytes_unknown_files': len(sel) - len(known),
             'expected': d.get('expected', {}), 'warnings': warnings}
        ddir = os.path.join(root, d['id'])
        os.makedirs(ddir, exist_ok=True)
        _atomic_json(os.path.join(ddir, 'plan.json'), p)
        for part in d['parts']:
            page = LAST_PAGES.pop(part.get('pdr_id'), None)
            if page:
                open(os.path.join(ddir, f"landing_{part['pdr_id']}.html"), 'w').write(page)
        summary['datasets'][d['id']] = {k: p[k] for k in ('pilot', 'selected', 'selected_bytes_known', 'selected_bytes_unknown_files')}
        summary['datasets'][d['id']]['manual'] = any(m.get('manual') for m in metas)
        summary['datasets'][d['id']]['unresolved_parts'] = unresolved
        summary['datasets'][d['id']]['warnings'] = warnings
        summary['datasets'][d['id']]['notes'] = [n for m in metas for n in (m.get('notes') or [])] + [m['error'] for m in metas if m.get('error')]
        _print_plan(d, p, metas)
    need = sum(v['selected_bytes_known'] for v in summary['datasets'].values())
    free = shutil.disk_usage(root).free
    summary.update({'planned_bytes_known': need, 'free_bytes': free, 'disk_ok': free > 1.1 * need})
    _atomic_json(os.path.join(root, '_plan_summary.json'), summary)
    log(f'\nPLAN tier <= {args.tier}: {need / 1e9:.2f} GB known, free {free / 1e9:.1f} GB, disk ok {summary["disk_ok"]}')
    bad = {k: v['unresolved_parts'] for k, v in summary['datasets'].items() if v.get('unresolved_parts')}
    if bad:
        log(f'UNRESOLVED parts (fix access before get): {bad}')
    return summary


def _print_plan(d, p, metas):
    log(f"\n== {d['id']} ({d.get('pilot')}): {p['selected']} files at tier <= {p['tier_max']}, "
        f"{p['selected_bytes_known'] / 1e9:.2f} GB known, {p['selected_bytes_unknown_files']} files of unknown size")
    for m in metas:
        extra = {k: m[k] for k in ('version_id', 'license', 'notes', 'error', 'security_check', 'datacite_sizes', 'subcollections', 'incomplete_subcollections',
                                   'datacite_error', 'landing_error', 'landing_status', 'skipped') if m.get(k)}
        log(f"   part {m['part']} [{m['repository']}] {json.dumps(extra)[:600]}")
        if m.get('manual'):
            log('   MANUAL: open the landing page in a browser, download every file, then run: '
                f"fetch_s.py manual --dataset {d['id']} --src <download folder>")


def _atomic_json(path, obj):
    tmp = path + '.tmp'
    with open(tmp, 'w') as fh:
        json.dump(obj, fh, indent=1, default=str)
    os.replace(tmp, path)


# ---------------------------------------------------------------- download
def _hashers(digest_type):
    hs = {'sha256': hashlib.sha256()}
    if digest_type and digest_type not in hs:
        hs[digest_type] = hashlib.new(digest_type)
    return hs


def _companion_sha256(f):
    url = f.get('sha256_companion')
    if not url:
        return None
    try:
        status, _, body = http_get(url, timeout=60)
        if status == 200:
            m = re.search(rb'\b([0-9a-fA-F]{64})\b', body)
            return m.group(1).decode().lower() if m else None
    except Exception:  # noqa: BLE001
        return None
    return None


def _rehash_part(part, digest_type):
    hs, pos = _hashers(digest_type), 0
    if os.path.exists(part):
        with open(part, 'rb') as fh:
            for chunk in iter(lambda: fh.read(CHUNK), b''):
                for h in hs.values():
                    h.update(chunk)
                pos += len(chunk)
    return hs, pos


def _expected_total(r, pos):
    """Total bytes the server promises for this response, or None (chunked without length)."""
    cr = r.headers.get('Content-Range')
    if r.status == 206 and cr and '/' in cr:
        tail = cr.rsplit('/', 1)[1].strip()
        return int(tail) if tail.isdigit() else None
    cl = r.headers.get('Content-Length')
    return int(cl) if cl and cl.isdigit() and r.status == 200 else None


def download_one(f, dest):
    """Stream f['url'] to dest with resume. A short body raises and resumes. Returns a manifest entry."""
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if not f.get('digest') and f.get('sha256_companion'):
        dg = _companion_sha256(f)
        if dg:
            f['digest'], f['digest_type'] = dg, 'sha256'
    entry = {'path': f['path'], 'url': f['url'], 'tier': f.get('tier'), 'part': f.get('part'), 'repo_bytes': f.get('bytes'),
             'repo_digest': f.get('digest'), 'digest_type': f.get('digest_type')}
    if os.path.exists(dest):
        entry.update(_hash_file(dest, f.get('digest_type')))
        entry['verified'] = _check(entry, f)
        if entry['verified'] is not False:
            entry['status'] = 'present'
            return entry
        os.replace(dest, dest + '.bad')  # a corrupt copy (for example a bad rsync) never stays in place
        log(f'  {f["path"]}: present copy fails its checksum, moved to .bad, downloading again')
    part = dest + '.part'
    hs, pos = _rehash_part(part, f.get('digest_type'))
    url = _safe_url(f['url'])
    done = False
    for attempt in range(8):
        extra = {'Range': f'bytes={pos}-'} if pos else {}
        req = urllib.request.Request(url, headers=_headers(f['url'], extra))
        try:
            with OPENER.open(req, timeout=600) as r:
                if pos and r.status == 200:  # server ignored the range: restart cleanly
                    hs, pos = _hashers(f.get('digest_type')), 0
                    mode = 'wb'
                else:
                    mode = 'ab' if pos else 'wb'
                total = _expected_total(r, pos)
                with open(part, mode) as out:
                    for chunk in iter(lambda: r.read(CHUNK), b''):
                        out.write(chunk)
                        for h in hs.values():
                            h.update(chunk)
                        pos += len(chunk)
                if total is not None and pos < total:
                    raise ConnectionError(f'short read: {pos} of {total} bytes')
            done = True
            break
        except urllib.error.HTTPError as e:
            if e.code == 416:  # range past the end: the part is complete
                done = True
                break
            if e.code in (401, 403):
                entry.update({'status': f'HTTP {e.code}', 'verified': None})
                log(f'  {f["path"]}: HTTP {e.code}. For Dryad, set DRYAD_TOKEN or download by hand.')
                return entry
            wait = _retry_after(e.headers, attempt)
            log(f'  {f["path"]}: HTTP {e.code}, retry in {wait} s')
            time.sleep(wait)
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError, http.client.HTTPException) as e:
            wait = min(300, 2 ** attempt * 5)
            log(f'  {f["path"]}: {type(e).__name__}: {e}, resume in {wait} s')
            time.sleep(wait)
            hs, pos = _rehash_part(part, f.get('digest_type'))  # resume from what is on disk
    if not done:
        entry.update({'status': 'failed', 'verified': None, 'bytes_on_disk': pos})
        return entry
    entry.update({'bytes': pos, 'sha256': hs['sha256'].hexdigest()})
    if f.get('digest_type') and f['digest_type'] != 'sha256':
        entry[f['digest_type']] = hs[f['digest_type']].hexdigest()
    ok = _check(entry, f)
    entry['verified'] = ok
    if ok is False:
        os.replace(part, dest + '.bad')
        entry['status'] = 'checksum_or_size_mismatch'
    else:
        os.replace(part, dest)
        entry['status'] = 'downloaded'
    entry['retrieved'] = now()
    return entry


def _hash_file(path, digest_type):
    hs = _hashers(digest_type)
    n = 0
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(CHUNK), b''):
            n += len(chunk)
            for h in hs.values():
                h.update(chunk)
    out = {'bytes': n, 'sha256': hs['sha256'].hexdigest()}
    if digest_type and digest_type != 'sha256':
        out[digest_type] = hs[digest_type].hexdigest()
    return out


def _check(entry, f):
    """True when size and repository digest agree, False on any mismatch, None when the repository gives no digest."""
    if isinstance(f.get('bytes'), int) and entry.get('bytes') != f['bytes']:
        return False
    if not f.get('digest'):
        return None
    mine = entry.get(f['digest_type']) if f['digest_type'] != 'sha256' else entry.get('sha256')
    return bool(mine) and mine.lower() == f['digest'].lower()


def get(args):
    reg = load_registry()
    root = root_dir(reg)
    summary = plan(args)
    if not summary['disk_ok']:
        sys.exit('STOP: not enough free disk for the planned files (need 1.1 x planned bytes).')
    if summary['planned_bytes_known'] > BIG and not args.yes:
        sys.exit(f"STOP: {summary['planned_bytes_known'] / 1e9:.1f} GB planned. Rerun with --yes to proceed.")
    bad_total = 0
    for d in select(reg, args.dataset):
        ddir = os.path.join(root, d['id'])
        p = json.load(open(os.path.join(ddir, 'plan.json')))
        todo = [f for f in p['files'] if f['tier'] <= args.tier]
        if not todo:
            log(f"== {d['id']}: nothing to fetch by script" + (' (manual dataset)' if summary['datasets'][d['id']]['manual'] else ''))
            continue
        mpath = os.path.join(ddir, 'manifest.json')
        man = json.load(open(mpath)) if os.path.exists(mpath) else {'dataset': d['id'], 'license': d.get('license'), 'files': {}}
        man['parts'] = p['parts']
        man['unresolved_parts'] = p.get('unresolved_parts', [])
        if man['unresolved_parts']:
            log(f"== {d['id']}: WARNING unresolved parts {man['unresolved_parts']}: the dataset stays incomplete (R1)")
        log(f"== {d['id']}: fetching {len(todo)} files with {args.jobs} jobs")

        def work(f):
            try:
                e = download_one(f, os.path.join(ddir, 'files', f['path']))
            except Exception as ex:  # noqa: BLE001 (one bad file never stops the other datasets)
                e = {'path': f['path'], 'url': f['url'], 'status': 'failed', 'verified': None, 'error': f'{type(ex).__name__}: {ex}'}
            with LOCK:
                man['files'][f['path']] = e
                man['updated'] = now()
                _atomic_json(mpath, man)
            log(f"  {e['status']:>24} {f['path']} {e.get('bytes')} verified={e.get('verified')}")
            return e
        with cf.ThreadPoolExecutor(max_workers=args.jobs) as ex:
            res = list(ex.map(work, todo))
        bad = [e for e in res if e.get('verified') is False or e.get('status') in ('failed', 'checksum_or_size_mismatch') or str(e.get('status')).startswith('HTTP')]
        unverified = [e for e in res if e.get('verified') is None]
        bad_total += len(bad)
        log(f"== {d['id']}: {len(res) - len(bad)} ok ({len(unverified)} without a repository digest), {len(bad)} failed")
    write_inputs(root)
    if bad_total:
        sys.exit(f'{bad_total} files failed or mismatched: see the manifests')


def verify(args):
    """Recompute sha256 of every manifest file, fail on any repository mismatch and on planned files with no good entry."""
    reg = load_registry()
    root = root_dir(reg)
    worst = 0
    for d in select(reg, args.dataset):
        ddir = os.path.join(root, d['id'])
        mpath = os.path.join(ddir, 'manifest.json')
        if not os.path.exists(mpath):
            log(f'{d["id"]}: no manifest')
            worst += 1
            continue
        man = json.load(open(mpath))
        bad = 0
        for rel, e in man['files'].items():
            p = os.path.join(ddir, 'files', rel)
            if not os.path.exists(p):
                log(f'  missing {rel}')
                bad += 1
                continue
            h = _hash_file(p, None)
            if h['sha256'] != e.get('sha256') or h['bytes'] != e.get('bytes'):
                log(f'  CHANGED since the manifest: {rel}')
                bad += 1
            elif e.get('verified') is False or e.get('status') in ('failed', 'checksum_or_size_mismatch', 'present_but_mismatch'):
                log(f'  repository mismatch: {rel} ({e.get("status")})')
                bad += 1
        planned = 0
        ppath = os.path.join(ddir, 'plan.json')
        if os.path.exists(ppath):
            pl = json.load(open(ppath))
            for f in pl['files']:
                if f['tier'] <= pl.get('tier_max', 1):
                    planned += 1
                    e = man['files'].get(f['path'])
                    if not e or e.get('status') not in ('downloaded', 'present'):
                        log(f'  planned but not on host: {f["path"]}')
                        bad += 1
            for part in pl.get('unresolved_parts', []):
                log(f'  unresolved repository part: {part}')
                bad += 1
        log(f'{d["id"]}: {len(man["files"])} manifest files, {planned} planned, {bad} problems')
        worst += bad
    sys.exit(1 if worst else 0)


def manual(args):
    reg = load_registry()
    root = root_dir(reg)
    d = select(reg, [args.dataset])[0]
    ddir = os.path.join(root, d['id'])
    dst = os.path.join(ddir, 'files')
    os.makedirs(dst, exist_ok=True)
    partial = [os.path.join(b, n) for b, _, ns in os.walk(args.src) for n in ns
               if n.endswith(('.crdownload', '.part', '.download', '.partial', '.tmp')) or n.startswith('.~')]
    if partial:
        sys.exit(f'STOP: unfinished browser downloads in {args.src}: {partial[:5]}')
    entries = {}
    for base, _, names in os.walk(args.src):
        for n in names:
            src = os.path.join(base, n)
            rel = os.path.relpath(src, args.src)
            target = os.path.join(dst, rel)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            (shutil.move if args.move else shutil.copy2)(src, target)
            e = {'path': rel, 'url': 'manual browser download', 'status': 'manual', **_hash_file(target, None), 'retrieved': now()}
            entries[rel] = e
            log(f'  {rel} {e["bytes"]} {e["sha256"][:12]}')
    exp = d.get('expected', {})
    n, total = len(entries), sum(e['bytes'] for e in entries.values())
    want_n, want_b = exp.get('files'), exp.get('bytes_total_approx')
    ok_n = want_n is None or n == want_n
    # DataCite prints MB with two decimals and does not say whether it means 10^6 or 2^20 bytes: accept either within 0.5 %
    ok_b = want_b is None or any(abs(total - w) <= 0.005 * w for w in (want_b, want_b * 1.048576))
    man = {'dataset': d['id'], 'license': d.get('license'), 'files': entries, 'updated': now(),
           'manual_check': {'files': n, 'expected_files': want_n, 'bytes': total, 'expected_bytes_approx': want_b,
                            'count_ok': ok_n, 'size_ok': ok_b,
                            'note': 'the repository publishes no per-file checksum: sha256 here is the first record'}}
    _atomic_json(os.path.join(ddir, 'manifest.json'), man)
    write_inputs(root)
    log(f'{d["id"]}: {n} files, {total / 1e9:.3f} GB. count ok {ok_n}, size ok {ok_b}')
    if not (ok_n and ok_b):
        sys.exit('STOP: the manual download does not match DataCite (count or size). Check for missing files.')


def write_inputs(root):
    lines = ['# Track S inputs (generated by fetch_s.py inputs)', '', f'Generated {now()}. Paste into LOG.md at stage start (inputs check).', '']
    for ddir in sorted(os.listdir(root)):
        mpath = os.path.join(root, ddir, 'manifest.json')
        if not os.path.isfile(mpath):
            continue
        man = json.load(open(mpath))
        h = hashlib.sha256(open(mpath, 'rb').read()).hexdigest()
        files = man.get('files', {})
        nb = sum((e.get('bytes') or 0) for e in files.values())
        nver = sum(1 for e in files.values() if e.get('verified') is True)
        lines.append(f"- {ddir}: {len(files)} files, {nb / 1e9:.3f} GB, repository-verified {nver}, manifest sha256 {h}")
    open(os.path.join(root, 'INPUTS_trackS.md'), 'w').write('\n'.join(lines) + '\n')
    log(f'wrote {os.path.join(root, "INPUTS_trackS.md")}')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    for name in ('plan', 'get'):
        s = sub.add_parser(name)
        s.add_argument('--tier', type=int, default=1)
        s.add_argument('--dataset', nargs='*')
        if name == 'get':
            s.add_argument('--yes', action='store_true')
            s.add_argument('--jobs', type=int, default=2)
    s = sub.add_parser('verify')
    s.add_argument('--dataset', nargs='*')
    s = sub.add_parser('manual')
    s.add_argument('--dataset', required=True)
    s.add_argument('--src', required=True)
    s.add_argument('--move', action='store_true')
    sub.add_parser('inputs')
    args = ap.parse_args(argv)
    if args.cmd == 'plan':
        plan(args)
    elif args.cmd == 'get':
        get(args)
    elif args.cmd == 'verify':
        verify(args)
    elif args.cmd == 'manual':
        manual(args)
    else:
        write_inputs(root_dir(load_registry()))


if __name__ == '__main__':
    main()
