"""Separation D (V5_SPEC 3.1), likelihood-ratio reading and the agent fit tool share one forward model.

mu_m(x) = t_m * flux_m * (sum_g A_g * sig_g(x; s, z, L, u) + b0 + b1 * (x - 80) / 70)   for X-ray measurements
mu_m(x) = t_m * (sum_g An_g * sig_g(x; L, u) + bn0 + bn1 * (x - 80) / 70)                for the neutron measurement
Linear parameters (A_g >= 0 per instrument and group, background per instrument) are solved by weighted NNLS (variable projection);
nonlinear ones (s in the manual range, z in the manual range, L within 30 % of the true size, side parameters u) by multi-start
L-BFGS-B. D = min over branches of the other side of sum (mu_truth - mu_alt)^2 / mu_truth."""
from dataclasses import dataclass, asdict
import math
import numpy as np
from scipy.optimize import nnls, minimize
from . import physics as P
from . import scenarios as SC

S_RANGE = (-0.20, 0.20)        # manual displacement range (X3)
Z_RANGE = (-0.01, 0.01)
L_REL = 0.30
BG_SLOPE = -0.3                 # hidden background slope relative to b0 (same for every world)


@dataclass(frozen=True)
class Meas:
    radiation: str = 'xray'
    start: float = 10.0
    step: float = 0.04
    n: int = 1501
    t: float = 0.5
    optics: str = 'standard'
    si_standard: bool = False

    @property
    def x(self): return P.grid(self.start, self.step, self.n)
    @property
    def flux(self): return 1.0 if self.radiation == 'neutron' else P.FLUX[self.optics]
    @property
    def cost(self): return P.NEUTRON['cost_min'] if self.radiation == 'neutron' else P.cost_min(self.n, self.t)
    def key(self): return asdict(self)


DEFAULT = Meas()
NEUTRON = Meas('neutron', P.NEUTRON['start'], P.NEUTRON['step'], P.NEUTRON['n'], P.NEUTRON['t'], 'neutron', False)


def meas_from(d):
    if d.get('radiation') == 'neutron': return NEUTRON
    return Meas('xray', float(d['start']), float(d['step']), int(d['n']), float(d['t']), d.get('optics', 'standard'), bool(d.get('si_standard', False)))


# ---------------------------------------------------------------- truth
def world_truth(world):
    """hidden truth of a world (server side only): groups, nuisances, scales."""
    h = SC.hidden(world); s = SC.WORLD_SCEN[world]; d = SC.SCEN[s]
    groups = d['worlds'][world]['phases']
    ref_world = SC.twins(s)[0]                      # scale calibrated on the first twin, shared by twins
    ref = d['worlds'][ref_world]['phases']
    x = DEFAULT.x
    sig = sum(P.signal(x, g, 'xray', 'standard', h['L_nm'], 0.0, 0.0) for g in ref)     # nominal geometry: scale shared by twins
    A = h['N'] / (DEFAULT.t * sig.max())
    xn = NEUTRON.x
    sign = sum(P.signal(xn, g, 'neutron', 'neutron', h['L_nm']) for g in ref)
    An = h['Nn'] / (NEUTRON.t * sign.max())
    return dict(world=world, scen=s, groups=groups, A=A, An=An, b0=h['bg'], b1=BG_SLOPE * h['bg'], bn0=h['bgn'] / NEUTRON.t,
                bn1=BG_SLOPE * h['bgn'] / NEUTRON.t, disp_mm=h['disp_mm'], zero_deg=h['zero_deg'], L_nm=h['L_nm'])


def mu_truth(tr, m):
    x = m.x
    if m.radiation == 'neutron':
        sig = sum(P.signal(x, g, 'neutron', 'neutron', tr['L_nm']) for g in tr['groups'])
        return m.t * (tr['An'] * sig + tr['bn0'] + tr['bn1'] * (x - 80) / 70)
    sig = sum(P.signal(x, g, 'xray', m.optics, tr['L_nm'], tr['disp_mm'], tr['zero_deg'], m.si_standard) for g in tr['groups'])
    return m.t * m.flux * (tr['A'] * sig + tr['b0'] + tr['b1'] * (x - 80) / 70)


# ---------------------------------------------------------------- model fit
def _design(meas, groups, s, z, L):
    """columns per instrument: group signals (nonneg), b0 (nonneg), +slope, -slope. Returns list of (rows per meas, col index map)."""
    cols_x, cols_n = [], []
    rows = []
    for m in meas:
        x = m.x; w = m.t * m.flux
        if m.radiation == 'neutron':
            g = [w * P.signal(x, gr, 'neutron', 'neutron', L) for gr in groups]
        else:
            g = [w * P.signal(x, gr, 'xray', m.optics, L, s, z, m.si_standard) for gr in groups]
        bl = (x - 80) / 70
        rows.append((m.radiation, np.column_stack(g + [w * np.ones_like(x), w * bl, -w * bl])))
    ng = len(groups) + 3
    insts = sorted({r for r, _ in rows})
    blocks = []
    for r, M in rows:
        full = np.zeros((M.shape[0], ng * len(insts)))
        k = insts.index(r); full[:, k * ng:(k + 1) * ng] = M; blocks.append(full)
    return np.vstack(blocks), insts, ng


def _lin_solve(Xd, y, w):
    sw = np.sqrt(w)
    coef, _ = nnls(Xd * sw[:, None], y * sw, maxiter=50 * Xd.shape[1])
    r = y - Xd @ coef
    return float((w * r * r).sum()), coef


