"""Specimen generation.

A specimen is a height field (nm) plus a material-index map, both evaluated on
a world-aligned raster given in micrometres. Because everything is addressed by
world coordinate and hashed by lattice cell, the specimen is stable under
magnification and stage moves: zooming in shows more of the same object rather
than a new random one.
"""

import numpy as np

from . import procedural as pr
from .params import SAMPLES

# Above this many lattice cells the individual features are far smaller than a
# pixel, so they are rendered as an unresolved texture instead. Reported in the
# render metadata as `features_resolved: false`. The limit is a wall-clock
# budget: ~90k features costs roughly two seconds.
MAX_CELLS = 90000


def _subgrid(xs, ys, x0, x1, y0, y1):
    """Index window of the raster covering a world-space bounding box."""
    ix0 = int(np.searchsorted(xs, x0, "left"))
    ix1 = int(np.searchsorted(xs, x1, "right"))
    iy0 = int(np.searchsorted(ys, y0, "left"))
    iy1 = int(np.searchsorted(ys, y1, "right"))
    if ix1 <= ix0 or iy1 <= iy0:
        return None
    return ix0, ix1, iy0, iy1


def _stamp(height, material, window, sub_h, mat_id):
    """Composite a feature into the height map inside its bounding box.

    ``sub_h`` is zero where the feature does not cover the pixel, so the test
    must exclude those pixels explicitly - otherwise the empty corners of the
    bounding box would flatten the substrate they overlap.
    """
    ix0, ix1, iy0, iy1 = window
    view_h = height[iy0:iy1, ix0:ix1]
    hit = (sub_h > 0.0) & (sub_h > view_h)
    view_h[hit] = sub_h[hit]
    material[iy0:iy1, ix0:ix1][hit] = mat_id


def _cell_range(xs, ys, cell):
    ix0, ix1, iy0, iy1 = pr.cells_covering(xs[0], xs[-1], ys[0], ys[-1], cell)
    count = (ix1 - ix0 + 1) * (iy1 - iy0 + 1)
    return (ix0, ix1, iy0, iy1), count


def _unresolved_texture(xs, ys, feature_um, seed, amplitude_nm):
    """Stand-in for features far finer than one pixel.

    Individually the features are invisible; what survives is the mottling of
    their collective height variation. The coarse scale is tied to the raster
    rather than to the feature, because anything finer than a few pixels would
    only alias into white noise instead of reading as texture.
    """
    raster_um = float(abs(xs[1] - xs[0])) if xs.size > 1 else max(feature_um, 1e-6)
    coarse = max(feature_um * 6.0, raster_um * 5.0)
    fine = max(feature_um, raster_um * 1.5)
    X, Y = np.meshgrid(xs, ys)
    mottle = pr.fbm(X / coarse, Y / coarse, seed, octaves=4, salt=71)
    grain = pr.fbm(X / fine, Y / fine, seed, octaves=2, salt=73)
    return amplitude_nm * (0.8 * (mottle - 0.5) + 0.2 * (grain - 0.5))


def _substrate(xs, ys, feature_um, seed):
    """Mounting substrate: carbon tape is rough, never optically flat."""
    X, Y = np.meshgrid(xs, ys)
    scale = max(feature_um * 0.45, 1e-6)
    coarse = pr.fbm(X / scale, Y / scale, seed, octaves=4, salt=57)
    fine = pr.fbm(X / (scale * 0.12), Y / (scale * 0.12), seed, octaves=3, salt=59)
    amplitude_nm = min(feature_um * 45.0, 900.0)
    return amplitude_nm * (0.7 * (coarse - 0.5) + 0.3 * (fine - 0.5))


# ---------------------------------------------------------------------------
# Individual specimens
# ---------------------------------------------------------------------------


