# MC v2.2 census (MV1f; HTEM_MC2_RULES_v22.md)

Scope: (d) 346 libraries (MV1d); (e) 556 (F2 fully cached 210). Dev never yields facts. (c) reproduces MV1d byte for byte: **yes**.

**Round (e): GO.** 1 groups >= 2: met; 2 types >= 3: met; 3 critical >= 60: met; 4 test >= 15: met; 5 fresh: met. Built groups: optical, structural; types L3, L8, L4, L6; critical 163, in test 30.

## Side by side: critical items (systems), includable

| Type | (c) v2.1, 346 | (d) v2.2, 346 | (e) v2.2, all | (e) fresh F2 | (e) includable |
|---|---|---|---|---|---|
| L1 | 8 (4) | 5 (2) | 5 (2) | unconfirmed (< 6 fresh items) (0) | no |
| L2 | 9 (4) inc | 5 (2) | 5 (2) | unconfirmed (< 6 fresh items) (0) | no |
| L3 | 16 (7) inc | 16 (7) inc | 24 (11) | pass (12) | yes |
| L4 | 39 (16) inc | 27 (10) | 34 (11) | pass (12) | yes |
| L5 | 5 (3) | 5 (3) | 5 (3) | unconfirmed (< 6 fresh items) (0) | no |
| L6 | 25 (14) inc | 14 (10) | 18 (11) | pass (6) | yes |
| L7 | 73 (33) inc | 34 (19) | 38 (21) | unconfirmed (< 6 fresh items) (4) | no |
| L8 | 44 (21) inc | 44 (21) inc | 87 (40) | pass (57) | yes |
| Round | GO (structural held) | NO-GO | GO | | |

## (e) per type

| Type | Decided | Critical (systems) | N-Sn-Zn share | Naive fails | Controls avail / kept (share) | Critical test / fresh | C2 | C1 | C3/C4 | Effect median (p10-p90) | Losses |
|---|---|---|---|---|---|---|---|---|---|---|---|
| L1 | 22 | 5 (2) | 60% | 23% | 17 / 2 (0.29) | 2 / 0 | 1.00 (7) | pass | fail | 0.312 (0.0877 to 1.46) | not eligible 374, key not decided 75, robustness (grid) 12 |
| L2 | 31 | 5 (2) | 60% | 16% | 26 / 2 (0.29) | 1 / 0 | 0.71 (7) | pass | pass | 3.8 (-3.36 to 9.38) | not eligible 442, robustness (grid) 10 |
| L3 | 137 | 24 (11) | 54% | 18% | 113 / 10 (0.29) | 5 / 8 | 0.88 (96) | pass | pass | 0.0758 (-0.332 to 0.219) | not eligible 133, key not decided 213 |
| L4 | 53 | 34 (11) | 0% | 64% | 19 / 15 (0.31) | 8 / 7 | 0.89 (201) | pass | pass | 0.0565 (0.0304 to 0.102) | not eligible 446 |
| L5 | 16 | 5 (3) | 60% | 31% | 11 / 2 (0.29) | 3 / 0 | 0.67 (6) | pass | fail | 0.418 (-0.462 to 0.633) | not eligible 1293, robustness (grid) 8, library cap 2 155 |
| L6 | 256 | 18 (11) | 0% | 7% | 238 / 8 (0.31) | 3 / 4 | 1.00 (15) | pass | pass | 0.0969 (0.0341 to 0.285) | key not decided 130, not eligible 97 |
| L7 | 59 | 38 (21) | 8% | 64% | 21 / 16 (0.30) | 5 / 4 | 0.41 (88) | pass | pass | 44 (6 to 44) | not eligible 372, robustness (grid) 52 |
| L8 | 434 | 87 (40) | 7% | 20% | 347 / 37 (0.30) | 14 / 43 | 0.75 (214) | pass | pass | 17 (3 to 43) | not eligible 49 |

## (e) cheap rules: k/n, binomial p, cap

- **L1:** highest x 1/7 p=0.967; lowest x 2/7 p=0.822; naive Rs argmin 2/7 p=0.822; panel centre 1/7 p=0.967; thickest 4/7 p=0.263 CAP FAIL; thinnest 1/7 p=0.967
- **L2:** minus thickness slope 2/7 p=0.822; naive slope 2/7 p=0.822; zero 2/7 p=0.822
- **L3:** R argmin 9/34 p=0.960; highest x 9/34 p=0.960; lowest x 9/34 p=0.960; naive T argmax 10/34 p=0.917; panel centre 4/34 p=1.000; thinnest 7/34 p=0.994
- **L4:** Vegard 15/49 p=0.944
- **L5:** always lower 3/7 p=0.549; always no decided difference 4/7 p=0.263 CAP FAIL; naive verdict 2/7 p=0.822
- **L6:** midpoint 1/26 p=1.000; no boundary 8/26 p=0.894
- **L7:** all (naive) 16/54 p=0.952; all minus 2 5/54 p=1.000; zero 26/54 p=0.127
- **L8:** all 11/124 p=1.000; zero (naive) 37/124 p=0.992

