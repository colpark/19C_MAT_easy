# SEM image API

A small HTTP API that generates synthetic scanning-electron-microscope
micrographs from the meta information you would set on a real column: specimen,
accelerating voltage, spot size, working distance, magnification, focus,
stigmators, detector, dwell time, tilt, and the usual artefacts.

It exists because [MyScope's SEM simulator](https://myscope.training/SEM_simulator.html)
has no API — it is a client-side teaching page with no server endpoint behind
it. Rather than scraping that page with a headless browser, this reimplements
the underlying image formation, so image generation is scriptable, deterministic
and documented.

Every accepted parameter has an explicit boundary, declared once in
`sem_api/params.py` and served at `GET /schema`. Out-of-range values are
refused with the boundary in the error body; nothing is silently clipped unless
you ask for it with `?clamp=1`.

## Run it

Needs Python 3.9+ and three libraries — numpy, scipy and Pillow. No web
framework: the HTTP layer is standard library only.

```bash
python3 -m pip install -r requirements.txt
```

```bash
python3 -m sem_api.server --port 8080
# playground:  http://127.0.0.1:8080/
# schema:      http://127.0.0.1:8080/schema
```

```bash
# a PNG straight to disk
curl -o spheres.png \
  "http://127.0.0.1:8080/render?sample=spheres&feature_size_um=8&magnification=2000&accelerating_voltage_kv=15&detector=SE"

# same thing as JSON, with the derived optics alongside the image
curl -X POST http://127.0.0.1:8080/render?format=json \
  -H 'Content-Type: application/json' \
  -d '{"sample":"particles","detector":"BSE","magnification":1200,"dwell_time_us":20}'
```

Or use it as a library, without the server:

```python
from sem_api import render, validate

image, meta = render(validate({"sample": "fibres", "magnification": 800}))
image.save("fibres.png")
print(meta["effective_resolution_nm"], meta["depth_of_field_um"])
```

## Endpoints

| method | path | returns |
|---|---|---|
| `GET` | `/` | interactive playground; every control is built from `/schema` |
| `GET` | `/health` | liveness probe |
| `GET` | `/schema` | every parameter with its boundary, plus samples, detectors, defaults |
| `GET` | `/samples` | specimen list and what `feature_size_um` means for each |
| `GET` | `/metadata?…` | derived optics for a parameter set, without rendering |
| `GET` | `/render?…` | `image/png`, parameters as query string |
| `POST` | `/render` | `image/png`, parameters as a JSON body |

Modifiers: `?format=json` returns `{parameters, metadata, image_png_base64}`
instead of a PNG; `?clamp=1` pulls out-of-range numbers to the nearest boundary
instead of returning `400`.

A PNG response also carries the derived values as headers:
`X-SEM-Field-Of-View-Um`, `X-SEM-Pixel-Size-Nm`, `X-SEM-Probe-Diameter-Nm`,
`X-SEM-Effective-Resolution-Nm`, `X-SEM-Interaction-Range-Nm`,
`X-SEM-Electrons-Per-Pixel`, `X-SEM-Frame-Time-S`, `X-SEM-Features-Resolved`.

## Parameters and their boundaries

24 parameters, all optional — anything you omit takes its default. Limits are
inclusive.

### What is on the stage
| parameter | unit | boundary | default | meaning |
|---|---|---|---|---|
| `sample` | - | `spheres` \| `pollen` \| `fibres` \| `particles` \| `fracture` \| `grid` | `spheres` | Specimen loaded on the stage. |
| `feature_size_um` | um | 0.01 … 200 | `5.0` | Characteristic specimen feature size; its meaning per sample is given by GET /samples (sphere diameter, fibre diameter, mesh pitch...). |
| `stage_x_um` | um | -10000 … 10000 | `0.0` | Stage X position. The specimen is generated in world coordinates, so panning and zooming stay consistent for a given seed. |
| `stage_y_um` | um | -10000 … 10000 | `0.0` | Stage Y position. |
| `tilt_deg` | deg | 0 … 70 | `0.0` | Specimen tilt about the X axis. Foreshortens the image in Y, raises secondary-electron yield and increases apparent relief. |
| `seed` | - | 0 … 2.14748e+09 | `1234` | Deterministic specimen seed. Same seed + same stage position = same specimen, at any magnification. |

### Electron beam
| parameter | unit | boundary | default | meaning |
|---|---|---|---|---|
| `accelerating_voltage_kv` | kV | 0.2 … 30 | `15.0` | Beam energy. Low kV: surface detail, strong edge effect, more charging. High kV: smaller probe but a much larger interaction volume, so fine surface detail is washed out. |
| `spot_size` | - | 1 … 10 | `3.0` | Condenser/spot-size index as on a real column. Beam current scales as spot^3 (less noise) while the probe diameter grows as spot^1.8 (less resolution). |

### Column and scan geometry
| parameter | unit | boundary | default | meaning |
|---|---|---|---|---|
| `working_distance_mm` | mm | 2 … 40 | `10.0` | Objective working distance. Short WD: best resolution. Long WD: greater depth of field but a larger probe. |
| `magnification` | x | 10 … 300000 | `1000.0` | Magnification referred to a 127 mm wide display, i.e. field of view = 127000 / magnification micrometres. |
| `focus_offset_um` | um | -200 … 200 | `0.0` | Defocus. 0 = in focus. The resulting blur is the defocus times the convergence semi-angle, so it only matters at high magnification. |
| `astigmatism_x` | - | -1 … 1 | `0.0` | Stigmator 0/90 degree component. Non-zero values stretch the probe into an ellipse and smear detail along one direction. |
| `astigmatism_y` | - | -1 … 1 | `0.0` | Stigmator 45/135 degree component. |
| `scan_rotation_deg` | deg | 0 … 360 | `0.0` | Scan rotation. Rotates the raster relative to the specimen without moving the stage. |

### Detector and scan speed
| parameter | unit | boundary | default | meaning |
|---|---|---|---|---|
| `detector` | - | `SE` \| `BSE` | `SE` | Detector in use. See GET /schema -> detectors. |
| `dwell_time_us` | us | 0.05 … 200 | `10.0` | Pixel dwell time. Collected electrons per pixel scale linearly with it, so shot noise falls as 1/sqrt(dwell). |
| `width_px` | px | 128 … 2048 | `1024` | Image width in pixels. |
| `height_px` | px | 128 … 2048 | `768` | Image height in pixels. |

### Display processing
| parameter | unit | boundary | default | meaning |
|---|---|---|---|---|
| `brightness` | - | -1 … 1 | `0.0` | Detector brightness offset, added after contrast. |
| `contrast` | - | 0.1 … 3 | `1.0` | Detector contrast gain about mid-grey. |
| `gamma` | - | 0.2 … 3 | `1.0` | Display gamma applied to the final grey levels. |
| `databar` | - | `true` \| `false` | `True` | Burn the instrument data bar and scale bar into the bottom of the image. |

### Imaging artefacts
| parameter | unit | boundary | default | meaning |
|---|---|---|---|---|
| `charging` | - | 0 … 1 | `0.0` | Specimen charging propensity (0 = conductive/coated). The rendered severity also depends on kV, and is minimal near the ~1.5 kV E2 crossover. |
| `drift_um_per_frame` | um | 0 … 20 | `0.0` | Specimen/thermal drift over one frame. Shears the image along the slow scan direction. |

### Rejected values

```console
$ curl "http://127.0.0.1:8080/render?accelerating_voltage_kv=99"
{
  "error": "accelerating_voltage_kv = 99 is outside its boundary [0.2, 30] kV",
  "parameter": "accelerating_voltage_kv",
  "boundary": {"min": 0.2, "max": 30.0, "unit": "kV"}
}
```

Unknown parameter names are rejected the same way, so a typo can never be
silently ignored:

```console
$ curl "http://127.0.0.1:8080/render?magnifcation=100"
{"error": "unknown parameter 'magnifcation'; see GET /schema for the 24 accepted parameters", ...}
```

## Specimens

`feature_size_um` means something slightly different for each specimen, and
each one carries its own materials, which is what drives backscatter contrast.

| sample | what it is | `feature_size_um` is | materials (Z) |
|---|---|---|---|
| `spheres` | monodisperse latex spheres on carbon | mean sphere diameter | C (6), polystyrene (5.6) |
| `pollen` | spiked biological grain, Au/Pd coated | mean grain diameter | C (6), Au/Pd coat (40) |
| `fibres` | non-woven polymer fibre mat | fibre diameter | C (6), polymer (5.8) |
| `particles` | mixed light/heavy particles on carbon | mean particle diameter | C (6), alumina (10.6), Au (79) |
| `fracture` | brittle fracture surface | dominant roughness wavelength | steel (26) |
| `grid` | lithographic mesh / TEM grid | mesh pitch | C film (6), Cu bar (29) |

Specimens are generated in world coordinates from `seed`, not per image, so
`magnification` really zooms into the same object and `stage_x_um` /
`stage_y_um` really pan across it. Use `particles` with `detector=BSE` to see
atomic-number contrast; use `grid` for a sharp, flat test target.

## What the model actually does

Parameters are not decorative — each one drives the image through a physical
relation, so the images degrade the way a real instrument's do.

- **Field of view** is `127000 / magnification` micrometres, the usual
  127 mm-display convention.
- **Probe diameter** grows as `spot^1.8` and with working distance, and shrinks
  with beam energy.
- **Interaction volume** uses the Kanaya-Okayama range,
  `R[um] = 0.0276·A·E^1.67 / (Z^0.89·rho)`, computed from the specimen's own
  materials. It is why raising kV sharpens the probe yet washes out surface
  detail, and why BSE images are blurrier than SE images of the same field.
- **Secondary electrons** follow a `1/cos(theta)` topographic law with a
  kV-dependent exponent, an Everhart-Thornley detector off to the upper right,
  and shadowing in recesses. The topographic term is capped, standing in for a
  finite escape volume and a saturating amplifier.
- **Backscattered electrons** use Reimer's `eta(Z)` polynomial with Arnal's
  tilt dependence, viewed through an on-axis annular detector: strong
  compositional contrast, weak topography.
- **Defocus and astigmatism** are converted to blur through the convergence
  semi-angle, so both are invisible at low magnification and ruinous at high
  magnification, exactly as on the instrument.
- **Shot noise** is Poisson on the collected electrons, which scale as
  `spot^3 · dwell`. Halving the dwell time raises the noise by `sqrt(2)`.
- **Charging** is scaled by distance from the ~1.5 kV E2 crossover, and shows
  up as bright edge glow and streaks trailing along the fast scan direction.
- **Tilt** foreshortens the image, tilts the surface into the beam, and raises
  the yield; **drift** shears the frame along the slow scan direction.
- **Exposure** fixes only the mean grey level with a soft highlight knee, and
  deliberately does not stretch the histogram — otherwise an unresolved
  specimen would come back with the same contrast as a sharp one.

Two honest caveats: the probe-size and beam-current relations are empirical
fits chosen to span realistic behaviour across the parameter boundaries, not
calibrated against a specific column; and specimen features far below one pixel
are drawn as an unresolved texture rather than individually, reported as
`features_resolved: false` in the metadata.

## Layout

```
sem_api/
  params.py       every parameter, its boundary, and validation   <- start here
  physics.py      probe size, electron range, SE/BSE yields, noise
  scene.py        specimen height fields and material maps
  procedural.py   coordinate-addressed noise (stable under zoom/pan)
  render.py       the pipeline: specimen -> signal -> blur -> noise -> display
  databar.py      instrument data bar and scale bar
  server.py       the HTTP layer
  playground.html the interactive page served at /
tests/test_sem_api.py
requirements.txt  the three libraries the code imports
```

## Tests

```bash
python3 -m unittest discover -s tests -v    # 29 tests, ~3 s
```

They cover the boundary contract (defaults in range, both limits inclusive,
out-of-range and unknown names rejected, clamping), determinism from the seed,
the physical trends above, and every HTTP endpoint including the error paths.
