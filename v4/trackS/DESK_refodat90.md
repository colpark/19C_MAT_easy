# DESK refodat90 (Track S round 3; host A spark-112b; 2026-10-07)

Deposit: refodat doi:10.71758/refodat.90. Browser download, 14 files, sha256 in v4_host/trackS/refodat90/manifest.json. A CEM I mortar surface, ion-milled (Ar BIB), imaged by several methods. Decision rule: D0 (DESK_refodat_rule.md).

## 1. R3: methods source
**Sources, hashed:**
- files/measurement_overview.pdf (sha256 193093336bd652a8...): a layout figure only ("height map", "BSE", "EDX", "µXRF Si-map (segmentation)"), no methods text.
- Notebooks: process_EDX_phase_dataset.ipynb (1fa4e7725693e26f...), NI-evaluation+EDX-segmentation.ipynb (eb5f90c4cf0a896f...), CM process_dataset.ipynb (834be09b3f265559...).
- NI-Auswertung.py is empty (e3b0c442..., the empty-file hash).

**The methods text is the DataCite description**, quoted verbatim:
- "A mortar prism (CEM I) with dimensions of 9 × 3.5 mm² was ion-milled using an argon broad ion beam device (EM TIC 3X, Leica) for a total of 72 h at 6 kV and 2 mA"
- "SEM: Helios G4 UX, Thermo Fisher Scientific EDX: XMaxN 80 and Ultim Extreme, Oxford NI: Hysitron TS 77 Select with a Berkovich tip, Bruker CM: VK-X3050, Keyence"
- "SEM-BSE 47104 × 18232 84.3099 3971.3 × 1537.1"; "SEM-EDX 1024 × 704 288.722 295.7 × 203.3"; "NI position 1 40 × 20 5.0 100 × 200 NI position 2 65 × 20 5.0 100 × 325"

**Acquisition settings:**
- BSE, from the FEI tags of a raw tile (Tile Set (2)): HV 10000 V, BeamCurrent 1e-10 A, Dwelltime 3e-07 s, PixelWidth 8.43099e-08 m, detector "CBS", WD 4.81 mm, 4096 × 4096 px.
- EDX: Oxford Aztec project (REF Beton BIB.oip/.oipx, 125 .dat files, reports/Electron Image 1.tiff). The settings sit inside the proprietary project, which has no open reader. D gap.
- µXRF: EDAX Orbis spectrum image fullmap.Spd, 388 × 1148 px × 4000 channels. The description says "The scaling of this dataset is rather unreliable and was corrected by aligning it to other images".
- NI: Hysitron TS 77 Select, Berkovich; Pmax about 2000 µN (NI_pos*.csv).

## 2. Registration (D0 condition 1): FAIL
**Transform.** The authors' georeferencer points were fitted with an affine. It reproduces their listed residuals exactly (BSE RMS 38.1 source px = 3.2 µm; EDX PNG RMS 3.5 px). The EDX index map full_phase_map.tif (702 × 1022) is the 3× nearest source of full_phase_map.png.

**Result:** median 0.35 um, p95 8.86 um over 558 windows; after removing the median offset median 0.32, p95 8.94; pseudo-BSE/BSE window correlation median 0.23. D0 needs a median ≤ 1.0 µm and a 95th percentile ≤ 2.0 µm, so condition 1 fails on the 95th percentile.

**Diagnostic, disclosed, not a gate:**
- 72 % of windows lie within 1 µm and 76 % within 2 µm, but 16 % exceed 5 µm.
- The 57 windows with post-shift correlation ≥ 0.5 have a median of 0.18 µm and a 95th percentile of 0.49 µm.
- So the global alignment is good. The tail comes from windows where the 11-class pseudo-BSE carries little of the BSE texture, and D0 allows no window filtering.

**Outputs:** v4_host/trackS/refodat90/desk/registration.json and registration_map.png (script readers/desk_registration_r90.py, frozen D0m).

## 3. Indentation level
- **Tables only.** NI_pos1.csv (800 indents) and NI_pos2.csv (1300) list per-indent instrument outputs: "File,hc(nm),Pmax(µN),S(µN/nm),A(nm^2),hmax(nm),heff(nm),Er(GPa),H(GPa),A,hf(nm),m,X(mm),Y(mm),Drift(nm/s)". The raw .hys load-displacement files are not deposited.
- **Area function and frame compliance:** not recorded. A comes per indent from the authors' calibration. D gap.
- **Levels:** Pmax, hmax and positions are instrument readings (M). S, A, Er and H come from the instrument's Oliver-Pharr fit with an unrecorded area function (A). Modulus can rank only as author values (A), and our own O-P is impossible without curves.

## 4. EDX level
- **.spd:** the only .spd is the µXRF (XRF-RAW/fullmap.Spd). It is a raw spectrum image (counts per channel per pixel, 388 × 1148 × 4000, uint32), so an M-level route exists for µXRF in a later round. Its sidecars (.SPC/.IPR) differ in filename case, a source quirk.
- **EDX raw:** the Aztec project (.oip and .dat) is proprietary, with no open reader in the kit. No M-level EDX route exists now.
- **Phase labels:** the deposit lists 13 labels; the notebook's phase_names dict, verbatim:

  > 0: "pores", 1: "AFm/AFt", 2: "alite/belite", 3: "matrix", 4: "CH", 5: "C-A-S-H", 6: "alite/belite", 7: "C3A/C4AF", 8: "C3A/C4AF", 9: "Mg-C-A-S-H", 10: "Slag", 11: "quartz", 12: "C-S-H"

  The phase map has 11 merged labels: {0: 'AFm/AFt', 1: 'C-A-S-H', 2: 'C-S-H', 3: 'C3A/C4AF', 4: 'CH', 5: 'Mg-C-A-S-H', 6: 'Slag', 7: 'alite/belite', 8: 'matrix', 9: 'pores', 10: 'quartz'}.
- **Derivation:** the colours of an Aztec phase image ("Phase Image 3.tif", 13 colours) were matched to names by hand ("# has to be manually matched"), then duplicates merged. The phase map is author-derived (A/I): validation only.
- No EDX reader was built (per the prompt).

## 5. R11 and R12
- The ITZ pair (wall-effect packing against CH enrichment from bleeding) is pre-registered in physics_refodat.py (ITZ_PAIR), with signatures on porosity, anhydrous fraction, indent modulus and portlandite slopes against distance.
- Claims come from templates only; there is no claim ladder.

## 6. Levels
- **Frozen bins:** 0-10, 10-20, 20-30, 30-50 and 50-100 µm, so at most 5 levels.
- **Indents per bin (NI_pos2):** 92 / 40 / 41 / 83 / 208, with 676 beyond 100 µm. The aggregate is the authors' EDX quartz class (A), regions of at least 2000 px, as a desk count only; our aggregate mask is a reader-stage step.
- All 5 bins hold at least 3 indents. **T7 needs 7 or more levels, so it cannot open.**

## D0 decision
**refodat90: no reader stage.** Condition 1 (registration) fails: 95th percentile 8.86 µm against ≤ 2.0 µm. Condition 2 was not evaluated, because the spatial split belongs to the reader stage, which does not run. M0 stays GO WITH CHECKS.