L8 depth: deep {'facts': 21, 'critical': 21, 'mix': 21}, shallow {'facts': 413, 'critical': 66, 'mix': 103}; single-constraint baseline (T > 1.05 count) 0.8306451612903226.

## (e) fresh confirmation (F2 only)

| Type | Fresh items | Fresh critical | Status | Worst rule |
|---|---|---|---|---|
| L1 | 0 | 0 | unconfirmed (< 6 fresh items) | - |
| L2 | 0 | 0 | unconfirmed (< 6 fresh items) | - |
| L3 | 12 | 8 | pass | naive T argmax 4/12, p=0.839 |
| L4 | 12 | 7 | pass | Vegard 5/12, p=0.837 |
| L5 | 0 | 0 | unconfirmed (< 6 fresh items) | - |
| L6 | 6 | 4 | pass | no boundary 2/6, p=0.815 |
| L7 | 4 | 4 | unconfirmed (< 6 fresh items) | - |
| L8 | 57 | 43 | pass | zero (naive) 14/57, p=0.961 |

## (e) groups

| Group | Includable | Critical | Systems | In test | Builds |
|---|---|---|---|---|---|
| electrical | - | 0 | 0 | 0 | no |
| optical | L3, L8 | 111 | 43 | 19 | yes |
| structural | L4, L6 | 52 | 19 | 11 | yes |

## (e) intention pairs and probes

- **L2+L7:** 14 libraries carry both (embedded critical 2, audit critical 5)
- **L3+L8:** 62 libraries carry both (embedded critical 24, audit critical 27)
- **L1 probe:** 22 decided libraries (5 critical; naive pick invalid in 4). **L3 trap:** 34 items, naive pick has T > 1.05 in 14.

## (e) critical items by system

- **L1:** N-Sn-Zn 3, Cu-S-Sn 2
- **L2:** N-Sn-Zn 3, Cu-S-Sn 2
- **L3:** N-Sn-Zn 13, Ba-Co-Fe-Y-Zr 2, Cu-Ge-S 1, Sn-Zn 1, Co-Ni-O 1, Ag-O 1, In-Mn-O 1, Cu-O-Zn 1, Cu-S-Sr 1, In-S 1, Cu-S-Sn 1
- **L4:** Co-Sn-Ta 6, S-Sn-Te 5, Mn-Se-Te 5, Mn-Se-Te-Zn 4, Mn-O-Zn 4, Cr-Mg-Mn-O 3, Co-Ni-O-Zn 2, Cr-Mg-Mn-N-O 2, Co-O-Zn 1, S-Se-Sn 1, Ba-Co-Fe-Y-Zr 1
- **L5:** N-Sn-Zn 3, N-Sb-Zn 1, Cu-S-Sn 1
- **L6:** Cu-In-S 3, Cu-S-Sb 3, Cu-Ge-S 2, Co-Ni-O-Zn 2, Mn-Se-Te-Zn 2, Cu-O-Zn 1, Co-Sb-Ti 1, Co-Sn-Ta 1, Co-Ni-O 1, Ni-O-Zn 1, Cu-S-Sn 1
- **L7:** Cu-O-Zn 8, N-Sn-Zn 3, Ga-O-Zn 3, Cu-O-Se 3, Cu-O-Se-Zn 3, Cu-S-Sn 2, Cu-N-O 2, Mo-N-Zn 1, Mo-N-W-Zn 1, Ge-N-Zn 1, N-Sb-Zn 1, S-Se-Sn 1, Co-Sn-Ta 1, Cu-Ge-S-Sn 1, Cu-O 1, Ga-Mg-O-Zn 1, Ga-Sn 1, Ba-Cr-O 1, S-Sn-Te 1, In-S 1, Cu-Ga-In-Se 1
- **L8:** Ga-O-Zn 7, In-O-Sn-Zn 6, N-Sn-Zn 6, Mn-Se-Te-Zn 5, Mn-O-Sn 5, Mn-O-Zn 4, Cr-Mn-O 4, Sn-Zn 3, Fe-In-O 3, H-In-Mn-O 3, Cu-O-Zn 3, Ba-Co-Fe-Y-Zr 2, Co-Sn-Ta 2, Cu-S-Sb 2, O-Sn-Ti-Zn 2, H-O-Ti-Zn 2, Cu-N-Ta 2, Mg-O-Zn 2, Ba-Cr-O 2, N-Ti 2, Co-Ni-O-Zn 1, Ba-Co-Fe-O-Zr 1, O-Ti-Zn 1, Cr-Mg-O 1, N-Sb 1, Ga-H-O-Zn 1, Ag-O-V 1, Cr-O-Zn 1, Mn-O 1, H-Mn-O-Sn 1, In-Mn-O 1, N-Ta 1, Cr-Cu 1, Cu-In-S 1, Ba-Fe-O-Y-Zr 1, Cu-S-Sr 1, In-S 1, Cu-S-Sn 1, Sn-Ti-Zn 1, Cu-O-Se-Zn 1
