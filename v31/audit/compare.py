#!/usr/bin/env python3
"""compare.py (A6): compare the auditor's outputs with the builder's inputs and write audit/removals.json + audit/summary.json.
Removals are data for generate.py (claims, cells, item keys); they never change a key.
  ticks       labels must equal the config's printed ticks (config list = prefix of the auditor's list, bottom-up/left-right).
              The scale answer is compared with the config's axis type; a disagreement is resolved only by pixel evidence
              (label positions fit with linear vs log scale; the larger residual loses), else the panel's cells are removed.
  claims      quantity, samples, relation, value compared field by field (units normalised: n_H to 1e19 cm^-3, S to |S| in uV/K,
              PF to uW cm^-1 K^-2); any mismatch removes every item built on that claim. T is compared and reported only.
  cannot_tell a "yes" (decidable) removes the item.
  overlays    each flag is checked against the marker pixels (verify_flags.py); a confirmed flag on a cell that feeds a key removes
              the items using that cell; flags shown false by the pixels (A5 replicas of the panel pass) are logged, not acted on."""
import json, math, os, sys
import numpy as np
V31 = '/home/aid1/Documents/harbor/v31'; OUT = f'{V31}/audit/outputs'
sys.path.insert(0, V31)
import text_values as TV

def norm_val(q, v, unit):
    if v is None: return None
    if isinstance(v, list): return [norm_val(q, a, unit) for a in v]
    v = float(v); u = (unit or '').lower()
    if q == 'n_H' and abs(v) > 1e15: v = v / 1e19
    if q == 'S': v = abs(v); v = v * 1000 if 'mv' in u else v
    if q == 'PF' and 'mw' in u and 'm-1' in u.replace('−', '-').replace('^', ''): v = v * 10
    return v

def same(a, b):
    if a is None or b is None: return a is None and b is None
    if isinstance(a, list) or isinstance(b, list):
        return isinstance(a, list) and isinstance(b, list) and len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-9)

summary, rem = {}, {'claims': [], 'cells': [], 'item_keys': [], 'reasons': []}
# ticks
cfg = json.load(open(f'{V31}/digitize_config.json')); tk = json.load(open(f'{OUT}/ticks.json')); rows = []
for r in tk:
    c = cfg[r['panel']]; key = 'y' if r['axis'] == 'y' else 'x'; want = c.get(f'{key}_ticks'); got = (r.get('parsed') or {}).get('labels') or []
    lab_ok = want is None or [float(v) for v in got[:len(want)]] == [float(v) for v in want]
    scale_cfg = 'log' if c.get(f'{key}_log') else 'linear'; scale_got = (r.get('parsed') or {}).get('scale'); ev = None
    if scale_got != scale_cfg:
        d = json.load(open(f'{V31}/digitized/{r["panel"]}.json'))[f'{key}_cal']['pairs']; px = np.array([a for a, _ in d]); v = np.array([b for _, b in d], float); res = {}
        for name, y in (('linear', v), ('log', np.log10(v))):
            A = np.vstack([px, np.ones_like(px)]).T; cf, *_ = np.linalg.lstsq(A, y, rcond=None); res[name] = float((np.abs(A @ cf - y) / abs(cf[0])).max())
        ev = {'fit_residual_px': res, 'pixel_evidence_favours': min(res, key=res.get)}
        if ev['pixel_evidence_favours'] != scale_cfg:
            rem['cells'] += [f'{r["panel"]}:'] ; rem['reasons'].append(f'ticks {r["panel"]}: scale {scale_got} vs config {scale_cfg}, pixels favour {ev["pixel_evidence_favours"]}')
    rows.append({'panel': r['panel'], 'axis': r['axis'], 'config_labels': want, 'auditor_labels': got, 'labels_match': lab_ok, 'config_scale': scale_cfg,
                 'auditor_scale': scale_got, 'scale_match': scale_got == scale_cfg, 'scale_evidence': ev})
    if not lab_ok: rem['reasons'].append(f'ticks {r["panel"]}: labels {got} vs config {want}'); rem['cells'] += [f'{r["panel"]}:']
summary['ticks'] = rows
# claims
cl = {r['claim']: r for r in json.load(open(f'{OUT}/claims.json'))}; rows = []
for e in TV.E:
    if e['kind'] != 'claim': continue
    b = e['predicate']; a = (cl.get(e['id']) or {}).get('parsed') or {}; q = b['quantity']
    f = {'quantity': a.get('quantity') == q,
         'samples': sorted(float(x) for x in (a.get('samples') or [])) == sorted(float(x) for x in b['samples']),
         'relation': a.get('relation') == b['relation'],
         'value': same(norm_val(q, a.get('value'), a.get('unit')), norm_val(q, b.get('value'), b.get('unit')))}
    tb, ta = b.get('T'), a.get('T')
    rows.append({'claim': e['id'], 'fields_match': f, 'T_match': (tb is None and ta is None) or (tb is not None and ta is not None and [float(t) for t in ta] == [float(t) for t in tb]),
                 'builder': b, 'auditor': a, 'agree': all(f.values())})
    if not all(f.values()): rem['claims'].append(e['id']); rem['reasons'].append(f'claim {e["id"]}: mismatch in ' + ', '.join(k for k, v in f.items() if not v))
summary['claims'] = rows
# cannot tell
if os.path.exists(f'{OUT}/cannot_tell.json'):
    ct = json.load(open(f'{OUT}/cannot_tell.json')); rows = []
    for r in ct:
        d = (r.get('parsed') or {}).get('decidable'); rows.append({'item_key': r['item_key'], 'item_id': r['item_id'], 'decidable': d, 'reason': (r.get('parsed') or {}).get('reason')})
        if d != 'no': rem['item_keys'].append(r['item_key']); rem['reasons'].append(f'cannot-tell {r["item_id"]} ({r["item_key"]}): auditor says decidable={d}')
    summary['cannot_tell'] = rows
# overlays (verified flags)
if os.path.exists(f'{OUT}/overlay_flags_verified.json'):
    vf = json.load(open(f'{OUT}/overlay_flags_verified.json')); summary['overlays'] = vf
    for f in vf:
        for c in f.get('remove_cells', []): rem['cells'].append(c); rem['reasons'].append(f'overlay {f["panel"]}: confirmed flag -> cell {c}')
json.dump(rem, open(f'{V31}/audit/removals.json', 'w'), indent=1); json.dump(summary, open(f'{V31}/audit/summary.json', 'w'), indent=1)
print(json.dumps(rem, indent=1))
