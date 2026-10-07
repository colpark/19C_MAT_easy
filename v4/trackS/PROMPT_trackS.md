# PanelBench v4.1 Track S: get the SEM pilot datasets ready

Prompt for Claude Code on the spark nodes.

## Context
v4.0 lives on branch `v4.0/2026-10-06` (head 13fef9b7) in `colpark/19C_MAT_easy`.
- David discarded Track A. v4.0 holds CrFeNi 61 items (T1 19, T2 3, T4 36, T7 3) and Allende 19 items (T1 4, T2 2, T3 8, T4 3, T5 1, T6 1). Oracle 80/80.
- Q2 and Q2b showed that the figures carry every decidable answer (B0 solves no decidable item). T2 is the hardest family (nano 0/10 trials, Sol 2/5 tasks).
- Spend so far: $1.9257, all under approved quotes.

Track S comes from the SEM multimodal screen (`notes/SEM multimodal datasets for PanelBench.md`, 62 candidates). The screen found that no candidate opens a reasoning family until a reader passes synthetic data and held out real evidence, and it chose three pilots:
- **S1:** the NIST AM Bench AMB2022-03 SEM record.
- **S2:** Stinville 2022 with Anjaria 2025, the same lab and pixel size on aged against solutionized IN718.
- **S3:** the two Weimar cement deposits on one Helios G4 UX at 84.3099 nm per pixel.

**Goal of this run:** every pilot deposit on the host with a verified manifest, desk checks, the magnification leak test, a validated and frozen reader per pilot, a separability pilot per pilot, and an M0 record per dataset with GO, GO WITH CHECKS or NO-GO. This run builds no items.

## Inputs (inputs check at every stage start)
The user places these on host A before the run. Record each path with its sha256 in `v4/LOG.md` at S0. A missing input stops the stage that needs it.
1. `~/Documents/harbor/trackS_kit/` (this kit):
   - `v4/trackS/` (code, registry, join rule templates, screen cards, tests, this prompt)
   - `notes/SEM multimodal datasets for PanelBench.md`
   - `notes/Raw measurement datasets for PanelBench.md`
2. `~/Documents/harbor/trackS_manual/refodat90/` and `.../refodat91/`. The user downloads these in a browser, because refodat serves a proof of work security check to scripts:
   - refodat90: 14 files, 7.02 GB
   - refodat91: 15 files, 1.04 GB

   If they are absent, run S1 and S2 and mark S3 waiting.

## Compute
Four nodes, credentials on file:
- host A `aid1@130.199.95.35`, the builder host with `~/Documents/harbor`, and its node 2 at `192.168.100.11` reached from host A
- host B `aid1@130.199.95.15`, and its node 2 at `192.168.100.11` reached from host B

Placement:
- Downloads run on host A. Host B may fetch the large Stinville archives in parallel, then copy them to host A with rsync and verify sha256 there.
- Reader development, synthetic validation and pilots run on CPU on host A and its node 2. Record the host for every run.
- No foundation model reader enters this run. The v4.0 FM reader test found none that qualifies (SAM 3/10, MatSAM 1/10, SAM 2.1 0/10 against classical 8/10). Use GPU only if a classical reader fails and the user approves an FM reader test.

## Hard rules
1. **Spend gate (skill I11).** This run makes no OpenRouter call and no other paid model call. If a step seems to need one (an audit, for example), write a quote in `v4/COST_QUOTE.md` and stop.
2. **No keys.** This run writes no keys and builds no items.
3. **Validation evidence.** Validation uses only deposit evidence, reference standards, a second instrument or the authors' reported values. Never add new human annotation, because the team has no annotators. Treat shipped labels (the refodat EDX phase map, for example) as author classifier output and state their bias.
4. **Freeze before real data.**
   - Freeze the join rules (label S2j) before `join_s.py` counts anything.
   - Freeze each reader with its synthetic validation (labels S4a, S4b, S4c) before it touches a real image.
   - `separability_s.py` refuses an unfrozen reader. Never use `--allow-unvalidated` for an M0 record.
5. **Key reader independence.** Record each reader, its version and its hash. A later T arm must offer different tools.
6. **Repository terms.**
   - Honor Retry-After and keep `--jobs` at 4 or fewer.
   - Never work around a security check, a login or a rate limit with another client or a mirror.
   - If Dryad refuses anonymous downloads, ask the user for a `DRYAD_TOKEN` (environment variable only).
