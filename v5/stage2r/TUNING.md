# Stage 2r tuning and selection log (V5_SPEC Appendix D; truth only, no FM call except D.4's orientation)

Candidates come from `stage2r/select.py` (rule v2 + r2, sha256 order; `stage2r/SELECTION.json`). Each row is one `python -m mcenv.tune2r`
report on node A2 or host A (`stage2r/tuning_runs/<tag>-<i>.json/.log`, index files list pick and settings; `summ.py` prints them).
Constraints are v5 section 3: C1 for 41; C2a (D(m0) < 9), C2b (cheapest decisive grid plan <= 90 min), C2c for 42 to 45; r3 and r4 of D.3.
The v5 plan grid is used (times 0.5, 2, 5, 10, 20 s).

| tag | scenario | candidate | settings | finding | decision |
|---|---|---|---|---|---|
| r0 | 41 | SrPbO3 cubic perovskite / ilmenite (wbm-1-39816, wbm-2-34330) | defaults | D(m0) 8742 / 7267 (loud) | **defaults** |
| r0, r42, screen42 | 42 | candidates 0 to 24 in hash order | N bisected so the louder twin has D(m0) = 6, pairs | candidate 0 CsInBr3 (Pnma / R3c): D(m0) 18.7 at N = 3 (r3 fails). Candidates 1 to 18: every pair is decided by a superlattice window inside 10-70 deg with standard optics (8 to 22 min), so strict r4 fails for all; candidate 8 BaHfO3 (Pnma / cubic) has its cheapest plan at 137 deg but its cubic twin is undecidable within budget at N 3000 | see the 42 decision below |
| r0, r43 | 43 | KVO3 (Pnma) + VO2 fluorite / VO2 rutile at 3 wt % | N 1000, 30, 100 | N 1000: D(m0) 282 / 311; N 30: D(m0) 0.78 / 0.62, cheapest 38.5 / 72 min (window 31.6 deg) | **N 30** |
| r0, r44 | 44 | Pb3K (wbm-1-23032), twins S 1 / 0 | N 30, 100, 300 | N 30: ordered twin D(m0) 8.3 while the disordered twin's best affordable D is 21.5: no N meets C2 with S = 1 | **twins S 0.7 / 0 (X21)** |
| r44b, r44c | 44 | Pb3K, S 0.7 / 0 | N 55, 62, 70, 100, 200 | N 62: disordered twin best 24.6; N 70: D(m0) 0.56 / 8.52, cheapest 72 / 8.4 min; N 100: D(m0) 15.9 | **N 70** (thin margins: D(m0) 8.52, best 31.1; disclosed) |
| r0, r45b | 45 | FeSc B2 (wbm-1-51682), S 0.7 / 0 | N 200, 400, 800 | N 200: disordered twin best 7.3; N 400: D(m0) 3.5 / 0.23, cheapest 8.4 / 72 min; N 800: D(m0) 11.6 | **N 500** (checked in the final constraint run) |

## Energy orientation (D.4, X19), MACE-MP-0 via the FM service, `stage2r/ORIENT.json`
- 41 SrPbO3: cubic perovskite -5.6572 eV/atom, ilmenite -5.7762 eV/atom (both converged). MACE ranks ilmenite lower, so the claim reads "cubic perovskite rather than ilmenite" and the claim-false twin (ilmenite) is the lower-energy structure.
- 44 Pb3K: L1_2 ordered -3.1164 eV/atom (19 steps), 2x2x2 fcc random cell (24 Pb + 8 K, seed 0) -3.1672 eV/atom (111 steps; the cell relaxed far from cubic, a, b, c = 9.17, 11.86, 11.44 A). MACE ranks the disordered cell lower, so the claim reads "has L1_2 order" and the claim-false twin (S = 0) is the lower-energy state. The distorted random cell is a caveat on what "disordered" means to MACE here.
