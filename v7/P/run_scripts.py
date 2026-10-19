"""V7-P3 driver: run one fixed-script episode per plan token, each as its own client process (python -I core.py POLICY URL TOKEN from
the clean folder), CONC at a time; skips tokens whose episode has already answered; one JSON line per episode in OUT.
  python run_scripts.py PLAN.jsonl POLICY URL OUT.jsonl CONC"""
import json, subprocess, sys, time, urllib.request, uuid, os
from concurrent.futures import ThreadPoolExecutor
plan, policy, url, out, conc = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5])
HERE = os.path.dirname(os.path.abspath(__file__))


def answered(tok):
    b = json.dumps(dict(token=tok, tool='status', args={}, rid=uuid.uuid4().hex)).encode()
    r = json.loads(urllib.request.urlopen(urllib.request.Request(url, data=b, headers={'Content-Type': 'application/json'}), timeout=120).read())
    return bool(r.get('ok') and r['result'].get('answered'))


def one(ep):
    tok = ep['token']
    if answered(tok): return dict(token=tok[:12], skipped='already answered')
    t0 = time.time()
    p = subprocess.run([sys.executable, '-I', os.path.join(HERE, 'core.py'), policy, url, tok], capture_output=True, text=True, timeout=7200)
    rec = dict(token=tok[:12], scen=ep['scen'], k=ep['k'], rc=p.returncode, sec=round(time.time() - t0, 1), cpu_note='client process wall time')
    try: rec.update(json.loads(p.stdout.strip().splitlines()[-1]))
    except Exception: rec['error'] = (p.stderr or '')[-400:]
    return rec


eps = [json.loads(l) for l in open(plan) if l.strip()]
with ThreadPoolExecutor(conc) as ex:
    for rec in ex.map(one, eps):
        with open(out, 'a') as f: f.write(json.dumps(rec) + '\n')
print('done', len(eps), flush=True)
