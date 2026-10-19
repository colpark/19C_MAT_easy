"""Stage 4 tuning and oracle plans (V5_SPEC I.5.6), truth only, no FM call. Scenarios 61-68 with their own hidden nuisances.
Loud: D(m0) >= 25 in both worlds at N 1000. Quiet: N = the largest N with max D(m0) <= 8 in both worlds (bisection on log N), then the
cheapest grid plan (singles and pairs) with D >= 25 in each world, cost <= 90 min. Writes OUT.json (per world: N, D(m0), cheapest plan).
  python -m mcenv.tune4 OUT.json"""
import os
for _v in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ.setdefault(_v, '1')
import json, math, sys, time
from multiprocessing import Pool
from . import stage4 as F
from . import scenarios as SC
from . import plangrid as PG
from .separation import separation, DEFAULT

HALF = 90.0


def _init(tune): F.install(tune)


def dm0(s, N):
    F.install({s: dict(N=N)})
    return [separation(w, [DEFAULT]) for w in SC.twins(s)]


def tune_quiet(s, target=8.0, lo=1e-3, hi=1000.0):
    for _ in range(30):
        mid = math.sqrt(lo * hi)
        if max(dm0(s, mid)) <= target: lo = mid
        else: hi = mid
    return round(lo, 4)


def main():
    S = F.install(); out = {}
    for s, d in S.items():
        t0 = time.time()
        if d['kind'] == 'loud':
            N = 1000.0; D = dm0(s, N)
            out[str(s)] = dict(kind='loud', N=N, worlds={str(w): dict(D_m0=round(x, 3), cheapest=dict(cost=0.0, D=round(x, 3), plan=[]))
                                                          for w, x in zip(SC.twins(s), D)}, ok=min(D) >= 25)
        else:
            N = tune_quiet(s); D = dm0(s, N); rec = dict(kind='quiet', N=N, worlds={})
            with Pool(18, initializer=_init, initargs=({s: dict(N=N)},)) as pool:
                for w, x in zip(SC.twins(s), D):
                    rows = PG.scan_world(w, pairs=True, max_cost=180.0, pool=pool); ch = PG.cheapest(rows)
                    rec['worlds'][str(w)] = dict(D_m0=round(x, 3), cheapest=None if ch is None else dict(cost=round(ch[0], 2), D=round(ch[1], 2),
                                                                                                         plan=[m.key() for m in ch[2]]))
            rec['ok'] = all(v['D_m0'] < 9 and v['cheapest'] and v['cheapest']['cost'] <= HALF for v in rec['worlds'].values())
            out[str(s)] = rec
        out[str(s)]['sec'] = round(time.time() - t0)
        print(s, json.dumps(out[str(s)])[:300], flush=True)
        json.dump(out, open(sys.argv[1], 'w'), indent=1)


if __name__ == '__main__':
    main()
