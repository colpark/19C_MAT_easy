#!/usr/bin/env python3
"""screen_sd.py (v3.2 course change): screen Nature-family articles for the Source Data build set: CC BY (own licence statement, no NC/ND),
an xlsx Source Data file, sheet names that name main-text figures. Pages cached in v32_host/fidelity/search/pages. Writes fidelity/sd_screen.json.
usage: screen_sd.py <ids file> ..."""
import sys as _pb_s, os as _pb_o
_pb_d = _pb_o.path.dirname(_pb_o.path.abspath(__file__))
while not _pb_o.path.exists(_pb_o.path.join(_pb_d, 'pbroot.py')) and _pb_o.path.dirname(_pb_d) != _pb_d: _pb_d = _pb_o.path.dirname(_pb_d)
_pb_s.path.insert(0, _pb_d)
from pbroot import ROOT, HOST
import json, os, re, sys, urllib.request, html as H
PAGES = f'{HOST}/fidelity/search/pages'; OUT = f'{ROOT}/fidelity/sd_screen.json'
def get(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0: return open(path, encoding='utf-8', errors='ignore').read()
    import time; time.sleep(2)
    try: d = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=120).read(); open(path, 'wb').write(d); return d.decode('utf-8', 'ignore')
    except Exception: return ''
res = json.load(open(OUT)) if os.path.exists(OUT) else {}
for f in sys.argv[1:]:
    for aid in [l.strip() for l in open(f) if l.strip()]:
        if aid in res: continue
        t = get(f'https://www.nature.com/articles/{aid}', f'{PAGES}/{aid}.html')
        txt = ' '.join(H.unescape(re.sub('<[^>]+>', ' ', t)).split())
        m = re.search(r'This article is licensed under a Creative Commons (.{0,160})', txt); lic = m.group(1) if m else ''
        cc_by = bool(m) and 'NonCommercial' not in lic and 'NoDerivatives' not in lic and lic.startswith('Attribution 4')
        xl = sorted(set(re.findall(r'https://media\.springernature\.com/original/springer-static/esm/[^"]*\.xlsx', t)))
        title = (re.search(r'<title>([^<|]*)', t) or [None, ''])[1].strip() if t else ''
        res[aid] = {'title': title, 'cc_by': cc_by, 'licence': lic[:120], 'xlsx': xl, 'source_data_stmt': 'Source data are provided' in txt,
                    'full_text': ' Results ' in txt or ' Results and discussion ' in txt, 'n_chars': len(txt)}
        print(aid, 'CC BY' if cc_by else 'not CC BY', len(xl), 'xlsx |', title[:80])
json.dump(res, open(OUT, 'w'), indent=1)
