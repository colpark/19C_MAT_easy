#!/usr/bin/env python3
"""Addendum B, B2 matching under MATCH_RULE_B2.json v1 (frozen B2pre before any matching).

usage: match_exp.py RAW_DIR C2DIR OUT.jsonl
Funnel side: the 55 xm-46 FPMD unit cells and the 11 1c-13 PET-MAD unit cells (structures from the AiiDA export
liion_cells.json / 1c13 cells), plus KNOWN_77 formulas (no computed structure deposited).
Experimental side: OBELiX all.csv (+ randomized CIFs), Liverpool LiIonDatabase.csv.
Every experimental record ends in exactly one class: exact, family, or no_match with a reason. Level A, never a key.
No-match reason added beyond the frozen list (labelling only, logged VC-E20): computed_structure_not_deposited.
"""
import csv, glob, json, os, re, sys
import numpy as np

LTOL, STOL, ATOL = 0.2, 0.3, 5
DOPE_MAX = 0.1
RT = (293.15, 303.15)


def comp(s):
    from pymatgen.core import Composition
    s = re.sub(r'\s+', '', str(s))
    return Composition(s)


def reduced(s):
    try:
        return comp(s).reduced_formula
    except Exception:
        return None


def is_integer_comp(c, tol=1e-3):
    return all(abs(v - round(v)) < tol for v in c.values())


ANIONS = {'O', 'S', 'Se', 'Te', 'F', 'Cl', 'Br', 'I', 'N', 'P', 'As', 'Sb'}


def family_dope(exp_c, par_c):
    """Doped/substituted relation: normalise the experimental composition to the parent's anion amount; every
    parent element changes by <= DOPE_MAX of its amount and every new element amounts to <= DOPE_MAX of the
    largest parent cation amount. Returns (is_family, max_fraction)."""
    pa = sum(v for e, v in par_c.get_el_amt_dict().items() if e in ANIONS)
    ea = sum(v for e, v in exp_c.get_el_amt_dict().items() if e in ANIONS)
    if pa <= 0 or ea <= 0:
        return False, None
    ex = {e: v * pa / ea for e, v in exp_c.get_el_amt_dict().items()}
    pd = par_c.get_el_amt_dict()
    cmax = max((v for e, v in pd.items() if e not in ANIONS), default=1.0)
    fr = []
    for e in set(ex) | set(pd):
        if e in pd:
            fr.append(abs(ex.get(e, 0.0) - pd[e]) / pd[e])
        else:
            fr.append(ex[e] / cmax)
    m = max(fr)
    return m <= DOPE_MAX + 1e-9, float(m)


def struct_match(s1, s2):
    from pymatgen.analysis.structure_matcher import StructureMatcher
    sm = StructureMatcher(ltol=LTOL, stol=STOL, angle_tol=ATOL, primitive_cell=True, scale=True, attempt_supercell=False)
    return bool(sm.fit(s1, s2))


def load_funnel(c2):
    from pymatgen.core import Structure
    F = []
    for c in json.load(open(os.path.join(c2, 'liion_cells_struct.json'))):
        F.append({'id': c['uuid'], 'set': c['set'], 'reduced': c['reduced'], 'structure': Structure.from_dict(c['structure'])})
    return F


def rt_pick(recs):
    rt = [r for r in recs if r['T_K'] is not None and RT[0] <= r['T_K'] <= RT[1]]
    if not rt:
        return None
    return sorted(rt, key=lambda r: (abs(r['T_K'] - 298.15), -r['sigma_S_cm']))[0]


