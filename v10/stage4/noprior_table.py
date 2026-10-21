"""Stage 4 no-prior heuristic table (V5_SPEC I.10), DFT structure files only: for each H-scenario polymorph, its prototype key
(anonymous formula, space group number at symprec 0.1, sorted Wyckoff letters of the symmetry-distinct sites) and the count of MP entries
with the same key among all MP entries of the same anonymous formula; is_most_frequent = its key is the most frequent key of that formula
type in MP (ties count as most frequent). Writes stage4/validation/noprior_prototypes.json.
  python stage4/noprior_table.py"""
import gzip, json, os, sys
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..'))
from pymatgen.core import Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from mcenv import stage4 as F
from mcenv import physics as P


def key(st):
    try:
        sga = SpacegroupAnalyzer(st, symprec=0.1); ds = sga.get_symmetry_dataset()
        wy = sorted({(int(e), w) for e, w in zip(ds.equivalent_atoms, ds.wyckoffs)})
        return (st.composition.anonymized_formula, int(ds.number), ''.join(sorted(w for _, w in wy)))
    except Exception: return None


def main():
    S = F.install()
    polys = {p: S[s] for s in S for p in S[s]['polymorphs'] if S[s]['claim_type'] == 'H'}
    anons = {P.PHASES[p].structure({'lattice_scale': 1.0}).composition.anonymized_formula for p in polys}
    d = json.load(gzip.open(os.path.join(HERE, '..', 'data', 'stage4', '2023-02-07-mp-computed-structure-entries.json.gz'), 'rt'))
    counts = {a: Counter() for a in anons}
    for k, e in d['entry'].items():
        st = Structure.from_dict(e['structure'])
        a = st.composition.anonymized_formula
        if a in anons:
            kk = key(st)
            if kk: counts[a][kk] += 1
    out = {}
    for p in polys:
        st = P.PHASES[p].structure({'lattice_scale': 1.0}); kk = key(st); c = counts[kk[0]]
        top = max(c.values()) if c else 0
        out[p] = dict(key=list(kk), mp_count=c.get(kk, 0), mp_top_count=top, mp_top_key=list(c.most_common(1)[0][0]) if c else None,
                      n_mp_formula_type=sum(c.values()), is_most_frequent=bool(c) and c.get(kk, 0) == top)
        print(p, out[p])
    json.dump(out, open(os.path.join(HERE, 'validation', 'noprior_prototypes.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
