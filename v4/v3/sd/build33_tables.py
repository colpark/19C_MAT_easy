#!/usr/bin/env python3
"""sd/build33_tables.py (A6): counts v3.2 vs v3.3, T4 balance per paper, and every dropped candidate/item with its reason
(from sd/<P>/items/build33_log.json) -> sd/BUILD33_TABLES.md."""
import sys as _pb_s, os as _pb_o
_pb_d = _pb_o.path.dirname(_pb_o.path.abspath(__file__))
while not _pb_o.path.exists(_pb_o.path.join(_pb_d, 'pbroot.py')) and _pb_o.path.dirname(_pb_d) != _pb_d: _pb_d = _pb_o.path.dirname(_pb_d)
_pb_s.path.insert(0, _pb_d)
from pbroot import ROOT, HOST
import json, subprocess
from collections import Counter
PS = ['P2', 'P3', 'P4', 'P5', 'P6']; F = ['t1', 't2', 't3', 't4', 't5', 't6', 't7']
L = ['# v3.3 build tables (A6)', '', '## Counts per paper and family, v3.2 (ba26fe4f) against v3.3', '', '| Paper | ' + ' | '.join(f.upper() for f in F) + ' | total |', '|---|' + '---|' * (len(F) + 1)]
for P in PS:
    old = [json.loads(l) for l in subprocess.run(['git', '-C', '/home/aid1/Documents/harbor/git/19C_MAT_easy', 'show', f'ba26fe4f:v32/sd/{P}/items/items.jsonl'], capture_output=True, text=True).stdout.splitlines() if l.strip()]
    new = [json.loads(l) for l in open(f'{ROOT}/sd/{P}/items/items.jsonl')]
    co, cn = Counter(i['family'] for i in old), Counter(i['family'] for i in new)
    L.append(f'| {P} | ' + ' | '.join(f'{co[f]} → {cn[f]}' for f in F) + f' | {len(old)} → {len(new)} |')
L += ['', '## T4 class balance per paper (target 28-38 % per class; F2 trim only removes)', '', '| Paper | consistent | contradicted | cannot tell | n | trimmed (class, source) |', '|---|---|---|---|---|---|']
for P in PS:
    lg = json.load(open(f'{ROOT}/sd/{P}/items/build33_log.json')); b = lg['t4_balance']; n = b['n']; f = b['final']
    tr = Counter((t['class'], t['source']) for t in b['trim'])
    L.append(f"| {P} | {f.get('consistent', 0)} ({f.get('consistent', 0) / n:.0%}) | {f.get('contradicted', 0)} ({f.get('contradicted', 0) / n:.0%}) | {f.get('cannot tell', 0)} ({f.get('cannot tell', 0) / n:.1%}) | {n} | "
             + ', '.join(f'{k[0]}/{k[1]} ×{v}' for k, v in tr.items()) + ' |')
L += ['', '## Dropped candidates and items, with reasons', '']
for P in PS:
    lg = json.load(open(f'{ROOT}/sd/{P}/items/build33_log.json')); L += [f'### {P}', '']
    for r in lg['t2']:
        if r.get('dropped'): L.append(f"- T2 `{r['set']}`{' ring ' + str(r['ring_x']) if r.get('ring_x') is not None else ''}: {r['dropped']}")
        else: L.append(f"- T2 `{r['set']}` ring {r['ring_x']}: kept ({len(r['classes'])} ambiguity classes)")
    for r in lg['t3']: L.append(f"- T3 `{r['id']}` {r.get('pair') or r.get('cond')}: " + (r['dropped'] if r.get('dropped') else f"margin {r.get('margin_combined_tol', r.get('inside_tol')):.2f} -> " + ('kept' if (r.get('margin_combined_tol') or 0) > 3 else 'dropped (margin <= 3)')))
    for r in lg['t5_t6']:
        if 'key' in r: L.append(f"- T5 `{r['pair']}`: key {r['key']} (A = first mechanism of the pair)" + (' (no key: comparisons disagree or none decidable -> dropped)' if r['key'] is None else '') + f" — comparisons {[(c[0], c[1], c[2]) for c in r['comparisons']]}")
        elif r.get('t6'): L.append(f"- T6 from `{r['pair']}`: {r['t6']}")
        elif r.get('dropped'): L.append(f"- T5 `{r['pair']}`: {r['dropped']}")
    for r in lg.get('t5_prior_trim', []): L.append(f"- T5 `{r['trimmed']}`: trimmed ({r['reason']})")
    t7 = lg['t7']; dr = [r for r in t7 if 'dropped' in r]; ev = [r for r in t7 if 'dropped' not in r]
    for r in dr: L.append(f"- T7 `{r['law']}`: {r['dropped']}")
    if ev:
        ok = lambda r, k: r[k] in (True, 'True')   # build33_log.json stores numpy booleans as strings (json default=str)
        g = Counter(('kept' if all(ok(r, k) for k in ('g1', 'g2', 'g3')) else 'failed ' + '+'.join(k for k in ('g1', 'g2', 'g3') if not ok(r, k))) for r in ev)
        L.append(f"- T7 `{ev[0]['law']}`: {len(ev)} held-out candidates: " + ', '.join(f'{k} {v}' for k, v in sorted(g.items())) + ' (cap 2 per held-out condition)')
        for r in ev:
            if not all(ok(r, k) for k in ('g1', 'g2', 'g3')) and len(ev) <= 20: L.append(f"  - held out {r['held_out']}: pred {float(r['pred']):.4g}, observed {float(r['observed']):.4g}, gates g1 {r['g1']}, g2 {r['g2']}, g3 {r['g3']}")
    for r in lg['t4_text']:
        if r.get('dropped'): L.append(f"- T4 text `{r['sid']}`: dropped — {r['dropped'] if isinstance(r['dropped'], str) else r['dropped'].get('why')}")
    for r in lg['t4_cannot']:
        if r.get('dropped'): L.append(f"- T4 cannot `{r['sid']}`: dropped — {r['dropped']}")
    L.append('')
open(f'{ROOT}/sd/BUILD33_TABLES.md', 'w').write('\n'.join(L) + '\n'); print('\n'.join(L[:20]))
