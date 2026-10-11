# Stage 2s tuning (V5_SPEC E.3, E.4; X30 to X35, X40, X43, X44)

Truth only, no FM call. Code `mcenv/tune2s.py` (plan costs), `mcenv/survey2s.py` (T4), `mcenv/difficulty2s.py`. Sweeps on host B and node A2
(node B2 unreachable, checked once at 2026-10-11T21:06:17Z) and host A; outputs in `stage2s/tuning_runs/`.

## Starting point
The stage 2r replacement-round tunables (47 N 10, 48 N 80, 49 N 70, 50 N 60; 46 defaults), L 100 nm, bg 20 cps.

## Sweeps and decisions
| run | scenario: N | result | decision |
|---|---|---|---|
| t0 (first search) | 47: 10; 49: 70 | 47: c_dec 54.3 (one 2-degree window); 49: no plan with planning D >= 40 | the pair search only paired singles with D > 0; without m0 a superlattice-only window has D = 0 (scale free), so the search was widened to every pair of windows at the middle width (X40) and rerun |
| t1a, t1b | 47: 10, 48: 80, 46: 1000; 49: 70 | 47 meets T1 to T3 and T2' with B = 66; 48: c_dec 44.1, T2 holds, T2' fails (the survey's own data cut the further plan to 35.9 min); 46: control C1s holds; 49: still no plan at N 70 even at 20 s per step | retune N for 48 and 49/50 (count rate first, E.4) |
| s/f series | 48: 150-400; 49: 250-1500; 50: 250-1500 | stopped: too slow at 5 to 8 processes each (2 to 9 s per two-window evaluation); one stale process (its PID file had been deleted by an rsync --delete of the sweep folder) killed by process group | a lighter minimiser for ranking plans (fast mode: 48 Sobol points, 3 refinements, no polish) with the chosen plan re-evaluated at full precision and its times rescaled exactly (homogeneity) or bisected again; the sync script now excludes the sweep outputs |
| g series (fast) | 48: 200, 400; 49: 400; 50: 400, 1000 | 48 at 200: c_dec 16.5, all constraints with B = 20; 49 at 400: the cheapest decisive plan is the full 10-70 scan (37.7 min) and the placebo plan is the same scan; 50 at 400: a Si-standard window (22.1 min), placebo plan key D 107 on the ordered world; 50 at 1000: the full scan again | 49 and 50 are prior-independent (X43): no count rate makes the cheapest plan depend on the lattice prior, window widths do not touch the full-range scan |
| h series (final, fast search + full-precision final) | 46: 1000 (B 30); 47: 10 (B 66); 48: 200 (B 20); 49: 330; 50: 300 | see DIFFICULTY.md | frozen |

## Final tunables and budgets (frozen at V5-13a)
| scenario | N | B (min) | rule | constraints |
|---|---|---|---|---|
| 46 loud control | 1000 | 30 | max(round(1.25 c_dec), 30) | C1s: the default survey alone gives key D 8743 / 7270 |
| 47 SrOsO3 cubic / Pnma | 10 | 66 | ceil(1.2 x 54.33) | T1, T2, T2', T3 hold (c_loc 155 min: at N 10 a survey localizing the lattice to 1 % costs more than the budget) |
| 48 MnPbO3 + PbO2 / MnO2 | 200 | 20 | ceil(1.2 x 16.51) | T1, T2, T2', T3 hold (no placebo-quality plan within 20 min; after a 12.5-min survey 7.5 min are left, under one overhead) |
| 49 Pb3K order | 330 | 61 | ceil(1.2 x 50.59) | T1, T2 hold; T2', T3 fail: the cheapest decisive plan is the full 10-70 scan (X43) |
| 50 CoMg order | 300 | 29 | ceil(1.2 x 23.71) | T1, T2 hold; T2', T3 fail (X43) |

Window widths stay {2, 4, 6} degrees in every scenario (restricting them cannot touch the full-range scans that make 49 and 50 prior-independent).

## T4 (X44, reported): a lattice-independent survey that spends the whole budget
| scenario | best survey | key D (claim-true, claim-false world) | a truth verdict counts in both worlds? |
|---|---|---|---|
| 47 | 20-80 deg at 0.04 deg, 2.24 s | 15.6, 11.3 | yes |
| 48 | 15-75 deg at 0.04 deg, 0.40 s | 19.4, 12.7 | yes |
| 49, 50 | the decisive plan is itself a survey (49) or affordable after one (50) | - | yes |

In every quiet scenario an agent that spends its budget on one wide scan, refines the lattice from it and reads correctly gets a verdict that counts (9 <= D < 25) without any prior; only a decisive answer (D >= 25 in both worlds) needs the prior in 47 and 48. The ratio of survey to decisive efficiency is set by the scenario, so N cannot change it. The analysis reports decisive pair resolution (both worlds D >= 25 with the truth verdict) beside pair resolution, decided here before any stage 2s model run.

## Scripted planner (before any gate count; V5-E18)
The first ceiling smoke on 47 misread world 464 in 3 of 5 episodes. Fixed before any freeze: size from the better-fitting hypothesis, both targets at the smaller of the two N normalizations, polymorph refinements kept only if consistent within 1 %. Ceiling smoke after the fix: 10/10 on 47. Planner priors (equal to the worlds' design values, arm-neutral): size 100 nm, background 20 cps, neutron background 50 counts per point, pseudo-truths S 0.7 / 0 and 3 wt % impurity.
