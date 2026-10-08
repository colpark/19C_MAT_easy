# DESK HTEM MC (v4.5 MC0; host A spark-112b; 2026-10-08)

**Sources.** The descriptor (Zakutayev et al. 2018, PMC5881410) and the method papers arXiv 2105.05160, 2206.03594 and 2306.02233, all hashed in DESK_htem.md, plus the API records themselves.
- Data-side checks: `htem/mc/desk_mc.py` (1797 cached samples, 565 cached libraries), output `v4_host/htem/mc/desk_mc.json`, plus a NaN-safe recheck logged in LOG.md.
- The papers give no XRD background, frame, Kα2, optical normalization, incidence-angle or probe-range statement: a text search for each topic over the four sources returned only unrelated spans (magnetometry background subtraction, GIWAXS frames).

## XRD processing state
- **Background.** Records carry `xrd_intensity` and a separate `xrd_background` array (1795/1795 with finite values). Intensities are **not** background-subtracted. The background is about 97 % of the median intensity, the 5th-percentile intensity is about 8000 counts, and no intensity is negative. The API background is a database-processed curve: level A, never keyed.
- **Area-detector frames.** Records name a `.gfrm` file (Bruker frame). The integrated 1D pattern shows no frame-edge steps: 2 step candidates in 1795 patterns, at unrelated angles. Frames are treated as merged without steps.
- **Kα2.** The Kα1/Kα2 splitting is 2 tanθ·Δλ/λ: 0.076° at 30° and 0.133° at 50°. The fitted FWHM of strong peaks (2693 peaks, P1r2 + P2r2 matrices) has median 0.59° (2θ ≤ 40°) and 1.01° (> 40°), and the 10th percentile is 0.43°. **Kα2 is unresolved.** Family H6 (Kα2 shoulder) is dropped (VM-E01).

## Optical
- **Absolute or normalized.** T and R are reported as fractions: median maximum T 0.81, median maximum R 0.39, median 95th-percentile T + R 0.94. They behave as absolute values. However, 93 of 1463 spectra exceed T = 1.05 (99th-percentile maximum 2.56), consistent with a reference or normalization artifact on some records. That is a measurement-side signature, recorded for MC3 and MC4.
- **Incidence angle.** Not stated in any source (D gap, as in DESK_htem).
- **Substrate.** `deposition_substrate_material` is given on 378 of 565 libraries: Eagle 2k 284, EXG/ExG/exg 48, Glass 13, Quartz 16, sapphire 3. It is None on 187.
- **Bare-substrate references.** No library or sample record is a bare substrate: 1 library has no elements, and it has no optical data. **No substrate reference exists.** Transparent-region bands must come from the films themselves and from dev replicates.

## Four-point probe
- **Raw I-V.** 579 positions carry finite paired arrays: mostly 5 points, others 7-33.
- **Sweep span.** Most curves sweep to about ±1 µA (451); others to 0.5 µA (45), 0.1 µA (14) or 1 mA (8). 37 curves have |I| below 5e-8 A everywhere: a near-zero sweep, recorded for MC6.
- **Ranges.** No current or voltage range or compliance is stated in any source (D gap). **MC6 uses only data-intrinsic criteria** (linearity, polarity, noise, zero-current sweep), never an instrument ceiling.

## XRF
`xrf_type` over 565 cached libraries: maxxi 308, fischer 193, smx 63, fischerXUV 1. The instrument differs per library, so composition comparisons across libraries carry an instrument term. MC rules compare positions inside one library, or across libraries of the same xrf_type.

## Replicates
Replicate groups (same recipe key, including temperature, with 2 or more multimodal libraries): 37 groups in 23 systems. Top systems: Mn-Se-Te-Zn 5, Mn-O-Zn 4, Cu-O-Zn 3, Cu-N 3, N-Sn-Zn 3, Mn-O 2; 17 more systems have 1 each.