7. **Untrusted data.** Archives unpack only through `inventory_s.py extract` (path traversal guarded). Read deposit notebooks and scripts as text. Never execute them.
8. **Keep data out of git.** `v4_host/trackS/` stays on the host. Commit code, join rules, M0 records, verified cards, pilot tables without images, `DESK_<id>.md` notes and reports.
9. **Credentials.** Never write credentials into a file.
10. **Ledgers.** Continue the error ledger at V4-E20 and log every command, version and hash in `v4/LOG.md`.
11. **Bugs and rule gaps.**
    - Fix code bugs yourself, rerun the tests (53 must pass) and rerun the affected stage.
    - A change to a frozen definition (a gate, a tolerance, a separability rule) is a rule gap. Stop and post it.
12. **Push.** Push after S2 and after S6, with a status note in `v4/STATUS.md`.

## S0. Setup
1. Create branch `v4.1/<date>` from `v4.0/2026-10-06` (13fef9b7). Copy `trackS_kit/v4/trackS/` to `v4/trackS/` and `trackS_kit/notes/` to `v4/notes/`.
2. Run `uv pip install -r v4/trackS/requirements_s.txt` into `v4/.venv-v4`, then refreeze the environment list.
3. Run `v4/trackS/tests/test_kit.py`. All 53 tests must pass before any download.
4. Run the inputs check and log it.

## S1. Fetch
1. Run `fetch_s.py plan --tier 1` and log the sizes per dataset, free disk and any unresolved parts.
   - For mds2-2775 the RMM record lists Traces and Pads without files, so the resolver reads the landing page. If it finds no files there, inspect the saved `landing_mds2-2775.html`, extend the resolver, log V4-E entries and rerun the tests.
2. Run `fetch_s.py get --tier 1 --jobs 2`. Every Dryad and NIST file must match its repository sha256. A file without a repository digest gets its first sha256 in the manifest.
3. Register the refodat downloads with `fetch_s.py manual --dataset refodat90 --src ...` (and refodat91). The file count and total size must match DataCite.
4. Run `fetch_s.py verify` and `fetch_s.py inputs`, then paste `INPUTS_trackS.md` into LOG.md.
5. Stop and post if a part stays unresolved or a checksum fails after one retry.

## S2. Desk checks
1. Run `inventory_s.py extract`, `scan` and `readers` for every dataset.
2. Read each README and descriptor, fill `joinrules/<id>.json` (maps and confirmed patterns), freeze the rules (S2j), then run `join_s.py`. Zero unmatched data files is the target, and every unmatched file gets a line in the desk note.
3. Write `v4/trackS/DESK_<id>.md` for each dataset. Answer its questions from file evidence:

| Dataset | Questions |
|---|---|
| amb2022_03 | Does mds2-2775 hold raw SEM images (SE or BSE TIFF with native tags) or only EBSD and EDS exports? Which lines (folder "multiple traces L-01 to L212") and pads map to which of the 7 laser cases (245 to 325 W, 800 to 1200 mm/s, spot 49 to 82 um)? Are the 21 single tracks (3 per case) in this record? Do EDS and EBSD ship as raw files (.h5oina, .bcf, .cpr, .crc) or as exports (CSV, TIFF)? Pin every record version. |
| stinville2022 | From README_file.txt: the names of the four strain steps (plastic strain 0.17, 0.32, 0.61, 1.26 %). Where do the BSE and SE slice images sit? Does a stress strain file exist inside an archive? Do raw patterns cover only two slices, and do raw DIC tiles exist anywhere? |
| anjaria2025 | From README.md: the tile layout per strain level (0.38, 0.62, 1.02, 1.95 %), the reference images, the pixel size tags, and how the single EBSD map (718_SS.ang) registers to the BSE tiles. Does Calvat et al. 2026 (Anjaria and Stinville among the authors) describe this deposit? |
| refodat90 | The member list, the EDX label table (13 index values, 11 distinct labels), whether the indentation files hold raw load displacement curves or only results, and the two grids (40 x 20, 65 x 20). |
| refodat91 | The specimen map 21C, 21H, 25C, 25H to mix (M38, M44), w/c and carbonation state. The LTDSC paste specimens that join each mix. The MAPS tile tags. |

4. Push.

