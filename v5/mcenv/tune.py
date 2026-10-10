"""Tuning report for one scenario under given tunables (V5-1). Usage: python -m mcenv.tune SCEN [key=value ...]
Prints per world: D(m0), cheapest decisive grid plan (D >= 25) and its cost, best affordable D overall, best affordable X-ray-only D,
best affordable D confined to 10-70 deg without the standard, neutron-plan D."""
import os
for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"): os.environ.setdefault(_v, "1")
import json, sys, time
from multiprocessing import Pool
from . import scenarios as SC
from . import plangrid as PG
from .separation import NEUTRON


def _init(tune):
    SC.TUNE.update({int(k): v for k, v in tune.items()})


def report(scen, over, procs=18, pairs=True):
    tune = {scen: dict(SC.TUNE[scen], **over)}
    _init(tune)
    out = {'scen': scen, 'tune': tune[scen], 'worlds': {}}
    with Pool(procs, initializer=_init, initargs=(tune,)) as pool:
        for w in SC.twins(scen):
            t0 = time.time()
            rows = PG.scan_world(w, pairs=pairs, pool=pool)
            ch = PG.cheapest(rows)
            ba = PG.best_affordable(rows)
            bx = PG.best_affordable(rows, pred=lambda m: m.radiation == 'xray')
            bd = PG.best_affordable(rows, pred=lambda m: m.radiation == 'xray' and not m.si_standard and m.start >= 10 and m.start + m.step * (m.n - 1) <= 70.0001)
            nd = [r for r in rows if r[2] == (NEUTRON,)]
            f = lambda r: None if r is None else dict(cost=round(r[0], 1), D=round(r[1], 2), plan=[m.key() for m in r[2]])
            out['worlds'][w] = dict(D_m0=round(rows[0][1], 2), cheapest=f(ch), best=f(ba), best_xray=f(bx), best_default_range=f(bd),
                                    neutron=round(nd[0][1], 2) if nd else None, n_rows=len(rows), sec=round(time.time() - t0))
    return out


if __name__ == '__main__':
    scen = int(sys.argv[1]); over = {}
    for a in sys.argv[2:]:
        k, v = a.split('='); over[k] = float(v)
    print(json.dumps(report(scen, over), indent=1))
