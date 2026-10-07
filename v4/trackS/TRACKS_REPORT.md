# Track S round 2 (2026-10-07)

Prompt: v4.1 Track S round 2 (AM Bench reader 2, AlSi10Mg pilot, SA508 throttled retry, kit fixes). David's decisions:
- SEM rule widened to EBSD/EDS maps with a native step.
- Stinville parked (DIC is level A).
- Anjaria deferred.
- AlSi10Mg active.

No paid call, no keys, no items. Hosts: host A (spark-112b), host A node 2 (spark-0b70, AM Bench reader), host B (wcs-180522, throttled fetches). Ledger V4-E25 onward; freeze labels K2, S4a2, S4a2rv, S4d-phys, S4d, S4d-rv, S4e, S4e-b, S4e-c.

## Summary
| Dataset | Pilot | M0 | Families the scorer keeps | Why |
|---|---|---|---|---|
| alsi10mg_luo2024 | S1b (SE + curves), 60 sets | **GO** | T1 pass, T4 pass; T2, T3, T5, T6 fail R6; T7 fails R6 and R7 | All 60 sets (David): 177/180 specimens, UTS ratio 1.001 to the authors. Separability partial: 31/59 adjacent pairs in VED order, ANOVA p 1.7e-21, min ratio 0.072. 32-set run was 5/31. Cell reader S4d failed its constant-bias gate. Fields curated (R7 fail). |
| amb2022_03 | S1 (EBSD) | **NO-GO (cancelled by David)** | none | Reader S4a-2 passed synthetic but failed held-out (2/7 cases, Spearman 0.64). David cancelled the dataset on 2026-10-07. |
| stinville2022 | S2 | NO-GO | none | Parked by David; every series observable is A (K2 provenance stop). |
| anjaria2025 | S2 | GO WITH CHECKS | T1-T4 check | Deferred by David (needs a DIC reader). |
| sa508_ebw | reserve | SA508_PENDING | | Throttled retry on host B. |
| refodat90 | S3 (BSE tiles) | **GO WITH CHECKS** | pilot pending | Browser download (14 files, 7.36 GB = DataCite 7020.67 MiB). 176 raw BSE tiles, all FEI-tagged at 84.31 nm (magleak constant). One mortar surface: the only series is spatial (ITZ distance), so R6 needs a frozen reader and spatial bins. |
| refodat91 | S3 (BSE tiles + LTDSC, strength, frost) | **GO WITH CHECKS** | pilot pending | Browser download (15 files, 1.09 GB). 64 raw BSE tiles (16 per specimen, 84.31 nm, constant). 2 x 2 design (w/c 0.40/0.60 x carbonated/uncarbonated, CEM III/B, M38/M44), one specimen per condition: tiles are spatial units (optimistic). T7 fails (3 levels < params + 4). |

## B-60: AlSi10Mg on all 60 sets (David, 2026-10-07)
- Join rules S2j-alsi-60: sets 1-60, series ordered by VED (J/mm3), frozen before sets 33-60 were computed. UTS for sets 1-32 was already seen; the order comes from design records only.
- Curves S4e-60 (curves_alsi60.py, the S4e procedures, frozen before running):
  - 177/180 specimens; sets 4, 7 and 33 have 2 replicates (blank or non-numeric columns, logged);
  - UTS ours/authors 1.001, max |diff| 27.2 MPa;
  - yield (A) ratio 0.976, Spearman 0.917.
- Separability (UTS, specimens as units, VED order):
  - partial: 31/59 adjacent pairs beyond 2 SE;
  - ANOVA p 1.7e-21, minimum between/within ratio 0.072;
  - 32 T2 ambiguity classes.
- M0: GO, unchanged. T1 and T4 pass; T2, T3, T5 and T6 fail R6; T7 fails R6 and R7.
  - R6 still needs every adjacent pair separated.
  - SEM covers sets 1-32 only, so no SE observable reaches sets 33-60.
- Host files (not in git): curves_alsi60.json, pilot_alsi60_uts.csv, curves_alsi60_vs_authors.json, pilot_alsi60_uts_separability.json.

