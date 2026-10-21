"""V7-2: family T worlds (truth, physics and heuristics only; no FM call, no LLM).
Compounds
  paired set  scenarios 301-330: the 30 B1 bench compounds (v6/bench/WORLDS_B1.json, in_bench) in scenario order; L = B1 twin A's polymorph
              (the DFT ground state), H = twin B's; B1's library, names and count rate N
  fresh set   scenarios 331-360: from the V6-8 frame (v6/bench/selection_b1.json), excluding B1: the 6 unused E reserves (243-248), then
              K compounds in V6-8 order (the unused K reserves 231-240, then the diversity-passing compounds the full K stratum turned
              away), N = 0.7 N_q; no two T compounds share an anonymous formula with the same structure-type pair (V6-8 diversity, applied
              over the whole T set); later ones form the reserve, in order
Library: every polymorph of the frame pair (2 or 3) and two same-system distractors by the stage 4b rule (v6/bench/build_b1.py).
Samples: pre and post, each with its own hidden displacement U(-0.05, 0.05) mm, zero offset U(-0.01, 0.01) deg and crystallite size
U(100, 120) nm (the B1 range: 100 nm base, x 1.2 hold), seeded by sha256('v7-sample|scen|sample'); the same in all four cells of the quad.
Quad: cell 1 H to L (true), 2 L to L, 3 H to H, 4 L to H (false); fm_decides true on cells 1 and 4. Hold worlds per cell: 10+c displacement
+0.10 mm, 20+c zero offset +0.005 deg, 30+c size x 1.2, applied to both samples.
  python v7/T/build_T.py"""
import gzip, hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); V7 = os.path.join(HERE, '..'); V6 = os.path.join(V7, '..', 'v6')
sys.path.insert(0, V7)
import numpy as np

FRESH_N = 30
h = lambda s: hashlib.sha256(s.encode()).hexdigest()
CELLS = {1: ('H', 'L', 'SUPPORTED', True), 2: ('L', 'L', 'REFUTED', False), 3: ('H', 'H', 'REFUTED', False), 4: ('L', 'H', 'REFUTED', True)}
HOLDS = {10: dict(disp_add=0.10), 20: dict(zero_add=0.005), 30: dict(L_factor=1.2)}


def nuis(scen, sample):
    r = np.random.default_rng(int(h(f'v7-sample|{scen}|{sample}')[:16], 16))
    return dict(disp_mm=round(float(r.uniform(-0.05, 0.05)), 6), zero_deg=round(float(r.uniform(-0.01, 0.01)), 6), L_nm=round(float(r.uniform(100, 120)), 3))


def distractors(f, pool, mp, cache):
    """stage 4b rule (v6/bench/build_b1.py): first two structures by sha256 of id of other reduced formulas of the chemical system."""
    from pymatgen.core import Composition, Structure
    from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
    from mcenv import stage2 as S2
    els = {e.symbol for e in Composition(f).elements}
    cands = sorted([(h(i), i, comp) for i, comp in pool if {e.symbol for e in comp.elements} <= els and len(comp.elements) >= 2
                    and comp.reduced_formula != f], key=lambda t: t[0])
    picked, log = [], []
    for _, i, comp in cands:
        st = S2.wbm(i) if i.startswith('wbm-') else SpacegroupAnalyzer(Structure.from_dict(mp[i]['structure']), symprec=1e-3).get_conventional_standard_structure()
        sga = SpacegroupAnalyzer(st, symprec=1e-3); key = (comp.anonymized_formula, sga.get_space_group_number())
        rec = dict(id=i, formula=comp.reduced_formula, sites=len(st), spacegroup=sga.get_space_group_symbol(), sg_number=key[1])
        if len(st) > 24: rec['reason'] = 'more than 24 sites'
        elif any((p['anon'], p['sg_number']) == key for p in picked): rec['reason'] = 'same prototype as the first distractor'
        elif any(p['formula'] == rec['formula'] for p in picked): rec['reason'] = 'same formula as the first distractor'
        else: rec['anon'] = key[0]; picked.append(rec); cache[i] = st
        log.append(rec)
        if len(picked) == 2: break
    return picked, log, len(cands)


def label(st):
    from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
    return f'{st.composition.reduced_formula} ({SpacegroupAnalyzer(st, symprec=0.1).get_space_group_symbol()})'


