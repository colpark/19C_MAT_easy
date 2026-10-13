"""Stage 4b dev split and stated errors (V5_SPEC J.4). Dev formulas: pool formulas with sha256 % 10 == 0 and at least 2 polymorphs,
in sha256 order, 120 per chemistry class (a formula counts in every class it belongs to; it is taken while any of its classes is short).
  python stage4b/dev4b.py list OUT.json                         host A: dev entries with conventional structures
  python stage4b/dev4b.py relax IN.json OUT.json SHARD NSHARD    node A2, MACE venv: FM relax (mcenv.fm_service.relax)
  python stage4b/dev4b.py gap IN_RELAXED.json OUT.json           node A2, gap venv: MEGNet PBE gap on the relaxed structures
  python stage4b/dev4b.py errors IN.json FM.json GAP.json OUT.json   host A: errors, reliability tables, m*"""
import hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..'))
QUOTA = 120
CLASSES = ('ternary_or_less', 'quaternary', 'pbe_u', 'magnetic_or_mixed_valence')
POOL = os.path.join(HERE, '..', 'data', 'stage4b', 'pool4b.json')


def dev_list(out):
    from mcenv import stage2 as S2
    P = json.load(open(POOL))
    dev = sorted([f for f, v in P.items() if v['dev'] and len(v['entries']) >= 2], key=lambda f: hashlib.sha256(f.encode()).hexdigest())
    n = {c: 0 for c in CLASSES}; rows = []
    for f in dev:
        cl = P[f]['classes']
        if not any(n[c] < QUOTA for c in cl): continue
        for c in cl: n[c] += 1
        for e in P[f]['entries'][:5]:
            rows.append(dict(id=e['id'], formula=f, classes=cl, e_form=e['e_form'], e_hull=e['e_hull'], gap=e['gap'], pbe_u=e['pbe_u'],
                             structure=S2.wbm(e['id']).as_dict()))
        if all(v >= QUOTA for v in n.values()): break
    json.dump(rows, open(out, 'w'))
    print(len({r['formula'] for r in rows}), 'dev formulas,', len(rows), 'entries; per class', n)


def relax(inp, out, shard, nshard):
    from mcenv.fm_service import relax as R
    rows = json.load(open(inp)); res = json.load(open(out)) if os.path.exists(out) else {}
    for i, r in enumerate(rows):
        if i % nshard != shard or r['id'] in res: continue
        try: res[r['id']] = R(r['structure'])
        except Exception as e: res[r['id']] = dict(error=f'{type(e).__name__}: {str(e)[:200]}')
        if len(res) % 20 == 0: json.dump(res, open(out, 'w')); print(len(res), flush=True)
    json.dump(res, open(out, 'w')); print('done', len(res), flush=True)


def gap(inp, out):
    import matgl, torch
    from pymatgen.core import Structure
    m = matgl.load_model('MEGNet-BandGap-mfi-MP-2019.4.1'); res = {}
    for mid, r in json.load(open(inp)).items():
        if 'error' in r: continue
        try: res[mid] = max(0.0, float(m.predict_structure(structure=Structure.from_dict(r['structure']), state_attr=torch.tensor([0]))))
        except Exception as e: res[mid] = None
    json.dump(res, open(out, 'w')); print('done', len(res))


