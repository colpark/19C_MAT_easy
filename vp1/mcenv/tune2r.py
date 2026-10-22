"""Stage 2r tuning and constraint report (V5_SPEC D.2, D.3 r3/r4; v5 section 3 constraints, v5 plan grid). Truth only, no FM call.
  V5_S2R_PICK=42:1 V5_2R_TUNE='{"42": {"N": 50}}' python -m mcenv.tune2r OUT.json SCENS [--pairs]
Per world: D(m0), cheapest decisive grid plan, best affordable D, best 10-70 deg plan (any optics, no standard), neutron D; checks C1 (41),
C2a, C2b (<= 90 min), r4 (42: the cheapest decisive plan lies outside 10-70 deg or uses high-resolution optics)."""
import os
for _v in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ.setdefault(_v, '1')
import argparse, json, time
from multiprocessing import Pool
from . import stage2r as S2R
from . import scenarios as SC
from . import plangrid as PG
from .separation import NEUTRON, DEFAULT

S2R.install()


def in_default(m): return m.radiation == 'xray' and not m.si_standard and m.start >= 10 - 1e-9 and m.start + m.step * (m.n - 1) <= 70 + 1e-6


def report(w, pool, pairs):
    t0 = time.time(); rows = PG.scan_world(w, pairs=pairs, pool=pool)
    f = lambda r: None if r is None else dict(cost=round(r[0], 3), D=round(r[1], 4), plan=[m.key() for m in r[2]])
    ch = PG.cheapest(rows); s = SC.WORLD_SCEN[w]
    out = dict(world=w, scen=s, D_m0=round(rows[0][1], 4), cheapest=f(ch), cheapest9=f(PG.cheapest(rows, 9.0)), best=f(PG.best_affordable(rows)),
               best_xray=f(PG.best_affordable(rows, pred=lambda m: m.radiation == 'xray')), best_default_range=f(PG.best_affordable(rows, pred=in_default)),
               neutron=round(next(r[1] for r in rows if r[2] == (NEUTRON,)), 4), n_rows=len(rows), sec=round(time.time() - t0))
    out['checks'] = checks(out)
    return out, rows


def checks(r):
    s = r['scen']; c = r['cheapest']; C = {}
    if s == 41: C['C1'] = r['D_m0'] >= 25
    else:
        C['C2a'] = r['D_m0'] < 9; C['C2b'] = c is not None and c['cost'] <= 90
        if s == 42 and c is not None:
            C['r4_strict'] = all(not in_default(DEFAULT.__class__(**m)) or m['optics'] == 'high_resolution' for m in c['plan'])
            lo = min(m['start'] for m in c['plan']); hi = max(m['start'] + m['step'] * (m['n'] - 1) for m in c['plan'])
            C['r4'] = all(m['radiation'] == 'xray' for m in c['plan']) and hi - lo <= 6.0 + 1e-9      # amended r4 (X28): one 2theta interval of at most 6 deg
    return C


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('scens'); ap.add_argument('--pairs', action='store_true')
    ap.add_argument('--procs', type=int, default=19)
    a = ap.parse_args(); scens = [int(x) for x in a.scens.split(',')]
    res = dict(tune={s: SC.TUNE[s] for s in scens}, pick={s: SC.SCEN[s]['pick'] for s in scens}, worlds={})
    with Pool(a.procs) as pool:
        for s in scens:
            for w in SC.twins(s):
                res['worlds'][w], _ = report(w, pool, a.pairs); print(json.dumps(res['worlds'][w]), flush=True)
                json.dump(res, open(a.out, 'w'), indent=1)


if __name__ == '__main__':
    main()
