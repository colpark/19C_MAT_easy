# HTEM round 2 pre-registration (frozen HR0 before any new reading)

Round 2 aims at inference families (T3, T7). Base: the H9 items and gates (4236d092). Prompt: PanelBench 2026-10-08, Part 1. Ledger: VH-E11 onward (VH-E07 to VH-E10 were used by H9). Freeze labels HR0 to HR6.

**Disclosure.** Before this freeze the builder has seen:
- the round-1 dev statistics, H4 and H5 summaries, H6 and H9 items, and the nano results on H8 items
- the census ranking (`census/ranking.csv`) with its scores and columns

The builder has not seen any probe optical spectrum or XRD pattern of an oxide system, and no E04 or E_U value of any sample.

## 1. Optical observables

### 1.1 E04 (reader S4ho2)
- **Input:** α(E) from the kit's `readers/optical.absorption()` on the contiguous unsaturated run, with `t_min` from config (0.01).
- **Definition:** E04 is the lowest photon energy where α first reaches 10^4 cm^-1, scanning upward in energy along the run. It is interpolated linearly in log10 α between the bracketing points.
- **Censored** when:
  - α never reaches 10^4 cm^-1 inside the run, or
  - the crossing lies within 0.1 eV of the saturation energy (`E_saturation`), or
  - the run has fewer than 6 points.

  Censored values are never keyed. The reader reports them as flagged.
- **Smoothing:** none. A single-point upward spike is not a crossing; this is a named default. The crossing must be confirmed by the next point also lying at 10^4 cm^-1 or above, or by the run ending at saturation.

### 1.2 Thickness provenance (decision)
- **Verbatim spans** (DESK_htem.md lines 26-28): "using thickness of the samples determined by XRF" (Sci. Data 2018); "Resistivity was calculated using XRF-measured film thickness." (arXiv 2306.02233). The instrument per library is not recorded (DESK_htem.md line 38).
- **Skill M1 test:** a value is M when the instrument itself reports it, and A when it is computed from other matrix quantities. Neither span says the number is the instrument software's own output. "Determined by XRF" also fits a fit or model applied to the XRF readings by the database pipeline. The restrictive choice (I3) applies.
- **Decision: thickness stays level A.**
- **Consequence (bounded-input rule):** E04 depends on thickness through α ∝ 1/d.
  - For every E04 key, recompute E04 with d × 0.75 and d × 1.25 (the pre-registered ±25 % relative thickness uncertainty).
  - Key E04 only where max |ΔE04| < tol_E04 / 2. Such keys are tagged `input_A_bounded`.
  - A sample whose shifted E04 is censored fails the rule.
- **E04 tolerance:** tol_E04 = 0.02 × the energy span of the fixed item axis, per system. The axis is [floor of the 5th percentile, ceil of the 95th percentile] of run energies on the dev library, rounded outward to 0.5 eV. It is frozen in config at HR1 from dev data only.

### 1.3 Urbach energy E_U (reader S4hu)
- **Definition:** E_U = 1 / slope of ln(αd) against E, by least squares over the run points with 10^3 ≤ α ≤ 10^4 cm^-1. ln(αd) = ln(−ln(T/(1−R))) does not depend on d.
- **Window:** the window bounds are α thresholds and so depend on d. As a restrictive addition, the bounded rule of 1.2 applies to E_U too: recompute with d × 0.75 and d × 1.25, and key only if the relative change is under 7.5 % (half the 15 % tolerance). Tag `input_A_bounded`.
- **Validity:** at least 5 points in the window, slope > 0, and R² ≥ 0.95. Otherwise E_U is None.
- **Tolerance:** 15 % relative (the synthetic gate level).
- **Keying:** E_U is reported always, and keyed only if it passes its own gates (HR1).

### 1.4 Edge width (selection only, never keyed)
Edge width is the energy span over which ln(αd) rises from 10 % to 90 % of its range along the unsaturated run. It is computed on the run, and both crossings are taken as the first upward crossing.

