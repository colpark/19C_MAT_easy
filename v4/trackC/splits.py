#!/usr/bin/env python3
"""C3.1 SPLITS.json (I12; skill C0 split manifest). The rule below is frozen before it sees any material list.

Family rule (anion / polyanion class, first match wins, on the reduced composition):
  phosphate  P and O present            borate   B and O present (no P)
  oxide      O present                  sulfide  S, Se or Te present (chalcogenide, no O)
  halide     F, Cl, Br or I present     nitride  N present
  other      everything else (intermetallics, carbides, borides, pnictides without N/O ...)
Held-out test family per source: the family whose share of that source's materials is closest to 20 % (ties: the
family name first in sha256(seed + name) order). Dev: 15 % of the remaining materials by a fixed seed (rounded
half up), drawn by sha256(seed + material_id) rank. Train: the rest. JARVIS 2D (figshare file 38950433) is a
whole held-out transfer set. Every entity keeps its split for every later artifact (I12).
usage: splits.py materials.jsonl OUT.json
"""
import hashlib, json, math, sys
from collections import Counter, defaultdict

SEED = 'trackC-v4.4-2026-10-07'
ORDER = ['phosphate', 'borate', 'oxide', 'sulfide', 'halide', 'nitride', 'other']


def family(reduced_formula):
    from pymatgen.core import Composition
    el = {e.symbol for e in Composition(reduced_formula).elements}
    if 'P' in el and 'O' in el:
        return 'phosphate'
    if 'B' in el and 'O' in el:
        return 'borate'
    if 'O' in el:
        return 'oxide'
    if el & {'S', 'Se', 'Te'}:
        return 'sulfide'
    if el & {'F', 'Cl', 'Br', 'I'}:
        return 'halide'
    if 'N' in el:
        return 'nitride'
    return 'other'


def h(x):
    return hashlib.sha256((SEED + x).encode()).hexdigest()


def split_source(mats):
    fam = {m['material_id']: family(m['reduced_formula']) for m in mats}
    cnt = Counter(fam.values())
    n = len(mats)
    test_fam = sorted(cnt, key=lambda f: (abs(cnt[f] / n - 0.20), h(f)))[0]
    rest = sorted([m for m in mats if fam[m['material_id']] != test_fam], key=lambda m: h(m['material_id']))
    n_dev = math.floor(0.15 * len(rest) + 0.5)
    dev = {m['material_id'] for m in rest[:n_dev]}
    out = {}
    for m in mats:
        mid = m['material_id']
        out[mid] = {'split': 'test' if fam[mid] == test_fam else ('dev' if mid in dev else 'train'), 'family': fam[mid],
                    'formula': m['reduced_formula']}
    return test_fam, dict(cnt), out


def main():
    from pymatgen.core import Composition
    mats = [json.loads(l) for l in open(sys.argv[1])]
    by = defaultdict(list)
    for m in mats:
        if 'reduced_formula' not in m:
            m['reduced_formula'] = Composition(m['formula']).reduced_formula
        by[m['source']].append(m)
    rep = {'seed': SEED, 'rule': __doc__.split('usage:')[0].strip(), 'sources': {}, 'materials': {}}
    for src, ms in sorted(by.items()):
        tf, cnt, out = split_source(ms)
        c = Counter(v['split'] for v in out.values())
        rep['sources'][src] = {'test_family': tf, 'family_counts': cnt, 'split_counts': dict(c)}
        rep['materials'].update(out)
    rep['held_out_transfer'] = {'jarvis_2d': {'file': 'jarvis_epc_data_2d.json.zip (figshare 38950433)', 'n': 161,
                                              'split': 'transfer_test'}}
    rep['petmad_1c13'] = 'the 11 1c-13 materials are not keyed; if used as demonstrator reference, split = test'
    json.dump(rep, open(sys.argv[2], 'w'), indent=1, sort_keys=True)
    print(json.dumps(rep['sources'], indent=1))


if __name__ == '__main__':
    main()
