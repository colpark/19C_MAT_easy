"""Shadow-D inputs for v5.2 (V5_SPEC E.6, F.7): measurement plans with the reference D, for a fresh implementation that reads only the
spec, WORLDS.json and peak_tables.json.
  python -m mcenv.shadow_plans_v52 2s OUT.json            stage 2s: per world, plans without m0 (the c_dec, c_loc, c_pla, default-survey and
                                                          T4 plans, random windows, pairs, the neutron pattern); keys use the true lattice
  python -m mcenv.shadow_plans_v52 3 GRADED3.jsonl OUT.json    stage 3: valid-only measurement lists of graded scripted episodes (the
                                                          failed measurement removed) and their grader D, about 15 per world"""
import os
for _v in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ.setdefault(_v, '1')
import json, random, sys
from multiprocessing import Pool
from . import scenarios as SC
from . import separation as SP

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _D(a):
    w, plan = a
    return SP.separation(w, [SP.meas_from(m) for m in plan]) if plan else 0.0


def plans_2s():
    from . import stage2s as ST
    ST.install(cost=False)
    C = json.load(open(os.path.join(ROOT, 'stage2s', 'validation', 'constraints.json')))['scen']
    rng = random.Random('v5-shadow-2s'); out = {}
    for s, r in C.items():
        base = []
        for k in ('c_dec', 'c_pla', 'c_loc_dec'):
            if r.get(k): base.append(r[k]['plan'])
        if r.get('c_loc'): base.append([r['c_loc']['meas']])
        base.append([SP.DEFAULT.key()])
        if r.get('T4_survey'): base.append([r['T4_survey']['best_survey']])
        base.append([SP.NEUTRON.key()])
        for _ in range(6):
            lo = round(rng.uniform(8, 140), 2); wd = rng.choice([2.0, 4.0, 6.0]); st = rng.choice([0.01, 0.02, 0.04])
            n = int(wd / st) + 1; opt = rng.choice(['standard', 'high_resolution'])
            base.append([dict(radiation='xray', start=lo, step=st, n=n, t=round(rng.uniform(0.5, 10), 3), optics=opt, si_standard=rng.random() < 0.2)])
        base.append(base[-1] + base[-2])
        for w in SC.twins(int(s)): out[str(w)] = [dict(plan=p) for p in base]
    return out


def plans_3(graded):
    from . import stage3 as F
    F.install()
    from . import server as S
    G = [json.loads(l) for l in open(graded) if l.strip()]
    by = {}
    for g in G: by.setdefault(g['world'], []).append(g)
    rng = random.Random('v5-shadow-3'); out = {}
    for w, eps in sorted(by.items()):
        eps = [e for e in eps if e['n_measurements'] >= 0]
        rng.shuffle(eps); seen = set(); rows = []
        for e in eps:
            stp = os.path.join(S.EPIS, e['token'], 'state.json')
            if not os.path.exists(stp): continue
            st = json.load(open(stp)); fi = (st.get('fault') or {}).get('index')
            plan = [r['spec'] for i, r in enumerate(st['measurements']) if i != fi]
            key = json.dumps(plan, sort_keys=True)
            if key in seen: continue
            seen.add(key); rows.append(dict(plan=plan, D_grader=e['D'], token=e['token'][:12], fault=st.get('fault') and st['fault']['type']))
            if len(rows) >= 15: break
        out[str(w)] = rows
    return out


def main():
    mode = sys.argv[1]
    if mode == '2s': out = plans_2s(); path = sys.argv[2]
    else: out = plans_3(sys.argv[2]); path = sys.argv[3]
    jobs = [(int(w), p['plan']) for w, ps in out.items() for p in ps]
    with Pool(int(os.environ.get('V5_PROCS', '16'))) as pool: ds = pool.map(_D, jobs, chunksize=1)
    i = 0
    for w, ps in out.items():
        for p in ps: p['D'] = round(float(ds[i]), 6); i += 1
    json.dump(dict(note='each plan lists every measurement D is computed on (no implicit m0); D is the reference value; stage 3 plans are '
                   'valid-only measurement lists (the failed measurement removed)', worlds=out), open(path, 'w'), indent=1)
    print(len(jobs), 'plans')


if __name__ == '__main__':
    main()
