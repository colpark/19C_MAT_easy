"""The render pipeline: validated parameters in, micrograph out.

Order of operations mirrors the instrument:

    specimen (world coords) -> scan geometry -> electron-solid signal
      -> probe/interaction-volume blur -> charging -> shot noise
      -> detector gain and display gamma -> data bar

Anything that is a *beam* effect happens before the noise; anything that is a
*display* effect happens after it.
"""

import numpy as np
from PIL import Image
from scipy import ndimage, signal as sp_signal

from . import databar, physics, scene

# Everhart-Thornley detector direction: upper right of the image, 30 deg
# elevation. Image row index increases downwards, hence the negative y.
_ET_DIR = np.array([0.612, -0.612, 0.5])
_ET_DIR = _ET_DIR / np.linalg.norm(_ET_DIR)

MAX_WORLD_RASTER = 4096


def _screen_to_world(p, width, height, pixel_um):
    """Sampling coordinates of every pixel, in specimen world micrometres."""
    sx = (np.arange(width) + 0.5 - width / 2.0) * pixel_um
    sy = (np.arange(height) + 0.5 - height / 2.0) * pixel_um

    rot = np.radians(p["scan_rotation_deg"])
    tilt = np.radians(p["tilt_deg"])
    drift = p["drift_um_per_frame"]
    identity = rot == 0.0 and tilt == 0.0 and drift == 0.0

    if identity:
        return sx + p["stage_x_um"], sy + p["stage_y_um"], None, None, True

    SX, SY = np.meshgrid(sx, sy)
    if rot:
        c, s = np.cos(rot), np.sin(rot)
        SX, SY = SX * c - SY * s, SX * s + SY * c
    if tilt:
        # A tilted specimen is foreshortened along Y on the screen, so one
        # screen micrometre covers more specimen along Y.
        SY = SY / np.cos(tilt)
    if drift:
        t = (np.arange(height) / max(height - 1, 1))[:, None]
        SX = SX + drift * t
        SY = SY + 0.35 * drift * t
    return None, None, SX + p["stage_x_um"], SY + p["stage_y_um"], False


def _build_fields(p, width, height, pixel_um):
    """Height (nm) and material index sampled on the screen raster."""
    xs, ys, XW, YW, identity = _screen_to_world(p, width, height, pixel_um)

    if identity:
        return scene.build(p["sample"], xs, ys, p["feature_size_um"], p["seed"])

    # Rasterise the specimen on a world-aligned grid, then sample it.
    step = pixel_um
    x0, x1 = float(XW.min()), float(XW.max())
    y0, y1 = float(YW.min()), float(YW.max())
    nx = int(np.ceil((x1 - x0) / step)) + 2
    ny = int(np.ceil((y1 - y0) / step)) + 2
    if max(nx, ny) > MAX_WORLD_RASTER:
        step *= max(nx, ny) / float(MAX_WORLD_RASTER)
        nx = int(np.ceil((x1 - x0) / step)) + 2
        ny = int(np.ceil((y1 - y0) / step)) + 2
    xs = x0 + np.arange(nx) * step
    ys = y0 + np.arange(ny) * step

    height_w, material_w, materials, resolved = scene.build(
        p["sample"], xs, ys, p["feature_size_um"], p["seed"]
    )
    coords = np.array([(YW - y0) / step, (XW - x0) / step])
    height_s = ndimage.map_coordinates(height_w, coords, order=1, mode="nearest")
    material_s = ndimage.map_coordinates(material_w, coords, order=0, mode="nearest")
    return height_s, material_s, materials, resolved


def _surface_signal(p, height_nm, material, materials, pixel_um):
    """Emitted signal per pixel before any blurring."""
    tilt = np.radians(p["tilt_deg"])
    dx_nm = pixel_um * 1000.0
    dy_nm = dx_nm / max(np.cos(tilt), 1e-3)

    dzdx = np.gradient(height_nm, axis=1) / dx_nm
    dzdy = np.gradient(height_nm, axis=0) / dy_nm
    # Tilting the stage tilts the surface with respect to the beam.
    dzdy = dzdy + np.tan(tilt)

    inv = 1.0 / np.sqrt(1.0 + dzdx ** 2 + dzdy ** 2)
    nx, ny, nz = -dzdx * inv, -dzdy * inv, inv
    cos_theta = nz

    z_values = np.array([m["z"] for m in materials], dtype=np.float64)
    z_map = z_values[np.clip(material, 0, len(materials) - 1)]

    if p["detector"] == "SE":
        sig = physics.secondary_yield(cos_theta, p["accelerating_voltage_kv"], z_map)
        toward = nx * _ET_DIR[0] + ny * _ET_DIR[1] + nz * _ET_DIR[2]
        sig = sig * (0.55 + 0.45 * np.clip(toward, 0.0, 1.0))
        # Shadowing: recessed points see less of the detector.
        blurred = ndimage.gaussian_filter(height_nm, sigma=8.0, mode="nearest")
        relief = height_nm - blurred
        spread = float(relief.std()) + 1e-6
        sig = sig * np.clip(0.55 + 0.45 * relief / (2.0 * spread), 0.15, 1.4)
    else:
        eta0 = physics.backscatter_coefficient(z_map)
        sig = physics.backscatter_tilt(eta0, cos_theta, z_map)
        # An annular on-axis detector is nearly blind to topography.
        sig = sig * (0.85 + 0.15 * cos_theta)

    return sig, z_map


