# D0: decision rule for the refodat reader stage (Track S round 3)

Frozen (label D0) on 2026-10-07, before any round-3 desk check. Written from the round-3 prompt and the DataCite descriptions only. At freeze time, no registration, EDX, indentation or BSE pixel statistics had been computed. The round-2 join only counted files and pixel sizes.

## refodat90: the reader stage runs only if both conditions hold
### 1. Registration (BSE to EDX)
Gate: median residual ≤ 1.0 µm and 95th-percentile residual ≤ 2.0 µm.

**Inputs:**
- The BSE montage. Use the deposited stitched BSE (BSE_High-Res.tif, 84.3099 nm/px, MAPS stitch of the raw tiles), or its georeferenced copy in the authors' QGIS packages.
- The EDX phase map (EDX_full_phase_map.tif, 1024 × 704 px at 288.722 nm/px, class index per pixel).

**Global transform:**
- The authors' global BSE-to-EDX transform comes from their QGIS alignment, either the georeferencing of the two rasters in the same project or the .qgz/.points files.
- If the deposit holds no usable authors' transform, the global transform is our own phase correlation of the whole overlap. This is logged, and the residual is then the spread of local offsets about that global offset.

**Procedure:**
1. Downsample the BSE to the EDX pixel (288.722 nm) by area averaging.
2. Build a pseudo-BSE image from the EDX class map. Each class gets the mass-weighted mean atomic number Z̄ of its nominal composition (table below). Literature compositions are named defaults; no tuning is allowed.
3. Map the downsampled BSE into the EDX frame with the global transform.
4. Choose at least 20 windows of 64 × 64 EDX px on a regular grid over the overlap. A window counts only if it has at least 2 classes, each covering at least 5 % of the window.
5. In each window, find the local offset by phase correlation with sub-pixel peak refinement, after normalizing both images to zero mean and unit variance.
6. Each window's residual is the magnitude of its local offset, in µm.
7. Report the median and 95th percentile over the windows, plus the residual map.

**No result:** if fewer than 20 windows qualify, the registration condition fails.

### 2. Held-out evidence
Gate: at least one validation route covers the held-out block.

**Routes:**
- the EDX phase map (level A), meaning at least 10 % of the held-out block's area lies inside the EDX map;
- indent positions with modulus values (level A or M) inside the held-out block, with at least 20 indents.

**Order:** the spatial split is frozen in the reader stage (step 1) before this condition is evaluated. The split may not be chosen to satisfy it.

## refodat91: the reader stage runs only if
Desk item 7 resolves all four BSE specimens (21H, 25H, 21C, 25C) to a mix, a w/c and a carbonation state, from the DataCite description and the files, and the join carries both factors.

## Pseudo-BSE Z̄ table (mass-weighted, nominal compositions; named defaults)
| EDX index | Label (deposit) | Composition used | Z̄ |
|---|---|---|---|
| 0 | pores | vacuum (BIB-milled surface, not impregnated) | 0.00 |
| 1 | AFm/AFt | ettringite Ca6Al2(SO4)3(OH)12·26H2O | 10.77 |
| 2, 6 | alite/belite | Ca3SiO5 | 15.06 |
| 3 | matrix | C-S-H Ca1.7SiO3.7·1.8H2O | 13.11 |
| 4 | CH | Ca(OH)2 | 14.30 |
| 5 | C-A-S-H | Ca1.7Al0.1SiO3.85·1.8H2O | 13.05 |
| 7, 8 | C3A/C4AF | mean of Ca3Al2O6 and Ca4Al2Fe2O10 | 15.49 |
| 9 | Mg-C-A-S-H | Mg1Ca1Al0.2SiO3.3·2H2O | 11.99 |
| 10 | Slag | CaO 40, SiO2 36, Al2O3 11, MgO 9, Fe2O3 1, SO3 3 wt % | 13.17 |
| 11 | quartz | SiO2 | 10.80 |
| 12 | C-S-H | Ca1.7SiO3.7·1.8H2O | 13.11 |

Phase correlation uses normalized images. Only the ordering and contrast of Z̄ matter, not BSE yield constants.

## Outcome
- **Both refodat90 conditions hold:** the S4r reader stage runs for refodat90.
- **Either fails:** no reader for refodat90. Record why; the dataset stays GO WITH CHECKS.
- **refodat91:** runs if its condition holds, independently of refodat90.
