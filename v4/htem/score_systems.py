#!/usr/bin/env python3
"""score_systems.py (stage H1): rank material systems for the pilot with the frozen rule in config.json (score section).

Stage A (library records, from census/systems.csv): eligibility n_multi >= eligible_min_multi.
Stage B (probe samples): for the top stage_b_k eligible systems by stage A, fetch probes_per_library samples per multimodal library
(first, middle and last sample id) and measure:
  spread     mean over libraries of the largest per-cation range of XRF cation fraction across the probes
  thickness  fraction of probes with a thickness value
  t_and_r    fraction of probes with both a transmission and a reflection spectrum
Score = w_multi*min(n_multi,cap)/cap + w_rep*min(n_rep,cap)/cap + w_temps*min(n_temps,cap)/cap + w_ele*[n_ele>0]
        + w_spread*min(spread/cap,1) + w_thick*thickness + w_tr*t_and_r + w_prior*[system in PRIOR_SYSTEMS.json]
PRIOR_SYSTEMS.json (or the path in $HTEM_PRIOR) must exist before this runs (a list of system keys the builder judges textbook-known, written from chemistry
knowledge only, before the census). The script refuses without it.

Picks: P1 = top score. P2 (transfer test) = the best scored system with a different anion class from P1, else the best system that
shares no cation with P1. Stage B always includes the best stage A system of every anion class, so P2 can exist when the top k are all
oxides. Writes census/ranking.csv and census/PICK.json.
usage: score_systems.py [--no-fetch]   (--no-fetch scores stage B from whatever samples are cached)
"""
import csv, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import htem_api as API
import sample_io as SIO

OUT = os.path.join(API.HOST, 'census')
S = API.CFG['score']


def stage_a(row):
    w, cap = S['weights'], S['caps']
    return (w['multi'] * min(int(row['n_multi']), cap['multi']) / cap['multi']
            + w['replicates'] * min(int(row['n_rep']), cap['replicates']) / cap['replicates']
            + w['temps'] * min(int(row['n_temps']), cap['temps']) / cap['temps']
            + w['electrical'] * (int(row['n_ele']) > 0))


def probe_ids(lib, k):
    ids = sorted(int(x) for x in (lib.get('sample_ids') or []))
    if not ids or k <= 0:
        return []
    if k == 1:
        return [ids[len(ids) // 2]]
    picks = [ids[round(i * (len(ids) - 1) / (k - 1))] for i in range(k)]
    return sorted(set(picks))


def stage_b(samples_by_lib):
    spreads, thick, tr, n = [], 0, 0, 0
    for samples in samples_by_lib:
        comps = [SIO.composition(s) for s in samples]
        comps = [c for c in comps if c]
        if len(comps) >= 2:
            els = set.intersection(*(set(c) for c in comps))
            if els:
                spreads.append(max(max(c[e] for c in comps) - min(c[e] for c in comps) for e in els))
        for s in samples:
            n += 1
            sm = SIO.summary(s)
            thick += sm['thickness']
            tr += sm['opt_T'] and sm['opt_R']
    return {'spread': round(sum(spreads) / len(spreads), 4) if spreads else 0.0,
            'thickness': round(thick / n, 3) if n else 0.0, 't_and_r': round(tr / n, 3) if n else 0.0, 'probes': n}


def score(row, b, prior):
    w, cap = S['weights'], S['caps']
    return round(stage_a(row) + w['spread'] * min(b['spread'] / cap['spread'], 1.0) + w['thickness'] * b['thickness']
                 + w['t_and_r'] * b['t_and_r'] + w['prior_flag'] * (row['system'] in prior), 4)


def pick(ranked, core=None):
    """P1 comes from the frozen stage B top k (core) only. The extra anion-class systems compete for P2 only."""
    if not ranked:
        return None, None
    pool = [r for r in ranked if core is None or r['system'] in core] or ranked
    p1 = pool[0]
    c1 = set(p1['system'].split('-')) - set(SIO.ANIONS)
    rest = [r for r in ranked if r is not p1]
    p2 = next((r for r in rest if r['anion'] != p1['anion']), None)
    if p2 is None:
        p2 = next((r for r in rest if not (set(r['system'].split('-')) - set(SIO.ANIONS)) & c1), None)
    return p1, p2


def main(argv):
    prior_path = os.environ.get('HTEM_PRIOR', os.path.join(HERE, 'PRIOR_SYSTEMS.json'))
    if not os.path.exists(prior_path):
        print('refusing: write v4/htem/PRIOR_SYSTEMS.json (textbook-known systems, from chemistry knowledge only) and freeze it first')
        return 2
    prior = set(json.load(open(prior_path)))
    rows = list(csv.DictReader(open(os.path.join(OUT, 'systems.csv'))))
    elig = [r for r in rows if int(r['n_multi']) >= S['eligible_min_multi']]
    elig.sort(key=lambda r: (-stage_a(r), r['system']))
    top = elig[:S['stage_b_k']]
    core = {r['system'] for r in top}
    for anion in sorted({r['anion'] for r in elig} - {r['anion'] for r in top}):  # so P2 can come from another anion class
        top.append(next(r for r in elig if r['anion'] == anion))
    c = API.Client()
    ranked = []
    for r in top:
        per_lib = []
        for lid in r['multi_ids'].split():
            try:
                if '--no-fetch' in argv:
                    lib = c.cached('library', lid)
                    if lib is None:
                        continue
                    ids = probe_ids(lib, S['probes_per_library'])
                    per_lib.append([x for x in (c.cached('sample', i) for i in ids) if x is not None])
                else:
                    lib = c.library(lid)
                    ids = probe_ids(lib, S['probes_per_library'])
                    got = []
                    for i in ids:
                        try:
                            got.append(c.sample(i))
                        except API.HTEMError as e:
                            print('skip sample', i, e)
                    per_lib.append(got)
            except API.HTEMError as e:
                print('skip library', lid, e)
        b = stage_b(per_lib)
        ranked.append({**{k: r[k] for k in ('system', 'anion', 'n_libs', 'n_multi', 'n_ele', 'n_full', 'n_rep', 'n_temps', 'temps')},
                       'stage_a': round(stage_a(r), 4), **b, 'prior_flag': int(r['system'] in prior),
                       'score': score(r, b, prior), 'multi_ids': r['multi_ids']})
    ranked.sort(key=lambda r: (-r['score'], r['system']))
    os.makedirs(OUT, exist_ok=True)
    if ranked:
        with open(os.path.join(OUT, 'ranking.csv'), 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(ranked[0].keys()))
            w.writeheader()
            w.writerows(ranked)
    p1, p2 = pick(ranked, core)
    out = {'P1': p1, 'P2': p2, 'eligible': len(elig), 'scored': len(ranked), 'requests': c.n_requests}
    json.dump(out, open(os.path.join(OUT, 'PICK.json'), 'w'), indent=1)
    print(json.dumps({'P1': p1 and p1['system'], 'P2': p2 and p2['system'], 'eligible': len(elig), 'scored': len(ranked)}, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
