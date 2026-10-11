# Stage 2r gate (V5-10), replacement round (round 2, final)

Pairs resolved out of k (k = 1..5), wrong conclusions in brackets, mean instrument cost. Planner: V5_SPEC D.6 (build, relax with the arm's relax, refine lattice_scale on m0 within +-5 %, cheapest grid plan with D >= 40 both ways by mcenv/separation.py, likelihood-ratio reading).

| scenario | placebo | fm | ceiling | FM beats placebo |
|---|---|---|---|---|
| 41 polymorph (loud control) | 0/5 (5) 5 min | 5/5 (0) 5 min | 5/5 (0) 5 min | yes (control, not gated) |
| 42 polymorph (quiet) | 4/5 (1) 120 min | 5/5 (0) 120 min | 5/5 (0) 50 min | yes |
| 43 trace phase | 0/5 (10) 35 min | 5/5 (0) 30 min | 5/5 (0) 30 min | yes |
| 44 L1_2 order | 0/5 (10) 111 min | 5/5 (0) 111 min | 5/5 (0) 111 min | yes |
| 45 B2 order | 0/5 (10) 90 min | 5/5 (0) 72 min | 5/5 (0) 72 min | yes |

**Ceiling precondition (5/5 on every scenario): met.**
**Gate (FM beats placebo on every quiet scenario, precondition met): PASS.**

## Plans chosen by the planner

- 41|ceiling: standard 19.71-21.71 deg, step 0.04, 0.5 s (planner D 7572.2; refined: {"perovskite_cubic": {"ls": 1.0, "chi2": 1718.562915573416}, "ilmenite": {"ls": 0.9558257156655915, "chi2": 10596.323588438932}, "L_fit": 102.13942913578357, "L_used": 100.0})
- 41|fm: standard 19.71-21.71 deg, step 0.04, 0.5 s (planner D 7516.1; refined: {"perovskite_cubic": {"ls": 0.9990427167906452, "chi2": 1718.5981406410192}, "ilmenite": {"ls": 0.9576393512754755, "chi2": 10585.879139715253}, "L_fit": 102.13749685862184, "L_used": 100.0})
- 41|placebo: standard 12.75-14.75 deg, step 0.04, 0.5 s (planner D 4158.3; refined: {"perovskite_cubic": {"ls": 1.0, "chi2": 10688.998607655718}, "ilmenite": {"ls": 1.0, "chi2": 10688.726997715024}, "L_fit": 999.9999999999998, "L_used": 100.0})
- 42|ceiling: standard 55.57-57.57 deg, step 0.01, 10.0 s; standard 55.57-57.57 deg, step 0.01, 2.0 s (planner D 42.0; refined: {"perovskite_cubic": {"ls": 1.0, "chi2": 1638.5447861184373}, "perovskite_Pnma": {"ls": 1.0, "chi2": 1644.7356166366353}, "L_fit": 72.25750704653173, "L_used": 100.0})
- 42|fm: neutron (planner D 20156.5; refined: {"perovskite_cubic": {"ls": 1.0, "chi2": 1637.8779462457874}, "perovskite_Pnma": {"ls": 1.0, "chi2": 1645.7592783264768}, "L_fit": 61.22545472767296, "L_used": 100.0})
- 42|placebo: neutron (planner D 32647.1; refined: {"perovskite_cubic": {"ls": 1.0, "chi2": 1664.3272347292223}, "perovskite_Pnma": {"ls": 1.0, "chi2": 1664.1044226029194}, "L_fit": 999.9999999999998, "L_used": 100.0})
- 43|ceiling: standard 23.77-25.77 deg, step 0.01, 5.0 s; standard 23.77-25.77 deg, step 0.02, 2.0 s (planner D 40.9; refined: {"main": {"ls": 1.0, "chi2": 1783.1583034727762}, "L_fit": 83.38365077313479, "L_used": 100.0})
- 43|fm: standard 24.00-26.00 deg, step 0.01, 5.0 s; standard 24.00-26.00 deg, step 0.02, 2.0 s (planner D 43.0; refined: {"main": {"ls": 1.0, "chi2": 2101.3433309229226}, "L_fit": 34.476502589383685, "L_used": 34.476502589383685})
- 43|placebo: standard 18.39-20.39 deg, step 0.01, 5.0 s; standard 18.39-20.39 deg, step 0.02, 5.0 s (planner D 41.6; refined: {"main": {"ls": 1.0, "chi2": 2527.4189624472097}, "L_fit": 999.9999999999998, "L_used": 100.0})
- 44|ceiling: standard 16.50-18.50 deg, step 0.01, 20.0 s; standard 16.50-18.50 deg, step 0.02, 20.0 s (planner D 46.5; refined: {"ord": {"ls": 1.0, "chi2": 1616.0228760318837}, "L_fit": 87.98422701835233, "L_used": 100.0})
- 44|fm: standard 16.50-18.50 deg, step 0.01, 20.0 s; standard 16.50-18.50 deg, step 0.02, 20.0 s (planner D 45.8; refined: {"ord": {"ls": 0.9913442241935286, "chi2": 1615.8790582898462}, "L_fit": 87.78689479807502, "L_used": 100.0})
- 44|placebo: standard 15.07-17.07 deg, step 0.01, 20.0 s; standard 15.07-17.07 deg, step 0.02, 20.0 s (planner D 43.6; refined: {"ord": {"ls": 1.0, "chi2": 2102.190741887128}, "L_fit": 25.283619447816818, "L_used": 100.0})
- 45|ceiling: standard 28.40-30.40 deg, step 0.01, 20.0 s (planner D 42.5; refined: {"ord": {"ls": 1.0, "chi2": 1765.933652848367}, "L_fit": 74.24812831888943, "L_used": 100.0})
- 45|fm: standard 28.36-30.36 deg, step 0.01, 20.0 s (planner D 40.4; refined: {"ord": {"ls": 1.0, "chi2": 1779.285398631466}, "L_fit": 65.9599740440053, "L_used": 100.0})
- 45|placebo: standard 26.42-28.42 deg, step 0.01, 20.0 s; standard 25.42-29.42 deg, step 0.01, 2.0 s (planner D 41.6; refined: {"ord": {"ls": 1.0, "chi2": 1947.8364316896163}, "L_fit": 999.9999999999998, "L_used": 100.0})
