#!/usr/bin/env python3
"""Synthetic Li trajectories with known D and Ea for validating msd.py and arrhenius.py (hard rule 6, I7).

Model: n_li ions hop on a cubic sublattice (spacing a) with Poisson rate Gamma(T) = nu exp(-Ea / k_B T) per ion,
each jump of length a along a random +-x/y/z, plus an Ornstein-Uhlenbeck vibration about the current site
(amplitude u_rms, relaxation tau_vib) that adds the plateau and noise of real MD; host atoms vibrate only.
True tracer D = Gamma a^2 / 6. Positions are wrapped into the cell to exercise unwrapping.
The regime is drawn to cover the deposit (C2 sets dt and length from the trajectories' own metadata):
  D from 1e-9 to 1e-4 cm^2/s, 100-180 ps, 10-64 Li, frame spacing 0.01-0.2 ps.
"""
import numpy as np

KB_EV = 8.617333262e-5


def gamma_for_D(D_cm2_s, a_A):
    return 6.0 * D_cm2_s * 1e4 / a_A ** 2     # per ps (D in Å^2/ps = 1e4 x cm^2/s)


def trajectory(D_cm2_s, n_li=32, n_host=64, t_ps=100.0, dt_ps=0.05, a_A=2.5, L_A=None, u_rms=0.25, tau_vib=0.2,
               seed=0):
    rng = np.random.default_rng(seed)
    nT = int(round(t_ps / dt_ps)) + 1
    L = L_A or a_A * max(4, int(np.ceil((n_li + n_host) ** (1 / 3))) + 2)
    cell = np.eye(3) * L
    g = gamma_for_D(D_cm2_s, a_A)
    site = rng.uniform(0, L, (n_li, 3))
    host = rng.uniform(0, L, (n_host, 3))
    lam = g * dt_ps
    dirs = np.array([[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]], float)
    phi = np.exp(-dt_ps / tau_vib)
    sig = u_rms / np.sqrt(3) * np.sqrt(1 - phi ** 2)
    vib = rng.normal(0, u_rms / np.sqrt(3), (n_li, 3))
    hvib = rng.normal(0, u_rms / np.sqrt(3), (n_host, 3))
    pos = np.empty((nT, n_li + n_host, 3))
    for t in range(nT):
        if t:
            k = rng.poisson(lam, n_li)
            for i in np.nonzero(k)[0]:
                site[i] += a_A * dirs[rng.integers(0, 6, k[i])].sum(0)
            vib = phi * vib + rng.normal(0, sig, vib.shape)
            hvib = phi * hvib + rng.normal(0, sig, hvib.shape)
        pos[t, :n_li] = site + vib
        pos[t, n_li:] = host + hvib
    pos = np.mod(pos, L)
    mask = np.zeros(n_li + n_host, bool)
    mask[:n_li] = True
    return {'pos': pos, 'cell': cell, 'dt_ps': dt_ps, 'mask': mask, 'D_true': D_cm2_s, 'n_li': n_li,
            'volume_A3': L ** 3}


def arrhenius_set(Ea_eV, D1000, temps=(1000, 750, 600, 500), times=(100, 125, 150, 180), seed=0, **kw):
    """Trajectories on the paper's ladder with D(T) = D1000 exp(-Ea/k (1/T - 1/1000))."""
    out = []
    for i, (T, tp) in enumerate(zip(temps, times)):
        D = D1000 * np.exp(-Ea_eV / KB_EV * (1.0 / T - 1.0 / 1000.0))
        tr = trajectory(D, t_ps=tp, seed=seed * 100 + i, **kw)
        tr['T'] = T
        out.append(tr)
    return out
