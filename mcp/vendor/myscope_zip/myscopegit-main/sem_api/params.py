"""Meta-information (parameter) specification for the SEM image API.

Every parameter that the renderer accepts is declared here exactly once, with
an explicit boundary. The same table drives:

  * request validation (``validate``)
  * the machine-readable ``GET /schema`` response
  * the README boundary table
  * the sliders in the playground page

Nothing in the renderer may read a parameter that is not declared here.
"""

from collections import OrderedDict

# ---------------------------------------------------------------------------
# Specimens
# ---------------------------------------------------------------------------
# Each specimen declares the materials it is built from. `z`/`a`/`rho` are the
# atomic number, atomic mass (g/mol) and density (g/cm^3) used by the physics
# model for backscatter yield and interaction-volume size.

SAMPLES = OrderedDict(
    [
        (
            "spheres",
            {
                "label": "Monodisperse latex spheres",
                "feature_meaning": "mean sphere diameter",
                "materials": [
                    {"name": "carbon substrate", "z": 6, "a": 12.0, "rho": 2.0},
                    {"name": "polystyrene sphere", "z": 5.6, "a": 11.4, "rho": 1.05},
                ],
            },
        ),
        (
            "pollen",
            {
                "label": "Pollen grain (spiked, biological)",
                "feature_meaning": "mean grain diameter",
                "materials": [
                    {"name": "carbon tape", "z": 6, "a": 12.0, "rho": 1.8},
                    {"name": "Au/Pd coated tissue", "z": 40.0, "a": 130.0, "rho": 8.0},
                ],
            },
        ),
        (
            "fibres",
            {
                "label": "Non-woven fibre mat",
                "feature_meaning": "fibre diameter",
                "materials": [
                    {"name": "carbon substrate", "z": 6, "a": 12.0, "rho": 2.0},
                    {"name": "polymer fibre", "z": 5.8, "a": 11.6, "rho": 1.2},
                ],
            },
        ),
        (
            "particles",
            {
                "label": "Mixed-composition particles on carbon (Z contrast)",
                "feature_meaning": "mean particle diameter",
                "materials": [
                    {"name": "carbon substrate", "z": 6, "a": 12.0, "rho": 2.0},
                    {"name": "alumina particle", "z": 10.6, "a": 20.4, "rho": 3.95},
                    {"name": "gold particle", "z": 79, "a": 197.0, "rho": 19.3},
                ],
            },
        ),
        (
            "fracture",
            {
                "label": "Brittle fracture surface (steel)",
                "feature_meaning": "dominant roughness wavelength",
                "materials": [{"name": "steel", "z": 26, "a": 55.8, "rho": 7.87}],
            },
        ),
        (
            "grid",
            {
                "label": "Lithographic mesh / TEM grid",
                "feature_meaning": "mesh pitch",
                "materials": [
                    {"name": "carbon film", "z": 6, "a": 12.0, "rho": 2.0},
                    {"name": "copper bar", "z": 29, "a": 63.5, "rho": 8.96},
                ],
            },
        ),
    ]
)

DETECTORS = OrderedDict(
    [
        (
            "SE",
            "Everhart-Thornley secondary-electron detector, mounted off-axis "
            "(upper right). Strong topographic and edge contrast.",
        ),
        (
            "BSE",
            "Annular backscattered-electron detector, on-axis. Compositional "
            "(atomic-number) contrast, weak topography, coarser resolution.",
        ),
    ]
)


def _p(name, group, unit, minimum, maximum, default, description, **extra):
    d = {
        "name": name,
        "group": group,
        "type": "number",
        "unit": unit,
        "min": minimum,
        "max": maximum,
        "default": default,
        "description": description,
    }
    d.update(extra)
    return (name, d)


