#!/usr/bin/env python3
"""join_s.py: map every inventoried file to its role, entity and condition with explicit rules (Track S, skill M0 sample IDs).

usage: join_s.py --dataset ID [--root DIR] [--rules joinrules/ID.json]

Rules file (JSON, written by the builder after reading the deposit README and descriptor, frozen before use):
  {"dataset": "...",
   "rules": [{"name": "...", "path_regex": "...(?P<field>...)...", "role": "sem_image", "set": {"field": "literal"}}, ...],
   "maps": {"field": {"value": {"other_field": "...", ...}}},       # value lookups, for example track -> laser case
   "condition_fields": ["case"], "order": {"case": ["1.1", "1.2", ...]},   # order is optional, numeric fields sort by value
   "unit_field": "track",                                             # replicate unit (specimen, track, grain, field, tile)
   "unit_type": "track"}
The first matching rule wins. Unmatched files stay in the table with role "unmatched" and the summary lists them, so nothing
drops silently. Roles: sem_image, sem_montage_tile, ebsd_map, ebsd_export, ebsd_patterns, eds_map, eds_spectrum, optical_image,
dic_field, xct, curve, indent, tile_layout, metadata, document, other.
Writes <root>/<ID>/join.csv and join_summary.json (with the sha256 of the rules file for LOG.md).
"""
import argparse
import collections
import csv
import hashlib
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
HARBOR = os.environ.get('HARBOR', '/home/aid1/Documents/harbor')
ROOT_DEFAULT = os.path.join(HARBOR, 'v4_host/trackS')
CARRY = ('pixel_size_nm', 'pixel_size_source', 'hfw_um', 'magnification', 'detector', 'kv', 'width', 'height', 'bits', 'lossy', 'XStep', 'XSTEP', 'ebsd_step')   # K2: native EBSD steps


BSE_DET = ('cbs', 'bse', 'bsed', 'vcd', 'abs', 'cbs detector', 'rbse', 'aes', 'qbsd', 'asb', 'esb')


def modality_of(rec):
    """K2: modality tag per file (SE, BSE, EBSD, EDS, optical, curve, indentation, DIC; '' for documents and other). A rule's
    'set': {'modality': ...} wins; SEM images use the 'mode' field, then the detector tag (ETD, TLD, InLens -> SE; CBS, BSED, vCD -> BSE)."""
    role = rec.get('role', '')
    if role in ('sem_image', 'sem_montage_tile'):
        mode = str(rec.get('mode') or '').upper()
        if mode in ('SE', 'BSE'):
            return mode
        det = str(rec.get('detector') or '').lower()
        if any(b in det for b in BSE_DET):
            return 'BSE'
        return 'SE' if det else 'SEM'
    return {'ebsd_map': 'EBSD', 'ebsd_export': 'EBSD', 'ebsd_patterns': 'EBSD', 'eds_map': 'EDS', 'eds_spectrum': 'EDS', 'optical_image': 'optical',
            'curve': 'curve', 'indent': 'indentation', 'dic_field': 'DIC', 'xct': 'XCT'}.get(role, '')


def apply_rules(rows, spec):
    rules = [dict(r, _re=re.compile(r['path_regex'], re.I)) for r in spec.get('rules', [])]
    maps = spec.get('maps', {})
    out = []
    for row in rows:
        rec = {'path': row['path'], 'ext': row['ext'], 'role': 'unmatched', 'rule': None}
        for r in rules:
            m = r['_re'].search(row['path'])
            if m:
                rec['role'] = r.get('role', 'other')
                rec['rule'] = r.get('name')
                rec.update({k: v for k, v in m.groupdict().items() if v is not None})
                rec.update(r.get('set', {}))
                break
        for field, table in maps.items():
            key = rec.get(field)
            if key is not None and str(key) in table:
                rec.update(table[str(key)])
        for k in CARRY:
            if row.get(k) is not None:
                rec[k] = row[k]
        rec.setdefault('modality', modality_of(rec))
        out.append(rec)
    return out


def summarize(recs, spec):
    roles = collections.Counter(r['role'] for r in recs)
    cfs = spec.get('condition_fields', [])
    unit = spec.get('unit_field')
    per = {}
    for cf in cfs:
        levels = collections.defaultdict(lambda: {'files': 0, 'units': set(), 'roles': collections.Counter()})
        for r in recs:
            if r.get(cf) is None:
                continue
            lv = levels[str(r[cf])]
            lv['files'] += 1
            lv['roles'][r['role']] += 1
            if unit and r.get(unit) is not None:
                lv['units'].add(str(r[unit]))
        per[cf] = {k: {'files': v['files'], 'units': len(v['units']), 'roles': dict(v['roles'])} for k, v in sorted(levels.items())}
    return {'roles': dict(roles), 'unmatched_examples': [r['path'] for r in recs if r['role'] == 'unmatched'][:40],
            'conditions': per, 'condition_fields': cfs, 'unit_field': unit, 'unit_type': spec.get('unit_type')}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dataset', required=True)
    ap.add_argument('--root', default=ROOT_DEFAULT)
    ap.add_argument('--rules')
    a = ap.parse_args(argv)
    rules_path = a.rules or os.path.join(HERE, 'joinrules', f'{a.dataset}.json')
    spec = json.load(open(rules_path))
    rows = [json.loads(line) for line in open(os.path.join(a.root, a.dataset, 'inventory.jsonl'))]
    recs = apply_rules(rows, spec)
    fields = ['path', 'ext', 'role', 'rule'] + sorted({k for r in recs for k in r} - {'path', 'ext', 'role', 'rule'})
    with open(os.path.join(a.root, a.dataset, 'join.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in recs:
            w.writerow(r)
    s = summarize(recs, spec)
    s.update({'dataset': a.dataset, 'rules_file': rules_path, 'rules_sha256': hashlib.sha256(open(rules_path, 'rb').read()).hexdigest()})
    json.dump(s, open(os.path.join(a.root, a.dataset, 'join_summary.json'), 'w'), indent=1)
    print(json.dumps({k: s[k] for k in ('roles', 'condition_fields', 'unit_field')}, indent=0))
    for cf, levels in s['conditions'].items():
        print(f'{cf}: ' + '; '.join(f'{k} files {v["files"]} units {v["units"]}' for k, v in levels.items()))
    if s['roles'].get('unmatched'):
        print(f"UNMATCHED {s['roles']['unmatched']} files, e.g. {s['unmatched_examples'][:5]}")


if __name__ == '__main__':
    main()
