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
    else:
        raise SystemExit(f'{a.cmd}: built in C2b')


if __name__ == '__main__':
    main()
