#!/usr/bin/env python3
"""oa_harvest.py: legal open-access full-text harvest for the MatMech SEM + multimodal pool.

Subcommands (run from the oa_harvest/ folder):
  targets    build targets.jsonl (doi, journal, year, title) from fm_supply_papers.json + MatMech data.json
  calibrate  Unpaywall lookups for the 249-DOI sample; compare with matmech_access_sample.csv
  lookup     Unpaywall lookup for every target -> unpaywall/<doi_safe>.json (resumable; errors retried once)
  plan       candidate PDF URLs per open-access paper -> plan.jsonl, split by DOI hash into shard_0/1.jsonl
  download   --shard N: download, validate, record -> status/<doi_safe>.json, pdfs/<journal>/<doi_safe>.pdf
  manifest   oa_manifest.csv, oa_failed.csv, closed_for_library.csv
  report     REPORT.md

Rules (PROMPT): legal OA only (Unpaywall locations, Europe PMC); every request carries the User-Agent with the
contact email; at most 1 request/second per remote host; back off on 429/503; robots.txt respected.
No model reads downloaded files: acceptance is checked by script only (%PDF, pages > 3, title/DOI on page 1).
"""
import argparse, collections, csv, hashlib, json, os, re, subprocess, sys, threading, time, urllib.parse
import urllib.robotparser
from concurrent.futures import ThreadPoolExecutor
import requests

EMAIL = os.environ['OA_EMAIL']  # contact email, required by Unpaywall
UA = f'causalmat-oa-harvest (mailto:{EMAIL})'
MATMECH = os.path.expanduser('~/Documents/causalmat/matmech')
PAPERS = os.path.expanduser('~/panels/fm_supply_papers.json')
SAMPLE = 'matmech_access_sample.csv'

def safe(doi): return urllib.parse.quote(doi, safe='')
def log(msg):
    line = f"- {time.strftime('%Y-%m-%d %H:%M:%S %Z')} [{os.uname().nodename}] {msg}\n"
    with open('LOG.md', 'a') as f: f.write(line)
    print(line, end='', flush=True)

class Polite:
    """Shared session: 1 request/s per remote host, backoff on 429/503, robots.txt cache."""
    def __init__(self):
        self.s = requests.Session(); self.s.headers['User-Agent'] = UA
        self.last, self.locks, self.robots = {}, collections.defaultdict(threading.Lock), {}
        self.glock = threading.Lock()
    def _wait(self, host):
        with self.locks[host]:
            dt = time.time() - self.last.get(host, 0)
            if dt < 1.0: time.sleep(1.0 - dt)
            self.last[host] = time.time()
    def allowed(self, url):
        p = urllib.parse.urlsplit(url); base = f'{p.scheme}://{p.netloc}'
        with self.glock:
            rp = self.robots.get(base)
        if rp is None:
            rp = urllib.robotparser.RobotFileParser()
            try:
                self._wait(p.netloc)
                r = self.s.get(base + '/robots.txt', timeout=20)
                rp.parse(r.text.splitlines() if r.status_code == 200 else [])
            except Exception:
                rp.parse([])
            with self.glock: self.robots[base] = rp
        return rp.can_fetch(UA, url)
    def get(self, url, stream=False, timeout=60):
        host = urllib.parse.urlsplit(url).netloc
        for attempt in range(4):
            self._wait(host)
            r = self.s.get(url, stream=stream, timeout=timeout, allow_redirects=True)
            if r.status_code in (429, 503) and attempt < 3:
                wait = r.headers.get('Retry-After'); wait = int(wait) if wait and wait.isdigit() else 30 * 2 ** attempt
                r.close(); time.sleep(min(wait, 600)); continue
            return r
        return r

