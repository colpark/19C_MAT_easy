#!/usr/bin/env python3
"""fetch_crossref.py: citation metadata for the 100 v0.24 papers from api.crossref.org (anonymous, 1 req/s) -> citations_crossref.json."""
import json, time, urllib.parse, urllib.request
P = json.load(open('papers_v024.json')); out = {}
for p in P:
    try:
        j = json.loads(urllib.request.urlopen(urllib.request.Request('https://api.crossref.org/works/' + urllib.parse.quote(p['doi']), headers={'User-Agent': 'PanelBench/0.24'}), timeout=30).read())['message']
        a = j.get('author') or [{}]
        out[p['key']] = {'doi': p['doi'], 'first_author': a[0].get('family', a[0].get('name', '?')), 'n_authors': len(j.get('author') or []),
                         'journal': (j.get('container-title') or ['?'])[0], 'year': ((j.get('published') or j.get('issued'))['date-parts'][0][0]), 'title': (j.get('title') or ['?'])[0]}
    except Exception as e: print('fail', p['key'], p['doi'], repr(e)[:80])
    time.sleep(1)
json.dump(out, open('citations_crossref.json', 'w'), indent=1, ensure_ascii=False)
import collections; print(len(out), collections.Counter(v['journal'] for v in out.values()).most_common(12), collections.Counter(v['year'] for v in out.values()))
