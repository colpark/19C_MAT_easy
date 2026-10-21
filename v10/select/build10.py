"""V10-3: the v10 worlds and DFT tables from a selection (truth only, no FM call, no LLM), in v7's formats so mcenv.bench6.setup (R) and
mcenv.family7.setup_H / setup_T (H, T) install them (mcenv/family10.py).
  scenarios  R 501.., H 601.., T 701.. (dev worlds: 591.., 691.., 791..), in the order bench, controls, bench reserves, control reserves,
             each in hash (rank) order
  library    every polymorph of the formula (s1.jsonl entries) and two same-system distractors by the stage 4b rule (v7/T/build_T.py)
  names      the B1 label rule ("formula (space group)", "[id]" on a repeat), as the pilot's qual10.names_of
  nuisances  R, H: seed_scen 'v10|FAM|formula' (scenarios.hidden); T: samples seeded 'v10-sample|formula|sample' (qual10.t_nuis)
  N          the unit's final N0 (bench) or 0.7 N_q (controls), from the selection
paired-v7 compounds: the library and names must equal the v7 world's (frames/WORLDS_B1.json, WORLDS_H.json, WORLDS_T.json); a mismatch stops.
Writes OUT/WORLDS_R10.json, WORLDS_H10.json, WORLDS_T10.json, library_structures10.json, TOOL_TABLES10.json (DFT only; FM after the freeze).
  python select/build10.py SELECTION.json OUT_DIR [dev]"""
import gzip, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); V10 = os.path.join(HERE, '..')
sys.path.insert(0, V10); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(V10, 'pilot'))
import build_T as BT
import qual10 as Q

FIRST = dict(R=501, H=601, T=701); DEV = dict(R=591, H=691, T=791)
CELLS = BT.CELLS; HOLDS = BT.HOLDS


def order(sel, fam):
    rows = [(r, 'take') for r in sel['bench'][fam]] + [(r, 'control') for r in sel['controls'][fam]]
    rb = sel.get('reserves', {}).get('bench', {})
    res = rb.get(fam, []) if fam != 'H' else rb.get('H_M', []) + rb.get('H_E', [])
    rows += [(r, 'reserve') for r in sorted(res, key=lambda r: r['rank'])]
    rows += [(r, 'control_reserve') for r in sel.get('reserves', {}).get('controls', {}).get(fam, [])]
    return rows


def v7_worlds():
    F = os.path.join(V10, 'frames'); out = {}
    for fam, f in (('R', 'WORLDS_B1.json'), ('H', 'WORLDS_H.json'), ('T', 'WORLDS_T.json')):
        for w in json.load(open(os.path.join(F, f)))['worlds']:
            if fam == 'R' and not w.get('in_bench'): continue
            out.setdefault((fam, w['formula']), w)
    return out


def main(sel_path, out_dir, dev=False):
    import pandas as pd
    from pymatgen.core import Composition
    from mcenv import stage2 as S2
    from mcenv import energy4 as E
    sel = json.load(open(sel_path)); os.makedirs(out_dir, exist_ok=True)
    DATA = os.path.join(V10, 'data', 'stage4')
    W = pd.read_csv(os.path.join(DATA, '2023-12-13-wbm-summary.csv.gz'))
    mpj = json.load(gzip.open(os.path.join(DATA, '2023-02-07-mp-computed-structure-entries.json.gz'), 'rt'))
    mp = {mid: mpj['entry'][k] for k, mid in mpj['material_id'].items()}
    pool = [(r.material_id, Composition(r.formula)) for r in W.itertuples(index=False)] + [(mid, Composition(v['composition'])) for mid, v in mp.items()]
    V7 = v7_worlds(); cache = {}; tables = dict(scenarios=[], dft={}); first = DEV if dev else FIRST
    for fam in ('R', 'H', 'T'):
        worlds = []
        for j, (r, slot) in enumerate(order(sel, fam)):
            s = first[fam] + j; f = r['formula']
            picked, log, npool = BT.distractors(f, pool, mp, cache)
            polys = r['poly_ids']
            for i in polys: cache[i] = S2.wbm(i)
            unit = dict(poly_ids=polys)
            names = Q.names_of(unit)                                       # polymorph names, the pilot's rule
            for p in picked:
                nm = BT.label(cache[p['id']])
                if nm in names.values(): nm = f"{nm} [{p['id']}]"
                names[p['id']] = nm
            ids = polys + [p['id'] for p in picked]
            dv = E.dft_values(ids)
            rec = dict(scen=s, formula=f, family=fam, slot=slot, role=r['role'], rank=r['rank'], flag=r['flag'], seed_scen=r['seed_scen'],
                       polymorph_ids=polys, distractors=picked, distractor_log=log, n_pool=npool, names_by_id=names, N=r['N'],
                       kind=r.get('kind'), plan=r.get('plan'), N_rec=r.get('N_rec'), N_plan=r.get('N_plan'), N_q=r.get('N_q'),
                       dft={names[i]: dv[i] for i in ids})
            if fam == 'T':
                rec.update(L=r['L'], H=r['H'], set='v10', stratum=r['flag'], budget=240.0,
                           samples={sm: Q.t_nuis(f, sm) for sm in ('pre', 'post')},
                           cells={str(c): dict(pre=v[0], post=v[1], key=v[2], fm_decides=v[3]) for c, v in CELLS.items()})
                if min(polys, key=lambda i: dv[i]['e_form']) != r['L']: raise ValueError(f'{f}: DFT lowest is not L')
            else:
                rec.update(a=r['A'], b=r['B'], stratum=r['flag'])
                if fam == 'R' and min(polys, key=lambda i: dv[i]['e_form']) != r['A']: raise ValueError(f'{f}: DFT lowest is not A')
                if fam == 'H':
                    rec.update(type=r['htype'], panel=r['flag'])
                    if not (dv[r['A']]['e_hull'] <= 0.03 + 1e-9 and dv[r['B']]['e_hull'] >= 0.07 - 1e-9): raise ValueError(f'{f}: twin hulls outside the bars')
            v7 = V7.get((fam, f))
            if r['flag'] == 'paired-v7' and v7 is not None:
                if v7['names_by_id'] != names or [d['id'] for d in v7['distractors']] != [p['id'] for p in picked]:
                    raise ValueError(f'{fam} {f}: library differs from the v7 world {v7["scen"]}')
                rec['v7_scen'] = v7['scen']
            worlds.append(rec); tables['scenarios'].append(str(s)); tables['dft'][str(s)] = rec['dft']
            print(fam, s, slot, f, r['flag'], [names[i] for i in ids], 'N', round(r['N'], 4), flush=True)
        json.dump(dict(first=first[fam], family=fam, kappa=sel['kappa'], worlds=worlds, status='draft: rows not yet run; not frozen'),
                  open(os.path.join(out_dir, f'WORLDS_{fam}10.json'), 'w'), indent=1)
    allids = sorted(cache)
    json.dump({k: cache[k].as_dict() for k in allids}, open(os.path.join(out_dir, 'library_structures10.json'), 'w'))
    json.dump(tables, open(os.path.join(out_dir, 'TOOL_TABLES10.json'), 'w'), indent=1, sort_keys=True)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], dev=len(sys.argv) > 3 and sys.argv[3] == 'dev')
