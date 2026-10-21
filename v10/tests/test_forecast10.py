"""V10-3 change 2: mcenv/forecast10.py. On v7 H worlds (installed from v10/frames at a test kappa, as test_neutron_scale.py):
  1. the grid map forecast10 uses equals agent_grid's;
  2. forecast's min over the grid equals v7's predict_separation value (the in-process planner v3 grid, min over the grid per hypothesis)
     and its nominal and median equal the in-process grid values at (100 nm, 0, 0) and the median over the 27 points;
  3. a repeated call is served from the cache; hypotheses and proposal sizes are validated; the cost includes Si preparation once;
  4. a call past the timeout raises a ToolError (the agent's outcome) and the next call still works.
  cd v10 && ~/v5env/bin/python tests/test_forecast10.py"""
import os, sys, time
for _v in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ.setdefault(_v, '1')
HERE = os.path.dirname(os.path.abspath(__file__)); V10 = os.path.join(HERE, '..')
sys.path.insert(0, V10); sys.path.insert(0, os.path.join(V10, 'graphexec')); sys.path.insert(0, HERE)
import numpy as np
from mcenv import scenarios as SC
from mcenv import separation as SP
from mcenv import tools_common as TC
from mcenv import server as S
from mcenv import forecast10 as FC
import adapters_mcenv as AD
from test_neutron_scale import install

WORLDS = (4011, 4092)
PROPOSAL = [dict(radiation='xray', start=30.0, stop=37.98, step=0.02, time_per_step=2.0, optics='standard')]


def episode_view(world, k=1):
    tr = SP.world_truth(world); scen = tr['scen']; d = SC.SCEN[scen]
    from mcenv import server4 as S4
    task = dict(formula=d['composition'], library=S4.library4(scen))
    m0 = SP.DEFAULT; y0 = S.noise_rng(f"{d.get('seed_scen', scen)}", k, 0).poisson(SP.mu_truth(tr, m0)).astype(int)
    return tr, scen, task, [m0], [y0]


def v7_inprocess(tr, scen, task, ms, ys, ms_new):
    polys = AD.polymorphs(task)
    nuis = FC.nuisances(scen, polys, ms, ys); nbs, nnbs = FC.scales(tr, polys[0], AD.SIZE_GRID)
    wm, gm = AD.agent_grid(task, dict(nuis, N_by_size=nbs, Nn_by_size=nnbs))
    vals = {}
    for w in sorted(gm):
        vals.setdefault(gm[w][0], {})[gm[w][1:]] = float(SP.separation(w, ms + ms_new))
    return gm, vals


def main():
    install(0.2); ok = True
    for world in WORLDS:
        tr, scen, task, ms, ys = episode_view(world)
        ms_new = [TC.parse_measure(p) for p in PROPOSAL]
        gm, vals = v7_inprocess(tr, scen, task, ms, ys, ms_new)
        same_map = gm == FC._grid_map(AD.polymorphs(task)); ok &= same_map
        cache = {}
        t0 = time.time(); r = FC.forecast(tr, scen, task, ms, ys, dict(proposal=PROPOSAL), si_prepared=False, cache=cache); dt = time.time() - t0
        for n, o in r['expected_delta_chi2_by_hypothesis'].items():
            v = vals[n]; arr = np.array(list(v.values()))
            exp = dict(nominal_delta_chi2=round(v[FC.NOMINAL], 3), min_delta_chi2=round(float(arr.min()), 3), median_delta_chi2=round(float(np.median(arr)), 3))
            match = o == exp; ok &= match
            print(f'world {world} {n}: forecast {o}  in-process {exp}  {"ok" if match else "MISMATCH"}')
        print(f'world {world}: {len(gm)} grid worlds, grid map {"ok" if same_map else "MISMATCH"}, {dt:.1f} s, cost {r["proposal_cost_minutes"]}')
        ok &= abs(r['proposal_cost_minutes'] - ms_new[0].cost) < 1e-3
        t0 = time.time(); r2 = FC.forecast(tr, scen, task, ms, ys, dict(proposal=PROPOSAL), si_prepared=False, cache=cache)
        ok &= r2.get('cached') is True and time.time() - t0 < 5
    # validation and Si preparation
    tr, scen, task, ms, ys = episode_view(WORLDS[0]); polys = AD.polymorphs(task)
    for bad in (dict(proposal=[]), dict(proposal=PROPOSAL * 4), dict(proposal=PROPOSAL, hypotheses=['nonexistent'])):
        try: FC.parse(bad, polys); ok = False; print('validation MISSING for', bad)
        except TC.ToolError as e: print('validation ok:', str(e)[:90])
    si = [dict(PROPOSAL[0], si_standard=True)] * 2
    h, mn = FC.parse(dict(proposal=si, hypotheses=polys[:1]), polys)
    r = FC.forecast(tr, scen, task, ms, ys, dict(proposal=si, hypotheses=polys[:1]), si_prepared=False)
    exp = round(sum(m.cost for m in mn) + FC.STD_PREP, 3); ok &= r['proposal_cost_minutes'] == exp and list(r['expected_delta_chi2_by_hypothesis']) == polys[:1]
    print('Si cost', r['proposal_cost_minutes'], 'expected', exp)
    # timeout, then recovery
    FC.TIMEOUT_S = 0.01
    try: FC.forecast(tr, scen, task, ms, ys, dict(proposal=PROPOSAL), si_prepared=False); ok = False; print('timeout MISSING')
    except TC.ToolError as e: print('timeout ok:', e)
    FC.TIMEOUT_S = 300
    r = FC.forecast(tr, scen, task, ms, ys, dict(proposal=PROPOSAL), si_prepared=False); ok &= bool(r['expected_delta_chi2_by_hypothesis'])
    print('after timeout: ok')
    print('FORECAST TEST PASSED' if ok else 'FORECAST TEST FAILED')
    FC._reset_pool()
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
