# DESK refodat91 (Track S round 3; host A spark-112b; 2026-10-07)

Deposit: refodat doi:10.71758/refodat.91. Browser download, 15 files (manifest.json). Decision rule: D0.

## 7. Specimen map: resolved
DataCite description, verbatim:

> "CEM III/B, w/c 0.40, carbonated 21C 84.3099 14928 x 3834 ... CEM III/B, w/c 0.40, uncarbonated 21H ... CEM III/B, w/c 0.60, carbonated 25C ... CEM III/B, w/c 0.60, uncarbonated 25H"

Mix labels: "M38 CEM III/0.40", "M44 CEM III/0.60".

| BSE specimen | Mix | w/c | Carbonation |
|---|---|---|---|
| 21C | M38 | 0.40 | carbonated |
| 21H | M38 | 0.40 | uncarbonated |
| 25C | M44 | 0.60 | carbonated |
| 25H | M44 | 0.60 | uncarbonated |

The join (V4-E26) carries both factors. join_summary: w_c 0.4 and 0.6 with 2 specimens each; carbonation carbonated and uncarbonated with 2 specimens each. Raw tiles: 16 per specimen, FEI-tagged at 84.31 nm.

## 8. LTDSC route
**Paste-to-mix mapping** (LTDSC baseline.csv; columns "name;cement;age [d];w/c ratio;storage;..."). The BSE specimens match the 70-day dried CEM III pastes:

| BSE specimen | LTDSC paste |
|---|---|
| 21H | III.70.04.unc-d ("CEMIII;70;0.4;uncarb/ dried") |
| 21C | III.70.04.c-d ("carb/ dried") |
| 25H | III.70.06.unc-d |
| 25C | III.70.06.c-d |

The paste is not the concrete, so the route compares at mix level only, by direction and ranking, never tile against curve.

**Levels:**
- `*_raw_data.csv` (raw heat flow): M.
- `*_cycle_A/B.csv` (the authors' baseline-corrected melting curves) and baseline.csv gradient, intercept and accumulated ice mass: A.

## 9. Curves
- **Compressive strength** (`Compressive strength.csv`/`.xlsx`). Format: "Name;Age;Storage;Length [mm];Width [mm];Height [mm];Mass [g];Maximum load [kN];...;Mean compressive strength fc,dry [MPa];..."
  - Three 150 mm cubes per mix at 28 d (20/65 storage), with raw dimensions, masses and maximum loads.
  - Load over area is M per DIN EN 12390-3. The authors' means and conversions are A.
  - Mixes: M2, M2_LP, M5, M5_LP, M8, M8_LP, M38, M38_LP, M38_LP' (an outlier removed), M41, M41_LP, M44, M44_LP.
- **Frost (CF/CIF, DIN CEN/TS 12390-9):**
  - Three groups: standard curing; AE concrete in calcium nitrate (.CN); AE concrete in demineralised water (.H2O).
  - Per mix: 01_RDME (USV raw transit times and RDME), liquid uptake (_Mass_liquid raw, _Liquid Uptake calculated) and scaling (_Mass_loss raw, _Scaling calculated).
  - Raw masses and transit times are M; the calculated columns are A.
- **Linkage:** the curves are per concrete mix. Only M38 and M44 link to the BSE specimens, and the carbonation state is not a factor of the strength or frost series.

## 10. R3, R11 and R12
- **R3:** the methods source is the DataCite description (no descriptor paper linked).
- **R11:** the carbonation pair (calcite densification against C-S-H decalcification coarsening) is pre-registered in physics_refodat.py (CARBONATION_PAIR), with signatures on BSE porosity, LTDSC pore size and freezable water.
- **R12:** claims come from templates only.

## D0 decision
**refodat91: the reader stage may run.** The specimen map resolves all four specimens, and the join carries both factors.

Note for the reader stage: refodat91's only real evidence for S4r is LTDSC. It is report-only by the prompt (different specimens), so S4r on refodat91 can pass synthetic gates but cannot reach R5 (held-out real evidence).
