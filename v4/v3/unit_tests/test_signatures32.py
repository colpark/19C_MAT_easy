#!/usr/bin/env python3
"""unit tests for the papers 2-6 signature tables: every table validates; every entry predicts >= 1 observable; for every paper with
pairs, >= 1 pair of remaining (audit-surviving) entries is decidable on a shared observable; removed entries are not used."""
import json, os, sys, itertools
V32 = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, V32)
import signatures as SG
fails = []
def check(n, c):
    print(('ok   ' if c else 'FAIL ') + n)
    if not c: fails.append(n)
for k in ('s039', 's098', 't042', 't051', 's048'):
    t = json.load(open(f'{V32}/papers/{k}/signatures.json')); rem = set(json.load(open(f'{V32}/papers/{k}/audit/removals.json')).get('signatures', []))
    check(f'{k}: table validates', SG.validate(t) == [])
    check(f'{k}: every entry predicts >= 1 observable', all(e['predicts'] for e in t.values()))
    live = {s: e for s, e in t.items() if s not in rem}
    dec = [(a, b, o) for (a, ea), (b, eb) in itertools.combinations(live.items(), 2) for o in set(ea['predicts']) & set(eb['predicts']) if SG.decidable(ea, eb, o)]
    check(f'{k}: >= 1 decidable pair among audit-surviving entries ({len(dec)})', len(dec) >= 1)
    check(f'{k}: prior ranks are 1 or 2', all(e['prior_rank'] in (1, 2) for e in t.values()))
print(f'\n{len(fails)} failures' if fails else '\nall passed'); sys.exit(1 if fails else 0)
