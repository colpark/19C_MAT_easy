# Stage 1b tuning log (V5_SPEC Appendix C; before V5-8, no model has seen a stage 1b world)

Post hoc (X16): retuned after seeing the v5 stage 1 results. Knobs: count rate N (X-ray) and Nn (neutron), crystallite size L and
background bg, and, where the twins sit at unequal distances from the threshold, the far twin's margin (C.2, X24). Each row is one
`python -m mcenv.tune1b` report (no pairs unless marked; `stage1b/tuning_runs/<tag>.json` and `.log`, index files list the settings;
`tuning_runs/summ.py` prints them). Sweeps ran on host B, node A2 and host A with BLAS pinned to one thread per worker. Node B2 was
unreachable (STATUS.md, 2026-10-11 12:09Z). The time grid is the refined one of C.3. Costs in minutes; "cheapest" is the cheapest grid
plan with D >= 25; C2e is the best affordable plan inside 10-70 deg with standard optics and no standard.

## Sweeps

| tag | scenario | settings | finding | decision |
|---|---|---|---|---|
| sw0 | 23-30 | v5 tunables | cheapest 25 (23), 7.5-30 (24), 5.4 (25), 120 neutron (26), 72/38.5 (27), 8.4/72 (28), 8.4-10 (30); C2e 35-50 (23), 28-258 (25) | every quiet scenario except 26 too cheap |
| s23, s23b | 23 | N 10-35, L 30/60, Nn 1000 | X-ray loses to the neutron pattern (Nn 1000 decides at 120 min); N 25 L 60: X-ray 72 min but C2e 11-16 | lower Nn; X-ray ratio high angle / default range too small |
| s23c, s23d, s23e | 23 | L 40-200, bg 2-20, N 8-45, Nn 100 | L >= 100 moves the cheapest window to (200) at 44 deg (inside 10-70); bg 2 worsens the ratio; L 40-50 leaves the tetragonal twin undecidable by X-ray while C2e is near 9 | **no N, L, bg meets C2b' and C2e with the X-ray route (X22)** |
| s23f, c1_23, c2_23 | 23 | L 60, Nn 400-500, N 16 then 13 | with pairs, C2e of the cubic twin is 11.1 at N 16; N 13: C2e 4.8 / 7.7 / 4.8, X-ray best 9.2-13.6 (< 25), neutron D 56 / 36 / 56 at 120 min | **N 13, L 60, bg 20, Nn 500: decisive route = neutron (X22)** |
| s24, c1_24, c5_24 | 24 | margin 1 % -> 0.6 % rutile in the claim-false twin; N 300-500 | v5 asymmetry 21.8 vs 8.4 min removed by 0.6 %; N 400 no plan; N 500 55 / 72; N 450 (pairs) 72 / 94; N 420 (pairs) 93.7 / 94.0 | **N 420, claim-false twin 0.6 % rutile (X24)** |
| s25b, s25c, c1_25, c2_25 | 25 | N 1-8, bg 2/20, Nn 100 | bg 20 makes D roughly quadratic in N; N 2.2 (pairs) 83.8 / 110.7; N 2.0 (pairs) 93.7 / 120 (neutron) | **N 2.0, L 30, bg 20, Nn 100 (X25)** |
| sw0, c1_26 | 26 | v5 tunables | neutron only, 120 min in every world; X-ray best 0.8; hold (size halved) neutron D 120 | **v5 tunables** |
| s27, c1_27 | 27 | margin +0.12 % -> +0.06 %; N 8-20 | N 16: C2e 8.6; N 20: C2e 11.5. N 14 (pairs): C2e 7.15, obvious route (Si standard, 10-70 deg) D 11.6 at the budget, high-resolution route 11.7 min | **N 14, larger-lattice world +0.06 % (X24); C7b infeasible with C2e (X23)** |
| s28, s28b, s28d, c1_28, c3_28, c4_28 | 28 | margin S 0.7 -> 0.43 in the claim-true twin; N 70-100, Nn 300 | S 0.43 equalises the twins (D 22.36 / 22.26 at N 90); D(N) is steep (best 23.8 at N 93, 25.7 at N 97 without pairs); N 100: 72 / 72 (too cheap); N 97 and 98 (pairs): 93.7 / 93.7 | **N 97, Nn 300, claim-true S 0.43 (X24, X25)** |
| s30, s30b, c1_30 | 30 | N 10-40, Nn 30 | Nn 1000 lets the neutron decide at 120; N 15 104-139; N 15.5 (pairs) 110.5 / 93.8 | **N 15.5, Nn 30 (X25)** |

## Hold worlds (C.5): every nuisance evaluated on the claim-true twin (with pairs)

| scenario | twin cheapest | displacement | zero | size | background | preferred | taken |
|---|---|---|---|---|---|---|---|
| 23 (c2_23, c1_23) | 120 (neutron) | 120 | 120 | none (X-ray and neutron below 25) | 120 | displacement | **displacement** |
| 24 (c5_24) | 93.7 | 93.7 | 93.7 | none | none | background | **displacement** (size and background break rule H) |
| 25 (c1_25, c2_25) | 93.7 | 93.7 | 83.8 | 120 (neutron) | 120 (neutron) | displacement | **displacement** |
| 26 (c1_26) | 120 | 120 | 120 | 120 | 120 | size | **size** |
| 28 (c7_28 at N 97; c1_28 at N 100) | 93.7 | 93.7 | 93.7 | 144 | none | size | **displacement** (size and background break rule H) |
| 29 | none (CANNOT_TELL) | - | - | - | none | background | **background** |
| 30 (c1_30) | 110.5 | 110.5 | - | - | - | displacement | **displacement** |
| 27 | keeps v5's displaced world (absolute s = +0.15 mm) | | | | | | |

The final values are in `mcenv/stage1b.py` (TUNE1B, MARGIN, HOLD) and checked by `mcenv/oracle1b.py` (stage1b/validation/CONSTRAINTS.md).

Note: the hold evaluations above ran before V5-E14 (the plan grid's windows then included the hold world's difference); the final oracle run after the fix (stage1b/validation/CONSTRAINTS.md, rule H) verifies the nuisance taken in every scenario.
