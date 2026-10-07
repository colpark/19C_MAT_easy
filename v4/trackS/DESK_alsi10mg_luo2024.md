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

---
# Round 2: active pilot S1b (modality SE), 2026-10-07

## Inputs check (B1)
Descriptor: Luo et al., Data in Brief 2024, 10.1016/j.dib.2024.110130 (PMC10859257). Open-access full text fetched from the Europe PMC REST API to v4_host/trackS/alsi10mg_luo2024/descriptor/dib_2024_110130_PMC10859257.xml, sha256 52563dade2c356e0eaf0c31c95fca469b5240d56b44ea6653c38c70e7995cf40.

## Desk questions (B2), answered from the files and the descriptor
| Question | Answer | Evidence |
|---|---|---|
| How are fields a-d placed? | **Chosen.** On each annotated 2000x overview the four 5000x boxes sit at different positions from sample to sample, aimed at melt-pool boundaries and at coarse and fine cell zones. There is no fixed grid. So `sampling = chosen` and `field_selection = curated`: R7 fails and T7 stays out. | the 32 *_Overview_Annotated.tif; readme in the SEM zip |
| Do SEM samples and tensile specimens share a build? | **Same specimens.** The SEM samples are the grip regions of the fractured tensile specimens ("The grip region was removed from the fractured sample ... mounted ... prepared for imaging"). The image names do not say which of the three replicates was imaged, so the join stays by process set. | descriptor, Methods |
| Tensile curves | Three workbooks, one per replicate group (group 1/2/3 = 60/58/60 specimens, one per set). Each sheet holds column pairs per set: axial engineering strain (mm/mm) and axial engineering stress (MPa). | readme; workbook headers |
| Tensile strain source | DIC on a speckle pattern (VIC-2D 6, subset 29 px, step 7 px, pixel 15.7-25.9 um), **24 mm virtual extensometer**. Strain is therefore author-computed: **level A** (as David ruled for the Stinville DIC). | descriptor |
| Tensile stress source | Load cell / area (engineering stress): a standard instrument equation, **level M**. The raw load column is not deposited. | descriptor; workbook |

**Consequences for the pilot:**
- Yield needs the strain, so yield is level A: a cross-check and T4 only, never a key. Ultimate strength (maximum engineering stress) is level M.
- The SEM images carry an FEI databar: crop rows below ResolutionY.
- **Disclosure:** the descriptor search printed rows of the authors' Table 7 (cell diameter, sets 1-21) and Table 9 (yield, sets 1-4) before the laws below were pre-registered. The law forms come from the round-2 prompt, not from those values.