def _unpack(theta, branch):
    s, z, lL = theta[:3]; u = theta[3:]
    return s, z, math.exp(lL), u


def fit_branch(meas, y, w, branch, L0, starts=None, s_range=S_RANGE, z_range=Z_RANGE, L_rel=L_REL, iters=60, L_bounds=None):
    """min over (s, z, L, u) of weighted SSR with linear params projected. Returns (chi2, theta dict, coef)."""
    y = np.concatenate([np.asarray(v) for v in y]) if isinstance(y, (list, tuple)) else y
    has_x = any(m.radiation == 'xray' for m in meas)
    Lb = L_bounds or (L0 * (1 - L_rel), L0 * (1 + L_rel))
    lo = [s_range[0] if has_x else 0, z_range[0] if has_x else 0, math.log(Lb[0])] + list(branch.lo)
    hi = [s_range[1] if has_x else 0, z_range[1] if has_x else 0, math.log(Lb[1])] + list(branch.hi)
    bounds = list(zip(lo, hi))

    def f(theta):
        s, z, L, u = _unpack(theta, branch)
        Xd, _, _ = _design(meas, branch.groups(u), s, z, L)
        return _lin_solve(Xd, y, w)[0]

    if starts is None: starts = default_starts(branch, L0, has_x)
    best = (np.inf, None)
    # coarse: evaluate starts, refine the best three
    vals = sorted(((f(np.clip(t0, lo, hi)), tuple(np.clip(t0, lo, hi))) for t0 in starts), key=lambda v: v[0])
    for v0, t0 in vals[:3]:
        r = minimize(f, np.array(t0), method='L-BFGS-B', bounds=bounds, options=dict(maxiter=iters, eps=_eps(branch, has_x)))
        if r.fun < best[0]: best = (r.fun, r.x)
    s, z, L, u = _unpack(best[1], branch)
    Xd, insts, ng = _design(meas, branch.groups(u), s, z, L)
    chi2, coef = _lin_solve(Xd, y, w)
    return chi2, dict(disp_mm=s, zero_deg=z, L_nm=L, u=list(map(float, u)), insts=insts, coef=coef.tolist(), ng=ng)


def _eps(branch, has_x):
    e = [1e-4, 2e-5, 1e-3] + [max(1e-6, 1e-3 * (h - l)) for l, h in zip(branch.lo, branch.hi)]
    return np.array(e)


def default_starts(branch, L0, has_x, s_true=None):
    ss = [-0.15, -0.05, 0.05, 0.15] if has_x else [0.0]
    if s_true is not None and has_x: ss = sorted(set(ss + [s_true]))
    us = [[]] if branch.dim == 0 else [list(v) for v in _ugrid(branch)]
    return [np.array([s, 0.0, math.log(L0)] + u) for s in ss for u in us]


def _ugrid(branch):
    pts = [np.linspace(l, h, 3) for l, h in zip(branch.lo, branch.hi)]
    mesh = np.meshgrid(*pts, indexing='ij')
    return np.column_stack([m.ravel() for m in mesh])


# ---------------------------------------------------------------- D
def separation(world, meas, tr=None, return_fit=False):
    """D for a world and a list of Meas (m0 included by the caller)."""
    tr = tr or world_truth(world)
    mu = [mu_truth(tr, m) for m in meas]
    y = np.concatenate(mu); w = 1.0 / np.maximum(y, 1e-9)
    best = (np.inf, None, None)
    for br in SC.other_side(world):
        starts = default_starts(br, tr['L_nm'], any(m.radiation == 'xray' for m in meas), tr['disp_mm'])
        chi2, th = fit_branch(meas, y, w, br, tr['L_nm'], starts)
        if chi2 < best[0]: best = (chi2, br.label, th)
    return (best[0], best[1], best[2]) if return_fit else best[0]


# ---------------------------------------------------------------- likelihood-ratio reading (scripted agents)
def lr_read(scen, meas, ys, L_guess, L_bounds=(5.0, 3000.0)):
    """fit claim side and other side on noisy data (Pearson chi2, weights from the fitted model, two passes). Returns dict."""
    y = np.concatenate([np.asarray(v, float) for v in ys])
    out = {}
    for side in ('claim_side', 'other_side'):
        best = np.inf
        for br in SC.SCEN[scen][side]:
            w = 1.0 / np.maximum(y, 1.0)
            st = default_starts(br, L_guess, any(m.radiation == 'xray' for m in meas))
            st += [np.concatenate([t[:2], [math.log(Lg)], t[3:]]) for t in st[:4] for Lg in (L_bounds[0] * 4, L_bounds[1] / 4)]
            chi2, th = fit_branch(meas, y, w, br, L_guess, starts=st, L_bounds=L_bounds)
            mu = _model(meas, br, th)
            w = 1.0 / np.maximum(mu, 1.0)
            chi2, th = fit_branch(meas, y, w, br, L_guess, starts=[np.array([th['disp_mm'], th['zero_deg'], math.log(th['L_nm'])] + th['u'])],
                                  L_bounds=L_bounds)
            best = min(best, chi2)
        out[side] = best
    out['dchi2'] = out['other_side'] - out['claim_side']
    return out


def _model(meas, br, th):
    Xd, _, _ = _design(meas, br.groups(th['u']), th['disp_mm'], th['zero_deg'], th['L_nm'])
    return Xd @ np.array(th['coef'])
