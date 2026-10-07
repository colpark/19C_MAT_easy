#!/usr/bin/env python3
"""Tracer MSD and diffusion coefficient (card L1, eq. 1 of Thakur et al.): D = slope(MSD(t)) / 6.

Procedure (frozen at C2 after synthetic validation, I4/I7; change only on synthetic or dev data):
  * positions are unwrapped with the minimum-image convention between consecutive frames (frames must be
    closer than half a cell; checked);
  * MSD(t) averages over atoms of the species and over time origins (eq. 1, <...>_tau), origins every
    `origin_stride` frames;
  * the slope is a least-squares line on lags in [FIT_START, FIT_END] x the trajectory length (the first
    10 % carries the ballistic and vibrational regime, lags past 50 % carry few independent origins);
  * the uncertainty is the larger of (a) the standard error of D over N_BLOCKS contiguous blocks (each fitted
    the same way) and (b) the per-atom bootstrap SE of the slope (revision R2, synthetic validation: block SE
    alone covered 77 % of errors within 3 SE).
Units: positions in Å, time in ps, D returned in cm^2/s (1 Å^2/ps = 1e-4 cm^2/s).
"""
import numpy as np

FIT_START, FIT_END = 0.10, 0.50
N_BLOCKS = 5
A2PS_TO_CM2S = 1e-4


def unwrap(pos, cell):
    """pos [T, N, 3] (Å, possibly wrapped), cell [3, 3] rows = lattice vectors (Å), or [T, 3, 3]."""
    pos = np.asarray(pos, float)
    cell = np.asarray(cell, float)
    out = np.empty_like(pos)
    out[0] = pos[0]
    for t in range(1, len(pos)):
        c = cell[t] if cell.ndim == 3 else cell
        inv = np.linalg.inv(c)
        d = pos[t] - pos[t - 1]
        f = d @ inv
        f -= np.round(f)
        out[t] = out[t - 1] + f @ c
    return out


def msd_curve(upos, dt_ps, origin_stride=1, max_lag_frac=FIT_END):
    """upos [T, N, 3] unwrapped. Returns lags_ps [L], msd [L] (Å^2) for lags 0..max_lag_frac*T."""
    T = len(upos)
    L = max(2, int(max_lag_frac * T) + 1)
    lags = np.arange(L)
    msd = np.zeros(L)
    origins = np.arange(0, T - 1, max(1, origin_stride))
    for k in lags[1:]:
        o = origins[origins + k < T]
        d = upos[o + k] - upos[o]
        msd[k] = np.mean(np.sum(d * d, axis=-1))
    return lags * dt_ps, msd


def fit_slope(lags_ps, msd, t_total_ps, start=FIT_START, end=FIT_END):
    m = (lags_ps >= start * t_total_ps) & (lags_ps <= end * t_total_ps)
    if m.sum() < 3:
        raise ValueError('fit window holds fewer than 3 lags')
    A = np.vstack([lags_ps[m], np.ones(m.sum())]).T
    (s, b), *_ = np.linalg.lstsq(A, msd[m], rcond=None)
    return s, b


def _atom_se(upos, dt_ps, t_total, stride, n_boot=200, seed=5):
    n = upos.shape[1]
    if n < 3:
        return float('nan')
    T = len(upos)
    L = int(FIT_END * T) + 1
    lags = np.arange(L)
    origins = np.arange(0, T - 1, stride)
    per = np.zeros((L, n))
    for k in lags[1:]:
        o = origins[origins + k < T]
        d = upos[o + k] - upos[o]
        per[k] = np.mean(np.sum(d * d, axis=-1), axis=0)
    t = lags * dt_ps
    m = (t >= FIT_START * t_total) & (t <= FIT_END * t_total)
    A = np.vstack([t[m], np.ones(m.sum())]).T
    rng = np.random.default_rng(seed)
    sl = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        (sb, _), *_ = np.linalg.lstsq(A, per[m][:, idx].mean(1), rcond=None)
        sl.append(sb)
    return float(np.std(sl, ddof=1) / 6.0 * A2PS_TO_CM2S)


def diffusion(pos, cell, dt_ps, species_mask=None, wrapped=True, origin_stride=None, n_blocks=N_BLOCKS):
    """Return dict(D, D_se, slope, intercept, t_total_ps, n_atoms, n_frames) with D in cm^2/s."""
    pos = np.asarray(pos, float)
    if species_mask is not None:
        pos = pos[:, np.asarray(species_mask, bool)]
    upos = unwrap(pos, cell) if wrapped else pos
    T = len(upos)
    t_total = (T - 1) * dt_ps
    stride = origin_stride or max(1, T // 200)
    lags, msd = msd_curve(upos, dt_ps, stride)
    s, b = fit_slope(lags, msd, t_total)
    D = s / 6.0 * A2PS_TO_CM2S
    Db = []
    if n_blocks and T >= 20 * n_blocks:
        nb = T // n_blocks
        for i in range(n_blocks):
            u = upos[i * nb:(i + 1) * nb]
            lb, mb = msd_curve(u, dt_ps, max(1, nb // 200))
            sb, _ = fit_slope(lb, mb, (len(u) - 1) * dt_ps)
            Db.append(sb / 6.0 * A2PS_TO_CM2S)
    se_block = float(np.std(Db, ddof=1) / np.sqrt(len(Db))) if len(Db) > 1 else float('nan')
    se_atom = _atom_se(upos, dt_ps, t_total, stride)
    se = float(np.nanmax([se_block, se_atom]))
    return {'D': float(D), 'D_se': se, 'D_se_block': se_block, 'D_se_atom': se_atom, 'D_blocks': [float(x) for x in Db], 'slope_A2_per_ps': float(s),
            'intercept_A2': float(b), 't_total_ps': float(t_total), 'n_atoms': int(pos.shape[1]),
            'n_frames': int(T), 'fit_window': [FIT_START, FIT_END], 'origin_stride': int(stride)}


def msd_for_panel(pos, cell, dt_ps, species_mask=None, wrapped=True, n_points=400):
    """MSD(t) over the full lag range for rendering (T1 panels): returns t_ps, msd_A2 (subsampled)."""
    pos = np.asarray(pos, float)
    if species_mask is not None:
        pos = pos[:, np.asarray(species_mask, bool)]
    upos = unwrap(pos, cell) if wrapped else pos
    T = len(upos)
    lags, msd = msd_curve(upos, dt_ps, max(1, T // 200), max_lag_frac=1.0 - 1.0 / T)
    idx = np.unique(np.linspace(0, len(lags) - 1, min(n_points, len(lags))).astype(int))
    return lags[idx], msd[idx]