## D: refodat (browser downloads by David, 2026-10-07)
- **Intake.** The downloads were refodat derivate zips. Their member counts and sizes match DataCite: 14 files at 7,361,710,114 B and 15 files at 1,089,139,004 B. They were extracted flat into trackS_manual/extract with CRC checks and registered with `fetch_s.py manual --move`. The archives inside were unpacked by `inventory_s.py extract` (path-traversal guarded). No file was executed.
- **R2.** pass on both (.tif, .tiff, .png, .jpg, .bmp, .spd, .csv, .xlsx).
- **Join (V4-E26).** The prospective rules over-matched, so they were rewritten against the files. Raw MAPS tiles are now the only SEM role: refodat90 176, refodat91 64. For refodat91 the w/c and carbonation map comes from the DataCite SEM table.
- **Magleak.** One native pixel size (84.31 nm) on every SEM tile of both datasets.
- **M0.** Both GO WITH CHECKS; the separability pilot is pending, since no validated reader exists yet.
  - refodat90 has no design series: one specimen, spatial ITZ bins only.
  - refodat91 has one specimen per condition, so its tiles are optimistic units. The LTDSC paste specimens need their own join to the concrete mixes.

## K: kit fixes (frozen K2; tests/test_k2.py 24/24, tests/test_kit.py 53/53)
1. **fetch_s.py:**
   - `--delay` with 0-50 % jitter, a per-host minimum interval, and one job by default for data.mendeley.com and data.nist.gov;
   - skips manifest-verified files;
   - error bodies (small JSON or HTML where data was expected) are kept as `.bad` with status `error_body`.
2. **inventory_s.py:** a proprietary twin (.osc/.cpr/.crc) with an open same-stem twin is `redundant`; R2 ignores it. Stinville R2 now passes.
3. **m0_s.py provenance:**
   - observables carry `level`, and an all-A condition series stops keys;
   - author desk ratios move to `design.separability_ratio_desk_A` (AM Bench 4.48), which R6 ignores;
   - `parked` stops.
4. **Widened SEM rule:**
   - EBSD/EDS maps with a native step (.ctf XStep, .ang XSTEP, HDF5 step) count as the SEM part;
   - the second modality is a non-map raw modality or a second SEM-instrument modality;
   - join.csv carries a `modality` column (SE/BSE by detector or rule; EBSD, EDS, curve, indentation, DIC, XCT).
5. **DEFAULT_TIER_RULES** for records of unknown size: documents and native exports at 1, rendered maps and HDF5 at 2, patterns and cubes at 3.

## A: AM Bench reader S4a-2 (pilot S1, modality EBSD)
- **Dev set:** the 4 pads, the case-1.1 bottom fields, and the L112 montage (fetched on host B, sha256 d675220c on both hosts).
  - The pad grains were labelled by position: 2,188 pool, 5,271 base.

  | Feature (median) | Pool | Base |
  |---|---|---|
  | Sigma-3 fraction | 0 | 0.44 |
  | KAM | 0.165 deg | 0.094 deg |
  | Aspect ratio | 4.2 | 1.9 |

  - Classifier: sigma3 <= 0.10 (balanced accuracy 0.927); KAM adds nothing.
- **Generator from the dev statistics:**
  - twinned base 90 % (exact Sigma-3 relations);
  - twin-free columnar fan, 50 % epitaxy, depths 60-260 um;
  - deep pools get a stitched bottom field.
  - Reader: a 20 um majority vote, tuned on dev seeds.
- **Synthetic, fresh seeds:** depth 10/10 within 10 %; censoring 5/5 flagged; stitching worked.
- **Held-out real** (21 tracks vs NIST Table 4, I4 disclosure in the desk note): **FAIL.**
  - 2/7 cases within max(10 %, 2 SD); Spearman 0.64.
  - Case 0: 136 vs 139.7 um. Case 1.1: 120 vs 227 (stitched).
- **Failure mode (V4-E25):** the majority disk erodes the narrow keyhole-like roots of real deep pools (the synthetic pools had broad bottoms). Candidate S4a-3 in DESK_amb2022_03.md.
- **Not run:** separability; the X-pad line-spacing check (needs pool centrelines).

## B: AlSi10Mg pilot S1b (modality SE + curves)
- **Descriptor:** Europe PMC PMC10859257, sha256 52563dad.
- **Desk:**
  - fields a-d curated (R7 fail, T7 out);
  - the SEM samples are the grips of the tensile specimens;
  - curves: 3 replicate workbooks; strain from the authors' DIC virtual extensometer (A); stress = load/area (M).
