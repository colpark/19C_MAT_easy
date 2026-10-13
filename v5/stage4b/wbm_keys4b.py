"""Stage 4b: the J.6 prototype key of every WBM entry (structure from the relaxed-structure file, symprec 0.1), precomputed once for
the panel's G rule 2 (V5-E29). Writes data/stage4b/wbm_keys.json {id: key}.
  python stage4b/wbm_keys4b.py"""
import json, os, sys
for _v in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ.setdefault(_v, '1')
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..'))
from multiprocessing import Pool
import pandas as pd


def _k(mid):
    from mcenv import stage2 as S2
    from mcenv import heuristics4b as H
    try: return mid, H.proto_key(S2.wbm(mid))
    except Exception: return mid, None


if __name__ == '__main__':
    ids = list(pd.read_csv(os.path.join(HERE, '..', 'data', 'stage4', '2023-12-13-wbm-summary.csv.gz')).material_id)
    with Pool(18) as p: out = dict(p.imap_unordered(_k, ids, chunksize=256))
    json.dump(out, open(os.path.join(HERE, '..', 'data', 'stage4b', 'wbm_keys.json'), 'w'))
    print(len(out), 'keys,', sum(v is None for v in out.values()), 'failed')
