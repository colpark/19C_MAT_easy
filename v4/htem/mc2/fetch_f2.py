#!/usr/bin/env python3
"""fetch_f2.py (v4.5 MC v2.2, F2; approved size): cache every sample of the remaining uncached multimodal libraries
(not fully cached after F1; 218 libraries) through the kit client (throttle 0.5 s plus jitter, retries, Retry-After).
Order by library id. Stops if requests exceed 11,000 or errors exceed 2 % of libraries attempted (after 10). Writes the F2 list and a
sha256 manifest (canonical JSON of each sample record) to $HTEM_HOST/mc/f2_manifest.json; progress in $HTEM_HOST/mc/f2_progress.log."""
import hashlib, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_mc2 as CM
LIST = os.path.join(CM.API.HOST, 'mc', 'f2_list.json')
if not os.path.exists(LIST):   # frozen at first run, before any fetch
    f1 = set(json.load(open(os.path.join(CM.API.HOST, 'mc', 'f1_list.json'))))   # F1 libraries excluded (8333: API-skipped samples)
    ids = sorted((r['id'] for r in CM.ROWS if not CM.fully_cached(r['id']) and r['id'] not in f1), key=int)
    json.dump(ids, open(LIST, 'w'))
ids = json.load(open(LIST)); c = CM.API.Client(); c.t['max_requests'] = 11000
log = open(os.path.join(CM.API.HOST, 'mc', 'f2_progress.log'), 'a'); t0 = time.time(); err = 0; man = {}
log.write(f'{time.strftime("%FT%T")} RUN START {len(ids)} libraries\n'); log.flush()
for k, lid in enumerate(ids):
    try:
        skipped = []; n = len(c.samples_of(lid, skipped))
    except CM.API.HTEMError as e:
        err += 1; log.write(f'{time.strftime("%FT%T")} library {lid} error {e}\n'); log.flush()
        if 'budget' in str(e).lower() or (k + 1 >= 10 and err / (k + 1) > 0.02): log.write('STOP\n'); break
        continue
    lib = CM.C.cached('library', lid)
    man[lid] = {sid: hashlib.sha256(json.dumps(CM.C.cached('sample', sid), sort_keys=True).encode()).hexdigest() for sid in (lib or {}).get('sample_ids') or []}
    log.write(f'{time.strftime("%FT%T")} {k + 1}/{len(ids)} library {lid} samples {n} requests {c.n_requests} skipped {len(skipped)} errors {err} elapsed {time.time() - t0:.0f}s\n'); log.flush()
json.dump({'libraries': ids, 'sha256': man, 'requests': c.n_requests, 'errors': err}, open(os.path.join(CM.API.HOST, 'mc', 'f2_manifest.json'), 'w'), indent=1)
log.write(f'{time.strftime("%FT%T")} RUN END requests {c.n_requests} errors {err}\n'); log.close()
