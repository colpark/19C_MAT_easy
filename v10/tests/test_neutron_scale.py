"""V10-0 step 5: the planner's neutron D equals the grader's D.

For three worlds (v7 H twins, installed from v10/frames with a test kappa), the lab's grader D of the neutron pattern alone
(separation.separation on the world's truth) is compared with planner v3's D for the same hypothesis: agent_grid built from the count
scales a planner reads through simulate (X-ray and, since V10-0, neutron), the grid world that holds the world's phase at its size.
Neutron data carry no displacement or zero offset, so every grid displacement and zero offset gives the same neutron D; the test takes
the minimum over them, as worst_case does. Also checks that the neutron D is linear in kappa (so V10-1 can solve kappa continuously).
  cd v10 && ~/v5env/bin/python tests/test_neutron_scale.py"""
import os, sys
for _v in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ.setdefault(_v, '1')
HERE = os.path.dirname(os.path.abspath(__file__)); V10 = os.path.join(HERE, '..')
sys.path.insert(0, V10); sys.path.insert(0, os.path.join(V10, 'graphexec'))
from mcenv import scenarios as SC
from mcenv import separation as SP
from mcenv import tools_common as TC
from mcenv import family7 as F7
import adapters_mcenv as AD

KAPPA_TEST = 0.2
WORLDS = (4011, 4022, 4091)          # H 401 twin A, 402 twin B, 409 twin A


def install(kappa):
    S = F7.setup_H(os.path.join(V10, 'frames', 'WORLDS_H.json'), os.path.join(V10, 'frames', 'library_structures_H.json'))
    SC.SCEN.update(S)
    for s, d in S.items():
        Nn, bgn = SC.neutron_scale(d['N'], kappa)
        SC.TUNE[s] = dict(L=100.0, N=d['N'], bg=20.0, Nn=Nn, bgn=bgn)
    SC.WORLD_SCEN.update({w: s for s, d in S.items() for w in d['worlds']})
    return S


def planner_neutron_D(world):
    scen = SC.WORLD_SCEN[world]; d = SC.SCEN[scen]; tr = SP.world_truth(world)
    from mcenv import server4 as S4
    task = dict(formula=d['composition'], library=S4.library4(scen))            # the library exactly as status shows it
    n0 = AD.polymorphs(task)[0]
    sim = lambda rad, L: float(max(TC.simulate(tr, dict(spec=dict(phases=[dict(name=n0, weight=1.0)], radiation=rad, start=10, stop=70, step=0.04,
                                                                  time_per_step=0.5, optics='standard', size_nm=L)))['expected_counts']))
    nuis = dict(background_cps=20.0, N_by_size={L: sim('xray', L) for L in AD.SIZE_GRID}, Nn_by_size={L: sim('neutron', L) for L in AD.SIZE_GRID})
    wm, gm = AD.agent_grid(task, nuis)
    phase = d['worlds'][world]['phases'][0][0][0]
    ws = [w for w, (n, L, dd, zz) in gm.items() if n == phase and L == tr['L_nm']]
    return min(float(SP.separation(w, [SP.NEUTRON])) for w in ws), len(ws)


def main():
    install(KAPPA_TEST)
    ok = True
    for w in WORLDS:
        Dg = float(SP.separation(w, [SP.NEUTRON]))
        Dp, n = planner_neutron_D(w)
        rel = abs(Dp - Dg) / max(1.0, Dg)
        print(f'world {w}: grader D(neutron) {Dg:.4f}  planner D(neutron) {Dp:.4f}  ({n} grid worlds)  rel diff {rel:.2e}')
        ok &= rel < 1e-4
    # linearity in kappa
    install(2 * KAPPA_TEST)
    w = WORLDS[0]; D2 = float(SP.separation(w, [SP.NEUTRON]))
    install(KAPPA_TEST); D1 = float(SP.separation(w, [SP.NEUTRON]))
    lin = abs(D2 / D1 - 2.0)
    print(f'linearity: D(2 kappa) / D(kappa) = {D2 / D1:.6f}')
    ok &= lin < 1e-3
    print('NEUTRON SCALE TEST PASSED' if ok else 'NEUTRON SCALE TEST FAILED')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
