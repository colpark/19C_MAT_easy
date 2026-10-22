"""V10-4 script runs: one client process per plan token (python -I scripts10.py POLICY URL TOKEN) from a fresh clean folder
~/v10scripts_run/POLICY/TOKEN12 holding only scripts10.py, core.py (v7's V7-P decision core) and recipes10.py (the frozen recipe suite),
each hash-checked against FREEZE.md row 'V10-4 scripts' before the batch (with --tuning, the S-match tuning runs on the tuning split
before that row exists, the check is skipped and logged). The process gets only PATH, LANG and the BLAS caps. Before the batch, the
V10-X10 table check on every server URL of the plan (tablecheck10.require). Skips tokens already recorded in OUT or already answered.
A crash or a time-out (7200 s) is recorded with its error and counts as unanswered. One JSON line per episode in OUT.
  python P/run_scripts10.py PLAN.jsonl OUT.jsonl CONC [--tuning]        (plan lines: token, policy, url, scen, world, k, family)"""
import hashlib, json, os, shutil, subprocess, sys, time, urllib.request, uuid
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); V10 = os.path.dirname(HERE); sys.path.insert(0, V10)
import tablecheck10
FILES = {'scripts10.py': os.path.join(HERE, 'scripts10.py'), 'core.py': os.path.join(HERE, 'core.py'),
         'recipes10.py': os.path.join(V10, 'pilot', 'recipes10.py')}
ROOT = os.path.expanduser('~/v10scripts_run')
PYX = os.path.expanduser('~/v5env/bin/python')


def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def check_freeze(tuning):
    hs = {f: sha(p) for f, p in FILES.items()}
    if tuning: return hs, 'tuning run: FREEZE row V10-4 scripts not required'
    rows = [l for l in open(os.path.join(V10, 'FREEZE.md')) if l.startswith('| V10-4 scripts |')]
    if not rows: raise SystemExit('no FREEZE.md row V10-4 scripts: hash the scripts before any bench run')
    miss = [f for f, h in hs.items() if f'{f} {h}' not in rows[-1]]
    if miss: raise SystemExit(f'script hash not in FREEZE V10-4 scripts: {miss} {hs}')
    return hs, 'hashes equal FREEZE V10-4 scripts'


def answered(url, tok):
    b = json.dumps(dict(token=tok, tool='status', args={}, rid=uuid.uuid4().hex)).encode()
    r = json.loads(urllib.request.urlopen(urllib.request.Request(url, data=b, headers={'Content-Type': 'application/json'}), timeout=300).read())
    return bool(r.get('ok') and r['result'].get('answered'))


def one(ep):
    tok, pol, url = ep['token'], ep['policy'], ep['url']
    d = os.path.join(ROOT, pol, tok[:12]); os.makedirs(d, exist_ok=True)
    for f, p in FILES.items(): shutil.copy(p, os.path.join(d, f))
    env = dict(PATH=os.environ.get('PATH', '/usr/bin:/bin'), LANG='C.UTF-8', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
    t0 = time.time()
    try:
        p = subprocess.run([PYX, '-I', os.path.join(d, 'scripts10.py'), pol, url, tok], cwd=d, capture_output=True, text=True, timeout=7200, env=env)
        rc, so, se = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired: rc, so, se = -9, '', 'timeout 7200 s'
    rec = dict(token=tok[:12], policy=pol, scen=ep.get('scen'), world=ep.get('world'), k=ep.get('k'), family=ep.get('family'), rc=rc,
               sec=round(time.time() - t0, 1))
    try: rec['result'] = json.loads(so.strip().splitlines()[-1])
    except Exception: rec['error'] = (se or '')[-800:]
    return rec


def main():
    a = [x for x in sys.argv[1:] if not x.startswith('--')]; tuning = '--tuning' in sys.argv
    plan, out, conc = a[0], a[1], int(a[2])
    eps = [json.loads(l) for l in open(plan) if l.strip()]
    hs, note = check_freeze(tuning); print('scripts', hs, note, flush=True)
    tablecheck10.require(f'scripts {os.path.basename(plan)} -> {out}', sorted({e["url"] for e in eps}))
    done = {json.loads(l)['token'] for l in open(out)} if os.path.exists(out) else set()
    todo = [e for e in eps if e['token'][:12] not in done and not answered(e['url'], e['token'])]
    print(len(todo), 'to run;', len(eps) - len(todo), 'recorded or answered', flush=True)
    with ThreadPoolExecutor(conc) as ex:
        for rec in ex.map(one, todo):
            rec['script_hashes'] = hs
            with open(out, 'a') as f: f.write(json.dumps(rec) + '\n')
    print('done', len(todo), flush=True)


if __name__ == '__main__':
    main()
