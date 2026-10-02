"""Tests for the SEM image API.

    python3 -m unittest discover -s tests -v
"""

import io
import json
import os
import sys
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sem_api import ParameterError, defaults, render, schema, validate  # noqa: E402
from sem_api.params import PARAMS, SAMPLES  # noqa: E402
from sem_api.server import Handler  # noqa: E402

SMALL = {"width_px": 160, "height_px": 128, "databar": False}


class TestBoundaries(unittest.TestCase):
    def test_defaults_are_inside_their_own_boundary(self):
        for name, spec in PARAMS.items():
            if spec["type"] in ("number", "integer"):
                self.assertGreaterEqual(spec["default"], spec["min"], name)
                self.assertLessEqual(spec["default"], spec["max"], name)
            elif spec["type"] == "enum":
                self.assertIn(spec["default"], spec["choices"], name)

    def test_every_parameter_declares_a_boundary(self):
        for name, spec in PARAMS.items():
            self.assertIn(spec["type"], ("number", "integer", "enum", "boolean"), name)
            if spec["type"] in ("number", "integer"):
                self.assertLess(spec["min"], spec["max"], name)
            if spec["type"] == "enum":
                self.assertTrue(spec["choices"], name)
            self.assertTrue(spec["description"].strip(), name)

    def test_out_of_range_is_rejected_with_the_boundary(self):
        with self.assertRaises(ParameterError) as ctx:
            validate({"accelerating_voltage_kv": 99})
        self.assertEqual(ctx.exception.parameter, "accelerating_voltage_kv")
        self.assertEqual(ctx.exception.boundary["max"], 30.0)

    def test_both_limits_are_inclusive(self):
        for name, spec in PARAMS.items():
            if spec["type"] not in ("number", "integer"):
                continue
            for edge in ("min", "max"):
                validate({name: spec[edge]})

    def test_unknown_parameter_is_rejected(self):
        with self.assertRaises(ParameterError) as ctx:
            validate({"magnifcation": 100})
        self.assertEqual(ctx.exception.parameter, "magnifcation")

    def test_bad_enum_lists_the_choices(self):
        with self.assertRaises(ParameterError) as ctx:
            validate({"sample": "banana"})
        self.assertEqual(ctx.exception.boundary["choices"], list(SAMPLES.keys()))

    def test_non_numeric_is_rejected(self):
        for bad in ("abc", "", None, float("nan"), float("inf")):
            if bad in ("", None):
                continue  # empty means "use the default"
            with self.assertRaises(ParameterError):
                validate({"magnification": bad})

    def test_clamp_pulls_to_the_nearest_limit(self):
        p = validate({"magnification": 1e9, "spot_size": -5}, clamp=True)
        self.assertEqual(p["magnification"], PARAMS["magnification"]["max"])
        self.assertEqual(p["spot_size"], PARAMS["spot_size"]["min"])

    def test_missing_parameters_fall_back_to_defaults(self):
        self.assertEqual(validate({}), defaults())

    def test_strings_are_accepted_for_numbers_and_booleans(self):
        p = validate({"magnification": "2500", "width_px": "256", "databar": "false"})
        self.assertEqual(p["magnification"], 2500.0)
        self.assertEqual(p["width_px"], 256)
        self.assertIs(p["databar"], False)

    def test_schema_covers_every_parameter(self):
        names = {entry["name"] for entry in schema()["parameters"]}
        self.assertEqual(names, set(PARAMS))
        self.assertEqual(set(schema()["defaults"] if "defaults" in schema() else defaults()),
                         set(PARAMS))