# ---------------------------------------------------------------------------
# The parameter table. Order is the presentation order.
# ---------------------------------------------------------------------------
PARAMS = OrderedDict(
    [
        # -- specimen ------------------------------------------------------
        (
            "sample",
            {
                "name": "sample",
                "group": "specimen",
                "type": "enum",
                "unit": None,
                "choices": list(SAMPLES.keys()),
                "default": "spheres",
                "description": "Specimen loaded on the stage.",
            },
        ),
        _p(
            "feature_size_um", "specimen", "um", 0.01, 200.0, 5.0,
            "Characteristic specimen feature size; its meaning per sample is "
            "given by GET /samples (sphere diameter, fibre diameter, mesh pitch...).",
        ),
        _p(
            "stage_x_um", "specimen", "um", -10000.0, 10000.0, 0.0,
            "Stage X position. The specimen is generated in world coordinates, "
            "so panning and zooming stay consistent for a given seed.",
        ),
        _p(
            "stage_y_um", "specimen", "um", -10000.0, 10000.0, 0.0,
            "Stage Y position.",
        ),
        _p(
            "tilt_deg", "specimen", "deg", 0.0, 70.0, 0.0,
            "Specimen tilt about the X axis. Foreshortens the image in Y, "
            "raises secondary-electron yield and increases apparent relief.",
        ),
        _p(
            "seed", "specimen", None, 0, 2147483647, 1234,
            "Deterministic specimen seed. Same seed + same stage position = "
            "same specimen, at any magnification.", type="integer",
        ),
        # -- beam ----------------------------------------------------------
        _p(
            "accelerating_voltage_kv", "beam", "kV", 0.2, 30.0, 15.0,
            "Beam energy. Low kV: surface detail, strong edge effect, more "
            "charging. High kV: smaller probe but a much larger interaction "
            "volume, so fine surface detail is washed out.",
        ),
        _p(
            "spot_size", "beam", None, 1.0, 10.0, 3.0,
            "Condenser/spot-size index as on a real column. Beam current scales "
            "as spot^3 (less noise) while the probe diameter grows as spot^1.8 "
            "(less resolution).",
        ),
        # -- optics --------------------------------------------------------
        _p(
            "working_distance_mm", "optics", "mm", 2.0, 40.0, 10.0,
            "Objective working distance. Short WD: best resolution. Long WD: "
            "greater depth of field but a larger probe.",
        ),
        _p(
            "magnification", "optics", "x", 10.0, 300000.0, 1000.0,
            "Magnification referred to a 127 mm wide display, i.e. "
            "field of view = 127000 / magnification micrometres.",
        ),
        _p(
            "focus_offset_um", "optics", "um", -200.0, 200.0, 0.0,
            "Defocus. 0 = in focus. The resulting blur is the defocus times the "
            "convergence semi-angle, so it only matters at high magnification.",
        ),
        _p(
            "astigmatism_x", "optics", None, -1.0, 1.0, 0.0,
            "Stigmator 0/90 degree component. Non-zero values stretch the probe "
            "into an ellipse and smear detail along one direction.",
        ),
        _p(
            "astigmatism_y", "optics", None, -1.0, 1.0, 0.0,
            "Stigmator 45/135 degree component.",
        ),
        _p(
            "scan_rotation_deg", "optics", "deg", 0.0, 360.0, 0.0,
            "Scan rotation. Rotates the raster relative to the specimen without "
            "moving the stage.",
        ),
        # -- signal / scan --------------------------------------------------
        (
            "detector",
            {
                "name": "detector",
                "group": "signal",
                "type": "enum",
                "unit": None,
                "choices": list(DETECTORS.keys()),
                "default": "SE",
                "description": "Detector in use. See GET /schema -> detectors.",
            },
        ),
        _p(
            "dwell_time_us", "signal", "us", 0.05, 200.0, 10.0,
            "Pixel dwell time. Collected electrons per pixel scale linearly with "
            "it, so shot noise falls as 1/sqrt(dwell).",
        ),
        _p(
            "width_px", "signal", "px", 128, 2048, 1024,
            "Image width in pixels.", type="integer",
        ),
        _p(
            "height_px", "signal", "px", 128, 2048, 768,
            "Image height in pixels.", type="integer",
        ),
        # -- image processing ----------------------------------------------
        _p(
            "brightness", "image", None, -1.0, 1.0, 0.0,
            "Detector brightness offset, added after contrast.",
        ),
        _p(
            "contrast", "image", None, 0.1, 3.0, 1.0,
            "Detector contrast gain about mid-grey.",
        ),
        _p(
            "gamma", "image", None, 0.2, 3.0, 1.0,
            "Display gamma applied to the final grey levels.",
        ),
        (
            "databar",
            {
                "name": "databar",
                "group": "image",
                "type": "boolean",
                "unit": None,
                "default": True,
                "description": "Burn the instrument data bar and scale bar into "
                "the bottom of the image.",
            },
        ),
        # -- artefacts ------------------------------------------------------
        _p(
            "charging", "artefacts", None, 0.0, 1.0, 0.0,
            "Specimen charging propensity (0 = conductive/coated). The rendered "
            "severity also depends on kV, and is minimal near the ~1.5 kV E2 "
            "crossover.",
        ),
        _p(
            "drift_um_per_frame", "artefacts", "um", 0.0, 20.0, 0.0,
            "Specimen/thermal drift over one frame. Shears the image along the "
            "slow scan direction.",
        ),
    ]
)

