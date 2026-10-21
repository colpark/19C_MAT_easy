"""V10-3 rows: kit D validate_d on a v10 unit, as v7's H/run_H_rows.py, T/run_T_rows.py and b1/run_b1_nodft.py, on server10.
  R  graph_R_v2_nodft.json; twins s*10+1 (A, SUPPORTED) and s*10+2 (B, REFUTED) and the six hold worlds s*10+3..8
  H  graph_H_v2.json; as R
  T  graph_T.json, budget 240; the quad (cells 1-4) and three hold worlds per cell (10+c, 20+c, 30+c)
  mode selection  rows='selection' with the ceiling adapters (arm v7-ceiling: energy and hull serve DFT, free); accept = the key
  mode all        rows='all' with the FM adapters (arm v7-gold: the lab FM); accept = the key, plus CANNOT_TELL where the FM margin is
                  inside the band (R: nearest other polymorph 0.045; H: hull 0.050 +- 0.02; T: cells where the FM decides, 0.045)
Gold uses planner v3 (V6-X18). Tokens are minted on the server host (admin new, V5_STAGE=10).
  V10_URL=... V10_SSH=host|local V10_CODE=dir V10_STATE=dir python select/rows10.py MODE WORLDS_DIR OUTDIR SCEN [SCEN ...]"""
import os, sys
for _v in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ.setdefault(_v, '1')
import json
HERE = os.path.dirname(os.path.abspath(__file__)); V10 = os.path.join(HERE, '..')
sys.path.insert(0, os.path.join(V10, 'graphexec')); sys.path.insert(0, V10)
import graphexec as G
import graphexec_d as GD
import adapters_mcenv as AD

URL = os.environ.get('V10_URL', 'http://127.0.0.1:8800/call')
GRAPH = {'R': 'graph_R_v2_nodft.json', 'H': 'graph_H_v2.json', 'T': 'graph_T.json'}
HOLDS2 = [('hold_displacement_+0.10mm', 'A', 3), ('hold_zero_+0.005deg', 'A', 4), ('hold_size_x1.2', 'A', 5),
          ('hold_displacement_+0.10mm', 'B', 6), ('hold_zero_+0.005deg', 'B', 7), ('hold_size_x1.2', 'B', 8)]
CELLS = {1: ('SUPPORTED', True), 2: ('REFUTED', False), 3: ('REFUTED', False), 4: ('REFUTED', True)}
HOLDS_T = [(10, 'hold_displacement_+0.10mm'), (20, 'hold_zero_+0.005deg'), (30, 'hold_size_x1.2')]
BAND = {'R': 0.045, 'H': 0.02, 'T': 0.045}


def records(wdir):
    out = {}; fm = {}
    for fam in 'RHT':
        p = os.path.join(wdir, f'WORLDS_{fam}10.json')
        if os.path.exists(p): out.update({w['scen']: w for w in json.load(open(p))['worlds']})
    tp = os.path.join(wdir, 'TOOL_TABLES10.json')
    if os.path.exists(tp): fm = json.load(open(tp)).get('fm', {})
    return out, fm


def env(batch):
    return AD.Env(URL, os.environ.get('V10_SSH', 'local'), os.environ.get('V10_CODE', V10), os.environ.get('V10_STATE', '~/v10_state'),
                  'V5_STAGE=10', batch=batch)


def inband(W, fm, twin=None):
    t = fm.get(str(W['scen']))
    if not t: return False
    nm = W['names_by_id']; polys = [nm[i] for i in W['polymorph_ids']]
    if W['family'] == 'T': return abs(t[nm[W['L']]]['e_form'] - t[nm[W['H']]]['e_form']) < BAND['T']
    true = nm[W['a'] if twin == 'A' else W['b']]
    if W['family'] == 'H': return abs(t[true]['e_hull'] - 0.050) < BAND['H']
    return abs(min(t[o]['e_form'] for o in polys if o != true) - t[true]['e_form']) < BAND['R']


