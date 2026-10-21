"""B1 V6-9 step 1: the bench worlds and DFT tables (truth files only, no FM call, no LLM). For every compound of bench/selection_b1.json
(takes and reserve), in the order K takes, E takes, K reserve, E reserve, scenario 201, 202, ...:
  library   every polymorph of the frame pair (2 or 3) and two distractors by the stage 4b rule (stage4b/distractors4b.py: the first two
            structures by sha256 of their id, WBM or MP, of other reduced formulas in the chemical system, at least two elements, at
            most 24 sites, distinct prototypes and formulas)
  worlds    s*10+1 holds polymorph A (claim true), s*10+2 polymorph B; hold worlds s*10+3..8 as the exemplar (V6-4)
  N         the selection's set point (0.7 N_q)
Writes bench/WORLDS_B1.json, bench/library_structures_b1.json (structure cache, so the server host needs no WBM data) and
bench/TOOL_TABLES_B1.json (DFT only; the FM table is added after the V6-9 world freeze).
  python v6/bench/build_b1.py"""
import gzip, hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..'))
import pandas as pd
from pymatgen.core import Composition, Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from mcenv import stage2 as S2
from mcenv import energy4 as E

DATA = os.path.join(HERE, '..', 'data', 'stage4')
MAX_SITES = 24
FIRST = 201
h = lambda s: hashlib.sha256(s.encode()).hexdigest()


def label(st): return f'{st.composition.reduced_formula} ({SpacegroupAnalyzer(st, symprec=0.1).get_space_group_symbol()})'


def main():
    sel = json.load(open(os.path.join(HERE, 'selection_b1.json')))['strata']
    order = [r for s in 'KE' for r in sel[s] if r['slot'] == 'take'] + [r for s in 'KE' for r in sel[s] if r['slot'] == 'reserve']
    frame = {m['rank']: m for m in (json.loads(l) for l in open(os.path.join(HERE, '..', 'exemplar', 'features', 's1.jsonl')))}
    W = pd.read_csv(os.path.join(DATA, '2023-12-13-wbm-summary.csv.gz'))
    mp = json.load(gzip.open(os.path.join(DATA, '2023-02-07-mp-computed-structure-entries.json.gz'), 'rt'))
    mp = {mid: mp['entry'][k] for k, mid in mp['material_id'].items()}
    pool = [(r.material_id, Composition(r.formula)) for r in W.itertuples(index=False)] + [(mid, Composition(v['composition'])) for mid, v in mp.items()]
    cache, worlds = {}, []
    for j, r in enumerate(order):
        m = frame[r['rank']]; f = m['formula']; scen = FIRST + j
        els = {e.symbol for e in Composition(f).elements}
        cands = sorted([(h(i), i, comp) for i, comp in pool if {e.symbol for e in comp.elements} <= els and len(comp.elements) >= 2
                        and comp.reduced_formula != f], key=lambda t: t[0])
        picked, log = [], []
        for _, i, comp in cands:
            st = S2.wbm(i) if i.startswith('wbm-') else SpacegroupAnalyzer(Structure.from_dict(mp[i]['structure']), symprec=1e-3).get_conventional_standard_structure()
            sga = SpacegroupAnalyzer(st, symprec=1e-3); key = (comp.anonymized_formula, sga.get_space_group_number())
            rec = dict(id=i, formula=comp.reduced_formula, sites=len(st), spacegroup=sga.get_space_group_symbol(), sg_number=key[1])
            if len(st) > MAX_SITES: rec['reason'] = f'more than {MAX_SITES} sites'
            elif any((p['anon'], p['sg_number']) == key for p in picked): rec['reason'] = 'same prototype as the first distractor'
            elif any(p['formula'] == rec['formula'] for p in picked): rec['reason'] = 'same formula as the first distractor'
            else: rec['anon'] = key[0]; picked.append(rec); cache[i] = st
            log.append(rec)
            if len(picked) == 2: break
        polys = [e['id'] for e in m['entries']]
        for i in polys: cache[i] = S2.wbm(i)
        ids = polys + [p['id'] for p in picked]
        names = {}
        for i in ids:
            nm = label(cache[i])
            if nm in names.values(): nm = f'{nm} [{i}]'
            names[i] = nm
        dv = E.dft_values(ids)
        low = min(polys, key=lambda i: dv[i]['e_form'])
        if low != m['a']['id']: raise ValueError(f'{f}: DFT lowest polymorph {low} is not world A {m["a"]["id"]}')
        worlds.append(dict(scen=scen, formula=f, stratum=r['stratum'], slot=r['slot'], rank=r['rank'], a=m['a']['id'], b=m['b']['id'],
                           polymorph_ids=polys, distractors=picked, considered=log, n_pool=len(cands), N=r['N'], N_q=r['N_q'],
                           names_by_id=names, dft={names[i]: dv[i] for i in ids}))
        print(scen, r['stratum'], r['slot'], f, [names[i] for i in ids], len(log), 'considered of', len(cands), flush=True)
    json.dump(dict(first=FIRST, worlds=worlds), open(os.path.join(HERE, 'WORLDS_B1.json'), 'w'), indent=1)
    json.dump({k: v.as_dict() for k, v in sorted(cache.items())}, open(os.path.join(HERE, 'library_structures_b1.json'), 'w'))
    T = dict(scenarios=[str(w['scen']) for w in worlds], dft={str(w['scen']): w['dft'] for w in worlds})
    json.dump(T, open(os.path.join(HERE, 'TOOL_TABLES_B1.json'), 'w'), indent=1, sort_keys=True)


if __name__ == '__main__':
    main()
