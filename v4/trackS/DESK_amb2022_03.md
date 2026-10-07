# DESK amb2022_03 (NIST mds2-2775 v1.0.0; measurement PDF v10; NIST open license)

Evidence: 2775_README.txt and "AMB2022-03-Microstructure Measurements.pdf" (last updated 2023-12-05), both repository sha256 verified; the landing-page file list (10,747 files); "AMB2022-03_measurement_and_result_descriptions_v10.pdf" (no repository digest, first sha256 in the manifest).

## Answers to the screen's questions
| Question | Answer |
|---|---|
| Raw SEM images? | **No.** The 483 TIFFs are rendered EBSD maps (IPF-X/Y/Z, All Euler, BC + IPF + GB) and EDS element maps. They carry plot borders, a scale bar, a raster note, and no pixel-size tag (96 dpi only). No SE or BSE micrograph exists in the record. |
| Lines and pads to laser cases | Track code L&lt;case digits&gt;&lt;repeat&gt;: L-01..L-03 = case 0 (285 W, 960 mm/s, 67 um); L111-113 = 1.1 (spot 49 um); L121-123 = 1.2 (82 um); L211-213 = 2.1 (1200 mm/s); L221-223 = 2.2 (800 mm/s); L311-313 = 3.1 (325 W); L321-323 = 3.2 (245 W). Folder "P4 multiple traces L-01 to L212" holds cases 0, 1.1, 1.2 and 2.1 repeats 1-2; "P1 multiple traces L213 to L323" holds 2.1 repeat 3, 2.2, 3.1, 3.2. Pads: BP2 (X-pad) P2 and P4 (cut 1.3 and 0.9 mm from the edge), BP3 (Y-pad) P2 and P3 (0.6 and 2.9 mm). |
| Are the 21 single tracks in the record? | Yes: one top-field EBSD map per track (1203 x 903 points, 0.25 um). The deep case-1.1 tracks add a 'bottom' field, and the P3 cross section holds a 4-field montage of track L112. |
| EDS and EBSD raw or exports? | Both. Raw: .ebsp patterns (2.66 TB), .raw EDS SmartMap cubes (0.58 TB), AZtec .oipx/.dat. Exports: .ctf, .h5oina, .csv (montage Euler and intercept histograms) and the TIFF renderings. |
| Record versions | mds2-2775 1.0.0; measurement and result descriptions v10; microstructure document dated 2023-12-05. |

## Fetch deviations
- V4-E21: the record is 3.37 TB, so tier rules were added by file type.
- V4-E22 and V4-E23: data.nist.gov returns HTTP 524 on larger files at about one file per several minutes, so tier 1 was cut to the documents and the 24 single-track .ctf files (27 files, 1.67 GB, all verified). The TIFF maps and pad exports are tier 2 (35 TIFFs on disk).

## Join (S2j-amb)
- 7 cases x 3 tracks, 0 unmatched files.
- Cases are ordered by areal energy density P/(vD): 2.1 < 1.2 < 3.2 < 0 < 3.1 < 2.2 < 1.1 (3.54-6.06 J/mm2).

## Magnification (S3)
- magleak: no_sem_images.
- All 24 single-track .ctf files share one native grid (0.25 um step, 1203 x 903): the scale is constant and native.

## Reader S4a (pilot S1): deferred
- **Observable:** melt-pool depth (and width) from the .ctf orientations.
  - Grains are rebuilt at 10 deg misorientation.
  - The pool is the surface-touching component of elongated grains (aspect >= 6), closed 2 um.
  - Depth is the maximum of the 20 um median lower envelope.
- **Synthetic, fresh seeds 200-209:** depth 10/10 within 10 % (pass); width 8/10 (fail, deferred).
- **Held-out real evidence (NIST Table 4 optical depths, n = 6 per case), gate frozen before measurement:**

| Case | NIST mean depth (um) | Ours, 3 tracks (um) | Within max(10 %, 2 SD) |
|---|---|---|---|
| 0 | 139.7 | 53.7 +- 40.7 | no |
| 1.1 | 227.2 | 20.2 +- 13.2 | no |
| 1.2 | 102.4 | 48.0 +- 29.1 | no |
| 2.1 | 109.7 | 21.2 +- 10.6 | no |
| 2.2 | 176.5 | 62.8 +- 79.8 | no |
| 3.1 | 166.1 | 21.9 +- 5.4 | no |
| 3.2 | 116.9 | 35.4 +- 17.8 | no |

  - 0 of 6 cases within tolerance (gate 5): **fail**.
  - Minimum adjacent between/within ratio 0.09 (gate 2; desk ratio 4.48 from Table 4): **fail**.
- **Cause:** the real pools are fans of wide, feathery columnar grains meeting at the centreline, not the narrow wedges of the synthetic model. The aspect rule captures fragments, and the depth reads 2-8x low (baseline track L-01: about 155 um by eye, read 100 um).
- **Correction logged before measurement:** the 4.48 check was first misread as a deepest/shallowest ratio.
- **Next iteration (needs David):** a synthetic generator built from the real fan morphology (wide columnar grains, twin-free pool against a twinned base), plus a classifier on twin content and grain size rather than aspect. Table 4 has now been seen, so a second validation against it would be weaker; mds2-2718 optical sections (tier 2, a second instrument) would be the cleaner held-out route.

