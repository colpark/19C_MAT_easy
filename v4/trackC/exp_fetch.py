#!/usr/bin/env python3
"""Addendum B, B2 C0.2: fetch the experimental Li-ion conductivity databases through each paper's data
availability statement, with the mc_fetch politeness rules (one request at a time, >= 2 s + jitter,
Retry-After, error bodies as .bad, html never saved as data, no login, no workaround).

Allowed targets (VC-E10, narrow extension of hard rule 3 for Addendum B, approved scope):
  OBELiX   : github.com/NRC-Mila/OBELiX (arXiv 2502.14234 'Data availability'), via the GitHub REST API
             (repo metadata incl. license) and codeload.github.com (one zip of the default branch)
  Liverpool: the open-access article doi:10.1038/s41524-022-00951-z on www.nature.com (to read its data
             availability statement), then only the host that statement names (added after reading, logged)
usage: exp_fetch.py obelix OUTDIR | exp_fetch.py liverpool-article OUTDIR | exp_fetch.py get URL OUT
"""
import json, os, sys, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mc_fetch as F

EXTRA = ('api.github.com', 'codeload.github.com', 'github.com', 'www.nature.com', 'raw.githubusercontent.com',
         'pcwww.liv.ac.uk')  # last: named by the Liverpool data availability statement (read 2026-10-07)
EXTRA_REDIRECT = ('codeload.github.com', 'raw.githubusercontent.com', 'objects.githubusercontent.com')
F.ALLOWED = F.ALLOWED + EXTRA
_orig = F._redirect_ok


def _redirect_ok(url):
    h = urllib.parse.urlparse(url).hostname or ''
    return h in EXTRA_REDIRECT or _orig(url)


F._redirect_ok = _redirect_ok
LOG = os.environ.get('FETCH_LOG', 'fetch_log.jsonl')


def obelix(out):
    os.makedirs(out, exist_ok=True)
    meta = F.get_json('https://api.github.com/repos/NRC-Mila/OBELiX', os.path.join(out, 'repo.json'), LOG)
    if not meta:
        raise SystemExit('no repo metadata')
    print('license:', meta.get('license'), 'default_branch:', meta.get('default_branch'), 'size_kB:', meta.get('size'))
    F.get_json('https://api.github.com/repos/NRC-Mila/OBELiX/license', os.path.join(out, 'license.json'), LOG)
    F.get_json('https://api.github.com/repos/NRC-Mila/OBELiX/releases', os.path.join(out, 'releases.json'), LOG)
    br = meta.get('default_branch', 'main')
    c = F.get_json(f'https://api.github.com/repos/NRC-Mila/OBELiX/commits/{br}', os.path.join(out, 'head.json'), LOG)
    sha = c['sha'] if c else br
    if meta.get('size', 0) > 2_000_000:  # kB; ask before anything large
        raise SystemExit('repo larger than 2 GB: ask first')
    ok = F.download(f'https://codeload.github.com/NRC-Mila/OBELiX/zip/{sha}', os.path.join(out, f'OBELiX_{sha[:12]}.zip'),
                    LOG)
    print('zip', ok, sha)


def liverpool_article(out):
    os.makedirs(out, exist_ok=True)
    r = F.request('https://www.nature.com/articles/s41524-022-00951-z', LOG)
    p = os.path.join(out, 's41524-022-00951-z.html')
    if r.status_code != 200:
        F._bad(p, r, LOG, r.url)
        raise SystemExit(f'article status {r.status_code}')
    open(p, 'wb').write(r.content)
    F._log(LOG, {'url': r.url, 'status': 200, 'out': p, 'bytes': len(r.content)})
    print('saved', p, len(r.content))


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'obelix':
        obelix(sys.argv[2])
    elif cmd == 'liverpool-article':
        liverpool_article(sys.argv[2])
    elif cmd == 'get':
        sys.exit(0 if F.download(sys.argv[2], sys.argv[3], LOG) else 1)


def liverpool_page(out):
    """The landing page named by the statement; html kept as page.html, csv links listed for `get`."""
    import re
    r = F.request('http://pcwww.liv.ac.uk/~msd30/lmds/LiIonDatabase.html', LOG)
    p = os.path.join(out, 'LiIonDatabase.html')
    if r.status_code != 200:
        F._bad(p, r, LOG, r.url)
        raise SystemExit(f'page status {r.status_code}')
    open(p, 'wb').write(r.content)
    F._log(LOG, {'url': r.url, 'status': 200, 'out': p, 'bytes': len(r.content)})
    links = sorted(set(re.findall(r'href="([^"]+\.(?:csv|xlsx|zip))"', r.text, re.I)))
    print('links', [urllib.parse.urljoin(r.url, l) for l in links])
    print(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', r.text))[:1500])


if __name__ == '__main__' and sys.argv[1] == 'liverpool-page':
    liverpool_page(sys.argv[2])