def main():
    from pymatgen.core import Composition, Structure
    from mcenv import stage2 as S2
    from mcenv import energy4 as E
    B = json.load(open(os.path.join(V6, 'bench', 'WORLDS_B1.json')))['worlds']; byscen = {w['scen']: w for w in B}
    sel = json.load(open(os.path.join(V6, 'bench', 'selection_b1.json')))
    frame = {m['rank']: m for m in (json.loads(l) for l in open(os.path.join(V6, 'exemplar', 'features', 's1.jsonl')))}
    b1cache = json.load(open(os.path.join(V6, 'bench', 'library_structures_b1.json')))
    cache = {k: Structure.from_dict(v) for k, v in b1cache.items()}
    out = []; seen = set()
    divkey = lambda m: (m['entries'][0]['key'].split('|')[0], tuple(sorted([m['a']['key'], m['b']['key']])))
    paired = [w for w in B if w.get('in_bench')]
    for j, w in enumerate(sorted(paired, key=lambda w: w['scen'])):
        m = frame[w['rank']]; seen.add(divkey(m))
        out.append(dict(scen=301 + j, set='paired', b1_scen=w['scen'], formula=w['formula'], stratum=w['stratum'], rank=w['rank'],
                        L=w['a'], H=w['b'], polymorph_ids=w['polymorph_ids'], distractors=w['distractors'], names_by_id=w['names_by_id'],
                        N=w['N'], N_q=w['N_q'], dft=w['dft']))
    # fresh: order E reserves 243-248, K reserves 231-240, then the K-full log entries
    order = [byscen[s] for s in range(243, 249)] + [byscen[s] for s in range(231, 241)]
    fullK = [r for r in sel['log'] if r.get('note') == 'stratum K full']
    W = None; mp = None; pool = None
    fresh = []
    for item in order + fullK:
        m = frame[item['rank']]; dk = divkey(m)
        if dk in seen: continue
        seen.add(dk)
        if 'names_by_id' in item:                                   # B1 reserve: library already built at V6-9
            rec = dict(set='fresh', source=f"B1 reserve {item['scen']} ({item['stratum']})", formula=item['formula'], stratum=item['stratum'], rank=item['rank'],
                       L=item['a'], H=item['b'], polymorph_ids=item['polymorph_ids'], distractors=item['distractors'], names_by_id=item['names_by_id'],
                       N=item['N'], N_q=item['N_q'], dft=item['dft'])
        else:
            if pool is None:
                import pandas as pd
                DATA = os.path.join(V7, 'data', 'stage4')
                W = pd.read_csv(os.path.join(DATA, '2023-12-13-wbm-summary.csv.gz'))
                mpj = json.load(gzip.open(os.path.join(DATA, '2023-02-07-mp-computed-structure-entries.json.gz'), 'rt'))
                mp = {mid: mpj['entry'][k] for k, mid in mpj['material_id'].items()}
                pool = [(r.material_id, Composition(r.formula)) for r in W.itertuples(index=False)] + [(mid, Composition(v['composition'])) for mid, v in mp.items()]
            f = m['formula']; picked, log, npool = distractors(f, pool, mp, cache)
            polys = [e['id'] for e in m['entries']]
            for i in polys: cache[i] = S2.wbm(i)
            ids = polys + [p['id'] for p in picked]; names = {}
            for i in ids:
                nm = label(cache[i])
                if nm in names.values(): nm = f'{nm} [{i}]'
                names[i] = nm
            dv = E.dft_values(ids)
            if min(polys, key=lambda i: dv[i]['e_form']) != m['a']['id']: raise ValueError(f'{f}: DFT lowest is not the frame A')
            rec = dict(set='fresh', source='V6-8 frame, K stratum (turned away by the full stratum)', formula=f, stratum='K', rank=m['rank'],
                       L=m['a']['id'], H=m['b']['id'], polymorph_ids=polys, distractors=picked, names_by_id=names,
                       N=round(0.7 * item['N_q'], 4), N_q=item['N_q'], dft={names[i]: dv[i] for i in ids}, distractor_log=log, n_pool=npool)
        fresh.append(rec); print('fresh', len(fresh), rec['formula'], rec['stratum'], rec['source'], flush=True)
        if len(fresh) >= FRESH_N + 10: break
    for j, rec in enumerate(fresh):
        rec['scen'] = 331 + j; rec['slot'] = 'take' if j < FRESH_N else 'reserve'
        out.append(rec)
    for w in out:
        w['samples'] = {sm: nuis(w['scen'], sm) for sm in ('pre', 'post')}
        w['cells'] = {str(c): dict(pre=v[0], post=v[1], key=v[2], fm_decides=v[3]) for c, v in CELLS.items()}
        w.setdefault('slot', 'take')
    json.dump(dict(cells=CELLS, holds=HOLDS, worlds=out), open(os.path.join(HERE, 'WORLDS_T_draft.json'), 'w'), indent=1)
    allids = {i for w in out for i in w['names_by_id']}
    json.dump({k: v.as_dict() for k, v in sorted(cache.items()) if k in allids}, open(os.path.join(HERE, 'library_structures_T.json'), 'w'))
    print(len(out), 'T compounds;', sum(w['set'] == 'fresh' and w['slot'] == 'take' for w in out), 'fresh takes')


if __name__ == '__main__':
    main()
