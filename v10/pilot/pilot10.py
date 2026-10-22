"""V10-1 pilot driver (truth-only, tuning split). Stages, in the prompt's order (steps 1, 2, 3, 4, 3, 4, then 5; T and the controls):
  s0  R and H tuning units, kappa unset: N_rec without R5, N_plan with X-ray candidates only, N0       -> kappa1 (step 3)
  s1  the same units at kappa1: N_rec with R5, N_plan with the neutron among the candidates, N0        -> kappa2 (step 3 again)
  s2  the same units at kappa2 (step 4 again) and step 5: the plan check at N0, qualification, recipe D at the final N; kappa2 is final
  s3  T units (the R tuning units that qualify for R) at kappa2 with T's budget (120 min per sample): steps 1, 2, 4, 5;
      v7 bars (N_q, 0.7 N_q, identification cost) on every R and H tuning unit at kappa2 (pilot controls; T controls take R's bars)
  s4  T pilot controls: T candidates that fail T qualification and pass the R unit's v7 bars, recipe D at N = 0.7 N_q
Kappa (step 3): the median over worlds of the R and H tuning units at N0 of D(neutron alone, kappa 1) / D(R1); kappa = 1 / median, rounded
to the nearest of {0.02, 0.05, 0.1, 0.2, 0.5, 1} on a log scale. Jobs run on host A (local) and host B (~/v10work), each job its own
process (runjobs.py); from s3 on also node A2 (amendment 2); results come back by rsync without delete.
  python pilot10.py all          (or: python pilot10.py s0 | s1 | ...)"""
import json, math, os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import frames10 as FR

RUN = os.path.join(HERE, 'run')
HOSTB = 'aid1@130.199.95.15'; REMOTE = 'v10work/pilot'
CONC = {'hostA': int(os.environ.get('V10_CONC_A', '10')), 'hostB': int(os.environ.get('V10_CONC_B', '18')),
        'nodeA2': int(os.environ.get('V10_CONC_A2', '9'))}
SHARE_B = 0.62
# V10-1a amendment 2 (orchestration only): node A2 (host A's node 2, the same machine type and Python stack; an s0 job reproduces
# host A's output exactly but for wall time) runs jobs of stages written after the amendment (s3, s4). Jobs already written keep
# their host. Each remote: name -> ssh target; the same REMOTE folder layout.
REMOTES = {'hostB': HOSTB, 'nodeA2': '192.168.100.11'}
WEIGHTS = {'hostA': CONC['hostA'], 'hostB': CONC['hostB'], 'nodeA2': CONC['nodeA2']}
KAPPA_SET = (0.02, 0.05, 0.1, 0.2, 0.5, 1.0)
SSH = ['ssh', '-o', 'LogLevel=ERROR', '-o', 'ConnectTimeout=20', '-n', HOSTB]


def ssh_to(target): return ['ssh', '-o', 'LogLevel=ERROR', '-o', 'ConnectTimeout=20', '-n', target]


def log(*a):
    with open(os.path.join(RUN, 'pilot10.log'), 'a') as f: f.write(time.strftime('%Y-%m-%dT%H:%M:%SZ ', time.gmtime()) + ' '.join(map(str, a)) + '\n')


def sh(cmd, **kw): return subprocess.run(cmd, capture_output=True, text=True, **kw)


def write_jobs(stage, jobs):
    d = os.path.join(RUN, stage, 'jobs'); os.makedirs(d, exist_ok=True)
    # heaviest first, alternating hosts by share (3-polymorph units cost about twice 2-polymorph ones)
    jobs = sorted(jobs, key=lambda J: -len(J['unit']['poly_ids']))
    n = {h: 0 for h in WEIGHTS}
    for J in jobs:                                              # heaviest first to the host least loaded for its slot count
        J['host'] = min(WEIGHTS, key=lambda h: ((n[h] + 1) / WEIGHTS[h], h)); n[J['host']] += 1
        name = J['unit']['id'].replace('|', '_').replace('(', '').replace(')', '') + f"__{J['mode']}.json"
        p = os.path.join(d, name)
        if not os.path.exists(p): json.dump(J, open(p, 'w'), indent=1)
    return d


def _alive(pid):
    try: os.kill(pid, 0); return True
    except OSError: return False


class _Adopted:
    def __init__(self, pid): self.pid = pid
    def poll(self): return None if _alive(self.pid) else 0


