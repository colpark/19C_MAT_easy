"""HTTP API for the SEM image generator.

Standard library only, so it runs with no install step:

    python3 -m sem_api.server --port 8080

Endpoints
    GET  /                 interactive playground (HTML)
    GET  /health           liveness probe
    GET  /schema           every parameter with its boundary, samples, detectors
    GET  /samples          specimen list with the meaning of feature_size_um
    GET  /metadata?...     derived optics for a parameter set, no rendering
    GET  /render?...       PNG micrograph, parameters as query string
    POST /render           PNG micrograph, parameters as a JSON body

    Add ?format=json to /render for {parameters, metadata, image_png_base64}.
    Add ?clamp=1 to pull out-of-range numbers to the nearest boundary instead
    of returning 400.
"""

import argparse
import base64
import io
import json
import os
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import physics
from .params import ParameterError, SAMPLES, defaults, schema, validate
from .render import render

MAX_BODY_BYTES = 64 * 1024
_HERE = os.path.dirname(os.path.abspath(__file__))


def _flatten_query(query):
    return {k: v[-1] for k, v in parse_qs(query, keep_blank_values=False).items()}


def _derived(p):
    fov = physics.field_of_view_um(p["magnification"])
    probe = physics.probe_diameter_nm(
        p["accelerating_voltage_kv"], p["spot_size"], p["working_distance_mm"]
    )
    materials = SAMPLES[p["sample"]]["materials"]
    mean_z = sum(m["z"] for m in materials) / len(materials)
    mean_a = sum(m["a"] for m in materials) / len(materials)
    mean_rho = sum(m["rho"] for m in materials) / len(materials)
    n = physics.electrons_per_pixel(
        p["spot_size"], p["dwell_time_us"], p["accelerating_voltage_kv"], p["detector"]
    )
    return {
        "field_of_view_um": fov,
        "pixel_size_nm": fov * 1000.0 / p["width_px"],
        "probe_diameter_nm": probe,
        "defocus_blur_nm": physics.defocus_blur_nm(
            p["focus_offset_um"], p["spot_size"], p["working_distance_mm"]
        ),
        "astigmatism_blur_nm": physics.astigmatism_blur_nm(
            p["astigmatism_x"], p["astigmatism_y"], p["spot_size"],
            p["working_distance_mm"],
        )[0],
        "interaction_range_nm": physics.kanaya_okayama_range_nm(
            p["accelerating_voltage_kv"], mean_z, mean_a, mean_rho
        ),
        "depth_of_field_um": physics.depth_of_field_um(
            p["magnification"], p["spot_size"], p["working_distance_mm"], p["width_px"]
        ),
        "electrons_per_pixel": n,
        "estimated_snr": n ** 0.5,
        "frame_time_s": p["dwell_time_us"] * 1e-6 * p["width_px"] * p["height_px"],
        "charging_severity": physics.charging_severity(
            p["charging"], p["accelerating_voltage_kv"]
        ),
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "SEMSimAPI/1.0"
    protocol_version = "HTTP/1.1"

    # -- plumbing ----------------------------------------------------------
    def log_message(self, fmt, *args):
        if self.server.verbose:
            super().log_message(fmt, *args)

    def _send(self, code, body, content_type, extra_headers=None):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, code, payload, extra_headers=None):
        self._send(code, json.dumps(payload, indent=2, default=float) + "\n",
                   "application/json; charset=utf-8", extra_headers)

    def _read_json_body(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        if length > MAX_BODY_BYTES:
            raise ParameterError("body", "request body larger than %d bytes" % MAX_BODY_BYTES)
        raw = self.rfile.read(length)
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            raise ParameterError("body", "request body is not valid JSON: %s" % exc)
        if not isinstance(parsed, dict):
            raise ParameterError("body", "request body must be a JSON object")
        return parsed

    # -- routes ------------------------------------------------------------
    def do_OPTIONS(self):
        self._send(204, b"", "text/plain", {"Access-Control-Allow-Methods": "GET, POST, OPTIONS"})

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        url = urlparse(self.path)
        query = _flatten_query(url.query)
        try:
            if url.path == "/":
                return self._playground()
            if url.path == "/health":
                return self._json(200, {"status": "ok", "service": "sem-image-api"})
            if url.path == "/schema":
                return self._json(200, {**schema(), "defaults": defaults()})
            if url.path == "/samples":
                return self._json(200, schema()["samples"])
            if url.path == "/metadata":
                p = validate(_strip_control(query), clamp=_flag(query, "clamp"))
                return self._json(200, {"parameters": p, "metadata": _derived(p)})
            if url.path == "/render":
                return self._render(_strip_control(query), query)
            return self._json(404, {"error": "no such endpoint: %s" % url.path,
                                    "endpoints": ["/", "/health", "/schema", "/samples",
                                                  "/metadata", "/render"]})
        except ParameterError as exc:
            return self._json(400, exc.as_dict())
        except Exception as exc:  # pragma: no cover - surfaced to the client
            traceback.print_exc()
            return self._json(500, {"error": "render failed: %s" % exc})

    def do_POST(self):
        url = urlparse(self.path)
        query = _flatten_query(url.query)
        try:
            if url.path not in ("/render", "/metadata"):
                return self._json(404, {"error": "POST is only accepted on /render and /metadata"})
            body = self._read_json_body()
            if url.path == "/metadata":
                p = validate(body, clamp=_flag(query, "clamp"))
                return self._json(200, {"parameters": p, "metadata": _derived(p)})
            return self._render(body, query)
        except ParameterError as exc:
            return self._json(400, exc.as_dict())
        except Exception as exc:  # pragma: no cover
            traceback.print_exc()
            return self._json(500, {"error": "render failed: %s" % exc})

    def _render(self, raw_params, query):
        p = validate(raw_params, clamp=_flag(query, "clamp"))
        image, meta = render(p)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG", optimize=False)
        png = buffer.getvalue()

        if query.get("format", "png").lower() == "json":
            return self._json(200, {
                "parameters": p,
                "metadata": meta,
                "image_png_base64": base64.b64encode(png).decode("ascii"),
            })

        headers = {
            "X-SEM-Field-Of-View-Um": "%.4g" % meta["field_of_view_um"],
            "X-SEM-Pixel-Size-Nm": "%.4g" % meta["pixel_size_nm"],
            "X-SEM-Probe-Diameter-Nm": "%.4g" % meta["probe_diameter_nm"],
            "X-SEM-Effective-Resolution-Nm": "%.4g" % meta["effective_resolution_nm"],
            "X-SEM-Interaction-Range-Nm": "%.4g" % meta["interaction_range_nm"],
            "X-SEM-Electrons-Per-Pixel": "%.4g" % meta["electrons_per_pixel"],
            "X-SEM-Frame-Time-S": "%.4g" % meta["frame_time_s"],
            "X-SEM-Features-Resolved": "true" if meta["features_resolved"] else "false",
            "Content-Disposition": 'inline; filename="sem_%s_%gx.png"'
                                   % (p["sample"], p["magnification"]),
        }
        return self._send(200, png, "image/png", headers)

    def _playground(self):
        path = os.path.join(_HERE, "playground.html")
        with open(path, "rb") as handle:
            self._send(200, handle.read(), "text/html; charset=utf-8")


_CONTROL_KEYS = ("format", "clamp")


def _strip_control(query):
    return {k: v for k, v in query.items() if k not in _CONTROL_KEYS}


def _flag(query, name):
    return str(query.get(name, "")).lower() in ("1", "true", "yes", "on")


def serve(host="127.0.0.1", port=8080, verbose=True):
    httpd = ThreadingHTTPServer((host, port), Handler)
    httpd.verbose = verbose
    print("SEM image API listening on http://%s:%d  (Ctrl-C to stop)" % (host, port))
    print("  playground: http://%s:%d/" % (host, port))
    print("  schema:     http://%s:%d/schema" % (host, port))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping")
    finally:
        httpd.server_close()


def main():
    parser = argparse.ArgumentParser(description="SEM image generation API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    serve(args.host, args.port, verbose=not args.quiet)


if __name__ == "__main__":
    main()
