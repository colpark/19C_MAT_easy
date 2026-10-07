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
