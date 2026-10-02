"""Electron-optical and signal-generation model.

The relations here are the standard textbook ones where a textbook relation
exists (Kanaya-Okayama range, Reimer's backscatter coefficient, Arnal's tilt
dependence); the probe-size and beam-current relations are empirical fits
chosen so that the parameter boundaries in :mod:`params` span the behaviour a
real column shows. Everything is documented so the model can be replaced with
a calibrated one without touching the API layer.
"""

import numpy as np

# Field of view is quoted against a 127 mm wide display, the convention that
# makes "magnification" a meaningful number on a micrograph.
DISPLAY_WIDTH_UM = 127000.0


def field_of_view_um(magnification):
    return DISPLAY_WIDTH_UM / magnification


def convergence_semi_angle_rad(spot_size, working_distance_mm):
    """Beam convergence half-angle. Larger spot = larger aperture-limited angle."""
    return (0.0030 + 0.0012 * spot_size) * (10.0 / working_distance_mm) ** 0.5


def probe_diameter_nm(kv, spot_size, working_distance_mm):
    """Effective probe diameter (FWHM).

    Grows with spot size (more current through the same optics), grows with
    working distance, and shrinks with beam energy because chromatic and
    diffraction contributions fall as the electrons get faster.
    """
    d = 1.2 * (spot_size ** 1.8) * (10.0 / kv) ** 0.35 * (working_distance_mm / 10.0) ** 0.6
    return float(max(d, 0.6))


def defocus_blur_nm(focus_offset_um, spot_size, working_distance_mm):
    alpha = convergence_semi_angle_rad(spot_size, working_distance_mm)
    return float(abs(focus_offset_um) * 1000.0 * alpha)


def astigmatism_blur_nm(astig_x, astig_y, spot_size, working_distance_mm):
    """Returns (magnitude_nm, azimuth_rad) of the extra one-directional blur.

    A stigmator setting is a fixed focal-length difference between two
    orthogonal planes, so like defocus it converts to a blur through the
    convergence angle: full deflection is treated as a 100 um focal split.
    """
    magnitude = float(np.hypot(astig_x, astig_y))
    if magnitude <= 0.0:
        return 0.0, 0.0
    alpha = convergence_semi_angle_rad(spot_size, working_distance_mm)
    blur = magnitude * 100000.0 * alpha
    azimuth = 0.5 * float(np.arctan2(astig_y, astig_x))
    return blur, azimuth


def kanaya_okayama_range_nm(kv, z, a, rho):
    """Electron range in nm. R[um] = 0.0276 * A * E^1.67 / (Z^0.89 * rho)."""
    r_um = 0.0276 * a * (kv ** 1.67) / ((z ** 0.89) * rho)
    return float(r_um * 1000.0)


def backscatter_coefficient(z):
    """Reimer's polynomial fit for normal incidence, valid over Z = 5..80."""
    z = np.asarray(z, dtype=np.float64)
    eta = -0.0254 + 0.016 * z - 1.86e-4 * z ** 2 + 8.3e-7 * z ** 3
    return np.clip(eta, 0.02, 0.62)


def backscatter_tilt(eta0, cos_theta, z):
    """Arnal's tilt dependence: eta(theta) = eta0 ** (1 / (1 + cos theta) ... )."""
    cos_theta = np.clip(cos_theta, 1e-3, 1.0)
    exponent = 9.0 / np.sqrt(np.maximum(z, 1.0))
    return np.clip(eta0 ** (cos_theta ** exponent), 0.0, 1.0)


# A real detector chain does not follow 1/cos all the way to a grazing edge;
# the escape volume is finite and the amplifier saturates. Capping the
# topographic term keeps edges bright without letting them swamp the grey
# levels of the flat areas.
MAX_TOPOGRAPHIC_GAIN = 6.0


def secondary_yield(cos_theta, kv, z):
    """Secondary-electron yield, normalised so flat carbon at 15 kV is ~1.

    The 1/cos(theta) law is what produces edge and topographic contrast; the
    exponent is larger at low kV because the escape depth is then a bigger
    fraction of the interaction volume.
    """
    cos_theta = np.clip(cos_theta, 0.02, 1.0)
    exponent = float(np.clip(1.45 - 0.30 * np.log10(max(kv, 0.2) / 1.0), 1.0, 1.6))
    topo = np.minimum(cos_theta ** (-exponent), MAX_TOPOGRAPHIC_GAIN)
    energy = (max(kv, 0.2) / 15.0) ** -0.35  # yield peaks at low kV
    material = 0.75 + 0.30 * np.sqrt(np.asarray(z, dtype=np.float64) / 30.0)
    return topo * energy * material


def electrons_per_pixel(spot_size, dwell_time_us, kv, detector):
    """Detected electrons per pixel; sets the shot-noise level.

    Beam current scales as spot^3 (probe area x brightness), the signal scales
    linearly with dwell time, and the BSE detector collects a smaller fraction
    of a smaller yield.
    """
    base = 1500.0 * (spot_size / 3.0) ** 3 * (dwell_time_us / 10.0) * (kv / 15.0) ** 0.4
    if detector == "BSE":
        base *= 0.30
    return float(max(base, 0.05))


def charging_severity(charging, kv):
    """How badly the specimen charges at this beam energy.

    Charging vanishes near the second crossover (yield = 1, about 1.5 kV for
    most insulators) and grows as the beam energy moves away from it.
    """
    if charging <= 0.0:
        return 0.0
    return float(charging * np.clip(abs(kv - 1.5) / 12.0, 0.0, 1.0))


def depth_of_field_um(magnification, spot_size, working_distance_mm, width_px):
    """Depth of field, quoted for a one-pixel circle of confusion."""
    alpha = convergence_semi_angle_rad(spot_size, working_distance_mm)
    pixel_um = field_of_view_um(magnification) / width_px
    return float(pixel_um / alpha)