def _apply_astigmatism(sig, blur_nm, azimuth, pixel_nm):
    sigma_px = min(blur_nm / 2.355 / pixel_nm, 60.0)
    if sigma_px < 0.15:
        return sig
    deg = np.degrees(azimuth)
    rotated = ndimage.rotate(sig, deg, reshape=False, order=1, mode="nearest")
    rotated = ndimage.gaussian_filter1d(rotated, sigma_px, axis=1, mode="nearest")
    return ndimage.rotate(rotated, -deg, reshape=False, order=1, mode="nearest")


def _apply_charging(sig, cos_theta_proxy, severity, seed, pixel_nm):
    """Bright edges and horizontal streaks from a non-conducting specimen."""
    slope = np.clip(1.0 - cos_theta_proxy, 0.0, 1.0)
    glow = ndimage.gaussian_filter(slope, sigma=max(2.0, 400.0 / pixel_nm), mode="nearest")
    sig = sig + severity * 1.8 * glow

    rng = np.random.default_rng((int(seed) * 2654435761 + 991) % (2 ** 32))
    rows = rng.random(sig.shape[0]) < (0.015 + 0.10 * severity)
    n_rows = int(rows.sum())
    if n_rows:
        width = sig.shape[1]
        # Each streak starts where the beam crossed a charged feature and
        # bleeds to the right along the fast scan direction.
        start = rng.integers(0, width, size=n_rows)[:, None]
        columns = np.arange(width)[None, :]
        amplitude = rng.uniform(0.4, 1.3, size=n_rows)[:, None] * severity
        impulse = amplitude * (columns == start)
        alpha = 0.985  # decay length ~1/(1 - alpha) pixels
        trail = sp_signal.lfilter([1.0], [1.0, -alpha], impulse, axis=1)
        sig[rows] = np.minimum(sig[rows] + trail, 2.5)
    return sig


TARGET_MEAN_LEVEL = 0.45
HIGHLIGHT_KNEE = 0.75


def _expose(sig):
    """Detector gain, set the way an operator sets it: mean level only.

    Deliberately *not* a percentile stretch. Stretching the histogram to fill
    the range would give a nearly featureless field the same contrast as a
    sharp micrograph, so unresolved specimens would come back as full-scale
    white noise. Fixing only the mean leaves the contrast where the physics put
    it, and the highlight knee stands in for amplifier saturation on edges.
    """
    mean = float(np.mean(sig))
    if mean <= 1e-9:
        return np.zeros_like(sig)
    v = sig * (TARGET_MEAN_LEVEL / mean)
    high = v > HIGHLIGHT_KNEE
    headroom = 1.0 - HIGHLIGHT_KNEE
    v[high] = HIGHLIGHT_KNEE + headroom * (1.0 - np.exp(-(v[high] - HIGHLIGHT_KNEE) / headroom))
    return np.clip(v, 0.0, 1.0)


