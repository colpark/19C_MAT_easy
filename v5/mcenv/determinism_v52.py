"""Determinism manifest for v5.2 (V5_SPEC E.6, F.7): the noisy arrays the servers return for a fixed plan per world and k, and the keys.
  python -m mcenv.determinism_v52 2s OUT.json     stage 2s: the scenario's c_dec plan (no m0), counts per k = 1..5, D of the plan
  python -m mcenv.determinism_v52 3 OUT.json      stage 3: m0 plus the stage 1b oracle plan of the mirrored world, with the fault applied
                                                  as the server does (F1 clipping included), counts per k, D over valid measurements and
                                                  the data key's delta
Run on host A, node A2 and host B; manifests must be identical."""
import hashlib, json, os, platform, sys
for _v in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ.setdefault(_v, '1')
import numpy as np
from . import scenarios as SC
from . import separation as SP
from .server import noise_rng

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    mode, outp = sys.argv[1], sys.argv[2]; out = {}
    if mode == '2s':
        from . import stage2s as ST
        ST.install(cost=False)
        C = json.load(open(os.path.join(ROOT, 'stage2s', 'validation', 'constraints.json')))['scen']
        for w in ST.worlds():
            s = SC.WORLD_SCEN[w]; tr = SP.world_truth(w); ms = [SP.meas_from(m) for m in C[str(s)]['c_dec']['plan']]
            for k in range(1, 6):
                h = hashlib.sha256()
                for idx, m in enumerate(ms): h.update(noise_rng(s, k, idx).poisson(SP.mu_truth(tr, m)).astype(np.int64).tobytes())
                out[f'{w}|{k}'] = h.hexdigest()[:16]
            out[f'{w}|D'] = f'{SP.separation(w, ms, tr):.6g}'
    else:
        from . import stage3 as F
        F.install()
        P = json.load(open(os.path.join(ROOT, 'stage1b', 'validation', 'oracle_plans.json')))
        for w in F.clean_worlds() + F.fault_worlds():
            s = SC.WORLD_SCEN[w]; tr = SP.world_truth(w); seed = SC.SCEN[s]['seed_scen']
            ms = [SP.DEFAULT] + [SP.meas_from(d) for d in (P.get(str(SC.SCEN[s]['worlds'][w]['mirror_1b'])) or [])]
            fault = F.assign(w, ms); fp = F.fault_params(w)
            for k in range(1, 6):
                h = hashlib.sha256()
                for idx, m in enumerate(ms):
                    rng = noise_rng(seed, k, idx)
                    if fault and idx == fault[0]:
                        mu, cap = F.fault_mu(tr, m, fault[1], fp, w)
                        c = np.minimum(rng.poisson(SP.mu_truth(tr, m)), int(round(cap))) if fault[1] == 'F1' else rng.poisson(mu)
                    else: c = rng.poisson(SP.mu_truth(tr, m))
                    h.update(c.astype(np.int64).tobytes())
                out[f'{w}|{k}'] = h.hexdigest()[:16]
            valid = [m for i, m in enumerate(ms) if not (fault and i == fault[0])]
            out[f'{w}|D_valid'] = f'{(SP.separation(w, valid, tr) if valid else 0.0):.6g}'
            if fault: out[f'{w}|delta'] = f"{F.data_key(w, ms, fault)['delta']:.6g}"
    man = hashlib.sha256(json.dumps(out, sort_keys=True).encode()).hexdigest()[:16]
    json.dump(dict(manifest=man, host=platform.node(), entries=out), open(outp, 'w'), indent=1, sort_keys=True)
    print(platform.node(), mode, 'manifest', man)


if __name__ == '__main__':
    main()