# ---------- targets ----------
def cmd_targets(a):
    L = json.load(open(PAPERS)); assert len(L) == 16487, f'expected 16487 papers, got {len(L)}'
    n = 0
    with open('targets.jsonl', 'w') as f:
        for p in L:
            d = json.load(open(os.path.join(MATMECH, p['journal'], p['doi'], 'data.json')))
            doi = re.sub(r'^https?://(dx\.)?doi\.org/', '', d['doi'].strip())
            f.write(json.dumps({'doi': doi, 'journal': p['journal'], 'year': p.get('year') or d.get('year'),
                                'title': d.get('title', '')}) + '\n'); n += 1
    dois = [json.loads(l)['doi'] for l in open('targets.jsonl')]
    log(f'targets: {n} papers, {len(set(dois))} unique DOIs (DOIs from MatMech data.json)')

# ---------- unpaywall ----------
def unpaywall(pol, doi):
    r = pol.get(f'https://api.unpaywall.org/v2/{urllib.parse.quote(doi)}?email={EMAIL}', timeout=30)
    return r.status_code, (r.json() if r.headers.get('content-type', '').startswith('application/json') else None)

def cmd_calibrate(a):
    pol = Polite(); os.makedirs('unpaywall_calib', exist_ok=True)
    rows = list(csv.DictReader(open(SAMPLE))); mism = []; cnt = collections.Counter()
    for r in rows:
        p = f"unpaywall_calib/{safe(r['doi'])}.json"
        if not os.path.exists(p):
            code, j = unpaywall(pol, r['doi']); json.dump({'http': code, 'data': j}, open(p, 'w'))
        j = json.load(open(p))['data'] or {}
        is_oa, st = str(bool(j.get('is_oa'))), j.get('oa_status') or 'error'
        cnt[st] += 1
        if is_oa != r['unpaywall_is_oa'] or st != r['oa_status']:
            mism.append((r['doi'], f"{r['unpaywall_is_oa']}/{r['oa_status']} -> {is_oa}/{st}"))
    log(f'calibrate: 249 DOIs, now {dict(cnt)} (sample: closed 163, gold 31, hybrid 21, green 22, bronze 12); '
        f'mismatches {len(mism)}: {mism}')
    if len(mism) > 10: log('calibrate: STOP, more than 10 mismatches'); sys.exit(2)

def cmd_lookup(a):
    pol = Polite(); os.makedirs('unpaywall', exist_ok=True)
    T = [json.loads(l) for l in open('targets.jsonl')]
    def run(todo, tag):
        errs = []
        for i, t in enumerate(todo):
            p = f"unpaywall/{safe(t['doi'])}.json"
            try:
                code, j = unpaywall(pol, t['doi'])
                if code == 200 and j: json.dump(j, open(p, 'w'))
                elif code == 404: json.dump({'doi': t['doi'], 'is_oa': False, 'oa_status': 'not_in_unpaywall', 'oa_locations': []}, open(p, 'w'))
                else: errs.append((t, f'http {code}'))
            except Exception as e: errs.append((t, repr(e)[:120]))
            if i % 500 == 0: print(f'{tag} {i}/{len(todo)} errors {len(errs)}', flush=True)
        return errs
    todo = [t for t in T if not os.path.exists(f"unpaywall/{safe(t['doi'])}.json")]
    log(f'lookup: {len(T)} targets, {len(todo)} to query')
    errs = run(todo, 'pass1'); log(f'lookup pass 1 done: {len(errs)} errors; retrying once')
    errs2 = run([t for t, _ in errs], 'retry')
    json.dump([{'doi': t['doi'], 'error': e} for t, e in errs2], open('lookup_errors.json', 'w'), indent=1)
    log(f'lookup done: {len(errs2)} DOIs still failing after one retry (lookup_errors.json)')

