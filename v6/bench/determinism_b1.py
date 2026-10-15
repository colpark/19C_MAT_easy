"""B1 V6-9 determinism (as V5-2): for every bench world (both twins and the six hold worlds of each of the 30 compounds) and the episode
seed k = 1, the noisy counts of the free scan m0 and of every gold-trace measurement of the world's twin (S1a plan, and S1d's when it
ran), drawn as the server draws them (Poisson of the noise-free expected counts with the noise key of the scenario, k and the measurement
index), hashed per array (sha256 of the integer list) and over all. The same seeds must give identical hashes on every host.
  python v6/bench/determinism_b1.py OUT.json"""
import os, sys
for _v in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ.setdefault(_v, '1')
import hashlib, json, platform, socket
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..'))
from mcenv import bench6 as B6, separation as SP, scenarios as SC
from mcenv import server as S


def meas(p):
    if p.get('radiation') == 'neutron': return SP.NEUTRON
    return SP.Meas('xray', p['start'], p['step'], int(round((p['stop'] - p['start']) / p['step'])) + 1, p['time_per_step'], p.get('optics', 'standard'), p.get('si_standard', False))


def main():
    B6.install()
    W = [w for w in json.load(open(os.path.join(HERE, 'WORLDS_B1.json')))['worlds'] if w['in_bench']]
    gold = os.path.join(HERE, '..', 'runs', 'bench', 'v6_9', 'gold')
    out, allh = {}, hashlib.sha256()
    for w in W:
        s = w['scen']
        for off in range(1, 9):
            world = s * 10 + off; tw = 'A' if off in (1, 3, 4, 5) else 'B'
            g = json.load(open(os.path.join(gold, f'gold_{s}_{tw}.json'))); st = {x['node']: x for x in g['steps']}
            plan = list(st['S1a']['outputs'].get('plan') or [])
            if st.get('S1d', {}).get('status') == 'ran': plan += list(st['S1d']['outputs'].get('plan') or [])
            tr = SP.world_truth(world); hs = []
            for idx, m in enumerate([SP.DEFAULT] + [meas(p) for p in plan]):
                mu = SP.mu_truth(tr, m)
                c = S.noise_rng(SC.SCEN[s].get('seed_scen', s), 1, idx).poisson(mu).astype(int)
                h = hashlib.sha256(json.dumps([int(x) for x in c]).encode()).hexdigest()[:16]; hs.append(h); allh.update(h.encode())
            out[str(world)] = hs
    res = dict(host=socket.gethostname(), python=platform.python_version(), n_worlds=len(out), n_arrays=sum(len(v) for v in out.values()),
               overall=allh.hexdigest()[:16], arrays=out)
    json.dump(res, open(sys.argv[1], 'w'), indent=1)
    print(res['host'], res['n_worlds'], 'worlds', res['n_arrays'], 'arrays', 'overall', res['overall'])


if __name__ == '__main__':
    main()
