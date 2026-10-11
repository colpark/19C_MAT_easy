# FM check on the selected stage 2 structures (2026-10-11, after selection rule v2, before the gate)

Lattice parameter a of the agent-buildable hypothesis after relax, against the WBM DFT truth (conventional cell). Placebo = the
volume-table rule (B.3); FM = MACE-MP-0 medium (FIRE, FrechetCellFilter, FixSymmetry, fmax 0.02).

| structure | truth a (A) | placebo a | placebo error | FM a | FM error |
|---|---|---|---|---|---|
| NiSeO3 cubic perovskite | 3.7566 | 4.9959 | +33.0 % | 3.8131 | +1.50 % |
| NiO2 rutile | 4.4121 | 5.9540 | +34.9 % | 4.6630 | +5.69 % |
| AgRh B2 | 3.1866 | 3.1347 | -1.63 % | 3.1685 | -0.57 % |
| AgRu B2 | 3.1637 | 3.1285 | -1.11 % | 3.1699 | +0.20 % |
| Ru3Ni L1_2 | 3.7604 | 3.7239 | -0.97 % | 3.7540 | -0.17 % |

- AgRh/AgRu lattice mismatch: truth 0.72 %, FM -0.04 %, placebo 0.20 %.
- Gate planner test (k = 1, S2-C and S2-D, FM and placebo arms): no plan reaches D >= 25 between the planner's own hypotheses in any of the four cases (the FM hypotheses fall outside the frozen +-1 % trust region for the oxides, and the FM end members predict no alloy splitting).
