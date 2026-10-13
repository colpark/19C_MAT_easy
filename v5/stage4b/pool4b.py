"""Stage 4b candidate pool (V5_SPEC J.4, J.5), DFT data only, no FM call. WBM reduced formulas with no MP entry, 3 or 4 elements, rule v2
extended; per formula its WBM entries with prototype key (structure, symprec 0.1), e_form, hull distance, PBE gap, site count of the
conventional cell, PBE+U flag; one entry per key (the lowest-energy entry). Dev formulas: sha256(formula) % 10 == 0 (X54).
Writes data/stage4b/pool4b.json.
  python stage4b/pool4b.py"""
import hashlib, json, os, sys
for _v in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ.setdefault(_v, '1')
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..'))
from multiprocessing import Pool
import pandas as pd
from pymatgen.core import Composition

DATA4 = os.path.join(HERE, '..', 'data', 'stage4')
OUT = os.path.join(HERE, '..', 'data', 'stage4b', 'pool4b.json')


def _entry(mid):
    from mcenv import stage2 as S2
    from mcenv import heuristics4b as H
    try:
        st = S2.wbm(mid); return mid, H.proto_key(st), len(st)
    except Exception as e:
        return mid, None, None


def main():
    from mcenv import heuristics4b as H
    import bz2
    W = pd.read_csv(os.path.join(DATA4, '2023-12-13-wbm-summary.csv.gz'))
    mp = json.load(gzip_open(os.path.join(DATA4, '2023-02-07-mp-computed-structure-entries.json.gz')))
    MPF = {Composition(e['composition']).reduced_formula for e in mp['entry'].values()}
    W['rf'] = [Composition(f).reduced_formula for f in W.formula]
    cand = {}
    for rf, g in W.groupby('rf'):
        if rf in MPF or not H.pool_ok(rf): continue
        cand[rf] = g
    print(len(cand), 'pool formulas', flush=True)
    cse = json.load(bz2.open(os.path.join(DATA4, '2022-10-19-wbm-computed-structure-entries.json.bz2'), 'rt'))
    hub = {mid: bool(cse['computed_structure_entry'][k]['parameters'].get('is_hubbard')) for k, mid in cse['material_id'].items()}
    ids = [mid for g in cand.values() for mid in g.material_id]
    with Pool(18) as p: keys = {m: (k, n) for m, k, n in p.imap_unordered(_entry, ids, chunksize=64)}
    out = {}
    for rf, g in cand.items():
        ents = {}
        for r in g.sort_values('e_form_per_atom_mp2020_corrected').itertuples(index=False):
            k, n = keys[r.material_id]
            if k is None or k in ents: continue
            ents[k] = dict(id=r.material_id, key=k, sites=n, e_form=float(r.e_form_per_atom_mp2020_corrected),
                           e_hull=float(r.e_above_hull_mp2020_corrected_ppd_mp), gap=float(r.bandgap_pbe), pbe_u=hub.get(r.material_id, False))
        pbe_u = any(e['pbe_u'] for e in ents.values())
        out[rf] = dict(entries=list(ents.values()), n_elements=len(Composition(rf).elements), classes=H.chem_classes(rf, pbe_u),
                       magnetic=H.magnetic_3d(rf), mixed_valence=H.mixed_valence(rf), dev=int(hashlib.sha256(rf.encode()).hexdigest(), 16) % 10 == 0)
    json.dump(out, open(OUT, 'w'))
    print(len(out), 'formulas;', sum(v['dev'] for v in out.values()), 'dev;', sum(len(v['entries']) >= 2 for v in out.values()), 'with >= 2 polymorphs')


def gzip_open(p):
    import gzip; return gzip.open(p, 'rt')


if __name__ == '__main__':
    main()
