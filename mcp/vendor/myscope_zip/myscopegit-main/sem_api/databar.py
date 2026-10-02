"""Instrument data bar and scale bar burnt into the bottom of the image."""

import numpy as np
from PIL import Image, ImageDraw, ImageFont

_FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/Library/Fonts/Arial.ttf",
]


def _font(size):
    for path in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Pillow < 10.1
        return ImageFont.load_default()


def _nice_length_um(target_um):
    """Round a length down to the nearest 1-2-5 x 10^n value."""
    exponent = np.floor(np.log10(target_um))
    base = target_um / (10.0 ** exponent)
    for step in (5.0, 2.0, 1.0):
        if base >= step:
            return step * (10.0 ** exponent)
    return 10.0 ** exponent


def _format_length(um):
    if um < 1.0:
        return "%g nm" % round(um * 1000.0, 3)
    if um >= 1000.0:
        return "%g mm" % round(um / 1000.0, 3)
    return "%g um" % round(um, 3)


def _format_mag(mag):
    if mag >= 1000.0:
        return "%.2f k x" % (mag / 1000.0)
    return "%.0f x" % mag


def draw(image, params, meta):
    """Return a new image with the data bar appended below the micrograph."""
    width, height = image.size
    bar_h = max(26, int(round(width * 0.045)))
    font = _font(max(11, int(bar_h * 0.42)))

    out = Image.new("L", (width, height + bar_h), 0)
    out.paste(image, (0, 0))
    draw_ctx = ImageDraw.Draw(out)
    draw_ctx.rectangle([0, height, width, height + bar_h], fill=20)
    draw_ctx.line([(0, height), (width, height)], fill=90)

    # --- scale bar (left) ---------------------------------------------------
    fov_um = meta["field_of_view_um"]
    length_um = _nice_length_um(fov_um / 5.0)
    length_px = int(round(length_um / fov_um * width))
    pad = max(8, bar_h // 5)
    y_mid = height + bar_h // 2
    x0 = pad
    x1 = x0 + length_px
    draw_ctx.line([(x0, y_mid), (x1, y_mid)], fill=255, width=max(2, bar_h // 12))
    tick = max(4, bar_h // 5)
    for x in (x0, x1):
        draw_ctx.line([(x, y_mid - tick), (x, y_mid + tick)], fill=255,
                      width=max(2, bar_h // 12))
    label = _format_length(length_um)
    draw_ctx.text((x0, y_mid - tick - int(bar_h * 0.46)), label, fill=255, font=font)

    # --- instrument settings (right) ---------------------------------------
    text = "  |  ".join(
        [
            "%.1f kV" % params["accelerating_voltage_kv"],
            _format_mag(params["magnification"]),
            "WD %.1f mm" % params["working_distance_mm"],
            "spot %g" % params["spot_size"],
            params["detector"],
            "%s/px" % _format_length(meta["pixel_size_nm"] / 1000.0),
        ]
    )
    bbox = draw_ctx.textbbox((0, 0), text, font=font)
    draw_ctx.text(
        (width - pad - (bbox[2] - bbox[0]), y_mid - (bbox[3] - bbox[1]) // 2 - 2),
        text,
        fill=235,
        font=font,
    )
    return out
