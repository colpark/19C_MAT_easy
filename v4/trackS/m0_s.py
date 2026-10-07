#!/usr/bin/env python3
"""m0_s.py: Track S M0 record per dataset: verified card fields, scorer statuses and a GO or NO-GO for the pilot.

usage: m0_s.py --dataset ID [--root DIR] [--pilot pilot_separability.json ...]

Reads <root>/<ID>/{manifest.json, inventory_summary.json, readers.json, join.csv, join_summary.json, magleak.json} and the
screen card cards/<ID>.json. Writes cards_verified/<ID>.json (only fields with file evidence change, each change logged) and
m0_<ID>.json, then scores the verified card with screen_dataset.py (same scorer as the screens).

STOP (NO-GO) when any holds: a planned file is missing or failed its repository checksum, a repository part stayed unresolved,
or a manual download misses its DataCite count or size (R1); an SEM image type has no working open reader (R2 fail); no raw SEM
image or no second raw modality matched the join rules (SEM rule); every SEM image is lossy JPEG.
CHECK (GO WITH CHECKS) when any holds: R2 check, SEM images without native pixel size, the magnification test not run, a leak
(resample first), SEM images that carry no condition level or miss some levels, a separability pilot pending, failed (series for
T1 and T4 only) or measured on spatial units only (the ratio stays out of R6 and is recorded as separability_ratio_spatial).
GO otherwise.
"""
import argparse
import collections
import copy
import csv
import datetime as dt
import importlib.util
import io
import json
import os
import statistics
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
HARBOR = os.environ.get('HARBOR', '/home/aid1/Documents/harbor')
ROOT_DEFAULT = os.path.join(HARBOR, 'v4_host/trackS')
SEM_ROLES = {'sem_image', 'sem_montage_tile'}
MAP_ROLES = {'ebsd_map', 'ebsd_export', 'eds_map'}   # K2 widened SEM rule (David 2026-10-07): SEM-instrument maps with a native step count
OTHER_ROLES = {'ebsd_map', 'ebsd_export', 'ebsd_patterns', 'eds_map', 'eds_spectrum', 'optical_image', 'dic_field', 'xct', 'curve', 'indent'}


def load(path, default=None):
    return json.load(open(path)) if os.path.exists(path) else default