GROUPS = OrderedDict(
    [
        ("specimen", "What is on the stage"),
        ("beam", "Electron beam"),
        ("optics", "Column and scan geometry"),
        ("signal", "Detector and scan speed"),
        ("image", "Display processing"),
        ("artefacts", "Imaging artefacts"),
    ]
)


class ParameterError(ValueError):
    """Raised when a request violates a declared boundary."""

    def __init__(self, parameter, message, boundary=None):
        super().__init__(message)
        self.parameter = parameter
        self.boundary = boundary

    def as_dict(self):
        d = {"error": str(self), "parameter": self.parameter}
        if self.boundary is not None:
            d["boundary"] = self.boundary
        return d


_TRUE = {"1", "true", "yes", "on", "t"}
_FALSE = {"0", "false", "no", "off", "f"}


def _coerce(spec, raw):
    name = spec["name"]
    kind = spec["type"]

    if kind == "enum":
        value = str(raw)
        if value not in spec["choices"]:
            raise ParameterError(
                name,
                "%r is not a valid %s; allowed values: %s"
                % (value, name, ", ".join(spec["choices"])),
                {"choices": spec["choices"]},
            )
        return value

    if kind == "boolean":
        if isinstance(raw, bool):
            return raw
        value = str(raw).strip().lower()
        if value in _TRUE:
            return True
        if value in _FALSE:
            return False
        raise ParameterError(
            name,
            "%r is not a valid boolean for %s" % (raw, name),
            {"choices": ["true", "false"]},
        )

    try:
        number = float(raw)
    except (TypeError, ValueError):
        raise ParameterError(name, "%r is not a number (%s expects %s)" % (raw, name, kind))
    if number != number or number in (float("inf"), float("-inf")):
        raise ParameterError(name, "%s must be finite" % name)

    lo, hi = spec["min"], spec["max"]
    if number < lo or number > hi:
        raise ParameterError(
            name,
            "%s = %g is outside its boundary [%g, %g]%s"
            % (name, number, lo, hi, " " + spec["unit"] if spec["unit"] else ""),
            {"min": lo, "max": hi, "unit": spec["unit"]},
        )
    if kind == "integer":
        return int(round(number))
    return number


def validate(raw_params, clamp=False):
    """Return a complete, validated parameter dict.

    Unknown keys are rejected so that a typo can never be silently ignored.
    With ``clamp=True`` numeric values outside their boundary are pulled to the
    nearest limit instead of raising.
    """
    raw = dict(raw_params or {})
    unknown = [k for k in raw if k not in PARAMS]
    if unknown:
        raise ParameterError(
            unknown[0],
            "unknown parameter %r; see GET /schema for the %d accepted parameters"
            % (unknown[0], len(PARAMS)),
            {"accepted": list(PARAMS.keys())},
        )

    out = {}
    for name, spec in PARAMS.items():
        if name not in raw or raw[name] is None or raw[name] == "":
            out[name] = spec["default"]
            continue
        if clamp and spec["type"] in ("number", "integer"):
            try:
                number = float(raw[name])
            except (TypeError, ValueError):
                raise ParameterError(name, "%r is not a number" % (raw[name],))
            number = min(max(number, spec["min"]), spec["max"])
            out[name] = int(round(number)) if spec["type"] == "integer" else number
            continue
        out[name] = _coerce(spec, raw[name])
    return out


def schema():
    """Machine-readable description of every parameter and its boundary."""
    return {
        "groups": [{"id": k, "label": v} for k, v in GROUPS.items()],
        "parameters": [dict(spec) for spec in PARAMS.values()],
        "samples": [
            {
                "id": key,
                "label": val["label"],
                "feature_size_um_means": val["feature_meaning"],
                "materials": val["materials"],
            }
            for key, val in SAMPLES.items()
        ],
        "detectors": [{"id": k, "description": v} for k, v in DETECTORS.items()],
    }


def defaults():
    return {name: spec["default"] for name, spec in PARAMS.items()}