## M0
- **NO-GO** (SEM rule: no raw SEM image). The deposit remains a strong EBSD/EDS source for a non-SEM pilot.
- Per the prompt, the reserves (alsi10mg_luo2024, sa508_ebw) are being fetched at tier 1.

---
# Round 2: reader S4a-2 (pilot S1, modality EBSD). Written before any S4a-2 code (2026-10-07)

## Sets
- **Dev set** (may be inspected and used for tuning):
  - the four pad cross sections: BP2 P2 and P4 (X-pad), BP3 P2 and P3 (Y-pad);
  - the P3 four-field montage of track L112;
  - the case-1.1 'bottom' fields of L111, L112 and L113.
- **Held out:** the 21 single-track top fields. They have been read once already, by S4a in round 1. Nothing in S4a-2 is tuned on them.
- **Disclosure (I4):** the NIST Table 4 means and our round-1 per-case S4a depths were seen when S4a failed. The S4a-2 classifier is designed from physics and the dev set, not from those numbers.

## Observable
Melt-pool depth: the deepest point of the pool boundary below the local surface, in um, per single-track cross section. Width is secondary (reported, not gating).

## Pool / base classification (physics)
Each grain is reconstructed from the .ctf orientations (10 deg misorientation, cubic symmetry). Its features:

| Feature | Definition | Expectation |
|---|---|---|
| Sigma-3 twin boundary fraction | Fraction of the grain's boundary length that is Sigma-3: 60 deg about <111>, Brandon tolerance 15/sqrt(3) = 8.66 deg | The base (annealed IN718 sheet) carries annealing twins; the resolidified pool carries none |
| KAM | Kernel average misorientation: mean misorientation to the 4 neighbours, below 5 deg | Higher in the pool (solidification cells, residual strain) |
| Size and shape | Equivalent diameter; aspect ratio and orientation of the major axis relative to the direction to the fusion-boundary centroid | Pool grains are columnar and point from the fusion boundary toward the centreline |

Classifier: grain-level thresholds on these features (or a two-feature rule). The thresholds are set on the dev set, where the upper remelted layer of the pads and the montage gives labelled pool by position, and the lower base gives base. They are then frozen.

## Depth and censoring
- The pool mask is the union of pool grains connected to the surface band, closed by a small disk.
- Depth is the lowest pool pixel in any column below the local surface (first indexed row).
- **Censored** when the pool mask reaches the last 5 um of the covered area and no further field covers it.
- Case 1.1: the bottom field is stitched to the top field by phase correlation of the orientation maps in their overlap. If the stitch fails, the depth is reported censored.

## Gates (frozen with the reader, S4a2)
- **Synthetic, fresh seeds:**
  - depth 9 of 10 within 10 %;
  - censoring always flagged when the pool leaves the covered area;
  - width reported, not gating.
- **Held-out real** (21 single tracks vs NIST Table 4 optical depths, a second instrument):
  - at least 5 of 7 cases with our mean depth within max(10 %, 2 NIST SD);
  - and the case order matches Table 4 (Spearman >= 0.9).
- **Dev-side length check** (not a gate): X-pad line spacing from the pool centrelines, against the authors' 108-109 um (110 um commanded).

## Round 2 results (S4a2; host A node 2 spark-0b70)
- **Dev (pads, dev_amb2.json):** 2,188 pool and 5,271 base grains labelled by position.

  | Feature (median) | Pool | Base |
  |---|---|---|
  | Sigma-3 fraction | 0 | 0.44 |
  | KAM | 0.165 deg | 0.094 deg |
  | Aspect ratio | 4.2 | 1.9 |

  Classifier: sigma3 <= 0.10 alone (balanced accuracy 0.927). KAM adds nothing.
- **Synthetic generator:** built from the dev statistics (twinned base 90 %, twin-free columnar fan, epitaxy 50 %).
  - The reader adds a 20 um spatial majority vote, tuned on dev seeds 100-107.
  - Fresh seeds: depth 10/10 within 10 %; censoring 5/5 flagged; deep pools stitched.
- **Held-out real** (21 tracks vs NIST Table 4; gate frozen before running): **fail.**
  - 2 of 7 cases within max(10 %, 2 SD) (gate 5).
  - Spearman 0.64 (gate 0.9).
  - Case 0: 136 vs 139.7 um. Case 2.1: 101 vs 110.
  - Under-read: 1.1 (120 vs 227, stitched), 2.2 (125 vs 177), 3.2 (91 vs 117), 1.2 (76 vs 102).
  - Within-case SD 6-50 um (NIST 1-3 um).
- **Failure mode:**
  - The real deep pools have narrow, keyhole-like roots. The synthetic pools are half-ellipses with broad bottoms.
  - The 20 um majority disk, which removes isolated misclassified base grains, also erodes a narrow pool root, so it cuts exactly the deepest part. The bias grows with depth (case 1.1 worst).
  - Secondary causes:
    - Epitaxial columnar grains near the root inherit twinned base grains (merged grains read as base).
    - The single-section EBSD depth differs from the optical section position.
- **Per the prompt the dataset stops here:** no separability pilot. A third iteration needs David. Candidate S4a-3:
  - a generator with keyhole roots measured on the L112 montage;
  - an anisotropic majority (along the pool axis) or a geodesic mask growth from the surface;
  - epitaxy handled by splitting merged grains at the fusion line (KAM step).
- **Not computed:** the X-pad line-spacing check (dev side, not a gate). It needs pad pool centrelines, which this failed reader does not provide reliably.
