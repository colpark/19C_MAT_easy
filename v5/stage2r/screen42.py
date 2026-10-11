"""Stage 2r shape 42 screening (D.3 r3, r4), truth only: for each passing candidate in hash order, the count rate N (within [3, 3000])
that brings the louder twin to D(m0) = 6, then the cheapest decisive grid plan per twin (C2b <= 90 min) and r4 (that plan lies outside
10-70 deg or uses high-resolution optics). Writes stage2r/tuning_runs/screen42.jsonl.
  python stage2r/screen42.py [FIRST LAST]"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
for _v in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ.setdefault(_v, '1')
from multiprocessing import Pool
from mcenv import stage2r as R
from mcenv import scenarios as SC
from mcenv import separation as SP
from mcenv import plangrid as PG
from mcenv.tune2r import in_default

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tuning_runs', 'screen42.jsonl')


def dm0(N):
    SC.TUNE[42]['N'] = N
    return max(SP.separation(w, [SP.DEFAULT]) for w in (403, 404))


def main():
    a, b = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, 24)
    for i in range(a, b + 1):
        R.PICK[42] = i
        try:
            S = R.setup()
        except Exception as e:
            open(OUT, 'a').write(json.dumps(dict(i=i, error=str(e))) + '\n'); continue
        SC.SCEN[42] = S[42]; SC.TUNE[42] = dict(L=100.0, N=1000.0, bg=20.0, Nn=1000.0, bgn=50.0); SC.WORLD_SCEN.update({403: 42, 404: 42})
        lo, hi = 3.0, 3000.0
        if dm0(lo) >= 6: rec = dict(i=i, formula=S[42]['composition'], protos=S[42]['protos'], N=lo, D_m0=dm0(lo), r3='fail: D(m0) >= 6 at N = 3')
        else:
            for _ in range(14):
                mid = (lo * hi) ** 0.5
                if dm0(mid) < 6: lo = mid
                else: hi = mid
            N = round(lo, 2); SC.TUNE[42]['N'] = N
            rec = dict(i=i, formula=S[42]['composition'], protos=S[42]['protos'], N=N, worlds={})
            with Pool(19) as pool:
                for w in (403, 404):
                    rows = PG.scan_world(w, pairs=True, pool=pool); ch = PG.cheapest(rows)
                    rec['worlds'][w] = dict(D_m0=round(rows[0][1], 3), cheapest=None if ch is None else dict(cost=round(ch[0], 2), plan=[m.key() for m in ch[2]]),
                                            r4=None if ch is None else all((not in_default(m)) or m.optics == 'high_resolution' for m in ch[2]))
            ws = rec['worlds'].values()
            rec['C2b'] = all(v['cheapest'] and v['cheapest']['cost'] <= 90 for v in ws); rec['r4'] = all(v['r4'] for v in ws)
            rec['passes'] = rec['C2b'] and rec['r4']
        print(json.dumps(rec), flush=True); open(OUT, 'a').write(json.dumps(rec) + '\n')


if __name__ == '__main__':
    main()
