"""Stage 4 stated errors (V5_SPEC I.7): the FM and placebo formation-energy MAE against DFT on a WBM dev split of 500 entries (the first
WBM ids by sha256 whose reduced formula shares no element pair with any selected scenario). FM calls on non-candidates only.
  python stage4/fm_dev.py list OUT_DEV.json              host A: the dev split with structures (conventional standard cells)
  python stage4/fm_dev.py relax IN_DEV.json OUT.json     node A2, MACE venv: FM relax of every dev structure (mcenv.fm_service.relax)
  python stage4/fm_dev.py mae IN_DEV.json FM.json OUT.json   host A: MP2020 + formation energy for FM and placebo, MAE against DFT"""
import hashlib, itertools, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..'))
N_DEV = 500


def dev_list(out):
    import pandas as pd
    from pymatgen.core import Composition
    from mcenv import stage2 as S2
    sel = json.load(open(os.path.join(HERE, 'SELECTION.json')))['chosen']
    pairs = {frozenset(p) for c in sel for p in itertools.combinations([e.symbol for e in Composition(c['formula']).elements], 2)}
    W = pd.read_csv(os.path.join(HERE, '..', 'data', 'stage4', '2023-12-13-wbm-summary.csv.gz'))
    W = W.assign(h=[hashlib.sha256(i.encode()).hexdigest() for i in W.material_id]).sort_values('h')
    rows = []
    for r in W.itertuples(index=False):
        els = [e.symbol for e in Composition(r.formula).elements]
        if {frozenset(p) for p in itertools.combinations(els, 2)} & pairs: continue
        rows.append(dict(id=r.material_id, formula=Composition(r.formula).reduced_formula, e_form_dft=float(r.e_form_per_atom_mp2020_corrected),
                         structure=S2.wbm(r.material_id).as_dict()))
        if len(rows) == N_DEV: break
    json.dump(rows, open(out, 'w'))
    print(len(rows), 'dev entries')


def relax_all(inp, out):
    from mcenv.fm_service import relax
    rows = json.load(open(inp)); res = {}
    if os.path.exists(out): res = json.load(open(out))
    for i, r in enumerate(rows):
        if r['id'] in res: continue
        try: res[r['id']] = relax(r['structure'])
        except Exception as e: res[r['id']] = dict(error=f'{type(e).__name__}: {str(e)[:200]}')
        if i % 25 == 0: json.dump(res, open(out, 'w')); print(i, flush=True)
    json.dump(res, open(out, 'w')); print('done', len(res), flush=True)


def mae(inp, fmp, out):
    import numpy as np
    from mcenv import energy4 as E
    rows = json.load(open(inp)); fm = json.load(open(fmp)); per = []
    for r in rows:
        rec = dict(id=r['id'], formula=r['formula'], dft=r['e_form_dft'])
        try:
            rec['placebo'] = E.placebo_eform(r['formula'])
            if 'error' in fm.get(r['id'], {'error': 'missing'}): rec['fm_error'] = fm.get(r['id'], {}).get('error', 'missing')
            else: rec['fm'] = E.fm_values([r['id']], fm)[r['id']]['e_form']
        except Exception as e: rec['fm_error'] = f'{type(e).__name__}: {str(e)[:120]}'
        per.append(rec)
    f = [abs(p['fm'] - p['dft']) for p in per if 'fm' in p]; pl = [abs(p['placebo'] - p['dft']) for p in per if 'placebo' in p]
    res = dict(n_dev=len(rows), fm=dict(n=len(f), mae=round(float(np.mean(f)), 4), median_ae=round(float(np.median(f)), 4)),
               placebo=dict(n=len(pl), mae=round(float(np.mean(pl)), 4), median_ae=round(float(np.median(pl)), 4)),
               fm_failures=[p for p in per if 'fm_error' in p], per_entry=per)
    json.dump(res, open(out, 'w'), indent=1)
    print(json.dumps({k: res[k] for k in ('n_dev', 'fm', 'placebo')}), len(res['fm_failures']), 'FM failures')


if __name__ == '__main__':
    m = sys.argv[1]
    if m == 'list': dev_list(sys.argv[2])
    elif m == 'relax': relax_all(sys.argv[2], sys.argv[3])
    else: mae(sys.argv[2], sys.argv[3], sys.argv[4])
