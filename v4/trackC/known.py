#!/usr/bin/env python3
"""Addendum B, B2 C0.1: KNOWN_77.json, the literature-known conductors that S9 (novelty) removed.

The paper gives the list by name in Sec 3.2.1 (no SI table). Each entry: the formula as printed (pdftotext
spacing), its normalised reduced formula, the sub-list it sits in, and a verbatim span that the code verifies
against the paper text. The count is reconciled against the stated 77 and every gap is logged.
usage: known.py PAPER_TEXT.txt OUT.json   (PAPER_TEXT from `pdftotext -layout 2601.03151.pdf`)
"""
import json, re, sys

# (printed, normalised input for pymatgen, sub-list); order of appearance in Sec 3.2.1
ENTRIES = [
    ('Li2 Ti6 O13', 'Li2Ti6O13', 'reviewed'), ('Li7 P3 S11', 'Li7P3S11', 'reviewed'),
    ('Li2 TeO4', 'Li2TeO4', 'reviewed'), ('Li6 NBr3', 'Li6NBr3', 'reviewed'), ('Li3 N 169', 'Li3N', 'reviewed'),
    ('LiI is well known', 'LiI', 'reviewed'), ('LiBr and LiCl', 'LiBr', 'reviewed'), ('LiBr and LiCl', 'LiCl', 'reviewed'),
    ('Li2 Se is used', 'Li2Se', 'reviewed'), ('Li3 BN2', 'Li3BN2', 'reviewed'), ('Li3 BS3', 'Li3BS3', 'reviewed'),
    ('Li4 SnSe4', 'Li4SnSe4', 'reviewed'), ('Li2 SiN2', 'Li2SiN2', 'reviewed'), ('Li2 SiP2', 'Li2SiP2', 'reviewed'),
    ('Li2 SiS3', 'Li2SiS3', 'reviewed'), ('LiBF4', 'LiBF4', 'reviewed'), ('Li3 BrO', 'Li3BrO', 'reviewed'),
    ('Li3Y (PS4 )2', 'Li3Y(PS4)2', 'reviewed'), ('Li3 PS4', 'Li3PS4', 'reviewed'), ('Li4 PN3', 'Li4PN3', 'reviewed'),
    ('Li5 AlS4', 'Li5AlS4', 'reviewed'), ('Li5 NCl2', 'Li5NCl2', 'reviewed'), ('Li7 BiO6', 'Li7BiO6', 'reviewed'),
    ('LiGa(SeO3 )2', 'LiGa(SeO3)2', 'reviewed'), ('LiH f2 (PO4 )3', 'LiHf2(PO4)3', 'reviewed'),
    ('LiInS2 is a', 'LiInS2', 'reviewed'), ('LiS 202', 'LiS', 'reviewed'), ('Li2 S is used', 'Li2S', 'reviewed'),
    ('Li3 InO3', 'Li3InO3', 'reviewed'), ('LiZnPS4', 'LiZnPS4', 'reviewed'), ('LiTi2 (PO4 )3', 'LiTi2(PO4)3', 'reviewed'),
    ('LiNbO3', 'LiNbO3', 'reviewed'), ('LiAlCl4', 'LiAlCl4', 'reviewed'), ('Li2 O is a', 'Li2O', 'reviewed'),
    ('Li2 Mo4 O13', 'Li2Mo4O13', 'reviewed'), ('LiSn2 (PO4 )3', 'LiSn2(PO4)3', 'reviewed'),
    ('Li4 SnS4', 'Li4SnS4', 'reviewed'), ('Li9 S3 N', 'Li9S3N', 'reviewed'), ('Li4 GeS4', 'Li4GeS4', 'reviewed'),
    ('LiCF3 SO3 is', 'LiCF3SO3', 'reviewed'), ('Li5 NBr2', 'Li5NBr2', 'reviewed'), ('Li10 N3 Br', 'Li10N3Br', 'reviewed'),
    ('Li3 In2 (PO4 )3', 'Li3In2(PO4)3', 'reviewed'), ('Li2 B6 O9 F2', 'Li2B6O9F2', 'reviewed'),
    ('Li2 SrTa2 O7', 'Li2SrTa2O7', 'reviewed'), ('Li7 SbO6', 'Li7SbO6', 'reviewed'),
    ('Li5Cl3 O', 'Li5Cl3O', 'kahle_proposed'), ('Li7 TaO6', 'Li7TaO6', 'kahle_proposed'),
    ('LiGaI4', 'LiGaI4', 'kahle_proposed'), ('LiGaBr3', 'LiGaBr3', 'kahle_proposed'),
    ('Li3CsCl4', 'Li3CsCl4', 'kahle_proposed'), ('Li2CsI3 which', 'Li2CsI3', 'kahle_proposed'),
    ('Li2WO4', 'Li2WO4', 'kahle_proposed'), ('LiAlSiO4', 'LiAlSiO4', 'kahle_proposed'),
    ('LiAlSe2', 'LiAlSe2', 'kahle_fpmd_low_T_insignificant'), ('Li4 Re6 S11', 'Li4Re6S11', 'kahle_fpmd_low_T_insignificant'),
    ('LiPO3', 'LiPO3', 'kahle_fpmd_low_T_insignificant'), ('Li3 Sc2 (PO4 )3', 'Li3Sc2(PO4)3', 'kahle_fpmd_low_T_insignificant'),
    ('Li4 P2 O7', 'Li4P2O7', 'kahle_fpmd_low_T_insignificant'), ('(LiI)2 Li3 SbS3', 'Li5I2SbS3', 'kahle_fpmd_low_T_insignificant'),
    ('Li6 PS5 I', 'Li6PS5I', 'kahle_fpmd_low_T_insignificant'), ('Li5 P(S2Cl)2', 'Li5PS4Cl2', 'kahle_fpmd_low_T_insignificant'),
    ('Li3 P7', 'Li3P7', 'kahle_fpmd_low_T_insignificant'), ('Li3 SbS3', 'Li3SbS3', 'kahle_fpmd_low_T_insignificant'),
    ('Li2 B3 O4 F3', 'Li2B3O4F3', 'kahle_fpmd_low_T_insignificant'), ('Li2 Mg2 (SO4 )3', 'Li2Mg2(SO4)3', 'kahle_fpmd_low_T_insignificant'),
    ('Li3 AsS3', 'Li3AsS3', 'kahle_fpmd_low_T_insignificant'), ('Li2 Si2 O5', 'Li2Si2O5', 'kahle_fpmd_low_T_insignificant'),
    ('Li2 NaB(PO4 )2', 'Li2NaB(PO4)2', 'kahle_fpmd_low_T_insignificant'), ('Li6Y (BO3 )3', 'Li6Y(BO3)3', 'kahle_fpmd_low_T_insignificant'),
    ('LiAuF4', 'LiAuF4', 'kahle_fpmd_low_T_insignificant'),
]
SPAN_HEADS = {
    'reviewed': 'In the following short review, we report these 77 structures and their current use case if applicable.',
    'kahle_proposed': 'Besides this, Kahle et al. 118 proposed following as fast Li-ion conductors:',
    'kahle_fpmd_low_T_insignificant': 'FPMD simulations performed by Kahle et al. 118 showed insignificant diffusion in '
                                      'the following structures at lower temperatures:',
}
# FPMD-studied materials printed in Tables 1-3 (for the overlap check only)
FPMD_TABLES = ['Li2Te2O5', 'Li2CsCl3', 'LiKSe', 'LiYS2', 'LiInSe2', 'LiAlS2', 'LiLuS2', 'Li7Te3O9F', 'Li5SiP3',
               'Li6RbBiO6', 'LiAuF6', 'Li3Na3Ga2F12', 'LiZrS2', 'Li2CdSnSe4', 'LiBa4Ga5Se12', 'Li3Na3Rh2F12', 'Li2HgO2',
               'Li2Ca2Ta3O10', 'Li2BeF4', 'Li2Ti4O9', 'LiY2Ti2S2O5', 'Li10BrN3', 'Li2Cs3Br5', 'Li8SeN2', 'Li8TeN2',
               'LiCF3SO3', 'Li2ZnBr4', 'LiBeP', 'Li5Br2N', 'Li10Si2PbO10', 'Li2ZnGeSe4', 'LiCs2I3', 'LiSr2Br5', 'LiGaSe2',
               'LiP7', 'LiMoPO6', 'LiY(MoO4)2', 'Li10B14Cl2O25', 'Li2P2PdO7', 'Li2B3PO8', 'Li2B2Se5', 'Li8Bi2(MoO4)7',
               'Li3AuS2', 'Li4CO4', 'LiCsI2', 'Li3CsBr4', 'Li3Cs2Br5', 'Li7NbO6', 'Li3Cs2I5', 'LiCs3Cl4', 'Li4Mo3O8',
               'Li5NaN2']