- **Physics pre-registered** (S4d-phys): cell vs P/v (fit), yield vs cell (fit, yield A: T4 only), UTS vs cell (fit, M), XCT vs Archimedes (agreement, both A: T4 only).
- **S4d cell reader** (skeleton-bounded cells after the generator's dilation bug was fixed): fresh seeds 9/10 within 10 % but size slope -0.156 (gate 0.10): **FAIL**.
  - Exploratory real: ratio to the authors' cell CSV 0.96 (CV 0.086), Spearman 0.39. The author set means hardly vary (0.77-1.29 um).
- **S4e:**
  - D1c validated in the DIC regime (94 % within 5 %, rank 100 %).
  - UTS (M): ratio 1.00 to the authors' table.
  - Yield (A): ratio 0.98, Spearman 0.79.
  - 94 of 96 specimens (one backtick header, one 'No data' column).
- **Separability:**
  - UTS per set (specimen units): partial, 5/31, ANOVA p 0.0015, ratio 0.034. T2 classes: [[4,14,23],[8,30,13,20,32,19,12],[7,3,24,1,18,31,11,25,6],[17,26,21,10],[27],[16,2,28,22,29,5,9,15]].
  - Cells (exploratory): partial, 6/31, ANOVA p 0.23.
- **What an item build would need (GO, T1 and T4):**
  - T1: reads on the curve panels (UTS) and on the 5000x fields, with keys from the S4e procedures.
  - T4: template claims on UTS rankings between merged classes, plus cannot-tell claims on yield and porosity (A).
  - Before any build:
    - an audit quote for the S4e procedures, the UTS template and the class merges;
    - the physics freeze stays (S4d-phys).
  - No T2/T3/T5-T7: R6 fails, and R7 fails for T7.

## C: SA508 throttled retry (host B)
SA508_RESULT

## D: waiting items
- refodat90/91: the browser downloads are still absent.
- Anjaria: deferred (David, 2026-10-07; no DIC reader this round).

## Other
- Node 2 MCP stack stopped at David's request (systemd user services stopped, not disabled).
- Host B's first run also pulled mds2-2718 (tier 2 in the registry) and stalled on NIST 524s. It was stopped, and the host-B registry copy demotes mds2-2718/2716 to tier 3.
- Storage (host A v4_host/trackS): stinville 13 GB, anjaria 11 GB, amb 7.1 GB, sa508 4.6 GB (pass 1 running), alsi 1.6 GB.

---

# Track S report (v4.1, 2026-10-07): SEM pilot datasets

Branch v4.1/2026-10-07. Run on host A (CPU). **No paid model call; no keys; no items.** Every command, version and hash is in v4/LOG.md, and errors V4-E20 to V4-E24 are in ERRORS.md.

## Summary
**No pilot reached a validated reader, so no separability pilot counts for M0 and no inference family opens yet.** The data and desk checks are in place for three of the five pilot deposits plus one reserve.

| Dataset | Pilot | M0 | Why |
|---|---|---|---|
| amb2022_03 | S1 | **NO-GO** | SEM rule: mds2-2775 holds no raw SEM image (EBSD and EDS exports and rendered maps only). The S1 depth reader failed its held-out gate against NIST Table 4. |
| stinville2022 | S2 | GO WITH CHECKS | The condition series lives on the DIC fields, not the SEM images. Magnification is untested (one DIC grid, so constant by construction). Pilot pending: the S4b-2 reader failed its segmentation gates. |
| anjaria2025 | S2 | GO WITH CHECKS | No native pixel size (README states 33.4 nm). Raw speckle tiles show no slip traces without DIC, so the reader is deferred. |
| refodat90 / refodat91 | S3 | **waiting** | The browser downloads are not on the host. |
| alsi10mg_luo2024 | reserve | GO WITH CHECKS | Raw FEI-tagged TIFFs, so the deposit is kept. Magnification independent of condition. No reader in this run (reserves get S2 and S3 only). |
| sa508_ebw | reserve | not scored | Mendeley served error pages for 741 of 1068 files after one retry (V4-E24). Stopped, no workaround. |

## Verified cards: scorer families (m0_<id>.json, cards_verified/<id>.json)
- amb2022_03: T1 check, T2 check, T3 check, T4 check, T5 check, T6 check, T7 check
- stinville2022: T1 fail, T2 fail, T3 check, T4 check, T5 check, T6 check, T7 fail
  - R2 fails on the EDAX .osc (no open reader). The same orientations ship as .ang, which opens.
- anjaria2025: T1 check, T2 check, T3 check, T4 check, T5 fail, T6 fail, T7 fail
- alsi10mg_luo2024: T1 check, T2 check, T3 check, T4 check, T5 check, T6 check, T7 check

## Magnification (S3)
| Dataset | Verdict | Evidence |
|---|---|---|
| amb2022_03 | no SEM images | All 24 single-track .ctf files: native 0.25 um step, 1203 x 903 grid (constant). The TIFF maps carry borders and no pixel tag. |
| stinville2022 | untested | Tagged SEM images are a depth series (195.3 and 781.25 nm). The 16 DIC fields share one 9058 x 9052 grid (100.34 nm per the README). |
| anjaria2025 | missing | No tags; every tile 4096 x 4096. README 33.4 nm, not used for keys. |
| alsi10mg_luo2024 | independent | 160 images, 4 pixel sizes that follow the image type (2000x vs 5000x), not VED, P or v. |

No leak was found, so no resampling rule was needed.

## Readers (S4)
**S4a amb_reader (S1, melt-pool depth from .ctf orientations).**
- Synthetic, fresh seeds:
  - depth 10/10 within 10 % (pass);
  - width 8/10 (fail: deferred).
- Held-out real (NIST Table 4 optical depths, gate frozen before measuring): 0/6 cases within max(10 %, 2 SD) (gate 5); minimum adjacent between/within 0.09 (gate 2; desk 4.48). **Fail.**
- The real pools are fans of wide, feathery columnar grains. The aspect rule tuned on narrow synthetic wedges reads fragments, so depths read 2-8x low.

**S4b / S4b-2 stv_reader (S2 Stinville, interior mean Exx per IPF colour domain).**
- Localization (area fraction above K x the field mean) was deferred on dev seeds: slip bands are sub-resolution at 401 nm.
- S4b failed the fresh-seed domain-mean gate (4/10), so the reader was revised (interior erosion).
- S4b-2, fresh seeds:

  | Gate | Result |
  |---|---|
  | domain mean | 10/10 (pass) |
  | segmentation | 8/10 (fail; 17/20 maps over both fresh sets) |

- Held-out real (domains from the raw .ang orientations, no colours): 78% of 602 domains matched at IoU >= 0.7 (gate 90 %). **Fail.** IPF-X colours merge neighbours that share a loading-direction colour.

**Anjaria (S2):** deferred, because slip traces need DIC on the raw speckle tiles.

**S3:** waiting.

**Key-reader independence:** amb_reader.py and stv_reader.py (hashes in FREEZE.md: S4a, S4b-2) are this run's readers. A later T arm must offer different tools.

## Separability (S5)
- **Stinville, exploratory only** (failed reader, --allow-unvalidated, never in M0): interior mean Exx per domain over 4 strain steps.
  - Every adjacent step separates by SE: 3/3 pairs, ANOVA p 6e-12.
  - Minimum between/within ratio 0.16 (target 2), on 345 spatial domains (optimistic).
  - The grain-to-grain spread dwarfs the step change.
- **S1:** not run (reader failed).
- **S3:** waiting.
- **The aged vs solutionized contrast:** not run (no observable passed in both deposits).

## T2 classes
None: no validated reader.

## Storage on host A (v4_host/trackS)
- Datasets: amb2022_03 6.9 GB, stinville2022 13 GB (with extracted), anjaria2025 11 GB, alsi10mg_luo2024 1.6 GB, sa508_ebw 4.5 GB (partial).
- Free about 940 GB.

## Deviations from the screen's desk facts
1. **mds2-2775:**
   - 3.37 TB, not a ~8 GB tier 1 (V4-E21).
   - No raw SEM image: the "SEM" of the record means EBSD/EDS maps (NO-GO).
   - data.nist.gov serves ~1 file per minutes, with HTTP 524 on large files (V4-E22, V4-E23).
2. **The 4.48 "desk depth ratio"** is the screen's minimum between/within separability ratio on Table 4 (3.1 vs 2.2), not a depth ratio. It was corrected in LOG.md before measuring.
3. **Dryad:**
   - Anonymous download is refused (HTTP 401); David supplied a token (environment only).
   - Anjaria's tiles are 8-bit, not 16-bit as its README says.
   - No DIC results are deposited for Anjaria.
4. **Calvat et al. 2026** (Adv. Eng. Mater., 10.1002/adem.202503166) is about 600 C fatigue and grain boundary sliding: not confirmed as the Anjaria descriptor.
5. **The orix 0.15 install** broke the kit's .ang fallback (V4-E20, fixed; 53/53 tests).
6. **Mendeley (sa508_ebw)** served error pages for most files (V4-E24).

## Decisions for David
1. **S1 second iteration:** a synthetic generator built from the real fan morphology (wide columnar grains, twin-free pool against a twinned base), validated on mds2-2718 optical sections (tier 2, second instrument), since Table 4 has now been seen. AM Bench is NO-GO for SEM, but a strong EBSD/EDS source.
2. **Stinville:** segment domains from the .ang orientations registered to the DIC grid (fit the degree-3 distortion between IPF_Raw_X and IPF_DistordedDIC_X), or accept the observable gate alone (a rule waiver).
3. **Anjaria:** a DIC reader (an open DIC code validated on synthetic speckle) would open its slip observable. That is new scope.
4. **S3:** the refodat browser downloads.
5. **sa508_ebw:** retry later, or drop.
