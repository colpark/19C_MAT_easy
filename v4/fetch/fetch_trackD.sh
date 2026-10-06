#!/bin/bash
# v4 Track D: download the rank-1 Hall-Petch deposits (CC BY 4.0) into v4_host/trackD/<alloy>/ (each in its own directory; never executed)
set -u; D=/home/aid1/Documents/harbor/v4_host/trackD
curl -sL -m 3600 -o $D/crconi/crconi_sciebo.zip "https://ruhr-uni-bochum.sciebo.de/s/kyYFnQ1UonJc7Wx/download"; echo "crconi rc=$? $(stat -c %s $D/crconi/crconi_sciebo.zip)"
curl -sL -m 3600 -o $D/mnfeni/mnfeni_sciebo.zip "https://ruhr-uni-bochum.sciebo.de/s/dkr1YdHihA4rTJL/download"; echo "mnfeni rc=$? $(stat -c %s $D/mnfeni/mnfeni_sciebo.zip)"
python3 - <<'PY'
import json, urllib.request, os
D = '/home/aid1/Documents/harbor/v4_host/trackD/crfeni'
def get(u): return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'panelbench-v4'}), timeout=120))
def walk(folder=None, prefix=''):
    q = f'https://data.mendeley.com/public-api/datasets/7d826s3mhf/files?version=1' + (f'&folder_id={folder}' if folder else '')
    for f in get(q):
        url = f.get('content_details', {}).get('download_url'); name = f.get('filename')
        if url:
            p = os.path.join(D, prefix, name); os.makedirs(os.path.dirname(p), exist_ok=True)
            urllib.request.urlretrieve(url, p); print('got', prefix + name, os.path.getsize(p), flush=True)
    for fo in get(f'https://data.mendeley.com/public-api/datasets/7d826s3mhf/folders/1') if folder is None else []:
        walk(fo['id'], fo['name'] + '/')
walk()
PY
sha256sum $D/*/*.zip > $D/sha256.txt 2>/dev/null; echo DONE