def _spheres(xs, ys, height, material, feature_um, seed, spiky=False):
    cell = feature_um * (1.6 if spiky else 1.15)
    (ix0, ix1, iy0, iy1), count = _cell_range(xs, ys, cell)
    if count > MAX_CELLS:
        height += _unresolved_texture(xs, ys, feature_um, seed, feature_um * 300.0)
        material[:] = 1
        return False

    height += _substrate(xs, ys, feature_um, seed)
    for cy in range(iy0, iy1 + 1):
        for cx in range(ix0, ix1 + 1):
            jx = pr.rand01(cx, cy, seed, 1)
            jy = pr.rand01(cx, cy, seed, 2)
            rr = pr.rand01(cx, cy, seed, 3)
            px = (cx + 0.15 + 0.7 * float(jx)) * cell
            py = (cy + 0.15 + 0.7 * float(jy)) * cell
            radius = 0.5 * feature_um * (0.78 + 0.44 * float(rr))
            window = _subgrid(xs, ys, px - radius, px + radius, py - radius, py + radius)
            if window is None:
                continue
            wix0, wix1, wiy0, wiy1 = window
            dx = xs[wix0:wix1] - px
            dy = ys[wiy0:wiy1] - py
            d2 = dx[None, :] ** 2 + dy[:, None] ** 2
            inside = d2 < radius * radius
            sub = np.zeros_like(d2)
            sub[inside] = np.sqrt(radius * radius - d2[inside])
            if spiky:
                # Echinate (spiked) grain: cones on a jittered lattice wrapped
                # over the grain, tallest where the surface faces the beam and
                # vanishing at the rim where they would point sideways.
                pitch = radius * 0.30
                u = np.broadcast_to(dx[None, :], d2.shape) / pitch
                v = np.broadcast_to(dy[:, None], d2.shape) / pitch
                cu = np.floor(u).astype(np.int64)
                cv = np.floor(v).astype(np.int64)
                # Distance to the nearest spine centre. The neighbouring cells
                # must be searched too: a jittered centre near a cell boundary
                # otherwise gets its cone clipped square at the boundary.
                dist = np.full(d2.shape, 4.0)
                for ov in (-1, 0, 1):
                    for ou in (-1, 0, 1):
                        nu, nv = cu + ou, cv + ov
                        ju = pr.rand01(nu, nv, seed, 41) * 0.5 + 0.25
                        jv = pr.rand01(nu, nv, seed, 42) * 0.5 + 0.25
                        dist = np.minimum(dist, np.hypot(u - (nu + ju), v - (nv + jv)))
                cone = np.clip(1.0 - dist / 0.42, 0.0, 1.0) ** 1.6
                # Spines point radially, so their projected height falls off
                # towards the rim of the grain where they point sideways.
                facing = np.sqrt(np.clip(sub / radius, 0.0, 1.0))
                sub[inside] += (cone * radius * 0.55 * facing)[inside]
                texture = pr.fbm(u * 2.5, v * 2.5, seed, octaves=2, salt=43)
                sub[inside] *= 1.0 + 0.06 * (texture[inside] - 0.5)
            _stamp(height, material, window, sub * 1000.0, 1)
    return True


def _fibres(xs, ys, height, material, feature_um, seed):
    cell = feature_um * 6.0
    (ix0, ix1, iy0, iy1), count = _cell_range(xs, ys, cell)
    if count > MAX_CELLS:
        height += _unresolved_texture(xs, ys, feature_um, seed, feature_um * 250.0)
        material[:] = 1
        return False

    height += _substrate(xs, ys, feature_um, seed)
    radius = 0.5 * feature_um
    half_len = cell * 0.9
    for cy in range(iy0, iy1 + 1):
        for cx in range(ix0, ix1 + 1):
            px = (cx + float(pr.rand01(cx, cy, seed, 11))) * cell
            py = (cy + float(pr.rand01(cx, cy, seed, 12))) * cell
            angle = float(pr.rand01(cx, cy, seed, 13)) * np.pi
            thick = radius * (0.7 + 0.6 * float(pr.rand01(cx, cy, seed, 14)))
            ux, uy = np.cos(angle), np.sin(angle)
            ex, ey = abs(ux) * half_len + thick, abs(uy) * half_len + thick
            window = _subgrid(xs, ys, px - ex, px + ex, py - ey, py + ey)
            if window is None:
                continue
            wix0, wix1, wiy0, wiy1 = window
            dx = (xs[wix0:wix1] - px)[None, :]
            dy = (ys[wiy0:wiy1] - py)[:, None]
            # Distance to the segment centred at (px, py) along (ux, uy).
            along = np.clip(dx * ux + dy * uy, -half_len, half_len)
            perp2 = (dx - along * ux) ** 2 + (dy - along * uy) ** 2
            inside = perp2 < thick * thick
            sub = np.zeros_like(perp2)
            sub[inside] = np.sqrt(thick * thick - perp2[inside])
            _stamp(height, material, window, sub * 1000.0, 1)
    return True


