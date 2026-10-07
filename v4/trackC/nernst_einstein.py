#!/usr/bin/env python3
"""Nernst-Einstein (card L2, eq. 2): sigma = N (Z e)^2 D_tr / (Omega k_B T H), with Haven ratio H = 1.

Model error (recorded, stated in every T3 stem): H is fixed at 1 by assumption ("In the dilute limit, we
assume it to be 1, though in practice it is often less than 1"); with H < 1 the true sigma is larger.
Inputs: N mobile ions in the cell, cell volume Omega in Å^3, D in cm^2/s, T in K, Z = 1 for Li+.
Output: sigma in mS/cm.
"""
E = 1.602176634e-19       # C
KB = 1.380649e-23         # J/K
HAVEN = 1.0
MODEL_ERROR = 'Haven ratio H = 1 assumed (tracer = charge diffusion); real H is often < 1, so sigma is a lower bound'


def sigma_mS_cm(n_ions, volume_A3, D_cm2_s, T_K, Z=1, H=HAVEN):
    D = D_cm2_s * 1e-4            # m^2/s
    V = volume_A3 * 1e-30         # m^3
    s = n_ions * (Z * E) ** 2 * D / (V * KB * T_K * H)   # S/m
    return s * 10.0               # 1 S/m = 10 mS/cm


def D_from_sigma(n_ions, volume_A3, sigma_mScm, T_K, Z=1, H=HAVEN):
    return sigma_mScm / sigma_mS_cm(n_ions, volume_A3, 1.0, T_K, Z, H)
