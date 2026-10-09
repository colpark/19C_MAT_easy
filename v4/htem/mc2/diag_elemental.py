#!/usr/bin/env python3
"""diag_elemental.py (v4.5 MC v2.2, addendum D1; diagnostic only): strong XRD peaks that no CO2-admissible phase explains and that
match an elemental phase CO2 excludes, per library in anion systems. Writes v4/htem/MC22_DIAG_ELEMENTAL.json and .md. No keys."""
import json, os, sys
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_mc2 as CM, co2_mc2 as CO2
ST = json.load(open(os.path.join(CM.API.HOST, 'refs', 'sticks_mc22.json')))['phases']
TOL = 0.3


def main():
    tot = Counter(); libs = {}; bysys = defaultdict(Counter)
    for r in CM.ROWS:
        if CM.SPL.get(r['id'], {}).get('split') == 'dev': continue
        s = r['system']; el = set(s.split('-'))
        if not el & CO2.ANIONS: continue
        P = CM.positions(r['id'])
        if P is None: continue
        adm = [t for p in ST if CO2.admissible(p, s) for t, _, _ in p['sticks']]
        elem = [p for p in ST if len(p['elements']) == 1 and p['elements'][0] in el and p['sticks']]
        hits = []; npk = 0
        for i, p in enumerate(P):
            pk = CM.peaks(P, i)
            if not pk: continue
            npk += 1; top = max(q['height'] for q in pk)
            for q in pk:
                if q['snr'] < 10 or q['height'] < 0.10 * top: continue
                tot['strong'] += 1
                if any(abs(q['center'] - t) <= TOL for t in adm): continue
                tot['unexplained'] += 1
                m = [{'phase': e['phase'], 'element': e['elements'][0], 'stick': round(t, 3), 'hkl': hk[0] if hk else None}
                     for e in elem for t, _, hk in sorted(e['sticks'], key=lambda x: -x[1])[:5] if abs(q['center'] - t) <= TOL]
                if m:
                    tot['elemental_match'] += 1
                    hits.append({'position': i + 1, 'two_theta': round(q['center'], 3), 'height_frac': round(q['height'] / top, 3), 'snr': round(q['snr'], 1), 'matches': m})
        if hits:
            pos = sorted({h['position'] for h in hits}); els = sorted({m['element'] for h in hits for m in h['matches']})
            libs[r['id']] = {'system': s, 'split': CM.SPL.get(r['id'], {}).get('split'), 'positions_with_xrd': npk, 'positions_affected': len(pos),
                             'share': len(pos) / npk if npk else None, 'elements': els, 'hits': hits}
            for e in els: bysys[s][e] += 1
    out = {'totals': dict(tot), 'libraries': libs, 'by_system': {k: dict(v) for k, v in bysys.items()}}
    json.dump(out, open(os.path.join(CM.HERE, 'MC22_DIAG_ELEMENTAL.json'), 'w'), indent=1)
    L = ['# Diagnostic D1: unexplained strong XRD peaks matching CO2-excluded elemental phases (no keys)', '',
         f"Strong peaks {tot['strong']}; unexplained by any CO2-admissible phase {tot['unexplained']}; matching an excluded elemental phase {tot['elemental_match']}. Libraries affected: {len(libs)}.", '',
         '## By system (libraries per matched element)', '', '| System | Element: libraries |', '|---|---|']
    for s, c in sorted(bysys.items()): L.append(f"| {s} | {', '.join(f'{e} {n}' for e, n in c.most_common())} |")
    L += ['', '## By library', '', '| Library | System | Split | Positions affected / with XRD | Elements | Example peak (2θ, height frac, SNR -> phase hkl) |', '|---|---|---|---|---|---|']
    for lid, v in sorted(libs.items(), key=lambda kv: -kv[1]['positions_affected']):
        h = max(v['hits'], key=lambda h: h['height_frac']); m = h['matches'][0]
        L.append(f"| {lid} | {v['system']} | {v['split']} | {v['positions_affected']} / {v['positions_with_xrd']} | {', '.join(v['elements'])} | {h['two_theta']}, {h['height_frac']}, {h['snr']} -> {m['phase']} {m['hkl']} |")
    open(os.path.join(CM.HERE, 'MC22_DIAG_ELEMENTAL.md'), 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L[:20]))


if __name__ == '__main__':
    main()
