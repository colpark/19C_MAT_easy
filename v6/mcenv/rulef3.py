"""Stage 3 rule F and fault schedule check (V5_SPEC F.3, F.4), truth only.
  python -m mcenv.rulef3 OUT.json [--types JSON]      (--types: per-scenario type override for the change order of F.4)
For every fault world: the oracle plan of its clean twin (stage 1b oracle_plans, m0 first), the measurement that fails under the
schedule, key_valid (D over valid measurements), D_all (settings-only D over every measurement), the data key over all measurements and
rule F (X41): the data key differs from key_valid (trusting changes the verdict) or the settings-only key over
every measurement differs from key_valid (counting the fault would make it decisive: the fault spoils it). For 57 also the obvious route of C.7 (Si standard, F5). For every clean world: the data key equals the
ordinary key (sanity)."""
import os
for _v in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ.setdefault(_v, '1')
import json, sys, math
from multiprocessing import Pool
from . import stage3 as F
from . import scenarios as SC
from . import separation as SP
from . import plangrid as PG
from . import grade as G

F.install()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLANS = json.load(open(os.path.join(ROOT, 'stage1b', 'validation', 'oracle_plans.json')))


def plan_of(world):
    p = PLANS.get(str(SC.SCEN[SC.WORLD_SCEN[world]]['worlds'][world]['mirror_1b']))
    return [SP.DEFAULT] + [SP.meas_from(d) for d in (p or [])]


def obvious_57(world):
    """C.7 obvious route at its largest affordable time (one Si-standard X-ray scan over 70-149.96 deg at 0.04 deg, standard optics)."""
    m = PG.window_meas(70.0, 149.96, 0.04, 1.0, 'standard', True)
    t = min(20.0, (PG.BUDGET - 5 - PG.STD_PREP) * 60 / m.n)
    return [SP.DEFAULT, PG.window_meas(70.0, 149.96, 0.04, t, 'standard', True)]


def check(world, ms, label):
    holds = SC.SCEN[SC.WORLD_SCEN[world]]['worlds'][world]['holds']
    fault = F.assign(world, ms)
    valid = [m for i, m in enumerate(ms) if fault is None or i != fault[0]]
    Dv = SP.separation(world, valid) if valid else 0.0
    Dall = SP.separation(world, ms) if ms else 0.0
    kv = G.key_set(holds, Dv); ka = F.data_key(world, ms, fault); ks = G.key_set(holds, Dall)
    return dict(world=world, scen=SC.WORLD_SCEN[world], plan=label, n_meas=len(ms), fault=None if fault is None else dict(index=fault[0], type=fault[1]),
                D_valid=round(Dv, 3), D_all=round(Dall, 3), key_valid=kv, key_all=ka['key'], delta=ka['delta'],
                chi2_claim=ka['chi2_claim'], chi2_other=ka['chi2_other'], key_all_settings=ks,
                changes=sorted(ka['key']) != sorted(kv), spoils=sorted(ks) != sorted(kv),
                rule_F=sorted(ka['key']) != sorted(kv) or sorted(ks) != sorted(kv))     # X41: trusting changes the verdict or spoils it


def job(args):
    world, which = args
    if which == 'oracle': return check(world, plan_of(world), 'oracle')
    if which == 'obvious': return check(world, obvious_57(world), 'obvious_route')
    if which == 'clean':
        ms = plan_of(world); holds = SC.SCEN[SC.WORLD_SCEN[world]]['worlds'][world]['holds']
        D = SP.separation(world, ms); ka = F.data_key(world, ms)
        return dict(world=world, scen=SC.WORLD_SCEN[world], plan='oracle', D=round(D, 3), key=G.key_set(holds, D), key_all=ka['key'],
                    delta=ka['delta'], agree=sorted(ka['key']) == sorted(G.key_set(holds, D)))


def main():
    out = sys.argv[1]
    if '--types' in sys.argv:
        for s, t in json.loads(sys.argv[sys.argv.index('--types') + 1]).items(): F.SCHEDULE[int(s)]['type'] = t
    jobs = [(w, 'oracle') for w in F.fault_worlds()] + [(w, 'obvious') for w in F.fault_worlds() if SC.WORLD_SCEN[w] == 57] + \
           [(w, 'clean') for w in F.clean_worlds()]
    with Pool(int(os.environ.get('V5_PROCS', '19'))) as pool: res = pool.map(job, jobs, chunksize=1)
    json.dump(dict(schedule={str(k): (dict(v, trigger=list(v['trigger'])) if not isinstance(v['trigger'], str) else v) for k, v in F.SCHEDULE.items()},
                   fault_params={str(w): F.fault_params(w) for w in F.fault_worlds()}, rows=res), open(out, 'w'), indent=1)
    for r in res: print(json.dumps(r))


if __name__ == '__main__':
    main()