def norm_text(t):
    return re.sub(r'\s+', ' ', t.replace('-\n', ''))


def main():
    txt, out = sys.argv[1], sys.argv[2]
    from pymatgen.core import Composition
    raw = open(txt).read()
    flat = norm_text(raw)
    rows, missing = [], []
    for printed, f, sub in ENTRIES:
        ok = printed in raw or printed in flat
        if not ok:
            missing.append(printed)
        rows.append({'printed': printed.split(' is ')[0].split(' 1')[0].split(' 2')[0].strip(), 'formula_input': f,
                     'reduced_formula': Composition(f).reduced_formula, 'sublist': sub,
                     'span_found_in_text': ok, 'list_span': SPAN_HEADS[sub], 'span_source': 'Sec 3.2.1 pp 8-10'})
    red = [r['reduced_formula'] for r in rows]
    uniq = sorted(set(red))
    fp = {Composition(x).reduced_formula for x in FPMD_TABLES}
    overlap = sorted(set(red) & fp)
    rep = {'id': 'KNOWN_77', 'stated_count': 77, 'stated_span': 'Out of these 132 structures, we rediscover 77 known '
           'Li-ion conductors and as such we exclude them from FPMD investigations.',
           'rule': 'literature review by the authors (S9, decision_type literature): not computable; the list is read '
                   'from the names printed in Sec 3.2.1',
           'n_entries': len(rows), 'n_unique_reduced_formulas': len(uniq),
           'gap_vs_77': 77 - len(uniq),
           'gap_note': 'the paper counts structures, the text names formulas: polymorphs of one formula count once '
                       'here; the list cannot be completed from the deposit (no S9 records outside the 55 FPMD '
                       'materials)',
           'overlap_with_fpmd_tables': overlap,
           'overlap_note': 'formulas named as known AND listed among the 55 FPMD-studied materials (Tables 1-3): '
                           'either polymorphs or a paper inconsistency (PI4)',
           'spans_missing': missing, 'entries': rows, 'evidence_level': 'I (author literature judgement); never a key'}
    json.dump(rep, open(out, 'w'), indent=1, ensure_ascii=False)
    print(json.dumps({k: v for k, v in rep.items() if k != 'entries'}, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
