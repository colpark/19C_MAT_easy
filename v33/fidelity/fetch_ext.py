#!/usr/bin/env python3
"""fetch_ext.py: Source Data xlsx and full-size figure PNGs of Nature-family articles into v32_host/fidelity/ext/<id>/ (host only, never git).
usage: fetch_ext.py <article-id> ..."""
import sys as _pb_s, os as _pb_o
_pb_d = _pb_o.path.dirname(_pb_o.path.abspath(__file__))
while not _pb_o.path.exists(_pb_o.path.join(_pb_d, 'pbroot.py')) and _pb_o.path.dirname(_pb_d) != _pb_d: _pb_d = _pb_o.path.dirname(_pb_d)
_pb_s.path.insert(0, _pb_d)
from pbroot import ROOT, HOST
import os, re, sys, urllib.request
EXT = f'{HOST}/fidelity/ext'; PAGES = f'{HOST}/fidelity/search/pages'
def get(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0: return True
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=600)
        if r.status != 200: return False
        open(path, 'wb').write(r.read()); return True
    except Exception: return False
for aid in sys.argv[1:]:
    d = f'{EXT}/{aid}'; os.makedirs(d, exist_ok=True); page = f'{PAGES}/{aid}.html'
    if not os.path.exists(page): get(f'https://www.nature.com/articles/{aid}', page)
    html = open(page).read()
    for u in sorted(set(re.findall(r'https://media\.springernature\.com/original/springer-static/esm/[^"]*\.xlsx', html))): get(u, f'{d}/{os.path.basename(u)}')
    j = aid[1:6]; n = aid.split('-')[2].lstrip('0'); pre = f"{j}_20{aid.split('-')[1][1:]}_{n}"
    for k in range(1, 13):
        fn = f'{pre}_Fig{k}_HTML.png'
        if not get(f'https://media.springernature.com/full/springer-static/image/art%3A10.1038%2F{aid}/MediaObjects/{fn}', f'{d}/{fn}'): break
    print(aid, sorted(os.listdir(d)))
