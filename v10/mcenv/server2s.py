"""Stage 2s environment server (V5_SPEC Appendix E). The stage 2r server (build, relax, arms placebo / fm / ceiling, ordered-only ceiling
match) with the stage 2s scenarios 46-50: no free default scan, 10-min overhead (neutron 125 min), a budget per scenario, the stage 2s
manual, and fit with optional lattice refinement (refine_lattice_scale: +-5 %, refined values and 1-sigma uncertainties).
  MCENV_STATE=... MCENV_PORT=8769 V5_FM_URL=http://192.168.100.11:8770/relax python -m mcenv.server2s"""
import math
import numpy as np
from . import server2r as S2RS          # stage 2r scenarios, stage 2 tools and arms, ordered-only ceiling match, V5_NO_FM mode
from . import server2 as S2S
from . import server as S
from . import scenarios as SC
from . import separation as SP
from . import tools_common as TC
from . import stage2s as ST

ST.install()


def budget(ep): return float(SC.SCEN[ep.tr['scen']]['budget'])


_prev_init = S.Episode.__init__


def _init(self, token, rec):
    """no free default scan in any arm (E.2): the stage 1 init skips m0 only for 'blind'."""
    _prev_init(self, token, dict(rec, arm='blind')); self.rec = rec


S.Episode.__init__ = _init


def t_status(ep, a):
    out = S2S.t_status(ep, a)
    B = budget(ep)
    out['manual'] = out['manual'].replace('{BUDGET}', f'{B:.0f}')
    out['budget_minutes'] = B; out['budget_left_minutes'] = round(B - ep.state['spent'], 3)
    return out


def t_measure(ep, a):
    m = TC.parse_measure(a)
    cost = m.cost + (S.STD_PREP if m.si_standard and not ep.state['std_prepared'] else 0.0)
    left = budget(ep) - ep.state['spent']
    if cost > left + 1e-9:
        raise TC.ToolError(f'over budget: this measurement costs {cost:.2f} min, {left:.2f} min left. Nothing was charged.')
    rec, counts = ep._acquire(m)
    return dict(id=rec['id'], start=m.start, step=m.step, n=m.n, radiation=m.radiation, cost_minutes=rec['cost'],
                budget_left_minutes=round(budget(ep) - ep.state['spent'], 3), counts=counts.tolist())


REFINE = 0.05


