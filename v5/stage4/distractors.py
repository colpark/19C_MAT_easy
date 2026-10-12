"""Stage 4 distractors (V5_SPEC I.5.7), DFT truth files only, no FM call: per scenario the first two structures by sha256 of their id
(WBM or MP) of other reduced formulas in the scenario's chemical system (element set a subset of the formula's elements, at least two
elements), at most 24 sites in the conventional standard cell, with distinct prototypes (anonymous formula and space group number
differ). Writes stage4/DISTRACTORS.json.
  python stage4/distractors.py"""
import gzip, hashlib, json, os, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..'))
import pandas as pd
from pymatgen.core import Composition, Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from mcenv import stage2 as S2

DATA = os.path.join(HERE, '..', 'data', 'stage4')
MAX_SITES = 24
h = lambda s: hashlib.sha256(s.encode()).hexdigest()


def main():
    chosen = json.load(open(os.path.join(HERE, 'SELECTION.json')))['chosen']
    W = pd.read_csv(os.path.join(DATA, '2023-12-13-wbm-summary.csv.gz'))
    mp = json.load(gzip.open(os.path.join(DATA, '2023-02-07-mp-computed-structure-entries.json.gz'), 'rt'))
    mp = {mid: mp['entry'][k] for k, mid in mp['material_id'].items()}
    pool = [(r.material_id, Composition(r.formula)) for r in W.itertuples(index=False)] + \
           [(mid, Composition(v['composition'])) for mid, v in mp.items()]
    out = {}
    for c in chosen:
        f = c['formula']; els = {e.symbol for e in Composition(f).elements}
        cands = sorted([(h(i), i, comp) for i, comp in pool if {e.symbol for e in comp.elements} <= els and len(comp.elements) >= 2
                        and comp.reduced_formula != f], key=lambda t: t[0])
        picked, log = [], []
        for _, i, comp in cands:
            st = S2.wbm(i) if i.startswith('wbm-') else SpacegroupAnalyzer(Structure.from_dict(mp[i]['structure']), symprec=1e-3).get_conventional_standard_structure()
            sga = SpacegroupAnalyzer(st, symprec=1e-3); key = (comp.anonymized_formula, sga.get_space_group_number())
            rec = dict(id=i, formula=comp.reduced_formula, sites=len(st), spacegroup=sga.get_space_group_symbol(), sg_number=key[1])
            if len(st) > MAX_SITES: rec['reason'] = f'more than {MAX_SITES} sites'
            elif any((p['anon'], p['sg_number']) == key for p in picked): rec['reason'] = 'same prototype as the first distractor'
            elif any(p['formula'] == rec['formula'] for p in picked): rec['reason'] = 'same formula as the first distractor'
            else: rec['anon'] = key[0]; picked.append(rec)
            log.append(rec)
            if len(picked) == 2: break
        out[f] = dict(distractors=picked, considered=log, n_pool=len(cands))
        print(f, [(p['id'], p['formula'], p['spacegroup'], p['sites']) for p in picked], len(log), 'considered of', len(cands))
    json.dump(out, open(os.path.join(HERE, 'DISTRACTORS.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