def run_stage(stage):
    d = os.path.join(RUN, stage)
    for h, tgt in REMOTES.items():
        S = ssh_to(tgt)
        sh(['rsync', '-a', '-e', 'ssh -o LogLevel=ERROR', os.path.join(HERE, '') , f'{tgt}:{REMOTE}/', '--exclude', 'run'])
        sh(S + [f'mkdir -p {REMOTE}/run/{stage}'])
        # the remote's own runner files stay its own (host A's copies lag by up to a minute and must not overwrite them)
        sh(['rsync', '-a', '-e', 'ssh -o LogLevel=ERROR', '--exclude', 'runjobs_*', d + '/', f'{tgt}:{REMOTE}/run/{stage}/'])
        if 'RUNNING' not in sh(S + [f'test -f {REMOTE}/run/{stage}/runjobs_{h}.pid && kill -0 $(cat {REMOTE}/run/{stage}/runjobs_{h}.pid) && echo RUNNING']).stdout:
            # not waited on: the ssh session stays open while the remote runner lives, so waiting would hold host A back
            subprocess.Popen(S + [f'cd {REMOTE} && setsid nohup ~/v5env/bin/python runjobs.py run/{stage} {h} {CONC[h]} > run/{stage}/runjobs_{h}.out 2>&1 < /dev/null &'],
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    pid_a = os.path.join(d, 'runjobs_hostA.pid')
    if os.path.exists(pid_a) and _alive(int(open(pid_a).read())):
        pa = _Adopted(int(open(pid_a).read()))                  # a runner of this stage is still alive (orchestrator restart): adopt it
    else:
        pa = subprocess.Popen([sys.executable, os.path.join(HERE, 'runjobs.py'), d, 'hostA', str(CONC['hostA'])],
                              stdout=open(os.path.join(d, 'runjobs_hostA.out'), 'a'), stderr=subprocess.STDOUT, start_new_session=True)
    log(stage, 'started; host A runner pid', pa.pid)
    n_jobs = len(os.listdir(os.path.join(d, 'jobs')))
    while True:
        time.sleep(60)
        r_done = []
        for h, tgt in REMOTES.items():
            sh(['rsync', '-a', '-e', 'ssh -o LogLevel=ERROR', f'{tgt}:{REMOTE}/run/{stage}/out/', os.path.join(d, 'out', '')])
            sh(['rsync', '-a', '-e', 'ssh -o LogLevel=ERROR', f'{tgt}:{REMOTE}/run/{stage}/runjobs_{h}.log', d + '/'])
            lg = os.path.join(d, f'runjobs_{h}.log')
            r_done.append(os.path.exists(lg) and open(lg).read().rstrip().split('\n')[-1].startswith('done '))   # the last line, not a stale one
        done = [f for f in os.listdir(os.path.join(d, 'out')) if f.endswith('.json')]
        if pa.poll() is not None and all(r_done): break
    log(stage, 'finished', len(done), 'of', n_jobs, 'jobs have output')
    return {f: json.load(open(os.path.join(d, 'out', f))) for f in done}


def kappa_from(results, key='ratio_at_N0'):
    rs = sorted(v['ratio'] for o in results.values() if o.get(key) for v in o[key].values() if v.get('ratio'))
    if not rs: return None, None
    med = rs[len(rs) // 2] if len(rs) % 2 else 0.5 * (rs[len(rs) // 2 - 1] + rs[len(rs) // 2])
    k = 1.0 / med
    return min(KAPPA_SET, key=lambda x: abs(math.log(x / k))), dict(median_ratio_k1=med, kappa_continuous=k, n_worlds=len(rs),
                                                                    deciles=[rs[int(q * (len(rs) - 1))] for q in (0.1, 0.5, 0.9)])


def units():
    R, H, F = FR.tuning_units(); return R, H


def stage_round(stage, kappa, final=False, fam=('R', 'H')):
    R, H = units()
    us = (R if 'R' in fam else []) + (H if 'H' in fam else [])
    write_jobs(stage, [dict(unit=u, mode='round', kappa=kappa, final=final) for u in us])
    return run_stage(stage)


def main(which):
    os.makedirs(RUN, exist_ok=True)
    st = json.load(open(os.path.join(RUN, 'state.json'))) if os.path.exists(os.path.join(RUN, 'state.json')) else {}
    save = lambda: json.dump(st, open(os.path.join(RUN, 'state.json'), 'w'), indent=1)
    if which in ('all', 's0') and 'kappa1' not in st:
        r = stage_round('s0', None); k, info = kappa_from(r); st.update(kappa1=k, kappa1_info=info); save(); log('kappa1', k, info)
    if which in ('all', 's1') and 'kappa2' not in st:
        r = stage_round('s1', st['kappa1']); k, info = kappa_from(r); st.update(kappa2=k, kappa2_info=info); save(); log('kappa2', k, info)
    if which in ('all', 's2') and 's2_done' not in st:
        r = stage_round('s2', st['kappa2'], final=True)
        k, info = kappa_from(r, 'ratio_at_final'); st.update(s2_done=True, final_ratio_info=info, kappa_final=st['kappa2']); save()
        log('final ratio', info)
        lo, hi = 0.5, 2.0; med = st['kappa2'] * info['median_ratio_k1']
        st['final_median_ratio'] = med; save()
        if not lo <= med <= hi: log('STOP for David: final median ratio', med, 'outside 0.5-2'); return
    if which in ('all', 's3') and 's3_done' not in st:
        R, H = units(); kap = st['kappa2']
        s2 = {o['unit']: o for o in _outs('s2')}
        qR = [u for u in R if s2.get(u['id'], {}).get('qualifies')]
        jobs = [dict(unit=FR.unit_T(u), mode='round', kappa=kap, final=True) for u in qR]
        jobs += [dict(unit=u, mode='v7bars', kappa=kap) for u in R + H]
        write_jobs('s3', jobs); run_stage('s3'); st['s3_done'] = True; save()
    if which in ('all', 's4') and 's4_done' not in st:
        kap = st['kappa2']; o3 = _outs('s3')
        tq = {o['unit']: o for o in o3 if o['mode'] == 'round'}; bars = {o['unit']: o for o in o3 if o['mode'] == 'v7bars'}
        R, H = units(); jobs = []
        for u in R:
            t = FR.unit_T(u)
            if t['id'] in tq and not tq[t['id']].get('qualifies') and bars.get(u['id'], {}).get('v7', {}).get('passes'):
                jobs.append(dict(unit=t, mode='recipes_at', kappa=kap, N=bars[u['id']]['v7']['N']))
        if jobs: write_jobs('s4', jobs); run_stage('s4')
        st['s4_done'] = True; save()
    log('pilot stages done for', which)


def _outs(stage):
    d = os.path.join(RUN, stage, 'out')
    return [json.load(open(os.path.join(d, f))) for f in sorted(os.listdir(d)) if f.endswith('.json')] if os.path.isdir(d) else []


if __name__ == '__main__':
    open(os.path.join(RUN, 'pilot10.pid'), 'w').write(str(os.getpid())) if os.path.isdir(RUN) else None
    main(sys.argv[1])