def errors(inp, fmp, gapp, out):
    import numpy as np
    from mcenv import energy4 as E
    rows = json.load(open(inp)); fm = json.load(open(fmp)); gp = json.load(open(gapp))
    ok = [r for r in rows if r['id'] in fm and 'error' not in fm[r['id']]]
    vals = E.fm_values([r['id'] for r in ok], fm)
    for r in ok:
        r['fm_e_form'] = vals[r['id']]['e_form']; r['fm_e_hull'] = vals[r['id']]['e_hull']; r['fm_gap'] = gp.get(r['id'])
    byf = {}
    for r in ok: byf.setdefault(r['formula'], []).append(r)
    items = {'R': [], 'H': [], 'G': []}; pairs = []
    for f, rs in byf.items():
        for r in rs:
            items['H'].append(dict(id=r['id'], classes=r['classes'], pred=0.050 - r['fm_e_hull'], true=0.050 - r['e_hull'], pbe_u=r['pbe_u']))
            if r['fm_gap'] is not None: items['G'].append(dict(id=r['id'], classes=r['classes'], pred=r['fm_gap'] - 0.5, true=r['gap'] - 0.5, pbe_u=r['pbe_u']))
            if len(rs) >= 2:
                o = [x for x in rs if x is not r]
                items['R'].append(dict(id=r['id'], classes=r['classes'], pred=min(x['fm_e_form'] for x in o) - r['fm_e_form'],
                                       true=min(x['e_form'] for x in o) - r['e_form'], pbe_u=r['pbe_u']))
        for i in range(len(rs)):
            for j in range(i + 1, len(rs)):
                pairs.append(dict(classes=rs[i]['classes'], err=(rs[i]['fm_e_form'] - rs[j]['fm_e_form']) - (rs[i]['e_form'] - rs[j]['e_form'])))
    mae = lambda xs: round(float(np.mean(np.abs(xs))), 4) if len(xs) else None
    stats = {}
    for cl in ('all',) + tuple(sorted({c for r in ok for c in r['classes']})):
        sel = [r for r in ok if cl == 'all' or cl in r['classes']]; ps = [p for p in pairs if cl == 'all' or cl in p['classes']]
        g = [r for r in sel if r['fm_gap'] is not None]
        stats[cl] = dict(n_entries=len(sel), n_formulas=len({r['formula'] for r in sel}),
                         energy_mae=mae([r['fm_e_form'] - r['e_form'] for r in sel]), polymorph_gap_mae=mae([p['err'] for p in ps]), n_pairs=len(ps),
                         hull_mae=mae([r['fm_e_hull'] - r['e_hull'] for r in sel]), gap_mae=mae([r['fm_gap'] - r['gap'] for r in g]),
                         gap_misclass_0p5=round(sum((r['fm_gap'] > 0.5) != (r['gap'] > 0.5) for r in g) / len(g), 4) if g else None)
    stats['pbe_u_only'] = stats.get('pbe_u'); stats['non_pbe_u'] = dict(energy_mae=mae([r['fm_e_form'] - r['e_form'] for r in ok if not r['pbe_u']]),
                                                                       hull_mae=mae([r['fm_e_hull'] - r['e_hull'] for r in ok if not r['pbe_u']]))
    grids = {'R': np.round(np.arange(0, 0.5001, 0.005), 3), 'H': np.round(np.arange(0, 0.5001, 0.005), 3), 'G': np.round(np.arange(0, 3.0001, 0.05), 2)}
    bins = {'R': [0, .01, .02, .04, .06, .08, .1, .15, .2, 9], 'H': [0, .01, .02, .04, .06, .08, .1, .15, .2, 9], 'G': [0, .1, .2, .4, .6, .8, 1, 1.5, 2, 99]}
    rel = {}
    for c, it in items.items():
        a = np.array([abs(x['pred']) for x in it]); wrong = np.array([(x['pred'] > 0) != (x['true'] > 0) for x in it])
        table = [dict(lo=bins[c][i], hi=bins[c][i + 1], n=int(((a >= bins[c][i]) & (a < bins[c][i + 1])).sum()),
                      sign_error_rate=round(float(wrong[(a >= bins[c][i]) & (a < bins[c][i + 1])].mean()), 3) if ((a >= bins[c][i]) & (a < bins[c][i + 1])).any() else None)
                 for i in range(len(bins[c]) - 1)]
        mstar = None
        for t in grids[c]:
            sel = a >= t
            if sel.sum() >= 20 and wrong[sel].mean() < 0.10: mstar = float(t); break
        rel[c] = dict(n_items=len(it), overall_sign_error=round(float(wrong.mean()), 4), table=table, m_star=mstar)
    json.dump(dict(n_dev_entries=len(rows), n_fm_ok=len(ok), stats=stats, reliability=rel, entries=ok if False else None), open(out, 'w'), indent=1)
    json.dump(ok, open(out.replace('.json', '_entries.json'), 'w'))
    print(json.dumps(dict(stats=stats['all'], m_star={c: rel[c]['m_star'] for c in rel}), indent=1))


if __name__ == '__main__':
    m = sys.argv[1]
    if m == 'list': dev_list(sys.argv[2])
    elif m == 'relax': relax(sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]))
    elif m == 'gap': gap(sys.argv[2], sys.argv[3])
    else: errors(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
