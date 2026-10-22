"""V10-4 S-plan and S-plan2 runs (v7's run_splan with the v10 changes): one splan10.py process per (world, k), CONC at a time, each its
own client process (python -I), V6_PROCS planner workers each. Before the batch: splan10.py and the family's graph spec hash-checked
against FREEZE.md row 'V10-4 scripts', and the V10-X10 table check on every server URL. Skips (world, k) already done in OUT.
  python P/run_splan10.py VARIANT FAMILY URLS(comma) SSH CODE STATE WORLDS(comma) KS(comma) BATCH OUT.jsonl CONC [PROCS]
(VARIANT: S-plan | S-plan2; SSH CODE STATE: where admin mints the token, as splan10.py)"""
import hashlib, json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); V10 = os.path.dirname(HERE); sys.path.insert(0, V10); sys.path.insert(0, HERE)
import tablecheck10
import splan10


def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def main():
    variant, fam, urls, ssh, code, state, worlds, ks, batch, out, conc = sys.argv[1:12]
    procs = sys.argv[12] if len(sys.argv) > 12 else '3'
    urls = urls.split(',')
    files = {'splan10.py': os.path.join(HERE, 'splan10.py'), splan10.GRAPH[fam][0]: os.path.join(V10, 'spec', splan10.GRAPH[fam][0])}
    hs = {f: sha(p) for f, p in files.items()}
    rows = [l for l in open(os.path.join(V10, 'FREEZE.md')) if l.startswith('| V10-4 scripts |')]
    miss = [f for f, h in hs.items() if not rows or f'{f} {h}' not in rows[-1]]
    if miss: raise SystemExit(f'not in FREEZE V10-4 scripts: {miss} {hs}')
    tablecheck10.require(f'{variant} {fam} {batch} -> {out}', urls)
    jobs = [(int(w), int(k)) for k in ks.split(',') for w in worlds.split(',')]
    done = set()
    if os.path.exists(out):
        for l in open(out):
            r = json.loads(l)
            if 'verdict' in r: done.add((r['world'], r['k']))
    jobs = [j for j in jobs if j not in done]

    def one(i_job):
        i, (w, k) = i_job; t0 = time.time()
        env = dict(os.environ, V6_PROCS=procs, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
        try:
            p = subprocess.run([sys.executable, '-I', os.path.join(HERE, 'splan10.py'), variant, fam, urls[i % len(urls)], ssh, code, state, str(w), str(k),
                                batch], capture_output=True, text=True, timeout=7200, env=env)
            rc, so, se = p.returncode, p.stdout, p.stderr
        except subprocess.TimeoutExpired: rc, so, se = -9, '', 'timeout 7200 s'
        rec = dict(variant=variant, world=w, k=k, rc=rc, sec=round(time.time() - t0, 1), hashes=hs)
        try: rec.update(json.loads(so.strip().splitlines()[-1]))
        except Exception: rec['error'] = (se or '')[-800:]
        return rec

    print(len(jobs), 'to run', flush=True)
    with ThreadPoolExecutor(int(conc)) as ex:
        for rec in ex.map(one, enumerate(jobs)):
            with open(out, 'a') as f: f.write(json.dumps(rec) + '\n')
    print('done', flush=True)


if __name__ == '__main__':
    main()
