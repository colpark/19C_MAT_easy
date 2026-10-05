#!/usr/bin/env python3
"""score_shortlist.py (Phase 4): score candidate papers from their provisional node graphs (selection/graphs/<key>.json) by code, then
pick the five-paper set that meets the coverage conditions. Law classes come from provenance.classify_law on each provisional graph.
Per paper (must hold): CC BY (license span), >= 3 conditions on the same samples, >= 2 instruments with M panels on those samples,
>= 3 of 7 families feasible, key panels line/scatter/bar.
Family feasibility on the provisional graph: T1 an M line/scatter/bar panel; T2 a plot panel with a legend over >= 3 conditions (image
variant: micrographs with scale bars at >= 3 conditions); T3 a law classed independent or agreement with M inputs and target; T4 an M
panel (claims) or a definition law (recompute audit); T5 a T5 pair with an observable on an M panel; T6 a T5 pair with >= 2 observables;
T7 a law classed fit or a T7 candidate.
Set coverage: >= 3 publishers, >= 3 domains, >= 3 distinct T3 law families with >= 20 T3 opportunities in total, T5 feasible in >= 2
papers, T7 in >= 2, micrographs with scale bars at >= 3 conditions in >= 3 papers. Writes selection/SHORTLIST.md and shortlist.json."""
import itertools, json, glob, os, sys
V32 = '/home/aid1/Documents/harbor/v32'; sys.path.insert(0, V32)
import provenance as P
SEL = f'{V32}/selection'; PREFERRED = ['S098', 'S039', 'T051', 'T042']   # the user's candidates that passed the screen
lic = {r['key']: r for r in json.load(open(f'{SEL}/license_pool.json'))}
rows = {}
for f in sorted(glob.glob(f'{SEL}/graphs/*.json')):
    gj = json.load(open(f)); k = gj['key']; nodes = []
    for n in gj['nodes']:
        nd = dict(n); nd.setdefault('evidence', {'kind': 'default', 'text': 'provisional'})
        if nd['evidence'].get('kind') not in ('span', 'default'): nd['evidence'] = {'kind': 'default', 'text': str(nd['evidence'])}
        if nd['level'] == 'A' and not nd.get('computed_from') and not nd.get('params'): nd['params'] = [{'name': 'provisional', 'kind': 'fit', 'fit_on': []}]
        nodes.append(nd)
    err = None
    try: g = P.Graph(nodes)
    except P.ProvenanceError as e: g, err = None, str(e)
    laws = []
    for L_ in gj.get('candidate_laws', []):
        if g is None: laws.append(dict(L_, law_class='graph error', mode=None)); continue
        try:
            cls, mode, why = P.classify_law({'id': L_['id'], 'inputs': L_['inputs'], 'target': L_['target'], 'params': L_.get('params', []), 'agreement': L_.get('agreement', False)}, g)
        except P.ProvenanceError as e: cls, mode, why = 'error', None, str(e)
        laws.append(dict(L_, law_class=cls, mode=mode, why=why))
    lv = {n['id']: n for n in nodes}
    plot = lambda n: n.get('chart_type') in ('line', 'scatter', 'bar')
    M_plot = [n for n in nodes if n['level'] == 'M' and n.get('panel') and plot(n)]
    A_pan = [n for n in nodes if n['level'] == 'A' and n.get('panel')]
    instr = {n.get('instrument') for n in nodes if n['level'] == 'M' and n.get('panel') and n.get('instrument')}
    t3 = [l for l in laws if l['law_class'] in ('independent', 'agreement') and all(lv.get(i, {}).get('level') == 'M' for i in l['inputs']) and lv.get(l['target'], {}).get('level') == 'M']
    defs = [l for l in laws if l['law_class'] == 'definition']; fits = [l for l in laws if l['law_class'] == 'fit']
    ncond = len(gj['conditions'].get('values') or [])
    micro = gj.get('micrograph_series', {}).get('conditions_with_scale_bar', 0) or 0
    t5 = [p for p in gj.get('t5_pairs', []) if any(lv.get(next((n['id'] for n in nodes if n.get('panel') == o['panel']), ''), {}).get('level') == 'M' for o in p['observables'])]
    fam = {'T1': bool(M_plot), 'T2': any(plot(n) and len(n.get('conditions_shown') or []) >= 3 for n in nodes if n.get('panel')) or micro >= 3,
           'T3': bool(t3), 'T4': bool(M_plot) or bool(defs), 'T5': bool(t5), 'T6': any(len(p['observables']) >= 2 for p in t5), 'T7': bool(fits) or bool(gj.get('t7_candidates'))}
    kc = gj.get('key_panel_chart_types', {})
    cond = {'CC BY': lic.get(k, {}).get('license_class') == 'CC BY', '>=3 conditions': ncond >= 3, '>=2 instruments (M panels)': len(instr) >= 2,
            '>=3 families': sum(fam.values()) >= 3, 'key panels line/scatter/bar': (kc.get('line', 0) + kc.get('scatter', 0) + kc.get('bar', 0)) >= max(1, kc.get('box', 0))}
    rows[k] = {'doi': gj['doi'], 'publisher': gj.get('publisher'), 'domain': gj.get('domain'), 'graph_error': err, 'conditions': ncond, 'instruments': sorted(i for i in instr if i),
               'M_plot_panels': [n['panel'] for n in M_plot], 'A_panels': [n['panel'] for n in A_pan], 'laws': [{k2: l.get(k2) for k2 in ('id', 'family', 'law_class', 'mode', 'opportunities', 'why')} for l in laws],
               't3_families': sorted({l.get('family') for l in t3}), 't3_opportunities': sum(l.get('opportunities') or 0 for l in t3),
               'families': fam, 'n_families': sum(fam.values()), 'conditions_met': cond, 'eligible': all(cond.values()),
               'micrograph_conditions_with_scale_bar': micro, 't5_pairs': [p['mechanisms'] for p in t5], 'chart_types': kc, 'risks': gj.get('risks', [])}
