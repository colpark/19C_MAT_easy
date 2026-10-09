#!/usr/bin/env python3
"""eligibility_mc2.py (v4.5 MC v2, MV1a): metadata-only eligibility of the 565 multimodal libraries per task type and system
(HTEM_MC2_RULES.md section 2), split into fully cached (census scope, VM-E03) and uncached. No fetch, no sample values.
Writes v4/htem/MC2_ELIGIBILITY.md and .json."""
import csv, json, os, sys
from collections import defaultdict
from itertools import combinations
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, HERE)
import htem_api as API
C = API.Client()
ROWS = [r for r in csv.DictReader(open(os.path.join(API.HOST, 'census', 'libraries.csv'))) if r.get('multi') == '1']
STICK_SYS = defaultdict(set)
for p in json.load(open(os.path.join(API.HOST, 'refs', 'sticks.json'))): STICK_SYS[p['system']].add(p['phase'])
ISO_PAIR = {'Mn-Se-Te-Zn'}   # rules L4: ZnSe / ZnTe zinc blende in the cached sticks


def n(r, k):
    try: return int(float(r.get(k) or 0))
    except ValueError: return 0


def cached(lid):
    lib = C.cached('library', lid); ids = (lib or {}).get('sample_ids') or []
    return bool(ids) and all(C.cached('sample', s) for s in ids)


def main():
    cache = {r['id']: cached(r['id']) for r in ROWS}
    ele = lambda r: n(r, 'has_ele') >= 10 and n(r, 'has_xrf') >= 10
    rules = {'L1': ele, 'L2': ele, 'L7': lambda r: n(r, 'has_ele') >= 10,
             'L3': lambda r: n(r, 'has_opt') >= 10, 'L8': lambda r: n(r, 'has_opt') >= 10,
             'L4': lambda r: r['system'] in ISO_PAIR and n(r, 'has_xrd') >= 10 and n(r, 'has_xrf') >= 10,
             'L6': lambda r: len(STICK_SYS.get(r['system'], ())) >= 2 and n(r, 'has_xrd') >= 10 and n(r, 'has_xrf') >= 10}
    tab = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for r in ROWS:
        for t, f in rules.items():
            if f(r): tab[t][r['system']][0 if cache[r['id']] else 1] += 1
    by_sys = defaultdict(list)
    for r in ROWS:
        if ele(r) and r.get('temp_c') not in (None, '', 'None'): by_sys[r['system']].append(r)
    for s, rs in by_sys.items():
        for a, b in combinations(rs, 2):
            if a['temp_c'] != b['temp_c']: tab['L5'][s][0 if cache[a['id']] and cache[b['id']] else 1] += 1
    out = {'n_libraries': len(ROWS), 'n_cached': sum(cache.values()), 'stick_systems': {k: sorted(v) for k, v in STICK_SYS.items()},
           'by_type': {t: {s: {'cached': v[0], 'uncached': v[1]} for s, v in sorted(d.items())} for t, d in sorted(tab.items())}}
    json.dump(out, open(os.path.join(HERE, 'MC2_ELIGIBILITY.json'), 'w'), indent=1)
    L = ['# MC v2 eligibility from metadata (MV1a; no fetch, no sample values)', '',
         f'Libraries: {len(ROWS)} multimodal, {out["n_cached"]} fully cached (census scope, VM-E03). Eligibility uses the library counters (has_ele, has_xrf, has_opt, has_xrd >= 10 positions), temp_c, and the cached COD sticks; it says nothing about whether the naive procedure fails. L5 counts library pairs.', '',
         '| Type | Systems (cached / any) | Cached | Uncached | Uncached share | Note |', '|---|---|---|---|---|---|']
    for t in ('L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7', 'L8'):
        d = tab.get(t, {}); c = sum(v[0] for v in d.values()); u = sum(v[1] for v in d.values())
        sc = sum(1 for v in d.values() if v[0]); sa = len(d); sh = u / (c + u) if c + u else 0
        note = ('mostly uncached' if sh > 0.5 else '') + ('; COD sticks limit systems' if t in ('L4', 'L6') else '')
        L.append(f'| {t} | {sc} / {sa} | {c} | {u} | {sh:.0%} | {note.strip("; ")} |')
    L += ['', '## Per system (cached / uncached)', '', '| System | ' + ' | '.join(f'L{i}' for i in range(1, 9)) + ' |', '|---' * 9 + '|']
    for s in sorted({s for d in tab.values() for s in d}):
        L.append(f'| {s} | ' + ' | '.join('{}/{}'.format(*tab[f'L{i}'][s]) if s in tab.get(f'L{i}', {}) else '-' for i in range(1, 9)) + ' |')
    open(os.path.join(HERE, 'MC2_ELIGIBILITY.md'), 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L[:16]))


if __name__ == '__main__':
    main()