def fit_refine(scen, ms, ys, spec, resolver):
    """fit with every phase's lattice_scale free within +-5 % of the value given (inside [0.9, 1.1]); 1-sigma uncertainties from the
    Fisher matrix of the fitted model (nonlinear parameters and the active linear ones)."""
    phases = TC._phases(spec, scen, resolver)
    ls0 = [p.get('lattice_scale', 1.0) for _, p, _ in phases]
    lo = [max(0.9, v * (1 - REFINE)) for v in ls0]; hi = [min(1.1, v * (1 + REFINE)) for v in ls0]
    br = SC.Branch(lambda u: [[(n, dict(p, lattice_scale=float(u[i])), w) for i, (n, p, w) in enumerate(phases)]], lo, hi)
    y = np.concatenate([np.asarray(v, float) for v in ys])
    L0 = float(spec.get('size_nm', 100.0)); has_x = any(m.radiation == 'xray' for m in ms)
    starts = [np.array([s, 0.0, math.log(L)] + list(np.clip(ls0, lo, hi))) for s in ((-0.15, -0.05, 0.05, 0.15) if has_x else (0.0,))
              for L in (L0, 20.0, 300.0)]
    w = 1.0 / np.maximum(y, 1.0)
    chi2, th = SP.fit_branch(ms, y, w, br, L0, starts=starts, L_bounds=(3.0, 3000.0))
    mu = SP._model(ms, br, th); w = 1.0 / np.maximum(mu, 1.0)
    st2 = [np.array([th['disp_mm'], th['zero_deg'], math.log(th['L_nm'])] + th['u'])]
    chi2, th = SP.fit_branch(ms, y, w, br, L0, starts=st2, L_bounds=(3.0, 3000.0))
    mu = SP._model(ms, br, th)
    # Fisher matrix at the optimum: columns d mu / d theta for s, z, ln L (X-ray only), each lattice_scale, and active linear coefficients
    coef = np.array(th['coef']); theta = [th['disp_mm'], th['zero_deg'], math.log(th['L_nm'])] + list(th['u'])
    def model(t):
        Xd, _, _ = SP._design(ms, br.groups(t[3:]), t[0], t[1], math.exp(t[2])); return Xd @ coef
    J = []; idx = ([0, 1] if has_x else []) + [2] + list(range(3, 3 + len(phases)))
    hs = {0: 1e-3, 1: 1e-4, 2: 1e-3}
    for k in idx:
        h = hs.get(k, 1e-5); a = list(theta); b = list(theta); a[k] += h; b[k] -= h
        J.append((model(a) - model(b)) / (2 * h))
    Xd, _, _ = SP._design(ms, br.groups(theta[3:]), theta[0], theta[1], math.exp(theta[2]))
    J += [Xd[:, j] for j in range(Xd.shape[1]) if coef[j] > 0]
    J = np.array(J); F = (J / np.maximum(mu, 1.0)) @ J.T
    try: C = np.linalg.pinv(F); sig = [float(math.sqrt(max(C[idx.index(3 + i), idx.index(3 + i)], 0.0))) for i in range(len(phases))]
    except Exception: sig = [None] * len(phases)
    tr_scale = SP.world_truth(SC.twins(scen)[0]); ng = th['ng']; res = {}
    for k, inst in enumerate(th['insts']):
        c = coef[k * ng:(k + 1) * ng]; nom = tr_scale['A'] if inst == 'xray' else tr_scale['An']
        res[inst] = dict(scale_relative_to_nominal=round(float(c[0] / nom), 5), background_cps=round(float(c[1]), 4),
                         background_slope_cps=round(float(c[2] - c[3]), 4))
    ids = [e.get('structure_id', e.get('name')) for e in spec['phases']]
    return dict(chi2=round(float(chi2), 3), n_points=int(len(y)), fitted=dict(
        displacement_mm=round(th['disp_mm'], 5) if has_x else None, zero_deg=round(th['zero_deg'], 5) if has_x else None,
        size_nm=round(th['L_nm'], 2), **res,
        lattice_scale=[dict(phase=str(i), refined=round(float(u), 6), sigma=None if s is None else round(s, 6), bounds=[round(l, 5), round(h, 5)])
                       for i, u, s, l, h in zip(ids, th['u'], sig, lo, hi)]),
        note='Pearson chi2 with model weights; scale, linear background per instrument, displacement (|s| <= 0.20 mm), zero offset '
             '(|z| <= 0.01 deg), size and each lattice_scale (within +-5 % of the value given) free; weights fixed as given; '
             'sigma = 1-sigma uncertainty from the Fisher matrix of the fitted model')


def t_fit(ep, a):
    ids = a.get('measurement_ids') or a.get('measurement_id')
    ids = [ids] if isinstance(ids, str) else list(ids or [])
    if not ids: raise TC.ToolError('give measurement_id or measurement_ids')
    ms = [ep.meas(i) for i in ids]; ys = [ep.counts(i) for i in ids]
    spec = a.get('spec') or {}
    if TC._bool(spec.get('refine_lattice_scale', a.get('refine_lattice_scale', False))):
        return fit_refine(ep.tr['scen'], ms, ys, spec, S2S.resolver_for(ep))
    return TC.fit(ep.tr['scen'], ms, ys, spec, S2S.resolver_for(ep))


S.TOOLS.update(status=t_status, measure=t_measure, fit=t_fit)

if __name__ == '__main__':
    S.main()