def run(mode, W, fm, out):
    fam, scen = W['family'], W['scen']
    arm = 'v7-ceiling' if mode == 'selection' else 'v7-gold'
    e = env(f'v10-3-{fam}-{mode}-{scen}'); g = GD.load(os.path.join(V10, 'spec', GRAPH[fam]))
    ex = GD.executor(g, AD.ADAPTERS, constants={'budget_min': 240.0} if fam == 'T' else None, source='gold')
    if fam == 'T':
        ib = mode == 'all' and inband(W, fm)
        def task(cell):
            key, fmd = CELLS[cell % 10]
            t = AD.make_task(e, scen * 100 + cell, arm, 1, 'T', key=key, extra=dict(planner='v2'))
            t['accept'] = [key] + (['CANNOT_TELL'] if ib and fmd else []); t['fm_decides'] = fmd
            return t
        worlds = {f'c{c}': task(c) for c in CELLS}
        holds = [(lab, f'c{c}', task(h + c)) for h, lab in HOLDS_T for c in CELLS]
    else:
        ct = {tw: mode == 'all' and inband(W, fm, tw) for tw in 'AB'}
        def task(world, tw):
            key = 'SUPPORTED' if tw == 'A' else 'REFUTED'
            t = AD.make_task(e, world, arm, 1, fam, key=key, extra=dict(planner='v2'))
            t['accept'] = [key] + (['CANNOT_TELL'] if ct[tw] else [])
            return t
        worlds = {'A': task(scen * 10 + 1, 'A'), 'B': task(scen * 10 + 2, 'B')}
        holds = [(lab, tw, task(scen * 10 + off, tw)) for lab, tw, off in HOLDS2]
    ext = None
    if mode == 'all':
        ext = dict(stratum=W['stratum'], panel_fails=False, blindfm_pairs_resolved=0, constant_prior_resolved=0,
                   source='keys differ across twins (T: across the quad), so a constant answer resolves no unit; the rule needs the identified phase(s)')
    res = GD.validate_d(g, ex, worlds, holds=holds, external=ext, rows=mode)
    for k, lg in res['logs'].items(): json.dump(lg, open(os.path.join(out, 'logs', f'{scen}_{k}.json'), 'w'), indent=1)
    summ = {}
    for k, w in worlds.items():
        b = res['logs'][f'base_{k}']
        json.dump(b, open(os.path.join(out, 'gold', f'gold_{scen}_{k}.json'), 'w'), indent=1)
        summ[k] = dict(verdict=b['verdict'], key=w['key'], accept=w['accept'], correct=b['verdict'] in w['accept'], cost_min=b['cost_min'],
                       phases=list(GD.final_phases(b, g)))
    core = [r for r in res['rows'] if r['test'] != 'faithfulness']
    r = dict(scen=scen, family=fam, mode=mode, formula=W['formula'], role=W['role'], slot=W['slot'], rows=res['rows'],
             pass_=all(x['pass'] for x in core), base=summ, tokens=e.tokens)
    json.dump(r, open(os.path.join(out, 'rows', f'{scen}.json'), 'w'), indent=1, default=str)
    return r


if __name__ == '__main__':
    mode, wdir, out = sys.argv[1], sys.argv[2], sys.argv[3]
    for d in ('gold', 'logs', 'rows'): os.makedirs(os.path.join(out, d), exist_ok=True)
    R, fm = records(wdir)
    for s in map(int, sys.argv[4:]):
        if os.path.exists(os.path.join(out, 'rows', f'{s}.json')): continue
        r = run(mode, R[s], fm, out)
        print(s, r['family'], r['role'], 'PASS' if r['pass_'] else 'FAIL', [x['test'] for x in r['rows'] if not x['pass']],
              {k: (v['verdict'], v['key'], v['cost_min']) for k, v in r['base'].items()}, flush=True)
