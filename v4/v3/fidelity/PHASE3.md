# Phase 3 fidelity gate (v3.2, run after Stage 5C, before 5D)

Gate (user decision): per feature type, in-scope coverage >= 80%, >= 90% of reads within 2u, |bias| <= 0.5u. Test set only: no reader change on this evidence (rule 5); lessons go to v3.3.

## Source Data

| paper | DOI | file | size | used |
|---|---|---|---|---|
| S030 | 10.1038/s41467-026-76588-z | 41467_2026_76588_MOESM4_ESM.xlsx (46 sheets) | 8011590 B | yes (main-text Fig. 3-5) |
| S001 | 10.1038/s41368-026-00438-3 | Zenodo 10.5281/zenodo.10723552 'Source Data.xlsx' (42 sheets) | 107153213 B | **no**: sheets do not match the published figures (sheet 'Fig. 2c' ROC AUCs LR 0.838 / RF 0.50 / DT 0.725 / XGB 0.645 match none of the published Fig. 2b-d legends; 'Fig. 5a' is NMR, published Fig. 5a is colony counts) |
| S021 | 10.1038/s41467-026-75215-1 | 41467_2026_75215_MOESM5_ESM.xlsx (21 sheets) | 3163867 B | **no**: Source Data for supplementary figures only; no v0.24 crops of supplementary figures |
| S013 | 10.1038/s41467-026-74102-z | none retrievable ("Source data are provided with this paper", no file linked; MOESM3-5 return 404) | - | no |

sha256: 3f5148feb1ea60f729aeff82e712a121f0f9b9dd2877f6f531ea13a15b4be266  S001_zenodo_10723552_Source_Data.xlsx; 091f7f0a839c991dd308fe78fc4f49ca940a3e68b7ad65ff56995f0cb403522e  S021_41467_2026_75215_MOESM5_ESM.xlsx; 12d5257134439bf2fcee61f3d1aea531daa8b5f75c757782ed7c9a26788c2591  S030_41467_2026_76588_MOESM4_ESM.xlsx

## Procedure

S030 panels cropped with the v0.24 store procedure (fidelity/crops.py). Frozen readers.py (F5). Inputs (logged in fidelity/phase3.py): legend boxes (excluded from the data area), series colours from legend swatches (declared swatch positions where automatic row grouping was ambiguous; bar colours from the top of each declared bar column), legend row -> Source Data column by the printed labels, x_none on the category axis of the bar chart. Feature positions fixed by rule before reading. Deviation from the Phase 3 text ("printed tick labels, nothing else"): the readers cannot run without series colours and legend boxes, so these 5D-type inputs were declared (flagged).

## Result per feature type

| feature type | in-scope | read | coverage | within 2u | bias (u) | median abs z | verdict |
|---|---|---|---|---|---|---|---|
| peak_x | 7 | 0 | 0% | 0% | nan | None | **FAIL** |
| y_at_x | 64 | 17 | 27% | 94% | 0.44 | 0.43 | **FAIL** |
| plateau | 21 | 7 | 33% | 86% | 5.10 | 0.23 | **FAIL** |
| extremum | 10 | 10 | 100% | 80% | 4.31 | 0.6 | **FAIL** |
| crossing | 0 | - | - | - | - | - | replica-only (no source-data test case) |
| bar_top | 5 | 5 | 100% | 40% | -18.45 | 2.37 | **FAIL** |
| x_end | 0 | - | - | - | - | - | replica-only (no source-data test case) |

Status per panel: F3c calibration failed 7, F3d calibration failed 21, F4a miss 4, F4a read 17, F4b calibration failed 14, F4c calibration failed 12, F4d miss 1, F4d read 7, F4e calibration failed 9, F5a read 10, F5b read 5

## Failures and causes

1. **Frame detection** (coverage): F3d, F3c, F4b, F4c, F4e - the frozen find_axes (dark < 110, tool_ceiling plot.py) misses 1-px frame lines that resampling splits over two pixels (grey 100-150). Same failure seen on four real S098 panels while building the 5C replica styles (replica frames were drawn 1.5 px and dark). 63 of 112 in-scope features lost here.
2. **Series confusion between similar pastel colours** (accuracy): F4a RL800@10% plateau read on another blue series (z = 36); F5a CaCl2 minimum taken at the second dip (174 C vs 117 C; RL800@25% light blue overlaps); F5b RL800@25% bar read on the wrong bar (light blue vs CaCl2 blue, z = -84).
3. **Bar tops low by 1.2-3.5u** on gradient-filled bars with error-bar caps (F5b): the mask top sits below the drawn top edge.
4. Misses where series overlap (F4a, F4d): returned None, as designed.

Where frames were found, y_at_x is accurate (17 reads, 94% within 2u, bias 0.44u) but coverage fails.

## Lessons for v3.3 (no change in v3.2)

- Replica frames must include thin (1 px), resampled, grey frame lines; find_axes needs an adaptive threshold validated on those replicas.
- Replica palettes must include the pastel same-family palettes common in Nature Communications figures (several light blues), with markers over lines.
- Bar replicas need gradient fills and error-bar caps.
- Phase 3 needs source data that matches the published figures: check a printed statistic (legend AUC, bar value) before using a deposit.

## Consequence

The gate is set before 5D: **no feature type passes**, so 5D (matrices from real panels) is not started. Decision needed from the user.