def scorer():
    spec = importlib.util.spec_from_file_location('screen_dataset', os.path.join(HERE, 'screen_dataset.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dataset', required=True)
    ap.add_argument('--root', default=ROOT_DEFAULT)
    ap.add_argument('--pilot', nargs='*', default=[])
    ap.add_argument('--registry', default=os.path.join(HERE, 'datasets_s.json'))
    ap.add_argument('--cards-dir', default=os.path.join(HERE, 'cards'))
    ap.add_argument('--out-dir', default=HERE)
    a = ap.parse_args(argv)
    ds = a.dataset
    d = os.path.join(a.root, ds)
    reg = {x['id']: x for x in json.load(open(a.registry))['datasets']}[ds]
    card0 = load(os.path.join(a.cards_dir, f'{ds}.json'), {})
    card = copy.deepcopy(card0)
    changes = []

    def setf(path, value, why):
        node = card
        for k in path[:-1]:
            node = node.setdefault(k, {})
        old = node.get(path[-1])
        if old != value:
            node[path[-1]] = value
            changes.append({'field': '.'.join(path), 'old': old, 'new': value, 'evidence': why})

    man = load(os.path.join(d, 'manifest.json'), {'files': {}})
    inv = load(os.path.join(d, 'inventory_summary.json'), {})
    rd = load(os.path.join(d, 'readers.json'), {})
    jsum = load(os.path.join(d, 'join_summary.json'), {})
    mag = load(os.path.join(d, 'magleak.json'), {})
    jrows = list(csv.DictReader(open(os.path.join(d, 'join.csv')))) if os.path.exists(os.path.join(d, 'join.csv')) else []

    files = man.get('files', {})
    bad = [k for k, e in files.items() if e.get('verified') is False or str(e.get('status', '')).startswith(('failed', 'HTTP', 'checksum', 'present_but'))]
    manual_ok = (man.get('manual_check') or {}).get('count_ok', True) and (man.get('manual_check') or {}).get('size_ok', True)
    plan = load(os.path.join(d, 'plan.json'), {})
    unresolved = sorted(set((man.get('unresolved_parts') or []) + (plan.get('unresolved_parts') or [])))
    planned_missing = [f['path'] for f in plan.get('files', []) if f['tier'] <= plan.get('tier_max', 1)
                       and (files.get(f['path']) or {}).get('status') not in ('downloaded', 'present')]
    r1 = bool(files) and not bad and manual_ok and not unresolved and not planned_missing
    setf(['access', 'raw_downloadable'], r1, f'{len(files)} files on host, {len(bad)} failures, {len(planned_missing)} planned files missing, '
                                              f'unresolved parts {unresolved}, manual check {man.get("manual_check")}')
    setf(['access', 'license'], reg.get('license'), 'registry (repository record)')

    r2 = rd.get('R2')
    if r2:
        setf(['readers', 'all_formats'], {'pass': True, 'fail': False}.get(r2), f'readers.json R2 {r2}')

    def native_step(r):
        for k in ('XStep', 'XSTEP', 'ebsd_step', 'pixel_size_nm'):
            try:
                if float(r.get(k) or 0) > 0 and (k != 'pixel_size_nm' or r.get('pixel_size_source') not in ('none', 'resolution_tag')):
                    return True
            except ValueError:
                pass
        return False
    sem_img = [r for r in jrows if r['role'] in SEM_ROLES]
    sem_maps = [r for r in jrows if r['role'] in MAP_ROLES and native_step(r)]
    sem = sem_img or sem_maps   # K2: SE/BSE images first; otherwise EBSD/EDS maps with a native step stand in as SEM-instrument data
    sem_modalities = sorted({r.get('modality') or r['role'] for r in sem_img + sem_maps})
    if sem_img:   # SE/BSE images are the SEM part; every other raw modality (EBSD, EDS, curves, ...) is a second modality
        other = collections.Counter(r['role'] for r in jrows if r['role'] in OTHER_ROLES)
    else:         # EBSD/EDS maps are the SEM part; the second modality is a non-map raw modality or a second SEM-instrument modality
        other = collections.Counter(r['role'] for r in jrows if r['role'] in OTHER_ROLES - MAP_ROLES - {'ebsd_patterns', 'eds_spectrum'})
        mods = collections.Counter(r.get('modality') or r['role'] for r in jrows if r['role'] in MAP_ROLES)   # the second modality needs no step
        if len(mods) >= 2:
            other.update({f'second SEM-instrument modality {m}': c for m, c in mods.items()})
    native = sum(1 for r in sem if native_step(r))
    frac = native / len(sem) if sem else 0.0
    if sem:
        setf(['calibration', 'absolute_scales'], True if frac >= 0.9 else (False if native == 0 else None),
             f'{native}/{len(sem)} SEM images carry a native pixel size')
    cfs = jsum.get('condition_fields') or []
    per_level = collections.Counter(r.get(cfs[0]) for r in sem if cfs and r.get(cfs[0]) not in (None, '')) if cfs else collections.Counter()
    semb = card.setdefault('sem', {})
    if sem:
        setf(['sem', 'image_count'], len(sem), 'join.csv SEM roles')
        if per_level:
            setf(['sem', 'images_per_condition'], int(statistics.median(per_level.values())), f'median over {cfs[0]} levels {dict(per_level)}')
        setf(['sem', 'native_metadata'], frac >= 0.9, f'{native}/{len(sem)} native')
    if mag.get('verdict'):
        v = mag['verdict'].split('+')[0]
        setf(['sem', 'magnification_fixed'], v == 'constant', f'magleak {mag["verdict"]}')
        semb['magnification_leak'] = v == 'leak'
    if inv.get('tile_layouts') and semb.get('field_selection') in (None, 'curated'):
        setf(['sem', 'field_selection'], 'montage', f'tile layout files {inv["tile_layouts"][:3]}')
    if inv.get('slide_or_document_exports'):
        semb['slide_exports'] = inv['slide_or_document_exports'][:10]

    pilots = []
    for p in a.pilot:
        res = load(p)
        pilots.append({'file': p, **{k: res.get(k) for k in ('verdict', 'pairs_separated', 'pairs', 'anova_p', 'min_between_over_within', 'optimistic_spatial_units', 'reader_freeze', 'exploratory', 'unit_type')}})
    counted = [x for x in pilots if x.get('verdict') in ('pass', 'partial', 'fail') and not x.get('exploratory')]
    replicate = [x for x in counted if not x.get('optimistic_spatial_units')]
    spatial = [x for x in counted if x.get('optimistic_spatial_units')]
    if replicate:
        best = max(replicate, key=lambda x: x.get('min_between_over_within') or 0)
        setf(['design', 'separability_ratio'], best.get('min_between_over_within'), f'pilot {best["file"]} ({best["verdict"]}, freeze {best["reader_freeze"]})')
    if spatial:
        best_s = max(spatial, key=lambda x: x.get('min_between_over_within') or 0)
        setf(['design', 'separability_ratio_spatial'], best_s.get('min_between_over_within'),
             f'spatial pilot {best_s["file"]} ({best_s["verdict"]}, units {best_s.get("unit_type")}): optimistic, not used for R6')

    # K2 provenance: an author-derived separability ratio (desk, from author values) never counts for R6
    des = card.setdefault('design', {})
    if des.get('separability_ratio') is not None and not replicate:
        des['separability_ratio_desk_A'] = des.pop('separability_ratio')
        changes.append({'field': 'design.separability_ratio -> design.separability_ratio_desk_A', 'value': des['separability_ratio_desk_A'],
                        'evidence': 'desk ratio from author values (A level); R6 ignores it (K2)'})
    reasons_stop, reasons_check = [], []
    obs = card.get('observables') or []
    series = [o_ for o_ in obs if o_.get('series')] or obs
    if series and all(str(o_.get('level', '')).upper() == 'A' for o_ in series):
        reasons_stop.append('Provenance: every keyed observable for the condition series is author-derived (A): no keys (K2)')
    if card.get('parked'):
        reasons_stop.append(f"parked: {card['parked']}")
    if not r1:
        reasons_stop.append('R1: files missing, failed checksum, unresolved repository parts, or manual count and size mismatch')
    sem_exts = {os.path.splitext(r['path'])[1].lower() for r in sem}
    if any((rd.get('by_ext', {}).get(e) or {}).get('status') == 'fail' for e in sem_exts):
        reasons_stop.append('R2: an SEM image type has no working open reader')
    if not sem:
        reasons_stop.append('SEM rule: no raw SEM image and no EBSD or EDS map with a native step matched the join rules')
    elif cfs and not per_level:
        reasons_check.append(f'no SEM image carries a level of {cfs[0]}: the condition series sits on another modality, so SEM keys need a join first')
    elif cfs and jsum.get('conditions', {}).get(cfs[0]) and len(per_level) < len(jsum['conditions'][cfs[0]]):
        reasons_check.append(f'SEM images cover {len(per_level)} of {len(jsum["conditions"][cfs[0]])} levels of {cfs[0]}')
    if not other:
        reasons_stop.append('SEM rule: no second raw modality matched the join rules')
    if sem and all(r.get('lossy') in ('True', True) for r in sem):
        reasons_stop.append('SEM rule: SEM images are lossy JPEG only')
    if r2 in (None, 'check'):
        reasons_check.append('R2 check: install the missing readers and rerun inventory_s.py readers')
    miss_share = (len(sem) - native) / len(sem) if sem else 0.0
    if sem and miss_share > 0.05:   # K3 (David's spec, round 3): flag a share of SEM-role files without native pixel metadata above 5 %
        reasons_check.append(f'K3: {len(sem) - native} of {len(sem)} SEM-role files ({miss_share:.0%}) lack native pixel metadata (> 5 %); check the join '
                             'rules for pyramid renders, thumbnails or processed copies before a scale-bar reader')
    if sem and frac < 0.9:
        reasons_check.append(f'R4: {len(sem) - native} SEM images without native pixel size (scale-bar reader or exclusion)')
    if not mag:
        reasons_check.append('magnification leak test not run (magleak_s.py)')
    elif mag.get('verdict', '').startswith('leak'):
        reasons_check.append('magnification leak: resample to one pixel size before measuring, keep scale out of T2 panels')
    elif mag.get('verdict', '').startswith(('untested', 'missing')):
        reasons_check.append(f'magnification test inconclusive ({mag["verdict"]})')
    if not counted:
        reasons_check.append('separability pilot pending (needs a validated, frozen reader)')
    elif all(x['verdict'] == 'fail' for x in counted):
        reasons_check.append('separability pilot failed: series for T1 and T4 only')
    if counted and not replicate:
        reasons_check.append('separability measured on spatial units only (fields, grains, tiles or indents): R6 stays check')
    decision = 'NO-GO' if reasons_stop else ('GO WITH CHECKS' if reasons_check else 'GO')

    card['state'] = (card0.get('state', '') + f' | verified desk fields {dt.date.today().isoformat()} from downloaded files (m0_s.py)').strip(' |')
    os.makedirs(os.path.join(a.out_dir, 'cards_verified'), exist_ok=True)
    vpath = os.path.join(a.out_dir, 'cards_verified', f'{ds}.json')
    json.dump(card, open(vpath, 'w'), indent=1)
    sd = scorer()
    R, notes, F = sd.families(card)
    buf = io.StringIO()
    with redirect_stdout(buf):
        sd.report(vpath)
    out = {'dataset': ds, 'pilot': reg.get('pilot'), 'decision': decision, 'stop': reasons_stop, 'checks': reasons_check,
           'evidence': {'files': len(files), 'failed_files': bad[:20], 'planned_missing': planned_missing[:20], 'unresolved_parts': unresolved,
                        'R2': r2, 'sem_images': len(sem), 'sem_native_fraction': frac, 'sem_missing_native_share': (len(sem) - native) / len(sem) if sem else None,
                        'second_modalities': dict(other), 'sem_modalities': sem_modalities, 'sem_images_per_level': dict(per_level), 'magleak': mag.get('verdict'),
                        'pilots': pilots, 'inventory': {k: inv.get(k) for k in ('files', 'images', 'pixel_size_sources', 'n_distinct_pixel_sizes', 'detectors', 'kv')}},
           'card_changes': changes, 'scorer': {'requirements': R, 'families': {k: list(v) for k, v in F.items()}, 'report': buf.getvalue()},
           'written': dt.datetime.now().astimezone().isoformat(timespec='seconds')}
    json.dump(out, open(os.path.join(a.out_dir, f'm0_{ds}.json'), 'w'), indent=1, default=str)
    print(f'{ds}: {decision}')
    for r in reasons_stop:
        print('  STOP', r)
    for r in reasons_check:
        print('  CHECK', r)
    print(buf.getvalue())


if __name__ == '__main__':
    main()