# ---------- plan ----------
PMC = re.compile(r'(PMC\d+)')
def candidates(j):
    locs = [l for l in (j.get('oa_locations') or []) if l]
    best = j.get('best_oa_location') or {}
    order = sorted(locs, key=lambda l: (l.get('host_type') != 'publisher', l.get('url_for_pdf') != best.get('url_for_pdf')))
    out, seen = [], set()
    for l in order:
        u = l.get('url_for_pdf')
        if u and u not in seen:
            seen.add(u); out.append({'url': u, 'host_type': l.get('host_type'), 'version': l.get('version'), 'license': l.get('license')})
    pmcs = {m for l in locs for m in PMC.findall(json.dumps(l))}
    for pmc in sorted(pmcs):
        u = f'https://europepmc.org/articles/{pmc}/pdf/render'
        if u not in seen: seen.add(u); out.append({'url': u, 'host_type': 'repository', 'version': 'europepmc', 'license': None})
    return out

def cmd_plan(a):
    T = {json.loads(l)['doi']: json.loads(l) for l in open('targets.jsonl')}
    shards = [open('shard_0.jsonl', 'w'), open('shard_1.jsonl', 'w')]; n = collections.Counter()
    with open('plan.jsonl', 'w') as f:
        for doi, t in T.items():
            p = f'unpaywall/{safe(doi)}.json'
            if not os.path.exists(p): n['no_lookup'] += 1; continue
            j = json.load(open(p))
            if not j.get('is_oa'): n['closed'] += 1; continue
            c = candidates(j); rec = {**t, 'candidates': c}
            f.write(json.dumps(rec) + '\n'); n['oa_with_url' if c else 'oa_no_url'] += 1
            shards[int(hashlib.sha256(doi.encode()).hexdigest(), 16) % 2].write(json.dumps(rec) + '\n')
    for s in shards: s.close()
    log(f'plan: {dict(n)}; shard_0 {sum(1 for _ in open("shard_0.jsonl"))}, shard_1 {sum(1 for _ in open("shard_1.jsonl"))}')

# ---------- download ----------
norm = lambda s: re.sub(r'[^a-z0-9]', '', (s or '').lower())
def title_on_page(text, title, doi):
    t, x = norm(title), norm(text)
    if norm(doi) and norm(doi) in x: return True
    if len(t) < 20: return t and t in x
    return any(t[i:i + 30] in x for i in range(0, max(1, len(t) - 30), 10))

def try_url(pol, rec, c, tmp):
    url = c['url']
    if not pol.allowed(url): return 'robots_disallowed', {}
    try:
        r = pol.get(url, stream=True, timeout=90)
    except Exception as e:
        return 'http_error', {'error': repr(e)[:150]}
    if r.status_code != 200: r.close(); return 'http_error', {'http': r.status_code}
    h = hashlib.sha256(); size = 0; first = b''
    with open(tmp, 'wb') as f:
        for chunk in r.iter_content(65536):
            if not first: first = chunk[:8]
            f.write(chunk); h.update(chunk); size += len(chunk)
            if size > 300 * 2 ** 20: break
    r.close()
    if not first.startswith(b'%PDF'): return 'not_pdf', {'content_type': r.headers.get('content-type'), 'bytes': size}
    try:
        info = subprocess.run(['pdfinfo', tmp], capture_output=True, text=True, timeout=60).stdout
        pages = int(re.search(r'Pages:\s+(\d+)', info).group(1))
    except Exception: return 'not_pdf', {'error': 'pdfinfo failed', 'bytes': size}
    if pages <= 3: return 'not_pdf', {'pages': pages, 'bytes': size}
    text = subprocess.run(['pdftotext', '-l', '1', tmp, '-'], capture_output=True, text=True, timeout=60).stdout
    if not title_on_page(text, rec['title'], rec['doi']): return 'title_mismatch', {'pages': pages, 'bytes': size}
    return 'ok', {'sha256': h.hexdigest(), 'bytes': size, 'pages': pages}

