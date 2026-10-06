# Track D M0 screen and separability pilot (2026-10-06)

Rules applied: skill M0, plus the plan's new rule 2 (separability pilot): before a metadata series counts as a measurement series,
between-condition differences must exceed the within-condition spread.

## Rank 1: CrFeNi Hall-Petch (Mendeley Data 10.17632/7d826s3mhf.1, CC BY 4.0). PASS: build
| Check | Result |
|---|---|
| Raw files, side 1 (grain size) | BSE channeling-contrast SEM TIFFs for 8 conditions (FEI metadata: PixelWidth, HFW, BSE). 1473 K files are 16-bit; 1573 K has only a JPG (scale bar needed). Authors' intercept results appear only as file names (`d=`, `c=`): A level, screen only, never keys |
| Raw files, side 2 (strength) | force / crosshead-displacement workbooks: compression at 293 K for 7 grain-size conditions (3-5 specimens each); compression 77-873 K and tension 77-473 K for the 1473 K / 60 min condition |
| License | CC BY 4.0 (Mendeley record): release-eligible |
| Sample IDs | compression: file name, folder and workbook header (anneal T in C and time) agree for every file. Tension: the `373K` folder holds 3 files named `_293K_` (V4-E11); their headers read `Zug_100` (100 C), so the folder is right. Test temperature comes from the header. Several tension specimens are interrupted tests (`5%`, `274MPa_5pt`) |
| Yield procedure | trackD/yieldproc.py (freeze D1): 0.2 % offset on the steepest-secant line of the crosshead curve. Synthetic gate (validate_yield.py): 300/300 within 2 %, rank of 5 % differences preserved 300/300 |
| Separability (293 K compression) | 21/21 condition pairs differ by more than 2 combined SE; all 6 adjacent pairs separate; one-way ANOVA p = 3e-14. Within-condition SD 0.2-12.4 MPa, adjacent gaps 16-75 MPa |
| Law (screen) | Hall-Petch against the authors' d: r = 0.979 (p = 1e-4), k = 805 MPa um^0.5, sigma0 = 103 MPa (procedure-defined yield, crosshead strain) |
| Anomaly | the 1573 K / 327 um condition yields higher (167.9 +- 11.0, n 5) than 1473 K / 162 um (145.5 +- 12.2, n 3): a candidate anomaly item if our own grain-size reader confirms the order |
| Second law | tension vs compression for the same condition and test temperature (agreement class), and the temperature dependence of yield (77-873 K) |

Remaining before keys (M2): our own grain-size reader with two methods (intercept with and without twin boundaries, and segmentation), validated
on synthetic microstructures, then checked against the authors' file-name values as held-out evidence. Key-reader independence
(plan rule 3): the key reader must differ from any tool offered in a T arm.

## Rank 2: sigma-phase growth in CrMnFeCoNi (Data in Brief deposit, CC BY 4.0). DEFERRED
| Check | Result |
|---|---|
| Raw files | 22 conditions (700-1000 C, 0.05-1000 h) x 4 BSE TIFFs; EDX line-scan workbooks (grain boundary, FCC-sigma) |
| Law sides | time and temperature are design records (D); the measured side is the sigma fraction or size, which needs a precipitate reader. Only one instrument carries the law |
| Images | 8-bit, no FEI metadata (pixel size from the scale bar only). Grain-orientation channeling contrast makes some matrix grains as bright as sigma: a global threshold fails (the UHCS reader failure mode, V4-E03/E04) |
| Separability pilot | not run: it needs a validated precipitate reader first. Running it on an unvalidated reader would repeat V4-E03 |
| Decision | build rank 1. Rank 2 can come back as a T-FM item source once the Track C FM result is known |

## CrFeNi grain-size reader (M2, freezes D3 and D4)
- trackD/grainsize.py: TV denoising, then two methods: Canny edge intercept (I) and watershed label intercept (II). Twins are counted (BSE has no orientation data).
- Development on synthetic dev seed 101. Absolute recovery is unreachable at the real noise level (boundaries between near-equal grays are invisible), so the gates were restated as a constant bias **before** the freeze.
- Fresh-seed validation (validate_grainsize.json):

  | Measure | I | II |
  |---|---|---|
  | Reader/truth | 1.41 | 1.37 |
  | Spread | 0.084 | 0.057 |
  | Size slope | -0.118 | -0.037 |
  | 1.4x ordering | 100 % | 100 % |

  The methods agree within 15 % on 95 % of images. All gates pass; method I's size slope sits close to its 0.12 limit.
- Real TIFFs (grains_crfeni.json): 29 images, 6 conditions. All are in the validated range after noise-driven binning.
  - Held-out check against the authors' twin-inclusive intercepts c (A level, rank and ratio only): Spearman 1.0 for both methods; our/c = 1.21 (CV 0.14) for I and 1.30 (CV 0.21) for II.
- 1573 K: stitched JPG with a scale bar and seams. Excluded from keys until the scale bar passes a pixel check plus a blind read.
- Hall-Petch with our grain sizes, 6 conditions: r = 0.972 (I) and 0.960 (II).
  - Leave-one-out residuals are -2 to -18 MPa, except 16.5mm/1273K at +42 MPa (I).
  - The two bar thicknesses (8.1 and 16.5 mm) may not share one line.
  - The model error must be frozen in the physics table before any T7 key.