## S3. Magnification leak test
1. Run `magleak_s.py` for every dataset. Log the verdict per condition field:
   - constant
   - independent
   - leak
   - missing
2. If a dataset leaks, write and freeze a resampling rule (one pixel size per pilot) before S4. Keep scale bars and magnification out of any later T2 panel.
3. If images lack native pixel sizes, either build a scale bar reader validated against tagged images, or exclude them. Never guess a scale.

## S4. Readers (one observable per pilot, chosen before looking at condition values)
For each pilot:
1. Write the observable definition and its gate in the desk note.
2. Build a synthetic generator with known truth that matches the deposit's pixel size, noise and contrast.
3. Tune only on synthetic dev seeds, then freeze.
4. Validate on fresh synthetic seeds, then on the held out real evidence below.
5. Use the skill M2 gates: 9 of 10 within the stated tolerance, or constant bias gates as in D3. A reader that fails stays out of keys, and the pilot records "deferred".

| Pilot | Observable (first choice, then fallback) | Held out real evidence |
|---|---|---|
| S1 | Melt pool depth and width on SEM cross sections if they show whole melt pools. Otherwise cell spacing near the fusion boundary. | NIST Table 4 depths (means with SDs) in the measurement PDF. Optical sections of the same tracks in mds2-2718 (second instrument). EBSD line spacing of 108 to 109 um against the commanded 110 um (length check). |
| S2 | Stinville: slip localization per grain from the HR-DIC fields (for example the area fraction above k times the mean effective strain, with k fixed on synthetic data). Anjaria: slip trace density per grain from the BSE tiles. | The authors' DIC against macroscopic strain agreement (-0.68 to +0.29 % of total deformation). Slip trace angles against the highest Schmid factor plane from EBSD (independent law). The 3D against 2D EBSD mismatch (7 % area, 1.6 degrees). |
| S3 | BSE phase and porosity classes by gray level on the refodat90 montage and the refodat91 MAPS tiles. Indentation modulus per phase if raw curves exist. | The shipped EDX phase map (author classifier output, report its bias). Micro XRF. LTDSC porosity of the matching pastes, as an ordering check only, because paste differs from concrete. |

## S5. Separability pilots
Build one pilot table per pilot with the frozen reader. Columns: condition, order, unit, sub, value.

| Pilot | Conditions | Unit | Notes |
|---|---|---|---|
| S1 | laser case ordered by energy density | track (3 per case) | Replicate units. Also reproduce the desk depth ratio of 4.48 from Table 4 with our own reader before trusting it. |
| S2 | strain level within each deposit | grain inside one specimen | Spatial units, so the output reads optimistic. Run the aged against solutionized contrast at matched strain only if one observable passed S4 in both deposits. |
| S3 | specimen or mix and carbonation state (refodat91), distance bin from the aggregate interface (refodat90) | tile or indent | Spatial units, so the output reads optimistic. |

Run `separability_s.py --reader-freeze <label> --unit-type <unit>` on each table. A failed series stays for T1 and T4 only (skill rule).

## S6. M0 and report
1. Run `m0_s.py --dataset <id> --pilot <pilot json>` for every dataset. It writes `m0_<id>.json` and `cards_verified/<id>.json` with every card change and its evidence.
2. If a pilot gets NO-GO, post the evidence first. Then fetch the reserve at tier 1 (`--dataset sa508_ebw` or `--dataset alsi10mg_luo2024`) and run S2 and S3 on it. The AlSi10Mg zip decides its inclusion: raw TIFF keeps it, slide exports drop it.
3. Write `v4/trackS/TRACKS_REPORT.md` with:
   - the GO decision per dataset with its stop and check reasons
   - the verified cards with scorer statuses and the families each keeps possible
   - the magnification verdicts
   - each reader with its synthetic and real validation
   - each separability pilot (pairs, ANOVA, ratio, unit type)
   - the classes for T2
   - storage used
   - every deviation from the screen's desk facts
4. Push. Stop and post a short summary. Wait for David's call on the v4.1 item build and any audit quote.

## Out of scope
Item generation, any model run, tier 3 downloads unless an S4 reader needs them (the Stinville 3D archives total about 51 GB), new datasets, and FM readers.

Expected time: S0 to S3 half a day, dominated by about 10 GB of tier 1 downloads plus the browser downloads. S4 and S5 take one to two days.
