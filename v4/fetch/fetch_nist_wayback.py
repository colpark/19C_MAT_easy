#!/usr/bin/env python3
"""fetch_uhcs_wayback.py (v4 Track C): the NIST MDR handle 11256/{HDL} (UHCS micrographs) no longer resolves; the archived bitstreams are
fetched from the Internet Archive (latest 200 snapshot per file, id_ raw mode), with backoff on 429. Output: v4_host/uhcsdb/nist940/<file>,
manifest.json (original URL, snapshot timestamp, bytes, sha256)."""
import hashlib, json, os, re, time, urllib.request, urllib.parse
import sys as _s; HDL = _s.argv[1] if len(_s.argv) > 1 else '940'; OUT = f'/home/aid1/Documents/harbor/v4_host/uhcsdb/nist{HDL}'; os.makedirs(OUT, exist_ok=True)
def get(url, tries=12):
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'panelbench-v4-fetch'}), timeout=600) as r: return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504): time.sleep(min(300, 20 * (k + 1))); continue
            raise
        except Exception: time.sleep(30)
    raise RuntimeError(url)
for prefix in (f'materialsdata.nist.gov/bitstream/handle/11256/{HDL}', f'materialsdata.nist.gov/handle/11256/{HDL}'):
    txt = get(f'http://web.archive.org/cdx/search/cdx?url={prefix}*&filter=statuscode:200').decode()
    rows = [l.split() for l in txt.splitlines() if l.strip()]
    latest = {}
    for r in rows:
        name = urllib.parse.urlparse(r[2]).path.split('/')[-1] or 'index.html'
        if name not in latest or r[1] > latest[name][1]: latest[name] = r
    json.dump({k: v for k, v in latest.items()}, open(f'{OUT}/cdx_{prefix.split("/")[1]}.json', 'w'), indent=1)
    print(prefix, sorted((k, v[6]) for k, v in latest.items()), flush=True)
    if 'bitstream' in prefix: files = latest
man = json.load(open(f'{OUT}/manifest.json')) if os.path.exists(f'{OUT}/manifest.json') else {}
for name, r in sorted(files.items(), key=lambda kv: int(kv[1][6]) if kv[1][6].isdigit() else 0):
    if name in man: continue
    data = get(f'http://web.archive.org/web/{r[1]}id_/{r[2]}')
    open(f'{OUT}/{name}', 'wb').write(data)
    man[name] = {'original': r[2], 'timestamp': r[1], 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    json.dump(man, open(f'{OUT}/manifest.json', 'w'), indent=1); print('got', name, len(data), flush=True); time.sleep(10)
print('DONE', flush=True)
