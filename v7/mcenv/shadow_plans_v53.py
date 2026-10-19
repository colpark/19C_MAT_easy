"""Shadow-D inputs for v5.3 stage 4 (V5_SPEC I.13): per world, measurement plans with the reference D, for a fresh implementation that
reads only the spec, stage4/WORLDS.json and stage4/peak_tables.json. Every plan lists every measurement D is computed on (m0 explicit):
m0 alone, m0 plus each oracle plan of the scenario, m0 plus random windows (singles and one pair), m0 plus the neutron pattern, and the
same windows without m0 (blind-style lists).
  python -m mcenv.shadow_plans_v53 OUT.json"""
import os
for _v in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ.setdefault(_v, '1')
import json, random, sys
from multiprocessing import Pool
from . import scenarios as SC
from . import separation as SP
from . import stage4 as F

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F.install()


def _D(a):
    w, plan = a
    return SP.separation(w, [SP.meas_from(m) for m in plan]) if plan else 0.0


def plans():
    P = json.load(open(os.path.join(ROOT, 'stage4', 'validation', 'oracle_plans.json')))
    rng = random.Random('v5-shadow-4'); out = {}
    for s in sorted({SC.WORLD_SCEN[w] for w in F.worlds()}):
        m0 = SP.DEFAULT.key(); base = [[m0]]
        for w in SC.twins(s):
            if P.get(str(w)): base.append([m0] + P[str(w)])
        base.append([m0, SP.NEUTRON.key()])
        win = []
        for _ in range(5):
            lo = round(rng.uniform(8, 140), 2); wd = rng.choice([2.0, 4.0, 6.0]); st = rng.choice([0.01, 0.02, 0.04])
            n = int(wd / st) + 1; opt = rng.choice(['standard', 'high_resolution'])
            win.append(dict(radiation='xray', start=lo, step=st, n=n, t=round(rng.uniform(0.5, 10), 3), optics=opt, si_standard=rng.random() < 0.2))
        base += [[m0, x] for x in win] + [[m0, win[0], win[1]]] + [[x] for x in win[:3]]
        for w in SC.twins(s): out[str(w)] = [dict(plan=p) for p in base]
    return out


def main():
    out = plans(); jobs = [(int(w), p['plan']) for w, ps in out.items() for p in ps]
    with Pool(int(os.environ.get('V5_PROCS', '16'))) as pool: ds = pool.map(_D, jobs, chunksize=1)
    i = 0
    for w, ps in out.items():
        for p in ps: p['D'] = round(float(ds[i]), 6); i += 1
    json.dump(dict(note='each plan lists every measurement D is computed on (m0 explicit); D is the reference value', worlds=out),
              open(sys.argv[1], 'w'), indent=1)
    print(len(jobs), 'plans')


if __name__ == '__main__':
    main()