class TestRendering(unittest.TestCase):
    def test_output_size_matches_the_request(self):
        image, _ = render(validate({**SMALL, "width_px": 200, "height_px": 150}))
        self.assertEqual(image.size, (200, 150))
        self.assertEqual(image.mode, "L")

    def test_databar_adds_rows_below_the_micrograph(self):
        plain, _ = render(validate({**SMALL, "databar": False}))
        barred, _ = render(validate({**SMALL, "databar": True}))
        self.assertEqual(plain.size[0], barred.size[0])
        self.assertGreater(barred.size[1], plain.size[1])

    def test_same_seed_gives_the_same_image(self):
        a, _ = render(validate({**SMALL, "seed": 7}))
        b, _ = render(validate({**SMALL, "seed": 7}))
        c, _ = render(validate({**SMALL, "seed": 8}))
        self.assertEqual(a.tobytes(), b.tobytes())
        self.assertNotEqual(a.tobytes(), c.tobytes())

    def test_every_sample_renders(self):
        for name in SAMPLES:
            image, meta = render(validate({**SMALL, "sample": name}))
            self.assertEqual(image.size, (160, 128))
            self.assertGreater(meta["field_of_view_um"], 0)

    def test_field_of_view_scales_inversely_with_magnification(self):
        _, low = render(validate({**SMALL, "magnification": 100}))
        _, high = render(validate({**SMALL, "magnification": 1000}))
        self.assertAlmostEqual(low["field_of_view_um"] / high["field_of_view_um"], 10.0, places=6)

    def test_longer_dwell_reduces_noise(self):
        import numpy as np

        # The seed fixes both the specimen and the noise stream, so rendering
        # the same scene at a very long dwell gives an almost noise-free
        # reference to measure the shot noise of the faster scans against.
        base = {**SMALL, "sample": "fracture", "magnification": 1000, "feature_size_um": 20}

        def noise_against_reference(dwell):
            reference = np.asarray(render(validate({**base, "dwell_time_us": 200}))[0], float)
            image = np.asarray(render(validate({**base, "dwell_time_us": dwell}))[0], float)
            return float(np.sqrt(((image - reference) ** 2).mean()))

        fast = noise_against_reference(0.05)
        medium = noise_against_reference(5.0)
        self.assertGreater(fast, 4.0 * medium)
        self.assertGreater(medium, 0.0)

    def test_backscatter_resolution_is_limited_by_the_interaction_volume(self):
        base = {**SMALL, "sample": "particles", "magnification": 20000}
        _, se = render(validate({**base, "detector": "SE"}))
        _, bse = render(validate({**base, "detector": "BSE"}))
        self.assertGreater(bse["effective_resolution_nm"], se["effective_resolution_nm"])

    def test_extreme_settings_still_produce_an_image(self):
        for extreme in (
            {"magnification": PARAMS["magnification"]["min"]},
            {"magnification": PARAMS["magnification"]["max"], "feature_size_um": 0.05},
            {"accelerating_voltage_kv": 0.2, "spot_size": 1, "dwell_time_us": 0.05},
            {"accelerating_voltage_kv": 30, "spot_size": 10, "tilt_deg": 70,
             "charging": 1.0, "drift_um_per_frame": 20, "scan_rotation_deg": 359},
            {"feature_size_um": 200, "magnification": 300000},
        ):
            image, meta = render(validate({**SMALL, **extreme}))
            self.assertEqual(image.size, (160, 128))
            self.assertTrue(0.0 < meta["pixel_size_nm"] < 1e9)


class TestHTTP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.server.verbose = False
        cls.base = "http://127.0.0.1:%d" % cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def get(self, path):
        with urlopen(self.base + path, timeout=60) as response:
            return response.status, response.headers, response.read()

    def test_health(self):
        status, _, body = self.get("/health")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["status"], "ok")

    def test_schema_lists_boundaries(self):
        _, _, body = self.get("/schema")
        payload = json.loads(body)
        by_name = {p["name"]: p for p in payload["parameters"]}
        self.assertEqual(by_name["accelerating_voltage_kv"]["min"], 0.2)
        self.assertEqual(by_name["accelerating_voltage_kv"]["max"], 30.0)
        self.assertEqual(len(payload["samples"]), len(SAMPLES))

    def test_render_returns_png_with_metadata_headers(self):
        status, headers, body = self.get("/render?width_px=160&height_px=128&magnification=500")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "image/png")
        self.assertTrue(body.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertAlmostEqual(float(headers["X-SEM-Field-Of-View-Um"]), 254.0, places=1)

    def test_render_json_format(self):
        _, _, body = self.get("/render?width_px=160&height_px=128&format=json")
        payload = json.loads(body)
        self.assertEqual(payload["parameters"]["width_px"], 160)
        self.assertIn("image_png_base64", payload)

    def test_post_render(self):
        request = Request(
            self.base + "/render?format=json",
            data=json.dumps({"sample": "grid", "width_px": 160, "height_px": 128}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=60) as response:
            payload = json.loads(response.read())
        self.assertEqual(payload["parameters"]["sample"], "grid")

    def test_out_of_range_returns_400_with_the_boundary(self):
        with self.assertRaises(HTTPError) as ctx:
            self.get("/render?spot_size=42")
        self.assertEqual(ctx.exception.code, 400)
        payload = json.loads(ctx.exception.read())
        self.assertEqual(payload["parameter"], "spot_size")
        self.assertEqual(payload["boundary"]["max"], 10.0)

    def test_unknown_endpoint_returns_404(self):
        with self.assertRaises(HTTPError) as ctx:
            self.get("/nope")
        self.assertEqual(ctx.exception.code, 404)

    def test_malformed_post_body_returns_400(self):
        request = Request(
            self.base + "/render",
            data=b"{not json",
            headers={"Content-Type": "application/json"},
        )
        with self.assertRaises(HTTPError) as ctx:
            urlopen(request, timeout=30)
        self.assertEqual(ctx.exception.code, 400)

    def test_metadata_endpoint_does_not_render(self):
        _, _, body = self.get("/metadata?magnification=1000&width_px=1024")
        payload = json.loads(body)
        self.assertAlmostEqual(payload["metadata"]["field_of_view_um"], 127.0, places=6)
        self.assertNotIn("image_png_base64", payload)

    def test_playground_is_served(self):
        status, headers, body = self.get("/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", headers["Content-Type"])
        self.assertIn(b"SEM image API", body)


if __name__ == "__main__":
    unittest.main(verbosity=2)