def load_obelix(raw):
    base = glob.glob(os.path.join(raw, 'obelix', 'x', 'OBELiX-*', 'data'))[0]
    rows = list(csv.DictReader(open(os.path.join(base, 'downloads', 'all.csv'))))
    cifdir = os.path.join(base, 'randomized_cifs')
    out = []
    for r in rows:
        s = r['Ionic conductivity (S cm-1)'].strip()
        val = None
        cens = None
        if s.startswith('<'):
            cens = 'upper_bound'
            s = s[1:]
        try:
            val = float(s)
        except ValueError:
            pass
        cif = os.path.join(cifdir, f"{r['ID']}.cif")
        out.append({'db': 'OBELiX', 'exp_id': r['ID'], 'composition': r['True Composition'] or r['Reduced Composition'],
                    'reduced': reduced(r['Reduced Composition']), 'T_K': 298.15, 'T_note': 'OBELiX: room temperature',
                    'sigma_S_cm': val, 'censored': cens, 'family_label': r['Family'], 'doi': r['DOI'],
                    'cif': cif if os.path.exists(cif) else None, 'license': 'CC-BY-4.0'})
    return out


def load_liverpool(raw):
    p = os.path.join(raw, 'liverpool', 'LiIonDatabase.csv')
    lines = open(p, encoding='utf-8-sig', errors='ignore').read().splitlines()
    h = next(i for i, l in enumerate(lines) if l.startswith('ID,'))
    rows = list(csv.DictReader(lines[h:]))
    by = {}
    for r in rows:
        try:
            v, T = float(r['target']), float(r['temperature'])
        except ValueError:
            continue
        by.setdefault(r['composition'], []).append({'db': 'Liverpool', 'exp_id': r['ID'], 'composition': r['composition'],
                                                    'reduced': reduced(r['composition']), 'T_K': T, 'sigma_S_cm': v,
                                                    'censored': None, 'family_label': r['family'], 'doi': r['source'],
                                                    'cif': None, 'license': 'academic use only (internal)'})
    out = []
    for k, recs in by.items():
        p_ = rt_pick(recs)
        if p_ is None:
            r0 = dict(recs[0])
            r0['no_rt'] = True
            out.append(r0)
        else:
            p_['n_temperatures'] = len(recs)
            out.append(p_)
    return out


def classify(e, funnel, known):
    from pymatgen.core import Structure
    if e.get('no_rt'):
        return 'no_match', 'no_rt_value', []
    if e['reduced'] is None:
        return 'no_match', 'parse_error', []
    try:
        ec = comp(e['composition'])
    except Exception:
        return 'no_match', 'parse_error', []
    same = [f for f in funnel if f['reduced'] == e['reduced']]
    if same and is_integer_comp(ec.reduced_composition):
        if e['cif']:
            try:
                es = Structure.from_file(e['cif'])
            except Exception:
                return 'no_match', 'parse_error', []
            hits = [f['id'] for f in same if struct_match(f['structure'], es)]
            if hits:
                return 'exact', None, hits
            return 'no_match', 'structure_mismatch', [f['id'] for f in same]
        return 'family', 'family_label_missing (computed side has no family label)', [f['id'] for f in same]
    fam = []
    for f in funnel:
        ok, m = family_dope(ec, comp(f['reduced']))
        if ok:
            fam.append(f['id'])
    if fam:
        return 'family', 'doped_or_substituted', fam
    if e['reduced'] in known:
        return 'no_match', 'computed_structure_not_deposited (KNOWN_77 formula)', []
    return 'no_match', 'formula_absent', []


def main():
    raw, c2, out = sys.argv[1:4]
    funnel = load_funnel(c2)
    known = {k['reduced_formula'] for k in json.load(open(os.path.join(os.path.dirname(__file__), 'KNOWN_77.json')))['entries']}
    recs = load_obelix(raw) + load_liverpool(raw)
    n = {}
    with open(out, 'w') as f:
        for e in recs:
            cls, why, ids = classify(e, funnel, known)
            e2 = {k: v for k, v in e.items() if k != 'cif'}
            e2.update({'has_cif': bool(e.get('cif')), 'match_class': cls, 'reason': why, 'funnel_ids': ids, 'level': 'A'})
            f.write(json.dumps(e2) + '\n')
            n[(e['db'], cls)] = n.get((e['db'], cls), 0) + 1
    print({f'{a}|{b}': v for (a, b), v in sorted(n.items())})


if __name__ == '__main__':
    main()
