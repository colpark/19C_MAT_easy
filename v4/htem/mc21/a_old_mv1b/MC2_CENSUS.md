# MC v2 census (MV1b; frozen rules HTEM_MC2_RULES.md, code mc2/ at MV1)

Scope: 222 non-dev fully cached libraries (VM-E03). Dev libraries only set E (MC2_ENERGY.json) and the noise (MC_CENSUS.json).

**Round: NO-GO.** Built types: L7; critical items over built types 39 (need 60), in the test split 9 (need 15), types built 1 (need 3).

| Type | Task | Eligible facts (systems) | Decided | Critical (systems) | Naive fails | Controls avail / kept | Critical in test | C2 | C3/C4 (cheap max vs control share + 10) | Effect median (p10-p90) | Builds |
|---|---|---|---|---|---|---|---|---|---|---|---|
| L1 | best conductor | 50 (21) | 21 | 6 (3) | 29% | 15 / 3 | 3 | 1.00 (9 pairs) | fail (0.56 vs 0.43) | 0.105 (0.00522 to 1.26) | no |
| L2 | resistivity trend | 17 (6) | 17 | 6 (2) | 35% | 11 / 3 | 2 | 0.75 (16 pairs) | fail (0.44 vs 0.43) | 3.17 (-9.55 to 19.2) | no |
| L3 | most transparent at E | 148 (43) | 55 | 10 (5) | 18% | 45 / 4 | 1 | 0.90 (21 pairs) | pass (0.36 vs 0.39) | 0.0758 (-0.162 to 0.184) | no |
| L4 | lattice constant at x0 | 6 (1) | 6 | 6 (1) | 100% | 0 / 0 | 2 | 0.93 (15 pairs) | pass (0.00 vs 0.10) | 0.131 (0.107 to 0.156) | no |
| L5 | temperature at matched composition | 10 (4) | 10 | 4 (2) | 40% | 6 / 2 | 1 | 0.70 (10 pairs) | fail (0.50 vs 0.43) | -0.218 (-0.847 to 0.619) | no |
| L6 | single-phase range | 21 (2) | 11 | 1 (1) | 9% | 10 / 0 | 0 | - (0 pairs) | pass (0.00 vs 0.10) | 0.196 (0.196 to 0.196) | no |
| L7 | valid Rs readings (audit) | 50 (21) | 50 | 39 (20) | 78% | 11 / 11 | 9 | 0.81 (110 pairs) | pass (0.26 vs 0.32) | 30 (6 to 44) | yes |
| L8 | impossible optical data (audit) | 201 (56) | 201 | 34 (16) | 17% | 167 / 15 | 4 | 0.80 (49 pairs) | fail (0.84 vs 0.41) | 10.5 (2.3 to 37.1) | no |

Effect units: L1 rho ratio (naive pick / key minimum); L2 slope difference (decades per unit fraction); L3 absorptance gap; L4 Å; L5 decades (L - Ln); L6 fraction; L7, L8 count difference.

## Critical items by system

- **L1:** N-Sn-Zn 3, Cu-S-Sn 2, Cu-Sb-Se 1
- **L2:** N-Sn-Zn 4, Cu-S-Sn 2
- **L3:** N-Sn-Zn 6, Cu-Ge-S 1, Ag-O 1, Cu-O-Zn 1, Cu-S-Sn 1
- **L4:** Mn-Se-Te-Zn 6
- **L5:** N-Sn-Zn 3, Cu-S-Sn 1
- **L6:** Mn-Se-Te-Zn 1
- **L7:** N-Sn-Zn 7, Cu-S-Sn 4, Cu-O-Zn 4, Ga-O-Zn 3, S-Sn-Te 2, Ca-S-Sn 2, Mg-O-Zn 2, Cu-Sb-Se 2, Cu-O-Se-Zn 2, Ga-Sn 1, Cu-Ge-S 1, S-Se-Sn 1, Cu-Ge-S-Sn 1, Cu-O 1, Cu-N-O 1, Ga-Mg-O-Zn 1, Ni-O 1, Cu-Ga-In-Se 1, Ba-Cr-O 1, Cu-O-Se 1
- **L8:** Mn-Se-Te-Zn 5, Mn-O-Zn 4, In-O-Sn-Zn 4, Cr-Mn-O 3, N-Sn-Zn 3, Co-Sn-Ta 2, Ga-O-Zn 2, Mg-O-Zn 2, N-Ti 2, Cr-Mg-O 1, Ag-O-V 1, Cr-O-Zn 1, Mn-O 1, Cu-S-Sn 1, Cu-O-Se-Zn 1, Cu-O-Zn 1

## Cheap-rule accuracy over the item mix

- **L1** (control share 0.33): naive Rs argmin 0.33, thickest 0.56, thinnest 0.22, panel centre 0.33, lowest x 0.22, highest x 0.44
- **L2** (control share 0.33): naive slope 0.33, zero 0.44, minus thickness slope 0.33
- **L3** (control share 0.29): naive T argmax 0.29, R argmin 0.36, thinnest 0.29, lowest x 0.36, highest x 0.36, panel centre 0.14
- **L4** (control share 0.00): Vegard 0.00
- **L5** (control share 0.33): naive verdict 0.33, always lower 0.50, always no decided difference 0.33
- **L6** (control share 0.00): no boundary 0.00, midpoint 0.00
- **L7** (control share 0.22): all (naive) 0.22, zero 0.26, all minus 2 0.06
- **L8** (control share 0.31): zero (naive) 0.31, T>1.05 only 0.84, all 0.02

## Losses

- **L1:** not eligible (positions or range) 172, key not decided 29
- **L2:** not eligible (positions or range) 205
- **L3:** not eligible (positions or range) 74, key not decided 93
- **L4:** not eligible (positions or range) 4
- **L5:** not eligible (positions or matched pairs < 5) 427, library cap 2 30
- **L6:** key not decided 10, not eligible (positions or range) 3
- **L7:** not eligible (positions or range) 172
- **L8:** not eligible (positions or range) 21
