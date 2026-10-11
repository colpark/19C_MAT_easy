# Stage 2r gate (V5-10), round 1

Pairs resolved out of k (k = 1..5), wrong conclusions in brackets, mean instrument cost. Planner: V5_SPEC D.6 (build, relax with the arm's relax, refine lattice_scale on m0 within +-5 %, cheapest grid plan with D >= 40 both ways by mcenv/separation.py, likelihood-ratio reading).

| scenario | placebo | fm | ceiling | FM beats placebo |
|---|---|---|---|---|
| 41 polymorph (loud control) | 0/5 (5) 5 min | 5/5 (0) 5 min | 5/5 (0) 5 min | yes (control, not gated) |
| 42 polymorph (quiet) | 0/5 (5) 120 min | 0/5 (5) 18 min | 5/5 (0) 120 min | no |
| 43 trace phase | 0/5 (6) 120 min | 0/5 (5) 120 min | 5/5 (0) 120 min | no |
| 44 L1_2 order | 0/5 (10) 111 min | 5/5 (0) 111 min | 5/5 (0) 111 min | yes |
| 45 B2 order | 5/5 (0) 38 min | 5/5 (0) 72 min | 5/5 (0) 72 min | no |

**Ceiling precondition (5/5 on every scenario): met.**
**Gate (FM beats placebo on every quiet scenario, precondition met): FAIL.**

## Plans chosen by the planner

- 41|ceiling: standard 19.71-21.71 deg, step 0.04, 0.5 s (planner D 7572.2; refined: {"perovskite_cubic": {"ls": 1.0, "chi2": 1718.562915573416}, "ilmenite": {"ls": 0.9558257156655915, "chi2": 10596.323588438932}, "L_fit": 102.13942913578357, "L_used": 100.0})
- 41|fm: standard 19.71-21.71 deg, step 0.04, 0.5 s (planner D 7516.4; refined: {"perovskite_cubic": {"ls": 0.9990423421487967, "chi2": 1718.6007618518056}, "ilmenite": {"ls": 0.9576393510071617, "chi2": 10585.879139723202}, "L_fit": 102.13691328503486, "L_used": 100.0})
- 41|placebo: standard 12.75-14.75 deg, step 0.04, 0.5 s (planner D 4158.3; refined: {"perovskite_cubic": {"ls": 1.0, "chi2": 10688.998607655718}, "ilmenite": {"ls": 1.0, "chi2": 10688.726997715024}, "L_fit": 999.9999999999998, "L_used": 100.0})
- 42|ceiling: neutron (planner D 39265.1; refined: {"perovskite_R3c": {"ls": 1.0, "chi2": 1644.3654259047746}, "perovskite_Pnma": {"ls": 1.0, "chi2": 1642.84620293753}, "L_fit": 999.9999999999998, "L_used": 100.0})
- 42|fm: standard 29.32-33.32 deg, step 0.01, 2.0 s (planner D 48.3; refined: {"perovskite_R3c": {"ls": 1.0, "chi2": 1644.7870131504365}, "perovskite_Pnma": {"ls": 1.0, "chi2": 1647.5490050229228}, "L_fit": 48.34152218084709, "L_used": 100.0})
- 42|placebo: neutron (planner D 34688.3; refined: {"perovskite_R3c": {"ls": 1.0, "chi2": 1646.2110055847202}, "perovskite_Pnma": {"ls": 1.0, "chi2": 1644.6512451215303}, "L_fit": 999.9999999999998, "L_used": 100.0})
- 43|ceiling: neutron (planner D 624.7; refined: {"main": {"ls": 1.0, "chi2": 1793.6084892699405}, "L_fit": 80.1955301697374, "L_used": 100.0})
- 43|fm: neutron (planner D 131.6; refined: {"main": {"ls": 1.0, "chi2": 1952.7634866225694}, "L_fit": 999.9999999999998, "L_used": 100.0})
- 43|placebo: neutron (planner D 400.9; refined: {"main": {"ls": 1.0, "chi2": 1949.2782625849168}, "L_fit": 999.9999999999998, "L_used": 100.0})
- 44|ceiling: standard 16.50-18.50 deg, step 0.01, 20.0 s; standard 16.50-18.50 deg, step 0.02, 20.0 s (planner D 46.5; refined: {"ord": {"ls": 1.0, "chi2": 1616.0228760318837}, "L_fit": 87.98422701835233, "L_used": 100.0})
- 44|fm: standard 16.50-18.50 deg, step 0.01, 20.0 s; standard 16.50-18.50 deg, step 0.02, 20.0 s (planner D 45.8; refined: {"ord": {"ls": 0.9913441858547819, "chi2": 1615.8790603337666}, "L_fit": 87.7865645524667, "L_used": 100.0})
- 44|placebo: standard 15.07-17.07 deg, step 0.01, 20.0 s; standard 15.07-17.07 deg, step 0.02, 20.0 s (planner D 43.6; refined: {"ord": {"ls": 1.0, "chi2": 2102.190741887128}, "L_fit": 25.283619447816818, "L_used": 100.0})
- 45|ceiling: standard 27.44-29.44 deg, step 0.01, 20.0 s (planner D 46.4; refined: {"ord": {"ls": 1.0, "chi2": 1775.5186837096521}, "L_fit": 108.84847238252466, "L_used": 100.0})
- 45|fm: standard 27.43-29.43 deg, step 0.01, 20.0 s (planner D 42.1; refined: {"ord": {"ls": 1.0048497454045169, "chi2": 1773.2429176796004}, "L_fit": 109.37815767174514, "L_used": 100.0})
- 45|placebo: standard 27.25-29.25 deg, step 0.01, 10.0 s (planner D 50.7; refined: {"ord": {"ls": 0.95, "chi2": 3671.6879423318155}, "L_fit": 19.999999999999996, "L_used": 20.0})
