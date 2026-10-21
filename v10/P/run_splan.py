"""V7-P3 / V7-F2 driver for S-plan: one splan.py process per (world, k), CONC at a time, each in its own client process (python -I).
Skips (world, k) already done in OUT. Usage:
  python run_splan.py FAMILY URLS(comma) SSH CODE STATE STAGE WORLDS(comma) KS(comma) BATCH OUT.jsonl CONC [PROCS]"""
import json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
fam, urls, ssh, code, state, stage, worlds, ks, batch, out, conc = sys.argv[1:12]
procs = sys.argv[12] if len(sys.argv) > 12 else '3'
urls = urls.split(','); HERE = os.path.dirname(os.path.abspath(__file__))
jobs = [(int(w), int(k)) for k in ks.split(',') for w in worlds.split(',')]
done = set()
if os.path.exists(out):
    for l in open(out):
        r = json.loads(l)
        if 'verdict' in r: done.add((r['world'], r['k']))
jobs = [j for j in jobs if j not in done]


def one(i_job):
    i, (w, k) = i_job; t0 = time.time()
    env = dict(os.environ, V6_PROCS=procs, OPENBLAS_NUM_THREADS='1')
    p = subprocess.run([sys.executable, '-I', os.path.join(HERE, 'splan.py'), fam, urls[i % len(urls)], ssh, code, state, stage, str(w), str(k), batch],
                       capture_output=True, text=True, timeout=7200, env=env)
    rec = dict(world=w, k=k, rc=p.returncode, sec=round(time.time() - t0, 1))
    try: rec.update(json.loads(p.stdout.strip().splitlines()[-1]))
    except Exception: rec['error'] = (p.stderr or '')[-500:]
    return rec


print(len(jobs), 'to run', flush=True)
with ThreadPoolExecutor(int(conc)) as ex:
    for rec in ex.map(one, enumerate(jobs)):
        with open(out, 'a') as f: f.write(json.dumps(rec) + '\n')
print('done', flush=True)
