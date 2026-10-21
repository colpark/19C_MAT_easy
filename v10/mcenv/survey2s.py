"""Stage 2s T4 (X44, reported, not enforced): the key D of the best lattice-independent survey that spends the whole budget.
Surveys: one X-ray scan, standard optics, step 0.04 deg, windows [a, a + 60] (a = 5, 10, ..., 90) and 70-149.96 deg, time per step at the
largest affordable value (<= 20 s). Per scenario: the survey whose smaller key D over the two worlds is largest.
  V5_2S_TUNE=... V5_2S_BUDGET=... python -m mcenv.survey2s OUT.json SCENS"""
import os
for _v in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ.setdefault(_v, '1')
import json, math, sys
from multiprocessing import Pool
from . import stage2s as ST
from . import scenarios as SC
from . import separation as SP

ST.install()


def surveys(B):
    out = []
    for lo, hi in [(float(a), float(a) + 60.0) for a in range(5, 95, 5)] + [(70.0, 149.96)]:
        n = int(math.floor((hi - lo) / 0.04 + 1e-9)) + 1
        t = min(20.0, (B - ST.OVERHEAD) * 60.0 / n)
        if t >= 0.1: out.append(SP.Meas('xray', lo, 0.04, n, round(t, 4), 'standard', False))
    return out


def job(a):
    w, m = a; return w, m.key(), SP.separation(w, [m])


def main():
    out, scens = sys.argv[1], [int(s) for s in sys.argv[2].split(',')]
    jobs = [(w, m) for s in scens for w in SC.twins(s) for m in surveys(SC.SCEN[s]['budget'])]
    with Pool(int(os.environ.get('V5_PROCS', '18'))) as pool: res = pool.map(job, jobs)
    R = {}
    for s in scens:
        ws = SC.twins(s); rows = {}
        for w, k, D in res:
            if w in ws: rows.setdefault(json.dumps(k, sort_keys=True), {})[w] = D
        best = max(rows.items(), key=lambda kv: min(kv[1].values()))
        R[s] = dict(budget=SC.SCEN[s]['budget'], N=SC.TUNE[s]['N'], best_survey=json.loads(best[0]), D_key=[round(best[1][w], 3) for w in ws],
                    resolvable_by_survey=min(best[1].values()) >= 9.0)
    json.dump(R, open(out, 'w'), indent=1); print(json.dumps(R, indent=1))


if __name__ == '__main__':
    main()