def coverage(keys):
    R = [rows[k] for k in keys]
    fams = set().union(*[set(r['t3_families']) for r in R])
    c = {'>=3 publishers': len({r['publisher'] for r in R}) >= 3, '>=3 domains': len({r['domain'] for r in R}) >= 3,
         '>=3 T3 law families': len(fams) >= 3, '>=20 T3 opportunities': sum(r['t3_opportunities'] for r in R) >= 20,
         'T5 in >=2 papers': sum(r['families']['T5'] for r in R) >= 2, 'T7 in >=2 papers': sum(r['families']['T7'] for r in R) >= 2,
         'micrographs (scale bars, >=3 conditions) in >=3 papers': sum(r['micrograph_conditions_with_scale_bar'] >= 3 for r in R) >= 3}
    return c, sorted(fams)
elig = [k for k, r in rows.items() if r['eligible']]
best = None
for combo in itertools.combinations(elig, min(5, len(elig))):
    c, fams = coverage(combo); score = (sum(c.values()), sum(k in PREFERRED for k in combo), sum(rows[k]['t3_opportunities'] for k in combo))
    if best is None or score > best[0]: best = (score, combo, c, fams)
out = {'papers': rows, 'eligible': elig, 'chosen': list(best[1]) if best else [], 'coverage': best[2] if best else {}, 't3_families': best[3] if best else [],
       'alternates': sorted([k for k in elig if not best or k not in best[1]], key=lambda k: -rows[k]['n_families'])[:3]}
json.dump(out, open(f'{SEL}/shortlist.json', 'w'), indent=1)
md = ['# Phase 4 shortlist (scored by code from provisional graphs)\n', '| key | DOI | publisher | domain | cond. | M plot panels | A panels | micrograph cond. w/ bar | T3 laws (class) | T5 pairs | families | eligible |', '|---|---|---|---|---|---|---|---|---|---|---|---|']
for k, r in rows.items():
    md.append(f"| {k} | {r['doi']} | {r['publisher']} | {r['domain']} | {r['conditions']} | {len(r['M_plot_panels'])} | {len(r['A_panels'])} | {r['micrograph_conditions_with_scale_bar']} | "
              + '; '.join(f"{l['id']} ({l['law_class']}{'/' + l['mode'] if l['mode'] else ''}, {l['opportunities']})" for l in r['laws']) + f" | {len(r['t5_pairs'])} | "
              + ', '.join(f for f, v in r['families'].items() if v) + f" | {'yes' if r['eligible'] else 'no: ' + ', '.join(c for c, v in r['conditions_met'].items() if not v)} |")
md += [f"\nChosen: {out['chosen']}; alternates: {out['alternates']}\n", '| coverage condition | met |', '|---|---|'] + [f'| {c} | {"yes" if v else "NO"} |' for c, v in out['coverage'].items()]
md.append(f"\nT3 law families in the chosen set: {out['t3_families']}")
open(f'{SEL}/SHORTLIST.md', 'w').write('\n'.join(md) + '\n'); print('\n'.join(md))
