# V8-1 supply and substrate (Gate S)

Builder-only: this file names published designs. Agent-facing text uses the hash ids below (hard rule 5). Produced by `v8/truth/supply.py` (sequence and CA geometry only; no FM call, no truth run) over the 20 PDBs of `pylesharley/DHR10micaX` at `09d10aa8`, `rosetta_models`, repeat period 50.

## 1. Repeat-unit count (amendment C item 1, reading per addendum D item 1.1)

U0 = `SSEVLELAIRLIKEVVENAQREGYDISEAAAAAAEAFAAVAEAAKAAGIT` (the modal inner 50-mer; sha256 eaec6763f0c3cc5f).

Mismatches are counted over all cyclic shifts, so a block's phase does not matter. "Inner block" excludes the first and last block of a sequence, which overlap a design's own caps.

| Reading | Count | Designs |
|---|---|---|
| **Family (in force, D 1.1):** at least one inner block within 2 of U0 | **16 of 20** | mica18, mica18NC, mica14-checker, mica2NC, mica6NC, honeycomb 3H to 7H, TrimerV1, TrimerV5, V1hb1 to V1hb4 |
| **Strict (rod source only):** every inner block within 2 of U0 | **10 of 20** | mica18, mica18NC, TrimerV1, TrimerV5, mica2NC, mica6NC, honeycomb 4H to 7H |

The family count of 16 reproduces amendment C's finding, with the same design list. The two counts differ only because six family designs carry one further inner block 5 to 30 mismatches from U0: the honeycomb 3H cap-like helix and the second (non-mica-facing) unit of the checker and V1hb trimers.

**U0 rod source:** mica18 passes the strict reading, so U0 rods come from it (D 1.1). Rod 19.7 × 3.7 nm, aspect 5.4, 17 internal repeats.

## 2. Distinct units and hash ids

Only the four 4H charge-pattern controls carry units distinct from U0, confirming amendment C. DE and KR count acidic and basic residues in the unit; net is KR − DE.

| Unit | Hash id | Source design | mm to U0 | DE | KR | net | sha256 (16) |
|---|---|---|---|---|---|---|---|
| U0 | HRm-ea | mica18 (and 15 others) | 0 | 9 | 4 | −5 | eaec6763f0c3cc5f |
| C1 | HRm-60 | 4H scrambled carb1 | 3 | 8 | 4 | −4 | 607f095c1edb9caa |
| C2 | HRm-ef | 4H scrambled carb2 | 5 | 8 | 4 | −4 | ef67e21d637ee64a |
| C3 | HRm-5d | 4H scrambled net1 | 8 | 10 | 6 | −4 | 5d91fb6abe299e47 |
| C4 | HRm-f1 | 4H scrambled net2 | 7 | 9 | 7 | −2 | f12b6a16f44a252c |

The C1 to C2 pair keeps the net charge of the carboxylate array and moves it (carb controls); C3 and C4 change the pattern at a higher charge (net controls). All four exist only as 4H monomers, 5.6 × 3.6 nm, aspect 1.6, so their rods are tiled to 14 and 18 repeats (amendment C item 4).

## 3. Split and Gate S

- **Dev:** U0 (HRm-ea), C1 (HRm-60), each on both surface cations.
- **Test:** C2 (HRm-ef), C3 (HRm-5d), C4 (HRm-f1), each on both surface cations = 6 (unit, cation) systems; each at 14 and 18 repeats = 12 rod systems, 24 worlds.

| Gate S condition | Required | Found | Result |
|---|---|---|---|
| Dev and test share no unit | disjoint | disjoint (U0, C1 vs C2, C3, C4) | pass |
| Dev units | ≥ 2 | 2 | pass |
| Test units | ≥ 3 | 3 | pass |

**Gate S: PASSED.**

## 4. Muscovite structure (amendment B item 5, addendum D item 1.2)

The IFF v1.5 repository on GitHub carries parameter files only; its README directs surface models to the distribution zip. That zip does ship muscovite models, so the first branch of D 1.2 applies and COD 1100011 is **not** used.

- **Source:** `interface_ff_1_5.zip` from bionanostructures.com/interface-md (sha256 42b26c36ee91254e), `INTERFACE_FF_1_5/MODEL_DATABASE/CLAY_MINERALS/`.
- **Files:** `mica1_cell.car` (f4c1b940dd72701b) and `.mdf` (c0251d548409a1e1); `mica15_single_layer.car` (cbe12ea46aba840b) and `.mdf` (156bff9013023353). Dated 2005, Materials Studio format, with IFF atom types, charges, hydroxyl hydrogens and the K+ layer already in place.
- **Cell check** against 2M1 literature (a 5.19, b 9.03, c 20.1 Å, β 95.8°): `mica1_cell` gives a 5.1918 (+0.03 %), b 9.0153 (−0.16 %), c 20.0457 (−0.27 %), β 95.735° (−0.07 %). **All within 1 %.** (COD 1100011 also passes, at +0.19, −0.04, +0.03, −0.02 %, and is recorded as the unused alternative.)
- **Composition check:** 84 atoms per cell, Z = 4, giving K₁Al₄Si₃O₁₂H₂ per K. Ideal muscovite KAl₂(AlSi₃)O₁₀(OH)₂ is K₁Al₃Si₃O₁₂H₂ per formula unit. The model's extra Al per K is the tetrahedral Al substitution counted separately: `mica1_cell` has 4 octahedral Al (types ay1, ay2, charge 1.448 and 1.449) plus 4 tetrahedral substitutions (ayt1, ayt2, charge 0.800) among 16 tetrahedral sites, the 1:4 Al:Si ratio muscovite requires. Total cell charge is exactly 0.0000.
- **Charges** match `charmm27_interface_v1_5.prm`: K+ 1.0, Si 1.1, octahedral Al 1.448/1.449, tetrahedral Al defect 0.8, surface O −0.550 (−0.783 next to an Al defect), octahedral O −0.758 and −0.683, hydroxyl H 0.200.
- **Hydroxyl hydrogens** are present in the model (8 per cell, type hoy), so no hydrogen placement or hydrogen-only relaxation is needed.
- **Na+ surface:** built by exchanging the surface K+ layer of this model for Na+ (amendment B item 2), using the IFF NA+ type (charge +1.0, ε −0.094 kcal/mol, Rmin/2 1.585 Å) from the same parameter file.
- **Slab:** `mica15_single_layer` (630 atoms, 25.96 × 27.05 Å, K+ on both basal surfaces) is the starting layer; the production slab is tiled from `mica1_cell` to hold the fragment with the margin V8-1 needs.
