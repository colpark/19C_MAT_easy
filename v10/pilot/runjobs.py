"""Run every job JSON in DIR/jobs that has no DIR/out/<name> yet, each as its own process (qual10.py), CONC at a time. Writes its PID to
DIR/runjobs_<host>.pid and a log line per job to DIR/runjobs_<host>.log. Jobs of other hosts are skipped by the host field.
  python runjobs.py DIR HOST CONC"""
import json, os, socket, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
D, HOST, CONC = sys.argv[1], sys.argv[2], int(sys.argv[3])
open(os.path.join(D, f'runjobs_{HOST}.pid'), 'w').write(str(os.getpid()))
os.makedirs(os.path.join(D, 'out'), exist_ok=True)
jobs = sorted(f for f in os.listdir(os.path.join(D, 'jobs')) if f.endswith('.json'))
todo = []
for f in jobs:
    J = json.load(open(os.path.join(D, 'jobs', f)))
    if J.get('host') not in (None, HOST): continue
    if os.path.exists(os.path.join(D, 'out', f)): continue
    todo.append(f)


def one(f):
    t0 = time.time(); err = os.path.join(D, 'out', f + '.err')
    env = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', V10_PROCS='2')
    with open(err, 'w') as e:
        rc = subprocess.run([sys.executable, os.path.join(HERE, 'qual10.py'), os.path.join(D, 'jobs', f), os.path.join(D, 'out', f + '.tmp')],
                            stdout=e, stderr=subprocess.STDOUT, env=env).returncode
    if rc == 0: os.replace(os.path.join(D, 'out', f + '.tmp'), os.path.join(D, 'out', f)); os.remove(err)
    with open(os.path.join(D, f'runjobs_{HOST}.log'), 'a') as L:
        L.write(f'{time.strftime("%Y-%m-%dT%H:%M:%S")} {f} rc={rc} {round(time.time() - t0)}s\n')
    return rc


with ThreadPoolExecutor(CONC) as ex: rcs = list(ex.map(one, todo))
with open(os.path.join(D, f'runjobs_{HOST}.log'), 'a') as L: L.write(f'done {len(todo)} jobs, {sum(r != 0 for r in rcs)} failed\n')
