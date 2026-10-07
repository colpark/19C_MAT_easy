#!/usr/bin/env python3
"""htem_api.py: polite, caching client for the public HTEM DB API (htem-api.nlr.gov; NREL is now NLR, old nrel.gov hosts stopped
resolving on 2026-05-29). No key is needed. Every response is cached once under $HTEM_HOST/cache/ with a sha256 manifest, so reruns and
retries never hit the server twice for the same object. A 404 leaves a .404 marker, so reruns do not ask again.

Endpoints used: /sample_library (list, optional ?element=A,B), /sample_library/<id>, /sample/<id>.

Rules (skill M0 fetch): one request at a time, a minimum interval with jitter, Retry-After honoured, exponential backoff, a hard request
budget checked before every attempt, the throttle stamped after each response, error bodies (non-JSON, a JSON error, or a record whose id
differs from the one asked for) kept as .bad and never parsed as data. PII fields (owner names and
emails) are stripped before anything is written.

usage:
  htem_api.py probe                       # one list call, prints count and field names
  htem_api.py list [--refresh]            # caches the full library list (--refresh replaces a stale copy)
  htem_api.py library <id> [<id> ...]     # caches library records
  htem_api.py samples <library_id> ...    # caches every sample of the given libraries
  htem_api.py manifest                    # prints cache size and verifies sha256 of every cached object
"""
import hashlib, http.client, json, os, random, sys, time, urllib.error, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(HERE, 'config.json')))
HOST = os.environ.get('HTEM_HOST', os.path.expanduser('~/Documents/harbor/v4_host/htem'))
CACHE = os.path.join(HOST, 'cache')
MANIFEST = os.path.join(HOST, 'manifest.jsonl')


class HTEMError(RuntimeError):
    pass


class NotFound(HTEMError):
    pass


