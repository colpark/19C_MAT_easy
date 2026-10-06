# v4 day-1 statistics: why Track A is large and Tracks B and C are small

## Track A: 248 items x 5 arms = 937 tasks
The 937 tasks are arm copies of 248 items: A0 248, B0 248, B1 137, R0 152, R0all 152.
The items are the full v3.0-v3.3 output for six papers, carried over, not built today.

| Source | Cells (level) | Panels | Entities x conditions | Items | T1 | T2 | T3 | T4 (matrix/text/recompute/cannot or template) | T5 | T7 | Inference items |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Paper 1 (Mo21, digitized) | 277 M | 9 | 5 samples x 7 T | 89 | 40 | 8 | 0 | 39 (21/12/4/2) | 0 | 2 | 10 |
| P2 Bi2Te3 | 186 (96 M, 90 A) | 7 | 6 x 6 T | 38 | 15 | 2 | 0 | 19 (9/3/2/5) | 2 | 0 | 4 |
| P3 perovskite/PI | 134 (122 M, 12 A) | 8 | 6 series, dense x | 35 | 12 | 0 | 0 | 19 (14/0/0/5) | 0 | 4 | 4 |
| P4 cementitious | 21 M | 3 | 4 x few | 28 | 9 | 0 | 2 | 17 (9/3/0/5) | 0 | 0 | 2 |
| P5 PVA hydrogels | 19 M | 4 | 9 x 1 | 29 | 10 | 0 | 0 | 19 (10/4/0/5) | 0 | 0 | 0 |
| P6 SrIrO3 | 2,430 (2,418 M, 12 A) | 5 | 6 curves (dense) | 29 | 10 | 0 | 0 | 17 (8/2/2/5) | 2 | 0 | 2 |
| **All** | **3,067** | **36** | | **248** | **96** | **10** | **2** | **130** | **4** | **6** | **22 (9 %)** |

**Why it is large:**
1. **Arms multiply tasks, not items.** Every item becomes one task per arm.
2. **The cheap families scale with panels.** Any M panel gives up to 3 T1 reads and a consistent/contradicted pair of matrix claims plus comparisons. That needs no law, so T1 + T4 make up 226 of 248 items (91 %).
3. **Inference needs law links.** T2, T3, T5 and T7 require a law between M quantities on shared entities, plus gates. Only 22 items (9 %) passed, mostly paper 1 (10) with its 5-sample x 7-temperature matrix and four linked transport panels.

## Track B: Allende, one grain, 15 candidates kept by the build gates, 1 after the audit
**Entities:** 1 grain; 3 regions defined by EDS (sulfide 331 px, Al pocket 370 px, silicate 1,991 px).
**Instruments:** EDS and STXM, over 4 elements. The HAADF tilt series is unused.
**Conditions:** none. One specimen has no processing or time series, so T7, condition-based T3 and T2 condition matching do not apply.

| Family | Candidates | Kept by build gates (B7) | Kept after audit Q1 (B8) | Reason for the loss |
|---|---|---|---|---|
| T1 spectrum reads | 2 | 2 | 0 | Sol tags the L3-L2 separation as A (computed from raw spectra) |
| T2 cross-modal match | 1 | 1 | **1** | passes (agreement law accepted; STXM maps allowed as T2 targets) |
| T3 agreement ranking | 12 element x region pairs | 7 (5 below 5 standard errors or opposite signs between instruments) | 0 | hidden STXM jump tagged A; region thresholds rejected |
| T4 claims | 6 | 3 (two-route rule dropped 3) | 0 | region thresholds rejected; all 4 text parses rejected |
| T5 Ni host | 3 pairs | 2 (textbook-prior trim) | 0 | region thresholds rejected; Ni-in-olivine signature removed |
| **Total** | **24** | **15** | **1** | |

**Why it is small:** one specimen with no condition series; three regions; and the blind audit's restrictive rule.
- The v3 tag prompt is written for paper-reported numbers. It reads our own raw-data procedures (edge jump, peak separation, region masks) as "computed", which is A.
- Sol also rejected the global median + MAD region thresholds as unreliable for sparse Poisson EDS counts.

**Two ways back. Neither applied; each needs your call or a quote:**
- (i) Register the raw-data procedures (edge jump, EDS net counts, peak separation) as definition-7 derived observables. This changes a frozen definition (a rule gap).
- (ii) Poisson-aware region definitions (per-bin likelihood ratio), then re-audit (about $0.01, new quote).

## Track C: UHCSDB, 0 items (decision: option (c), FM test only)

| Stage | Count |
|---|---|
| micrographs in the deposit | 961 |
| micron-bar scale agrees with the database | 949 |
| standard data-bar crop (484 rows) | 913 |
| measured by both readers | 902 |
| condition cells (>= 3 images at 1964X or 4910X) | 27 |
| items generated with reader C1 | 29 (T1 5, T5 23, T7 1; T2 0: one ambiguity class; T3 0: six pairs not separated) |
| items kept | **0**: readers fail held-out real evidence (V4-E03, V4-E04) |

**Why it is small:**
- The particle-size readers fail the human-annotated particles: 8/10 test images within 20 %, gate 9/10.
- The annotated truth itself orders 800 C as 3 h < 24 h < 85 h < 8 h, so the coarsening premise is weak on this deposit.
- **Decision (David, 2026-10-06): option (c).** UHCSDB serves the FM test only. The condition-series seed comes from Track D (the top candidates are the Laplanche group's Hall-Petch series).