def render(p):
    """Render a micrograph. ``p`` must already be validated by params.validate.

    Returns ``(PIL.Image, metadata)``.
    """
    out_w, out_h = int(p["width_px"]), int(p["height_px"])
    fov_um = physics.field_of_view_um(p["magnification"])

    # Supersampling stands in for the beam integrating continuously across each
    # pixel as it scans. Features smaller than a pixel need more subsamples or
    # they alias into white noise instead of averaging into texture.
    ss = 2
    if p["feature_size_um"] < 3.0 * (fov_um / out_w):
        ss = 4 if out_w * out_h <= 400000 else 3
    while ss > 1 and out_w * out_h * ss * ss > 9000000:
        ss -= 1
    width, height = out_w * ss, out_h * ss
    pixel_um = fov_um / width
    pixel_nm = pixel_um * 1000.0

    height_nm, material, materials, resolved = _build_fields(p, width, height, pixel_um)
    sig, z_map = _surface_signal(p, height_nm, material, materials, pixel_um)

    # --- probe and interaction volume --------------------------------------
    kv = p["accelerating_voltage_kv"]
    probe_nm = physics.probe_diameter_nm(kv, p["spot_size"], p["working_distance_mm"])
    defocus_nm = physics.defocus_blur_nm(
        p["focus_offset_um"], p["spot_size"], p["working_distance_mm"]
    )
    astig_nm, astig_azimuth = physics.astigmatism_blur_nm(
        p["astigmatism_x"], p["astigmatism_y"], p["spot_size"], p["working_distance_mm"]
    )
    mean_z = float(np.mean([m["z"] for m in materials]))
    mean_a = float(np.mean([m["a"] for m in materials]))
    mean_rho = float(np.mean([m["rho"] for m in materials]))
    range_nm = physics.kanaya_okayama_range_nm(kv, mean_z, mean_a, mean_rho)

    if astig_nm > 0.0:
        sig = _apply_astigmatism(sig, astig_nm, astig_azimuth, pixel_nm)

    # Beam blur budget, in nm on the specimen, before the raster is considered.
    beam_fwhm_nm = float(np.sqrt(probe_nm ** 2 + defocus_nm ** 2 + astig_nm ** 2))
    sigma_px = max(np.hypot(probe_nm, defocus_nm) / 2.355 / pixel_nm, 0.35)
    if p["detector"] == "SE":
        sharp = ndimage.gaussian_filter(sig, sigma_px, mode="nearest")
        broad_px = min(np.hypot(sigma_px, range_nm / 3.0 / 2.355 / pixel_nm), 80.0)
        broad = ndimage.gaussian_filter(sig, broad_px, mode="nearest")
        sig = 0.78 * sharp + 0.22 * broad
        signal_fwhm_nm = beam_fwhm_nm
    else:
        bse_px = min(np.hypot(sigma_px, range_nm / 2.5 / 2.355 / pixel_nm), 120.0)
        sig = ndimage.gaussian_filter(sig, bse_px, mode="nearest")
        # A backscatter image cannot be sharper than the interaction volume.
        signal_fwhm_nm = float(np.hypot(beam_fwhm_nm, range_nm / 2.5))
    # What the operator actually sees is limited by the coarser of the two.
    effective_nm = max(signal_fwhm_nm, fov_um * 1000.0 / out_w)

    # --- specimen charging --------------------------------------------------
    severity = physics.charging_severity(p["charging"], kv)
    if severity > 0.0:
        proxy = ndimage.gaussian_filter(np.abs(np.gradient(height_nm, axis=1)), 2.0)
        proxy = 1.0 - np.clip(proxy / (proxy.max() + 1e-9), 0.0, 1.0)
        sig = _apply_charging(sig, proxy, severity, p["seed"], pixel_nm)

    # --- detection ----------------------------------------------------------
    sig = _expose(sig)
    n_per_pixel = physics.electrons_per_pixel(
        p["spot_size"], p["dwell_time_us"], kv, p["detector"]
    )
    n_sub = max(n_per_pixel / (ss * ss), 1e-3)
    rng = np.random.default_rng((int(p["seed"]) * 7919 + 13) % (2 ** 32))
    sig = rng.poisson(np.clip(sig, 0.0, None) * n_sub) / n_sub

    # --- display ------------------------------------------------------------
    sig = (sig - 0.5) * p["contrast"] + 0.5 + p["brightness"]
    sig = np.clip(sig, 0.0, 1.0) ** (1.0 / p["gamma"])

    if ss > 1:
        sig = sig.reshape(out_h, ss, out_w, ss).mean(axis=(1, 3))

    image = Image.fromarray(np.clip(sig * 255.0, 0, 255).astype(np.uint8), mode="L")

    meta = {
        "field_of_view_um": fov_um,
        "field_of_view_y_um": fov_um * out_h / out_w,
        "pixel_size_nm": fov_um * 1000.0 / out_w,
        "probe_diameter_nm": probe_nm,
        "defocus_blur_nm": defocus_nm,
        "astigmatism_blur_nm": astig_nm,
        "interaction_range_nm": range_nm,
        "signal_fwhm_nm": signal_fwhm_nm,
        "effective_resolution_nm": float(effective_nm),
        "depth_of_field_um": physics.depth_of_field_um(
            p["magnification"], p["spot_size"], p["working_distance_mm"], out_w
        ),
        "electrons_per_pixel": n_per_pixel,
        "estimated_snr": float(np.sqrt(n_per_pixel)),
        "frame_time_s": p["dwell_time_us"] * 1e-6 * out_w * out_h,
        "charging_severity": severity,
        "mean_atomic_number": mean_z,
        "supersampling": ss,
        "features_resolved": resolved,
    }

    if p["databar"]:
        image = databar.draw(image, p, meta)
    return image, meta