def _particles(xs, ys, height, material, feature_um, seed):
    cell = feature_um * 1.8
    (ix0, ix1, iy0, iy1), count = _cell_range(xs, ys, cell)
    if count > MAX_CELLS:
        X, Y = np.meshgrid(xs / feature_um, ys / feature_um)
        height += _unresolved_texture(xs, ys, feature_um, seed, feature_um * 200.0)
        material[:] = np.where(pr.value_noise(X, Y, seed, 5) > 0.7, 2, 1)
        return False

    height += _substrate(xs, ys, feature_um, seed)
    for cy in range(iy0, iy1 + 1):
        for cx in range(ix0, ix1 + 1):
            px = (cx + float(pr.rand01(cx, cy, seed, 21))) * cell
            py = (cy + float(pr.rand01(cx, cy, seed, 22))) * cell
            size = float(pr.rand01(cx, cy, seed, 23))
            radius = 0.5 * feature_um * (0.30 + 1.25 * size ** 1.7)
            heavy = float(pr.rand01(cx, cy, seed, 24)) > 0.68
            reach = radius * 1.4
            window = _subgrid(xs, ys, px - reach, px + reach, py - reach, py + reach)
            if window is None:
                continue
            wix0, wix1, wiy0, wiy1 = window
            dx = (xs[wix0:wix1] - px)[None, :]
            dy = (ys[wiy0:wiy1] - py)[:, None]
            d = np.hypot(dx, dy)
            # Angular radius modulation turns the sphere into an angular grain.
            facet = pr.fbm(np.broadcast_to(dx, d.shape) / (radius * 0.55),
                           np.broadcast_to(dy, d.shape) / (radius * 0.55),
                           seed, octaves=2, salt=int(cx * 7 + cy * 13) & 0xFFFF)
            r_eff = radius * (0.72 + 0.52 * facet)
            inside = d < r_eff
            sub = np.zeros_like(d)
            sub[inside] = np.sqrt(np.clip(r_eff[inside] ** 2 - d[inside] ** 2, 0.0, None))
            _stamp(height, material, window, sub * 1000.0, 2 if heavy else 1)
    return True


def _fracture(xs, ys, height, material, feature_um, seed):
    X, Y = np.meshgrid(xs / feature_um, ys / feature_um)
    rough = pr.fbm(X, Y, seed, octaves=6, gain=0.55)
    # A ridged component gives the sharp facet edges of a brittle fracture.
    ridged = 1.0 - np.abs(2.0 * pr.fbm(X * 1.7, Y * 1.7, seed, octaves=4, salt=31) - 1.0)
    height += (0.62 * rough + 0.38 * ridged - 0.5) * feature_um * 700.0
    material[:] = 0
    return True


def _grid(xs, ys, height, material, feature_um, seed):
    pitch = feature_um
    bar = 0.30 * pitch
    soft = max((xs[1] - xs[0]) * 1.5, pitch * 1e-3)
    X, Y = np.meshgrid(np.mod(xs, pitch), np.mod(ys, pitch))

    def edge(v):
        return np.clip((bar - v) / soft, 0.0, 1.0) * np.clip(v / soft, 0.0, 1.0)

    mask = np.maximum(edge(X), edge(Y))
    # Slight sag of the support film between the bars.
    sag = pr.fbm(np.meshgrid(xs / (pitch * 4), ys / (pitch * 4))[0],
                 np.meshgrid(xs / (pitch * 4), ys / (pitch * 4))[1], seed, octaves=3)
    height += mask * pitch * 350.0 + (1.0 - mask) * (sag - 0.5) * pitch * 25.0
    material[:] = np.where(mask > 0.5, 1, 0)
    return True


_BUILDERS = {
    "spheres": lambda *a: _spheres(*a, spiky=False),
    "pollen": lambda *a: _spheres(*a, spiky=True),
    "fibres": _fibres,
    "particles": _particles,
    "fracture": _fracture,
    "grid": _grid,
}


def build(sample, xs, ys, feature_um, seed):
    """Return (height_nm, material_index, materials, features_resolved)."""
    height = np.zeros((ys.size, xs.size), dtype=np.float64)
    material = np.zeros((ys.size, xs.size), dtype=np.int16)
    resolved = _BUILDERS[sample](xs, ys, height, material, feature_um, seed)
    return height, material, SAMPLES[sample]["materials"], bool(resolved)