def cmd_download(a):
    pol = Polite(); os.makedirs('status', exist_ok=True)
    recs = [json.loads(l) for l in open(f'shard_{a.shard}.jsonl')]
    todo = [r for r in recs if not os.path.exists(f"status/{safe(r['doi'])}.json")]
    log(f'download shard {a.shard}: {len(recs)} papers, {len(todo)} to do, {a.workers} workers')
    done = collections.Counter(); lock = threading.Lock()
    def one(rec):
        attempts, final = [], {'download_status': 'no_url'}
        os.makedirs(f"pdfs/{rec['journal']}", exist_ok=True)
        tmp = f"pdfs/{rec['journal']}/.{safe(rec['doi'])}.part"
        for c in rec['candidates']:
            st, info = try_url(pol, rec, c, tmp)
            attempts.append({'url': c['url'], 'status': st, **info})
            if st == 'ok':
                os.replace(tmp, f"pdfs/{rec['journal']}/{safe(rec['doi'])}.pdf")
                final = {'download_status': 'ok', 'url_used': c['url'], 'host_type': c['host_type'], 'version': c['version'], **info}
                break
            final = {'download_status': st}
        if os.path.exists(tmp): os.remove(tmp)
        json.dump({'doi': rec['doi'], **final, 'attempts': attempts}, open(f"status/{safe(rec['doi'])}.json", 'w'))
        with lock:
            done[final['download_status']] += 1
            if sum(done.values()) % 200 == 0: print(time.strftime('%H:%M:%S'), dict(done), flush=True)
    with ThreadPoolExecutor(a.workers) as ex: list(ex.map(one, todo))
    log(f'download shard {a.shard} done: {dict(done)}')

# ---------- manifest + report ----------
PUB = [('Elsevier', ('10.1016/',)), ('Wiley', ('10.1002/', '10.1111/')), ('ACS', ('10.1021/',)),
       ('Springer Nature', ('10.1007/', '10.1038/', '10.1186/'))]
def publisher(doi):
    return next((n for n, ps in PUB if doi.lower().startswith(ps)), 'other')

def load_all():
    T = [json.loads(l) for l in open('targets.jsonl')]; rows = []
    for t in T:
        p = f"unpaywall/{safe(t['doi'])}.json"; j = json.load(open(p)) if os.path.exists(p) else {}
        s = f"status/{safe(t['doi'])}.json"; st = json.load(open(s)) if os.path.exists(s) else {}
        best = j.get('best_oa_location') or {}
        rows.append({'doi': t['doi'], 'journal': t['journal'], 'year': t['year'], 'title': t['title'],
                     'is_oa': bool(j.get('is_oa')), 'oa_status': j.get('oa_status') or ('lookup_error' if not j else ''),
                     'license': (best.get('license') or ''), 'host_type': st.get('host_type', ''), 'version': st.get('version', ''),
                     'url_used': st.get('url_used', ''),
                     'download_status': st.get('download_status', '' if not j.get('is_oa') else 'not_attempted'),
                     'sha256': st.get('sha256', ''), 'bytes': st.get('bytes', ''), 'pages': st.get('pages', ''),
                     'attempts': st.get('attempts', [])})
    return rows

