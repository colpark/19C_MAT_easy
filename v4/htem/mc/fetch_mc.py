#!/usr/bin/env python3
"""fetch_mc.py (v4.5 MC2): cache every sample of every census-eligible multimodal library through the kit client (throttle 0.5 s plus
jitter, retries with backoff, Retry-After honoured, budget max_requests per run; one job at a time). Libraries by id; already cached samples
cost nothing. Progress: $HTEM_HOST/mc/fetch_progress.log. Rerun to continue after the per-run budget."""
import csv, json, os, sys, time
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, HERE)
import htem_api as API
c = API.Client(); rows = sorted((r for r in csv.DictReader(open(os.path.join(API.HOST, 'census', 'libraries.csv'))) if r.get('multi') == '1'), key=lambda r: int(r['id']))
log = open(os.path.join(API.HOST, 'mc', 'fetch_progress.log'), 'a'); t0 = time.time(); skipped = []
for k, r in enumerate(rows):
    try:
        n = len(c.samples_of(r['id'], skipped))
    except API.HTEMError as e:
        log.write(f'{time.strftime("%FT%T")} library {r["id"]} error {e}\n'); log.flush()
        if 'budget' in str(e).lower(): break
        continue
    log.write(f'{time.strftime("%FT%T")} {k + 1}/{len(rows)} library {r["id"]} samples {n} requests {c.n_requests} skipped {len(skipped)} elapsed {time.time() - t0:.0f}s\n'); log.flush()
json.dump(skipped, open(os.path.join(API.HOST, 'mc', f'fetch_skipped_{int(t0)}.json'), 'w'))
log.write(f'{time.strftime("%FT%T")} RUN END requests {c.n_requests}\n'); log.close()
