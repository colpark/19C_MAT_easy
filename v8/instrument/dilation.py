"""Tip dilation (Villarrubia) as grey_dilation with the tip as the structuring element.

Fallback for Gwyddion pygwy, which has no Python 3 build on the Spark nodes (V8-0).
Heights and lengths share one unit (Angstrom). The tip is afmize's model: a
hemisphere of radius R joined to a cone of half-angle alpha.
"""
import numpy as np
from scipy.ndimage import grey_dilation


def tip_profile(radius, angle_deg, px, half_width_px=None):
    """Tip height relative to its apex (<= 0) on a (2h+1)^2 pixel grid."""
    a = np.radians(angle_deg)
    if half_width_px is None:
        half_width_px = int(np.ceil(3 * radius / px)) + 1
    r = px * np.hypot(*np.mgrid[-half_width_px:half_width_px + 1, -half_width_px:half_width_px + 1])
    r_join = radius * np.cos(a)  # sphere meets cone where the slope equals the cone's
    sphere = radius - np.sqrt(np.clip(radius**2 - r**2, 0, None))
    z_join = radius - np.sqrt(radius**2 - r_join**2)
    cone = z_join + (r - r_join) / np.tan(a)
    return -np.where(r <= r_join, sphere, cone)


def dilate(height, radius, angle_deg, px):
    """Image of `height` (2D, px spacing) scanned by the tip: max over tip of (h + tip)."""
    return grey_dilation(height, structure=tip_profile(radius, angle_deg, px), mode="nearest")
