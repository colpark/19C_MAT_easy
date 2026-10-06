#!/usr/bin/env python3
"""fetch_mendeley.py <dataset_id> <version> <out_dir>: download every file of a public Mendeley Data dataset, keeping its folder tree;
writes manifest.json (path, bytes, sha256). Folders come as a flat list with parent ids; files are listed per folder id."""
import hashlib, json, os, sys, urllib.request
ds, ver, out = sys.argv[1], sys.argv[2], sys.argv[3]; B = f'https://data.mendeley.com/public-api/datasets/{ds}'
get = lambda u: json.load(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'panelbench-v4'}), timeout=120))
folders = get(f'{B}/folders/{ver}'); byid = {f['id']: f for f in folders}
def path(fid):
    p = []
    while fid in byid: p.append(byid[fid]['name']); fid = byid[fid].get('parent_id')
    return '/'.join(reversed(p))
man = {}
for fid in [None] + list(byid):
    q = f'{B}/files?version={ver}' + (f'&folder_id={fid}' if fid else '&folder_id=root')
    for f in get(q):
        if not isinstance(f, dict): continue
        url = (f.get('content_details') or {}).get('download_url'); name = f.get('filename')
        if not url: continue
        rel = os.path.join(path(fid) if fid else '', name); p = os.path.join(out, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
        data = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (panelbench-v4)'}), timeout=600).read(); open(p, 'wb').write(data)
        man[rel] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}; print('got', rel, len(data), flush=True)
json.dump(man, open(os.path.join(out, 'manifest.json'), 'w'), indent=1); print('DONE', len(man), 'files')
