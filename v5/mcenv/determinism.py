"""Determinism manifest (V5_SPEC section 4): the noisy arrays the server returns for m0 and the oracle plan, per world and k, and D(m0).
  python -m mcenv.determinism ORACLE_PLANS.json OUT.json      (run on host A and host B; manifests must be identical)"""
import hashlib, json, os, platform, sys
for _v in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ.setdefault(_v, '1')
import numpy as np
from . import scenarios as SC
from . import separation as SP
from .server import noise_rng


def main():
    plans = json.load(open(sys.argv[1])); out = {}
    for w in SC.WORLDS:
        tr = SP.world_truth(w); ms = [SP.DEFAULT] + [SP.meas_from(d) for d in (plans.get(str(w)) or [])]
        for k in range(1, 6):
            h = hashlib.sha256()
            for idx, m in enumerate(ms):
                h.update(noise_rng(tr['scen'], k, idx).poisson(SP.mu_truth(tr, m)).astype(np.int64).tobytes())
            out[f'{w}|{k}'] = h.hexdigest()[:16]
        out[f'{w}|D_m0'] = f'{SP.separation(w, [SP.DEFAULT], tr):.6g}'
    man = hashlib.sha256(json.dumps(out, sort_keys=True).encode()).hexdigest()[:16]
    json.dump(dict(manifest=man, host=platform.node(), entries=out), open(sys.argv[2], 'w'), indent=1, sort_keys=True)
    print(platform.node(), 'manifest', man)


if __name__ == '__main__':
    main()