class Client:
    def __init__(self, cfg=CFG, cache=CACHE, manifest=MANIFEST, opener=None, sleep=time.sleep, clock=time.monotonic):
        self.cfg, self.cache, self.manifest = cfg, cache, manifest
        self.t = cfg['throttle']
        self.opener = opener or urllib.request.urlopen
        self.sleep, self.clock = sleep, clock
        self.last = None
        self.n_requests = 0
        os.makedirs(cache, exist_ok=True)

    # ---------- paths and cache
    def _path(self, kind, key):
        safe = str(key).replace('/', '_').replace(',', '-').replace('?', '_').replace('=', '_')
        d = os.path.join(self.cache, kind)
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, f'{safe}.json')

    def _record(self, path, body):
        rec = {'path': os.path.relpath(path, self.cache), 'sha256': hashlib.sha256(body).hexdigest(), 'bytes': len(body),
               'time': time.strftime('%Y-%m-%dT%H:%M:%S%z')}
        with open(self.manifest, 'a') as f:
            f.write(json.dumps(rec) + '\n')

    @staticmethod
    def strip_pii(obj, fields):
        if isinstance(obj, dict):
            return {k: Client.strip_pii(v, fields) for k, v in obj.items() if k not in fields}
        if isinstance(obj, list):
            return [Client.strip_pii(v, fields) for v in obj]
        return obj

    # ---------- throttled GET
    def _wait(self):
        if self.last is not None:
            gap = self.t['min_interval_s'] * (1 + random.random() * self.t['jitter_frac'])
            dt = self.clock() - self.last
            if dt < gap:
                self.sleep(gap - dt)

    def _get(self, url):
        err = None
        tries = self.t['max_retries'] + 1
        for attempt in range(tries):
            if self.n_requests >= self.t['max_requests']:
                raise HTEMError(f'request budget {self.t["max_requests"]} reached')
            self._wait()
            self.n_requests += 1
            req = urllib.request.Request(url, headers={'User-Agent': self.cfg['user_agent'], 'Accept': 'application/json'})
            last_try = attempt == tries - 1
            try:
                with self.opener(req, timeout=self.t['timeout_s']) as r:
                    body = r.read()
                    ctype = (r.headers.get('Content-Type') or '') if getattr(r, 'headers', None) else ''
                self.last = self.clock()
                return body, ctype
            except urllib.error.HTTPError as e:
                self.last = self.clock()
                err = e
                if e.code == 404:
                    raise NotFound(url) from e
                if e.code in (429, 500, 502, 503, 504, 524):
                    ra = e.headers.get('Retry-After') if e.headers else None
                    wait = float(ra) if ra and ra.replace('.', '', 1).isdigit() else self.t['backoff_s'] * 2 ** attempt
                    if not last_try:
                        self.sleep(min(wait, self.t.get('max_wait_s', 300)))
                    continue
                raise HTEMError(f'HTTP {e.code} for {url}') from e
            except (urllib.error.URLError, http.client.HTTPException, TimeoutError, ConnectionError, OSError) as e:
                self.last = self.clock()
                err = e
                if not last_try:
                    self.sleep(min(self.t['backoff_s'] * 2 ** attempt, self.t.get('max_wait_s', 300)))
        raise HTEMError(f'giving up on {url}: {err}')

    @staticmethod
    def is_error_body(body, ctype, expect, key=None):
        """True when the body is not the record we asked for. JSON is tried first, so a mislabeled content type never rejects data."""
        try:
            obj = json.loads(body)
        except ValueError:
            return True
        if expect == 'list':
            return not isinstance(obj, list)
        if not isinstance(obj, dict) or not obj:
            return True
        if obj.get('id') is None:  # records seen so far carry id; accept a record without one only if it looks like data
            looks = any(k in obj for k in ('sample_ids', 'elements', 'position', 'xrd_angle', 'sample_library_id'))
            return not looks or any(k in obj for k in ('error', 'message', 'detail'))
        try:
            return key is not None and int(obj['id']) != int(key)
        except (TypeError, ValueError):
            return True

    def fetch(self, kind, key, url, expect, refresh=False):
        path = self._path(kind, key)
        if os.path.exists(path) and not refresh:
            return json.load(open(path))
        if os.path.exists(path[:-5] + '.404') and not refresh:
            raise NotFound(url)
        try:
            body, ctype = self._get(url)
        except NotFound:
            open(path[:-5] + '.404', 'w').close()
            raise
        if self.is_error_body(body, ctype, expect, key if expect == 'dict' else None):
            with open(path[:-5] + '.bad', 'wb') as f:
                f.write(body)
            raise HTEMError(f'error body for {url} (kept as .bad)')
        obj = self.strip_pii(json.loads(body), set(self.cfg['pii_fields']))
        out = json.dumps(obj, sort_keys=True).encode()
        tmp = path + '.part'
        with open(tmp, 'wb') as f:
            f.write(out)
        os.replace(tmp, path)
        self._record(path, out)
        return obj

    def cached(self, kind, key):
        path = self._path(kind, key)
        return json.load(open(path)) if os.path.exists(path) else None

    # ---------- endpoints
    def libraries(self, elements=None, refresh=False):
        q = '' if not elements else '?element=' + ','.join(elements)
        key = 'all' if not elements else ','.join(sorted(elements))
        return self.fetch('library_list', key, f"{self.cfg['base_url']}/sample_library{q}", 'list', refresh=refresh)

    def library(self, lid):
        return self.fetch('library', lid, f"{self.cfg['base_url']}/sample_library/{int(lid)}", 'dict')

    def sample(self, sid):
        return self.fetch('sample', sid, f"{self.cfg['base_url']}/sample/{int(sid)}", 'dict')

    def samples_of(self, lid, skipped=None):
        """Every sample of a library. A sample that fails (404, error body, retries exhausted) is skipped and listed in skipped."""
        lib = self.library(lid)
        out = []
        for sid in lib.get('sample_ids') or []:
            try:
                out.append(self.sample(sid))
            except HTEMError as e:
                if skipped is not None:
                    skipped.append({'library': lid, 'sample': sid, 'error': str(e)})
        return out


def verify_manifest(cache=CACHE, manifest=MANIFEST):
    bad, n, total = [], 0, 0
    if not os.path.exists(manifest):
        return {'objects': 0, 'bytes': 0, 'bad': []}
    seen = {}
    for line in open(manifest):
        r = json.loads(line)
        seen[r['path']] = r
    for p, r in seen.items():
        fp = os.path.join(cache, p)
        n += 1
        if not os.path.exists(fp):
            bad.append((p, 'missing'))
            continue
        b = open(fp, 'rb').read()
        total += len(b)
        if hashlib.sha256(b).hexdigest() != r['sha256']:
            bad.append((p, 'sha256'))
    return {'objects': n, 'bytes': total, 'bad': bad}


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    c = Client()
    cmd, args = argv[0], argv[1:]
    if cmd == 'probe':
        libs = c.libraries()
        print(json.dumps({'count': len(libs), 'fields': sorted(libs[0].keys()) if libs else []}, indent=1))
    elif cmd == 'list':
        print(len(c.libraries(refresh='--refresh' in args)), 'library records cached')
    elif cmd == 'library':
        for a in args:
            c.library(a)
        print(len(args), 'library records cached')
    elif cmd == 'samples':
        n = 0
        for a in args:
            n += len(c.samples_of(a))
        print(n, 'samples cached', c.n_requests, 'requests')
    elif cmd == 'manifest':
        print(json.dumps(verify_manifest(), indent=1))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
