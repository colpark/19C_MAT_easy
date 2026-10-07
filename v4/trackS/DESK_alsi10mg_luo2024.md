# DESK alsi10mg_luo2024 (reserve; Zenodo 10008435; CC BY 4.0)

Evidence: the readme.txt files inside the archives, 'AlSi10Mg PSP feature table.xlsx' and the inventory. Tier 1: 12 files, 0.70 GB, all repository-checksum verified.

## Inclusion test (prompt S6): the high-magnification SEM zip
**Kept.** "[IR] SEM AlSi10Mg cell (high magn).zip" holds raw TIFFs with FEI tags, not slide exports.
- 192 ETD images: 32 samples (processing parameter sets 1-32, the small-hatch group), each with a 2000x overview, an author-annotated overview, and four 5000x fields a-d.
- Native pixel sizes: 41.5, 54.0, 134.9 and 179.9 nm.
- The two .pptx files (SEM cell, EBSD grain) are slide exports and stay documents.
- EBSD exists only as slide images: no .ang or .ctf.

## Join (S2j-alsi)
- 0 unmatched.
- Process conditions per set from the PSP table: P 60-370 W, v 250-1350 mm/s, h 0.1 mm, VED 19.8-306.7 J/mm3.
- The 32 annotated overviews are 'other' (author drawings), not measurement images. 160 SEM images enter the magnification test.
- Also present:
  - 3 stress-strain workbooks (178 curves over groups 1-3; set 1-32 is group 1);
  - grain and cell morphology CSVs (author segmentation output, A level);
  - XCT pore tables (A level).

## Magnification (S3)
- Verdict: **independent** for VED, P and v.
- The pixel size follows the image type (2000x vs 5000x) and not the condition.
- Resample before any cross-image measurement.

## Reader
Not built: reserves get S2 and S3 only in this run. The observable to try first would be cell size from the 5000x fields. Held-out evidence would be the authors' cell-morphology CSVs (author classifier output; report its bias).

## M0
- GO WITH CHECKS (separability pilot pending).
- Scorer: 0 of 5 inference families open until a reader validates. T2, T3, T5, T6 and T7 are possible after the checks.
