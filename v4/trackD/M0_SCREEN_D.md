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
