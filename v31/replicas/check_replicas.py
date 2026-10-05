#!/usr/bin/env python3
"""check_replicas.py (A5): run the frozen digitize.run() on every replica (same config, same colour convention as the crop
run) and score it against the truth.
Matching: each truth marker takes the nearest detection of the same series within 6 px in x and 2 marker sizes in y.
Per matched point: e = (detected value - true value) / u (u = the digitizer's own reading uncertainty of that point).
Truth markers count as occluded (a miss there is allowed) when < 50% of their pixels are visible or their centre lies within
1.2 x the larger marker size of any other marker (another series, or a touching neighbour of the same series): overlapping
markers merge or hide each other, and a miss there costs coverage, never a wrong value.
Gate per panel (all 5 replicas pooled): >= 95% of matched points with |e| <= 2, |mean e| <= 0.5, and no miss of a visible
marker (visible >= 50%). Also reported: detections matching no truth marker (false positives), and T error in K.
Writes v31/replicas/replica_check.json and prints the per-panel table."""
import glob, json, math, os, sys
import numpy as np
V31 = '/home/aid1/Documents/harbor/v31'; HOST = '/home/aid1/Documents/harbor/v31_host'
sys.argv = [sys.argv[0]]; sys.path.insert(0, V31)
import digitize as D
cfg = json.load(open(f'{V31}/digitize_config.json'))
D.CONVENTION = {0.0: 'green', 0.005: 'black', 0.01: 'red', 0.02: 'blue', 0.04: 'magenta'}; D.CONVENTION_FROM = ['F5a', 'F5b', 'F5e']
rows = {}; detail = []
SIZES = {p: {str(float(k)): v for k, v in m['sizes'].items()} for p, m in json.load(open(f'{V31}/replicas/make_summary.json')).items()}
for tf in sorted(glob.glob(f'{V31}/replicas/truth/*.json')):
    t = json.load(open(tf)); panel, k = t['panel'], t['k']
    D.HOST = f'{HOST}/replicas/{panel}_r{k}'
    res = D.run(panel, cfg)
    r = rows.setdefault(panel, {'points': 0, 'within2': 0, 'e': [], 'miss_visible': 0, 'miss_occluded': 0, 'false_pos': 0, 'dT': [], 'status': []})
    r['status'].append(res.get('status'))
    if res.get('status') != 'ok':
        r['miss_visible'] += sum(1 for v in t['truth'].values() for q in v if q['visible'] >= 0.5); continue
    for xs, truth in t['truth'].items():
        det = list(res['series'].get(xs, [])); used = set()
        for q in truth:
            cand = [(abs(p['px'] - q['px']) + abs(p['py'] - q['py']) / 4, i) for i, p in enumerate(det)
                    if i not in used and abs(p['px'] - q['px']) <= 6 and abs(p['py'] - q['py']) <= 2 * max(p['size_px'], 6)]
            if not cand:
                # overlap with any other marker (other series, or a same-series neighbour), scaled by the larger of the two sizes
                ov = [math.hypot(q['px'] - o['px'], q['py'] - o['py']) / (1.2 * max(SIZES[panel].get(xs, 8.0), SIZES[panel].get(xo, 8.0)))
                      for xo, vo in t['truth'].items() for o in vo if o is not q]
                near_other = min(ov or [1e9]); occl = q['visible'] < 0.5 or near_other < 1
                if not occl: r['miss_visible'] += 1
                else: r['miss_occluded'] += 1
                detail.append({'panel': panel, 'k': k, 'x': xs, 'T': q['T'], 'visible': q['visible'], 'near_other_in_1.2size': near_other, 'miss': True, 'occluded_truth': occl})
                continue
            i = min(cand)[1]; used.add(i); p = det[i]
            e = (p['y'] - q['value']) / p['u']; r['points'] += 1; r['within2'] += abs(e) <= 2; r['e'].append(e); r['dT'].append(p['x'] - q['T'])
            if abs(e) > 2: detail.append({'panel': panel, 'k': k, 'x': xs, 'T': q['T'], 'true': q['value'], 'det': p['y'], 'u': p['u'], 'e': e, 'occluded_det': p.get('occluded', False), 'visible': q['visible']})
        r['false_pos'] += len(det) - len(used)
out = {}
print(f"{'panel':6} {'points':>6} {'<=2u':>7} {'bias(u)':>8} {'miss vis':>8} {'miss occ':>8} {'false+':>6} {'|dT| med K':>10}  gate")
for panel, r in rows.items():
    share = r['within2'] / max(r['points'], 1); bias = float(np.mean(r['e'])) if r['e'] else float('nan')
    ok = share >= 0.95 and abs(bias) <= 0.5 and r['miss_visible'] == 0
    out[panel] = {'points': r['points'], 'share_within_2u': share, 'bias_u': bias, 'miss_visible': r['miss_visible'], 'miss_occluded': r['miss_occluded'],
                  'false_pos': r['false_pos'], 'median_abs_dT': float(np.median(np.abs(r['dT']))) if r['dT'] else None, 'status': r['status'], 'pass': ok}
    print(f"{panel:6} {r['points']:6d} {share:7.1%} {bias:8.2f} {r['miss_visible']:8d} {r['miss_occluded']:8d} {r['false_pos']:6d} {out[panel]['median_abs_dT'] or 0:10.2f}  {'PASS' if ok else 'FAIL'}")
json.dump({'panels': out, 'detail': detail}, open(f'{V31}/replicas/replica_check.json', 'w'), indent=1)