def cmd_manifest(a):
    rows = load_all(); cols = ['doi', 'journal', 'year', 'is_oa', 'oa_status', 'license', 'host_type', 'version', 'url_used',
                               'download_status', 'sha256', 'bytes', 'pages']
    with open('oa_manifest.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, cols, extrasaction='ignore'); w.writeheader(); w.writerows(rows)
    with open('oa_failed.csv', 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['doi', 'journal', 'year', 'oa_status', 'failure', 'urls_tried', 'landing_pages'])
        for r in rows:
            if r['is_oa'] and r['download_status'] != 'ok':
                j = json.load(open(f"unpaywall/{safe(r['doi'])}.json"))
                landing = sorted({l.get('url_for_landing_page') or l.get('url') for l in (j.get('oa_locations') or []) if l} - {None})
                w.writerow([r['doi'], r['journal'], r['year'], r['oa_status'], r['download_status'],
                            ' | '.join(f"{x['url']} [{x['status']}{' ' + str(x.get('http')) if x.get('http') else ''}]" for x in r['attempts']),
                            ' | '.join(landing)])
    with open('closed_for_library.csv', 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['publisher', 'doi', 'journal', 'year', 'title'])
        for r in sorted((r for r in rows if not r['is_oa']), key=lambda r: (publisher(r['doi']), r['journal'], str(r['year']))):
            w.writerow([publisher(r['doi']), r['doi'], r['journal'], r['year'], r['title']])
    c = collections.Counter(r['download_status'] for r in rows if r['is_oa'])
    log(f"manifest: {len(rows)} rows; open access {sum(r['is_oa'] for r in rows)}; download {dict(c)}; "
        f"closed {sum(not r['is_oa'] for r in rows)}")

def cmd_report(a):
    rows = load_all(); n = len(rows); oa = [r for r in rows if r['is_oa']]
    lic = lambda l: 'CC BY' if l in ('cc-by',) else ('CC BY-NC / ND / SA' if l.startswith('cc-') else ('public domain' if l in ('pd', 'cc0') else 'no licence / other'))
    def table(key, title):
        g = collections.defaultdict(lambda: collections.Counter())
        for r in rows:
            k = key(r); g[k]['papers'] += 1; g[k]['oa'] += r['is_oa']; g[k]['downloaded'] += r['download_status'] == 'ok'
            g[k]['failed'] += r['is_oa'] and r['download_status'] != 'ok'
        out = [f'### By {title}\n', f'| {title} | papers | open access | % OA | downloaded | failed |', '|---|---|---|---|---|---|']
        for k in sorted(g, key=str):
            v = g[k]; out.append(f"| {k} | {v['papers']} | {v['oa']} | {100 * v['oa'] / v['papers']:.0f}% | {v['downloaded']} | {v['failed']} |")
        return '\n'.join(out) + '\n'
    st = collections.Counter(r['oa_status'] for r in rows); dl = collections.Counter(r['download_status'] for r in oa)
    lc = collections.Counter(lic(r['license']) for r in oa); lcd = collections.Counter(lic(r['license']) for r in oa if r['download_status'] == 'ok')
    disk = subprocess.run(['du', '-sh', 'pdfs'], capture_output=True, text=True).stdout.split()[0] if os.path.exists('pdfs') else '0'
    ok = sum(r['download_status'] == 'ok' for r in rows)
    md = [f'# Open-access harvest report ({time.strftime("%Y-%m-%d")})\n',
          f'Pool: {n} papers (SEM + multimodal MatMech pool). Source: Unpaywall (email {EMAIL}), Europe PMC.\n',
          f'## Summary\n', f'- open access: **{len(oa)} ({100 * len(oa) / n:.1f}%)**; closed: {n - len(oa)}',
          f'- OA status: ' + ', '.join(f'{k} {v}' for k, v in st.most_common()),
          f'- downloaded and validated: **{ok}**; download status of OA papers: ' + ', '.join(f'{k} {v}' for k, v in dl.most_common()),
          f'- disk used by this host\'s PDFs: {disk}',
          f'- sample estimate (249 papers): about 3,800 open access (23%) after year adjustment; exact: {len(oa)} ({100 * len(oa) / n:.1f}%)\n',
          '## Licences (open-access papers)\n', '| licence | open access | downloaded |', '|---|---|---|']
    md += [f'| {k} | {v} | {lcd[k]} |' for k, v in lc.most_common()] + ['']
    md += [table(lambda r: r['journal'], 'journal'), table(lambda r: r['year'], 'year')]
    open('REPORT.md', 'w').write('\n'.join(md)); log(f'report written: OA {len(oa)}/{n}, downloaded {ok}')

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('--shard', type=int, default=0)
    ap.add_argument('--workers', type=int, default=8); a = ap.parse_args()
    {'targets': cmd_targets, 'calibrate': cmd_calibrate, 'lookup': cmd_lookup, 'plan': cmd_plan,
     'download': cmd_download, 'manifest': cmd_manifest, 'report': cmd_report}[a.cmd](a)