## 2. Anion composition
- `sample_io.composition()` gains `anion_frac`. It holds the XRF fractions of the anions measured as elements in the record (e.g. Se, Te), normalized over those anions only. These are the elements of sample_io.ANIONS that the record lists as bare-element entries. An anion the record does not list (often O or N) is absent, not zero.
- Cation fractions are unchanged, so the round-1 cells, items and hashes stay identical. Determinism confirms this by hash.
- **Condition variable for P2:** x = Se / (Se + Te) from `anion_frac`.
- **Bins:** width 0.05 (as round 1's Zn bins), frozen here. Every series stays inside one temperature level.
- **Tooling:** `pilot_table.py` gains `--frac anion|cation` and `--element <El>`. `--cation <El>` stays as the round-1 alias for `--frac cation --element <El>`.

## 3. Oxide system selection rule
Candidates are the anion-class O systems of the frozen `census/ranking.csv`, in its score order:
1. O-Sn-Ti-Zn
2. Cr-Mn-O
3. Co-Ni-O-Zn
4. Co-Ni-O
5. Mn-O
6. Ag-O-V
7. Cu-O-Zn

Evaluate them in order, and the first two that pass all three tests are O1 and O2.

**Test (a), structures.** Every phase in the candidate's phase list below has a measured COD structure with atom sites, and none is constructed or calculated. Each COD id is checked through the COD API with refs.py (throttled, cached). The lists are written now, from chemistry knowledge, before any pattern of these systems is read:

| System | Phase list |
|---|---|
| O-Sn-Ti-Zn | ZnO wurtzite; SnO2 rutile; TiO2 anatase; TiO2 rutile; Zn2SnO4 inverse spinel; Zn2TiO4 inverse spinel; ZnTiO3 ilmenite |
| Cr-Mn-O | Cr2O3 corundum; Mn2O3 bixbyite; Mn3O4 hausmannite; MnCr2O4 spinel; beta-MnO2 pyrolusite |
| Co-Ni-O-Zn | NiO rocksalt; CoO rocksalt; Co3O4 spinel; ZnO wurtzite; ZnCo2O4 spinel; NiCo2O4 spinel |
| Co-Ni-O | NiO rocksalt; CoO rocksalt; Co3O4 spinel; NiCo2O4 spinel |
| Mn-O | MnO rocksalt; Mn3O4 hausmannite; Mn2O3 bixbyite; beta-MnO2 pyrolusite |
| Ag-O-V | V2O5; VO2 (M1); Ag2O; Ag metal; beta-AgVO3; Ag3VO4 |
| Cu-O-Zn | CuO tenorite; Cu2O cuprite; Cu metal; ZnO wurtzite |

A COD entry flagged as theoretical, or one without atom sites, fails. When a phase has several COD entries, take the lowest id that has atom sites and an ambient-condition measurement. "Ambient" means no pressure field, or 0.1 MPa, and a temperature within 273-310 K, or none given.

**Test (b), edge width.** The median edge width on the census probe samples (the frozen probe_ids, cached) is 0.4 eV or less. Thickness comes from the record; probes without T, R and thickness are skipped, and at least 6 probes must remain.

**Test (c), E04.** At least half of the probes give an uncensored E04, and the median of those E04 lies inside the measured energy range.

Tests (b) and (c) use probe samples only. They are selection statistics, not keys, and the probes are not part of any item.

**Fallback.** If fewer than two candidates pass, round 2 runs with those that pass. The shortfall is reported, and the gate is never relaxed.

**P1 and P2.** P1 (N-Sn-Zn) re-tests E04 and E_U from the cached libraries and builds optical items only if its gates pass. P2 (Mn-Se-Te-Zn) carries the anion lever.

## 4. Libraries, dev and fetch (HR2)
- Libraries are chosen by the round-1 frozen rule (`select_pilot.py`: replicate groups, temperature coverage, electrical, id; at most 12).
- The dev library is `random.Random('htem-dev|<system>').choice(selected)`, as in round 1.
- Fetches go through htem_api with its throttle. References come from refs.py (COD only, by rule 3).

## 5. Physics table (HR3, frozen before any key)
- **Vegard (independent law; lattice constants from the COD structures of the end members):**
  - **P2:** zinc-blende (111) against x = Se / (Se + Te) across whole films, with no Zn-rich restriction as the prompt states. Model error is 0.5 % on a (round-1 named default).
  - **Keep rule:** the law must agree with the hidden cell within tolerance. Cells where Mn alloying moves the peak away from the law fail this keep rule rather than being keyed.
  - **O1 and O2:** Vegard only where the system's phase list contains two isostructural end members that form a solid solution, with the same space group and a sourced lattice constant for each. Otherwise there is none.
- **T7 fit law:** E04 (or E_U) = E0 + s·x over the system's composition variable x. This is the bowing form E = (1−x)E_A + xE_B − b·x(1−x) restricted to two free parameters with b = 0. The bootstrap is over the reading uncertainties.
  - **Composition variable:** for P2, x = Se / (Se + Te). For the oxides, the cation fraction with the largest range on the dev library (dev only, I7).
  - **Hold-out:** a contiguous composition block at one end (or another library, or another temperature), never an interior neighbour. Gates g1 to g4 as in v1.5, with at least 5 fit cells.
- **Phase identification:** as in round 1 (match_phase, 0.3 deg, score 0.6 or more).

## 6. Separability (HR4)
`separability_s.py` runs per validated observable and per temperature level, in library units where replicates exist:
- the XRD peak against the anion ratio for P2
- E04, and E_U if validated, against the composition variable for every system

Results are reported as they come out.

## 7. Items (HR5)
- **Families:** T1, T2, T3, T4 and T7, under skill v1.5 plus the H9 rules: no cannot-tell twin, the map keep rule, the text-cue gate and random A/B labels.
- **New rule: item-level typical-magnitude trim.** Every numeric item that the typical-magnitude rule (PRIOR_RULES_htem.md) solves is dropped, whether or not its family passes the family-level prior gate.
- **Typical values for new quantities:**
  - E04 typical = the textbook gap of the system's majority phase (the end-member binary oxide or chalcogenide gap of the dominant cation), rounded to 0.1 eV.
  - E_U typical = 0.1 eV.

  These are written in PRIOR_RULES_htem.md at HR3.
- **Build order:** O1 first; then O2 with configuration and table changes only (the code diff is reported); then P2 (and P1 if its optical gates pass).
- **Gates:** every v1.5 gate plus g4 for T7. Determinism on host A twice and host B. Export of A0, B0 and B0f, with the oracle at 1.0.

## 8. Go criteria for round 2
1. At least one inference family (T3 or T7) with 10 or more distinct facts, across P2, O1 and O2.
2. At least 3 families with 10 or more facts in at least one system.
3. Every keyed observable comes from a reader that passed its synthetic, replicate and database-rank gates.
4. The O2 build needs configuration and table changes only.

## 9. Reader gates (HR1, as the prompt states)
- **Synthetic, on fresh seeds:**
  - The seed base is recorded at the S4ho2 freeze. Generators are drawn from dev libraries only.
  - Ranges: E_U 0.03-0.30 eV and d 0.1-0.6 µm, with saturation and fringes.
  - E04 within 0.03 eV of truth on 9 of 10 seeds, with a constant bias (bias SD 0.02 eV or less).
  - Censoring flagged on every seed whose α never reaches 10^4 cm^-1.
  - E_U within 15 % on 9 of 10 seeds.
- **Replicate (M):** median |ΔE04| 0.05 eV or less over composition-matched replicate pairs (as build_matrix pairs them); median |ΔE_U| / mean 0.20 or less.
- **Database rank (A, bias reported):** Spearman ρ of 0.8 or more between E04 and `opt_direct_bandgap`, per system.
- **Failure:** a reader that fails a gate for a system gets no keys there. Log a VH-E and continue.

## Amendment HR0a (frozen before any real spectrum is read)
- **Absorption inversion (VH-E11).** The kit's single-pass form α = −ln(T/(1−R))/d has an apparent floor of ln(1 + R)/d in transparent regions, about 10^4 cm^-1 for 0.1 µm films. That floor sits on the E04 threshold and inside the E_U window.
  - **Dev seeds 0-99** (E_U 0.03-0.30 eV, d 0.1-0.6 µm): single-pass E04 is within 0.03 eV on 18 % (bias −0.17 eV) and gives E_U on 4 seeds. The exact incoherent film inversion, x = e^{−αd} solving T = (1−R)² x / (1 − R² x²), gives E04 within 0.03 eV on 100 % (bias 0.001 eV) and E_U within 15 % on 88 of 88.
  - **Change:** E04, E_U and the edge width use the incoherent inversion (readers/edge.py `absorption_incoherent`, config `edge_inversion: incoherent`), with the same pairing, saturation and contiguous-run rules as `optical.absorption()`. The round-1 Tauc reader is unchanged.
  - **Caveat:** the synthetic generator uses the same incoherent model, so the synthetic gate cannot test model mismatch. The replicate and database-rank gates on real data carry that test.
- **Bookkeeping:** this changes how α is computed for 1.1-1.4. The definitions themselves are unchanged. It is a reader choice made on dev synthetic evidence only (I7).
