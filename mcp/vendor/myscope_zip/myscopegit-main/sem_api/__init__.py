"""A small SEM (scanning electron microscope) image generation API.

Give it the meta information you would set on a real column - specimen, kV,
spot size, working distance, magnification, focus, stigmators, detector, dwell
time - and it returns a synthetic micrograph. Every accepted parameter and its
boundary is declared in :mod:`sem_api.params` and served by ``GET /schema``.
"""

from .params import ParameterError, defaults, schema, validate  # noqa: F401
from .render import render  # noqa: F401

__version__ = "1.0.0"
__all__ = ["render", "validate", "schema", "defaults", "ParameterError", "__version__"]
