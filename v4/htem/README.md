# Track H kit: HTEM DB as a PanelBench database source (v4.3)

HTEM (High Throughput Experimental Materials Database) now lives at `https://htem-api.nlr.gov/api` (NREL became NLR; the old nrel.gov
hosts stopped resolving on 2026-05-29). The API is public and needs no key. Each library is one sputtered thin film with 44 positions on a
4 x 11 grid. Per position it can hold an XRD pattern, UV-vis-NIR transmission and reflection spectra, XRF composition, thickness and
four-point-probe I-V points, plus process records. The kit builds no items and calls no model.

| File | Role | Stage |
|---|---|---|
| config.json | base URL, throttle, PII fields, census rounding, frozen system score, reader parameters, synthetic gates, fresh seed base | all |
| htem_api.py | polite caching client: throttle with jitter, budget per attempt, Retry-After (capped), 404 markers, error bodies kept as .bad, id check, PII stripped, sha256 manifest | H1, H2 |
| sample_io.py | parses library and sample records (flat and nested optical layouts), drops non-finite points, percent against fraction per T/R pair, cation fractions, level map (D, M, A) | all |
| census.py | library and system tables, recipe keys with (target, power) and (gas, flow) pairs, replicate groups, temperature levels | H1 |
| score_systems.py | frozen two-stage score, needs PRIOR_SYSTEMS.json (or $HTEM_PRIOR), picks P1 (from the frozen top k) and P2 (another anion class) | H1 |
| readers/xrd.py | SNIP background, width-scaled pseudo-Voigt fits, humps kept apart, d-spacing (needs the wavelength D record), phase match | H4 |
| readers/optical.py | absorption from T and R plus thickness, saturation-aware, direct Tauc gap with bootstrap error and censoring | H4 |
| readers/fpm.py | sheet resistance from the I-V slope (geometry factor is a D record), polarity flag, resistivity | H4 |
| synth.py | synthetic XRD (narrow, broad, amorphous), optical and I-V data with known truth | H4 |
| validate_readers.py | synthetic gates on dev (0 to 99) or fresh seeds (config fresh_seed_base, redraw at freeze) | H4 |
| refs.py | COD CIFs from REF_PHASES.json, stick patterns and lattice constants at the D-record wavelength (needs pymatgen) | H3 |
| build_matrix.py | readers on every sample of the given libraries: cells.jsonl, held-out against database A columns, replicate second route, skipped.json | H4 |
| pilot_table.py | separability CSV for v4/trackS/separability_s.py, one temperature level per series | H5 |
| render.py | deterministic, metadata-free panels: XRD stacks, spectra, library maps, scatter fits, T2 letters | H6 |
| tests/test_kit.py | 20 offline tests on a mocked API and synthetic samples, including every finding of an independent code review | H0 |

## Commands, in order
```
export HTEM_HOST=$HOME/Documents/harbor/v4_host/htem
P=v4/.venv-v4/bin/python
$P v4/htem/tests/test_kit.py                         # 20 passed
$P v4/htem/validate_readers.py                       # kit defaults: all_pass
$P v4/htem/htem_api.py probe                         # count and fields of the live library list
$P v4/htem/census.py --fetch-missing                 # census/libraries.csv, systems.csv, census_totals.json
$P v4/htem/score_systems.py                          # census/ranking.csv, PICK.json (needs PRIOR_SYSTEMS.json, frozen)
$P v4/htem/htem_api.py samples <library ids>         # cache samples of the pilot libraries
$P v4/htem/refs.py fetch && $P v4/htem/refs.py sticks   # needs REF_PHASES.json and the wavelength D record
$P v4/htem/validate_readers.py --seeds dev           # tune on dev only, then freeze S4hx, S4ho, S4hf with a new fresh base
$P v4/htem/validate_readers.py --fresh-base <N>      # fresh gates
$P v4/htem/build_matrix.py --tag P1 --freeze S4h <library ids>
$P v4/htem/pilot_table.py --tag P1 --obs Eg --cation <el> --bin 0.05 --temp <T>
$P v4/trackS/separability_s.py --table <csv> --reader-freeze S4h --unit-type specimen|field
```

## Known limits (record with the freezes)
- Tauc Eg is invariant to a constant thickness scale, so Eg stays keyable even if thickness turns out to be model-derived (level A).
  Resistivity and absorption magnitudes are not.
- The XRD reader reports peaks with FWHM at or above about 0.95 x max_fwhm_deg (crystallites under about 3 nm) as humps, never as peaks.
- A percent-scale T spectrum with no R channel and every value under 1.5 % reads as a fraction. Such a film is opaque, so no gap is keyed.
- Without deposition_compounds, power lists keep their recorded order, so a reordered identical recipe does not count as a replicate
  (false negative, never a false replicate).
