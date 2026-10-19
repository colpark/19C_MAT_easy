"""The shared placement set for the reference path and the FM path (amendment E item 4).

30 rigid placements per registry, sampled over the surface lateral unit cell with a
quasi-random sequence (scrambled Sobol, scipy.stats.qmc) under a fixed seed, so both
paths use the identical placements and differ only in the energy function.

A placement is an in-plane offset (in fractions of the two surface lattice vectors) plus
a small rotation about the surface normal and a small height offset. The lattice vectors
come from the slab's own cell, so the sample covers exactly one surface lateral unit cell.

The sequence is logged by `describe()` so a report can state it exactly.
"""
import numpy as np
from scipy.stats import qmc

N_PLACEMENTS = 30
SEED = 20261019          # fixed, logged
ROT_DEG = 6.0            # +/- rotation about the surface normal
DZ_RANGE = (-0.3, 0.6)   # Angstrom, height offset about the nominal gap


def describe():
    return dict(sequence="scipy.stats.qmc.Sobol(d=4, scramble=True)", seed=SEED,
                n_placements=N_PLACEMENTS, rot_deg=ROT_DEG, dz_range_A=list(DZ_RANGE),
                note="columns: fractional offset along a, fractional offset along b, "
                     "rotation about the surface normal, height offset")


def placement_table(n=N_PLACEMENTS, seed=SEED):
    """(n, 4) array: frac_a, frac_b in [0,1), rot_deg in +/-ROT_DEG, dz in DZ_RANGE."""
    s = qmc.Sobol(d=4, scramble=True, seed=seed).random(n)
    out = np.empty_like(s)
    out[:, 0] = s[:, 0]
    out[:, 1] = s[:, 1]
    out[:, 2] = (2 * s[:, 2] - 1) * ROT_DEG
    out[:, 3] = DZ_RANGE[0] + s[:, 3] * (DZ_RANGE[1] - DZ_RANGE[0])
    return out


def apply_placement(pos, row, lat_a, lat_b):
    """Offset and rotate a placed fragment in the surface plane.

    `pos` is the fragment already laid in its registry (Angstrom); `row` is one line of
    placement_table; lat_a and lat_b are the surface lattice vectors (Angstrom, 2-vectors).
    """
    fa, fb, rot, dz = row
    c = pos.mean(0)
    a = np.radians(rot)
    R = np.array([[np.cos(a), -np.sin(a), 0.0], [np.sin(a), np.cos(a), 0.0], [0.0, 0.0, 1.0]])
    out = (pos - c) @ R.T + c
    shift = fa * np.asarray(lat_a) + fb * np.asarray(lat_b)
    out[:, 0] += shift[0]
    out[:, 1] += shift[1]
    out[:, 2] += dz
    return out


if __name__ == "__main__":
    import json
    t = placement_table()
    print(json.dumps(describe()))
    print(f"first 3 rows:\n{np.round(t[:3], 4)}")
    print(f"frac_a range {t[:, 0].min():.3f} to {t[:, 0].max():.3f}; "
          f"frac_b {t[:, 1].min():.3f} to {t[:, 1].max():.3f}; "
          f"rot {t[:, 2].min():.2f} to {t[:, 2].max():.2f} deg; "
          f"dz {t[:, 3].min():.2f} to {t[:, 3].max():.2f} A")
