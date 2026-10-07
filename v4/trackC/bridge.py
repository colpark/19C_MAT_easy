#!/usr/bin/env python3
"""Addendum B bridges.

  bridge.py origin  --out B1_origin_liion.json      B1: input_origin / input_level per Li-ion funnel material
                                                     (from the unit cells' source_cif extras; AiiDA profile trackC)
  bridge.py table   --materials materials.jsonl --matches matches.jsonl --out BRIDGE_liion.csv
  bridge.py metrics --bridge BRIDGE_liion.csv --out BRIDGE_B2_results.json   (BRIDGE_METRICS_B2.md, frozen B2pre)
Experimental values are level A and never key an item (I2, I2c).
"""
import argparse, csv, json, math, sys
from collections import Counter


def origin(out):
    from aiida import load_profile, orm
    load_profile('trackC')
    rows = []
    for g, role in [('First_principles_MD_unitcells', 'xm46_fpmd_unitcell'),
                    ('finetuned_petmad_mlmd_screening_new_fast_li_conductors', '1c13_petmad')]:
        for n in orm.load_group(g).nodes:
            if not isinstance(n, orm.StructureData):
                continue
            if role == '1c13_petmad' and not n.base.extras.get('original_unitcell', None) is None:
                continue  # 1c-13 supercells point at their unit cell; tag unit cells only
            sc = n.base.extras.get('source_cif', {}) or {}
            db = (sc.get('db_name') or '').upper().replace('ICSD', 'ICSD')
            rows.append({'uuid': n.uuid, 'role': role, 'formula': n.get_formula(mode='hill_compact'),
                         'input_origin': {'db': db or 'unknown', 'id': sc.get('id'), 'license': sc.get('license'),
                                          'version': sc.get('version')},
                         'input_level': 'A' if db else 'unknown',
                         'release_eligible': False})
    c = Counter((r['role'], r['input_origin']['db']) for r in rows)
    rep = {'id': 'B1_origin_liion', 'n': len(rows), 'counts': {f'{a}|{b}': v for (a, b), v in sorted(c.items())},
           'note': 'refined experimental structures are level A inputs; ICSD/MPDS-derived items stay internal',
           'rows': rows}
    json.dump(rep, open(out, 'w'), indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k != 'rows'}, indent=1))


FAST = 1e-4   # S/cm = 0.1 mS/cm at room temperature (BRIDGE_METRICS_B2, frozen)
COLS = ['funnel_id', 'fate', 'eliminating_stage', 'pinball_sigma_1000K_mS_cm', 'fpmd_sigma_1000K_mS_cm',
        'petmad_D_or_sigma', 'outside_mlip_D', 'exp_sigma_S_cm', 'exp_T_K', 'exp_doi', 'exp_db', 'match_class',
        'evidence_level']


def table(materials, matches, out):
    M = [json.loads(l) for l in open(matches)]
    mats = {}
    for p in materials.split(','):
        for l in open(p):
            r = json.loads(l)
            mats[r.get('unitcell_uuid') or r.get('jid')] = r
    rows = []
    for m in M:
        if m['match_class'] not in ('exact', 'family'):
            continue
        for fid in m['funnel_ids']:
            r = mats.get(fid, {})
            fp = (r.get('stages', {}).get('FPMD', {}) or {}).get('1000', {})
            rows.append({'funnel_id': r.get('material_id', fid), 'fate': r.get('paper_class_A'),
                         'eliminating_stage': (r.get('fate') or {}).get('eliminating_stage'),
                         'pinball_sigma_1000K_mS_cm': None, 'fpmd_sigma_1000K_mS_cm': fp.get('sigma_H1'),
                         'petmad_D_or_sigma': None, 'outside_mlip_D': None, 'exp_sigma_S_cm': m['sigma_S_cm'],
                         'exp_T_K': m['T_K'], 'exp_doi': m['doi'], 'exp_db': m['db'], 'match_class': m['match_class'],
                         'evidence_level': 'A'})
    with open(out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    print(out, len(rows), 'matched pairs')
    return rows


def metrics(bridge_csv, matches, out):
    rows = list(csv.DictReader(open(bridge_csv)))
    M = [json.loads(l) for l in open(matches)]
    yields = Counter((m['db'], m['match_class']) for m in M)
    reasons = Counter((m['db'], m['reason']) for m in M if m['match_class'] == 'no_match')
    ex = [r for r in rows if r['match_class'] == 'exact']
    known = [m for m in M if (m['reason'] or '').startswith('computed_structure_not_deposited')]
    kf = sorted({(m['reduced'], m['db']) for m in known})
    known_fast = sorted({m['reduced'] for m in known if m['sigma_S_cm'] is not None and m['sigma_S_cm'] >= FAST})
    rep = {'match_yields': {f'{a}|{b}': v for (a, b), v in sorted(yields.items())},
           'no_match_reasons': {f'{a}|{b}': v for (a, b), v in sorted(reasons.items())},
           'M1_recall_by_gate': {'n_exact_fast': sum(float(r['exp_sigma_S_cm']) >= FAST for r in ex), 'by_gate': {},
                                 'note': 'no experimental record exact-matches a deposited funnel structure'},
           'M2_spearman': {'n_exact': len(ex), 'rho': None, 'ci95': None, 'note': 'n = 0: not computable'},
           'M3_classification': {'n': 0, 'note': 'no matched pairs; per-route tables empty'},
           'M4_temperature': {'n': 0},
           'descriptive_known77': {'formula_level_hits': len(kf), 'formulas': [k for k, _ in kf],
                                   'with_rt_sigma_ge_0.1_mS_cm': known_fast,
                                   'note': 'formula-level only (KNOWN_77 structures not deposited): the S9 literature '
                                           'exclusion meets experimental records for these formulas; not a match class'},
           'evidence_level': 'A', 'keys': 'none (I2, I2c)'}
    json.dump(rep, open(out, 'w'), indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k != 'descriptive_known77'}, indent=1))
    print('known77 formula hits', len(kf), 'fast', len(known_fast))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['origin', 'table', 'metrics'])
    ap.add_argument('--out', required=True)
    ap.add_argument('--materials')
    ap.add_argument('--matches')
    ap.add_argument('--bridge')
    a = ap.parse_args()
    if a.cmd == 'origin':
        origin(a.out)
    elif a.cmd == 'table':
        table(a.materials, a.matches, a.out)
    else:
        metrics(a.bridge, a.matches, a.out)


if __name__ == '__main__':
    main()
