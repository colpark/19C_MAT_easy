#!/usr/bin/env python3
"""fidelity/heldout_run.py: the fidelity gate on the held-out sets with frozen F6 readers (freeze check first). Truth rows from
heldout_truth.json (frozen before F6), reader inputs from heldout_inputs.json (set after F6, before this run). Per set and feature type:
coverage (reads / in-scope features; refusals, calibration failures and misses count against it), share within 2u, bias in u, share of
gross errors |z| > 5. Gate (user): coverage >= 80%, >= 90% within 2u, |bias| <= 0.5u, gross <= 2%.
usage: heldout_run.py -> fidelity/heldout_results.json, fidelity/HELDOUT_RESULTS.md"""
import sys as _pb_s, os as _pb_o
_pb_d = _pb_o.path.dirname(_pb_o.path.abspath(__file__))
while not _pb_o.path.exists(_pb_o.path.join(_pb_d, 'pbroot.py')) and _pb_o.path.dirname(_pb_d) != _pb_d: _pb_d = _pb_o.path.dirname(_pb_d)
_pb_s.path.insert(0, _pb_d)
from pbroot import ROOT, HOST
import json, subprocess, sys
import numpy as np
V32 = f'{ROOT}'; sys.path.insert(0, V32)
import readers as R
chk = subprocess.run([sys.executable, f'{V32}/freeze.py', '--check'], capture_output=True, text=True); print(chk.stdout.strip())
if chk.returncode: sys.exit('freeze check failed')
T = json.load(open(f'{V32}/fidelity/heldout_truth.json')); IN = json.load(open(f'{V32}/fidelity/heldout_inputs.json'))['panels']
FT = lambda f: {'x_at_extremum': 'extremum', 'y_at_extremum': 'extremum'}.get(f, f)
def key_of(r):
    if r['paper'] == 'S039' and r['panel'] == 'F16': return f"S039|F16|{r['series']}"
    return f"{r['paper']}|{r['panel']}"
panels = {}
def get_panel(k):
    if k in panels: return panels[k]
    q = IN.get(k)
    if q is None: panels[k] = ('error', 'no inputs'); return panels[k]
    if q.get('unsupported'): panels[k] = ('unsupported', q['unsupported']); return panels[k]
    series = [{'label': lab, 'value': v['value'], 'colour': v['colour']} for lab, v in q['series'].items()]
    series += [{'label': f'other{i}', 'value': f'other{i}', 'colour': c} for i, c in enumerate(q['others'])]
    pc = {'series': series}
    for kk in ('exclude', 'y_none', 'x_none', 'right_series', 'gradient_fill', 'x_ticks', 'y_ticks', 'crop', 'merge_gap'):
        if kk in q: pc['exclude_boxes' if kk == 'exclude' else kk] = q[kk]
    try: panels[k] = ('ok', R.Panel(q['img'], pc), q)
    except R.Refused as e: panels[k] = ('refused', str(e))
    except Exception as e: panels[k] = ('calibration failed', str(e))
    return panels[k]

rows = []
for r in T:
    k = key_of(r); q = IN.get(k, {}); out = dict(r, key=k)
    if r['series'] in q.get('skip_series', []): out['status'] = 'out of scope (source mapping)'; rows.append(out); continue
    p = get_panel(k)
    if p[0] != 'ok': out['status'] = p[0]; out['why'] = p[1]; rows.append(out); continue
    P, q = p[1], p[2]; args = dict(r['args'])
    if q['kind'] == 'bar':
        if q.get('per_bar_colour') or r['series'] in q['series']:
            val = q['series'][r['series']]['value']; args = {'index': 0}
        else:
            pre = next((lab for lab in q['series'] if r['series'].startswith(lab)), None)
            if pre is None: out['status'] = 'error'; out['why'] = 'series not mapped'; rows.append(out); continue
            val = q['series'][pre]['value']
    else:
        if r['series'] not in q['series']: out['status'] = 'error'; out['why'] = 'series not mapped'; rows.append(out); continue
        val = q['series'][r['series']]['value']
    try: rd = R.read(P, {'type': r['feature'], 'series': val, 'args': args})
    except Exception as e: rd = None; out['why'] = repr(e)[:120]
    if rd is None: out['status'] = 'miss'
    else: out.update(status='read', read=float(rd[0]), u=float(rd[1]), z=float((rd[0] - r['truth']) / rd[1]) if rd[1] > 0 else float('inf'))
    rows.append(out)

summ = {}
for st in ('external', 'internal', 'all'):
    for ft in ['peak_x', 'y_at_x', 'plateau', 'extremum', 'crossing', 'bar_top', 'x_end']:
        rr = [x for x in rows if (st == 'all' or x['set'] == st) and FT(x['feature']) == ft and not x['status'].startswith('out of scope')]
        if not rr: summ[f'{st}|{ft}'] = {'n': 0, 'verdict': 'no test case'}; continue
        z = np.array([x['z'] for x in rr if x['status'] == 'read']); n = len(rr)
        from collections import Counter
        st_c = Counter(x['status'] for x in rr)
        cov = len(z) / n; w = float((np.abs(z) <= 2).mean()) if len(z) else 0.0; b = float(z.mean()) if len(z) else float('nan'); g = float((np.abs(z) > 5).mean()) if len(z) else 0.0
        acc_ok = len(z) > 0 and w >= 0.9 and abs(b) <= 0.5 and g <= 0.02
        v = 'PASS' if acc_ok and cov >= 0.8 else ('ACCURACY PASS, COVERAGE < 80%' if acc_ok else ('NO READS' if not len(z) else 'FAIL (accuracy)'))
        summ[f'{st}|{ft}'] = {'n': n, 'read': len(z), 'coverage': cov, 'within_2u': w, 'bias_u': b, 'gross_gt5': g, 'median_abs_z': float(np.median(np.abs(z))) if len(z) else None,
                              'status_counts': dict(st_c), 'verdict': v}
json.dump({'rows': rows, 'summary': summ, 'freeze': chk.stdout.strip()}, open(f'{V32}/fidelity/heldout_results.json', 'w'), indent=1, default=float)
print(f"{'set|feature':22} {'n':>4} {'read':>4} {'cov':>5} {'<=2u':>5} {'bias':>6} {'gross':>6}  verdict   (status counts)")
for k, v in summ.items():
    if v['n'] == 0: print(f'{k:22} {0:4d}  -- no test case'); continue
    print(f"{k:22} {v['n']:4d} {v['read']:4d} {v['coverage']:5.0%} {v['within_2u']:5.0%} {v['bias_u']:6.2f} {v['gross_gt5']:6.1%}  {v['verdict']}   {v['status_counts']}")
