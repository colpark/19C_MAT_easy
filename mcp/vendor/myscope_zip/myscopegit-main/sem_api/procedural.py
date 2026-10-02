"""Deterministic, coordinate-addressed noise.

The specimen is defined as a function of world coordinates rather than of pixel
coordinates, so that changing magnification zooms into the *same* specimen and
moving the stage pans across it. That requires random numbers addressed by
lattice cell instead of drawn from a stream, which is what these hashes give.
"""

import numpy as np

_M32 = np.uint64(0xFFFFFFFF)


def _mix(h):
    h = (h ^ (h >> np.uint64(15))) & _M32
    h = (h * np.uint64(0x85EBCA6B)) & _M32
    h = (h ^ (h >> np.uint64(13))) & _M32
    h = (h * np.uint64(0xC2B2AE35)) & _M32
    h = (h ^ (h >> np.uint64(16))) & _M32
    return h


def hash2(ix, iy, seed, salt=0):
    """32-bit hash of an integer lattice cell. Works elementwise on arrays."""
    h = np.uint64((int(seed) & 0xFFFFFFFF) ^ ((int(salt) * 0x9E3779B1) & 0xFFFFFFFF))
    for k in (ix, iy):
        k = np.asarray(k, dtype=np.int64).astype(np.uint64) & _M32
        h = _mix((h ^ k) & _M32)
    return h


def rand01(ix, iy, seed, salt=0):
    """Uniform [0, 1) addressed by lattice cell."""
    return hash2(ix, iy, seed, salt).astype(np.float64) / 4294967296.0


def value_noise(x, y, seed, salt=0):
    """Smooth value noise on the unit lattice, in [0, 1]."""
    x0 = np.floor(x).astype(np.int64)
    y0 = np.floor(y).astype(np.int64)
    fx = x - x0
    fy = y - y0
    u = fx * fx * (3.0 - 2.0 * fx)
    v = fy * fy * (3.0 - 2.0 * fy)
    n00 = rand01(x0, y0, seed, salt)
    n10 = rand01(x0 + 1, y0, seed, salt)
    n01 = rand01(x0, y0 + 1, seed, salt)
    n11 = rand01(x0 + 1, y0 + 1, seed, salt)
    return (n00 * (1 - u) + n10 * u) * (1 - v) + (n01 * (1 - u) + n11 * u) * v


# Each octave is rotated by this angle so that the square lattice of the value
# noise does not show through as an axis-aligned grid in the finished image.
_OCTAVE_COS, _OCTAVE_SIN = np.cos(0.61), np.sin(0.61)


def fbm(x, y, seed, octaves=5, lacunarity=2.0, gain=0.5, salt=0):
    """Fractional Brownian motion, normalised to roughly [0, 1]."""
    total = np.zeros(np.broadcast(x, y).shape, dtype=np.float64)
    amp = 1.0
    norm = 0.0
    px, py = np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64)
    for i in range(octaves):
        total += amp * value_noise(px, py, seed, salt + i * 101)
        norm += amp
        amp *= gain
        px, py = (
            (px * _OCTAVE_COS - py * _OCTAVE_SIN) * lacunarity,
            (px * _OCTAVE_SIN + py * _OCTAVE_COS) * lacunarity,
        )
    return total / norm


def cells_covering(x0, x1, y0, y1, cell):
    """Integer cell index ranges covering a world-space rectangle."""
    ix0 = int(np.floor(x0 / cell)) - 1
    ix1 = int(np.floor(x1 / cell)) + 1
    iy0 = int(np.floor(y0 / cell)) - 1
    iy1 = int(np.floor(y1 / cell)) + 1
    return ix0, ix1, iy0, iy1
