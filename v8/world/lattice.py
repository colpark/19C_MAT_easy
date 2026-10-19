"""Lattice scan: periodic height field of the substrate surface cation sublattice, in the SCAN frame.

Hexagonal lattice, constant A_LAT = 5.19 A (rectangular-cell b = 9.02 A is ~ sqrt(3) a = 8.99 A, so the
hexagonal description is used); cation rows run along the three equivalent directions az, az+60, az+120
in the scan frame (az = hidden sample azimuth). Height field = sum of three cosines whose wave vectors are
perpendicular to the rows. Lattice-resolving mode: the tip is atomically sharp (no dilation); noise and
drift are applied; lengths in nm, heights in nm.
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sample as S, cost as C, render as R  # noqa: E402

A_LAT_NM = 0.519
B_LAT_NM = 0.902
CORRUGATION_NM = 0.05          # peak corrugation of the cation sublattice (assumed)
LATTICE_NOISE_REL = 0.1        # lattice-scan white sigma = this * world noise_nm (CALIBRATION.md: small-field raw images 0.003-0.03 nm)


def scan_lattice(world, plan, scan_seed=0):
    plan.validate()
    nz = world["nuisance"]
    px = plan.fov_nm / plan.npx
    minutes = plan.minutes()
    rng = np.random.default_rng(S.seed_int("lat", *world["key"], scan_seed, repr(plan.asdict())))
    amp = nz["drift_nm_min"] * plan.frame_minutes()
    pad = int(np.ceil(4 * amp / px)) + 2
    nx, ny = plan.npx + 2 * pad, plan.ny + 2 * pad
    xs = plan.cx_nm - plan.fov_nm / 2 + (np.arange(nx) - pad + 0.5) * px
    ys = plan.cy_nm - plan.ny * px / 2 + (np.arange(ny) - pad + 0.5) * px
    X, Y = np.meshgrid(xs, ys)
    k = 4 * np.pi / (np.sqrt(3) * A_LAT_NM)
    az = np.radians(nz["azimuth_deg"])
    ph0 = rng.uniform(0, 2 * np.pi, 3)   # stage position -> random lattice phase
    h = np.zeros((ny, nx))
    for j in range(3):
        th = az + np.radians(30 + 60 * j)       # wave vector perpendicular to row direction az+60j
        h += np.cos(k * (X * np.cos(th) + Y * np.sin(th)) + ph0[j])
    h *= CORRUGATION_NM / 3.0
    h = h + R.noise_image(rng, h.shape, LATTICE_NOISE_REL * nz["noise_nm"] * C.noise_scale(plan))
    dx, dy = R.drift_field(rng, h.shape, px, amp, R.DRIFT_CORR_FOV * plan.fov_nm)
    h = R.warp(h, dx, dy, px)[pad:pad + plan.ny, pad:pad + plan.npx]
    return dict(img=R.flatten_plane(h), px_nm=px, plan=plan, minutes=minutes)
