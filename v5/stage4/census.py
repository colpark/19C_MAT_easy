"""Stage 4 census (V5_SPEC I.5), DFT truth only, no FM call. Reads the WBM summary and the MP computed structure entries and writes
data/stage4/census4.json: per WBM reduced formula absent from MP (X50), its WBM entries (id, prototype, e_form and hull distance,
MP2020 corrected) and the rule v2 verdict. Candidate pairs per claim type (R, H) are then formed by stage4/select.py.
  python stage4/census.py"""
import gzip, importlib.util, json, os
from collections import defaultdict
import pandas as pd
from pymatgen.core import Composition

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, '..', 'data', 'stage4')
_spec = importlib.util.spec_from_file_location('sel_v5', os.path.join(HERE, '..', 'stage2', 'select.py'))
V5 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(V5)       # rule v2 helpers of v5 stage 2, unchanged


def mp_formulas():
    """reduced formulas of every MP computed structure entry (the Matbench Discovery MP snapshot)."""
    with gzip.open(os.path.join(DATA, '2023-02-07-mp-computed-structure-entries.json.gz'), 'rt') as f:
        d = json.load(f)
    out = set()
    if isinstance(d, dict) and 'entry' in d:                      # pandas-style {column: {index: value}}
        for e in d['entry'].values(): out.add(Composition(e['composition']).reduced_formula)
    else:
        for e in (d if isinstance(d, list) else d.values()): out.add(Composition(e['composition']).reduced_formula)
    return out


def main():
    W = pd.read_csv(os.path.join(DATA, '2023-12-13-wbm-summary.csv.gz'))
    MP = mp_formulas()
    by = defaultdict(list)
    for r in W.itertuples(index=False):
        if pd.isna(r.e_form_per_atom_mp2020_corrected) or pd.isna(r.e_above_hull_mp2020_corrected_ppd_mp) or not isinstance(r.wyckoff_spglib, str):
            continue
        c = Composition(r.formula); rf = c.reduced_formula
        by[rf].append(dict(id=r.material_id, proto=r.wyckoff_spglib.split(':')[0], nsites=int(r.n_sites),
                           e_form=float(r.e_form_per_atom_mp2020_corrected), e_hull=float(r.e_above_hull_mp2020_corrected_ppd_mp)))
    out = {}
    for rf, ents in by.items():
        if rf in MP: continue
        if len({e['proto'] for e in ents}) < 2: continue
        els = sorted(e.symbol for e in Composition(rf).elements)
        out[rf] = dict(elements=els, rule_v2=bool(V5.ok_elements(els) and len(els) <= 3 and V5.charge_ok(rf)), entries=ents)
    json.dump(dict(n_mp_formulas=len(MP), n_wbm_formulas=len(by), n_candidates=len(out), formulas=out),
              open(os.path.join(DATA, 'census4.json'), 'w'))
    print(len(MP), 'MP formulas;', len(by), 'WBM formulas;', len(out), 'absent from MP with >= 2 prototypes;',
          sum(v['rule_v2'] for v in out.values()), 'pass rule v2')


if __name__ == '__main__':
    main()
