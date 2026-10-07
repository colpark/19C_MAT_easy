# RECONCILE_liion (C2)

Card: CARD_liion.json (C1). Deposit: xm-46 (fpmd_structures, fpmd_trajectories, fpmd_screening_Li7NbO6). Our counts never edit the card (I7). Paper tables are level A (author outputs) and serve as targets only.

## Stage counts

| Stage | Stated | Ours | Class |
|---|---|---|---|
| S0-S5 sources to distance | 30,229 / 22,842 / 12,198 / 5,239 / 1,550 / 1,499 | not recountable | missing records (input CIFs not deposited; ICSD/MPDS licensed) |
| S6 electronic (> 1 eV) | 982 | 55/55 deposited cells electronic_insulator True | missing records (rejects not deposited) |
| S7 pinball self-consistency | 914 | 55/55 pinball_parameters_converged True | missing records |
| S7d drift | 851 | not recountable | missing records |
| S8 pinball sigma >= 1 mS/cm | 132 | 55/55 ionic_conductor True | missing records; paper inconsistency PI3 (Fig. 5 sums) |
| S9 novelty (exclude known) | 55 | 55 deposited unit cells (52 reduced formulas) | reconciles (55); KNOWN_77 list gap 6 (B2) |
| S10 FPMD 1000 K no diffusion | 18 (Table 1) | 1000 K runs deposited for 29 materials, all diffusive by the frozen reading; 17 Table 1 materials deposited only at ~600 K, 5 without any trajectory | missing records + deposit/paper inconsistency (VC-E18) |
| S11 ladder | 34 (9 + 25) | 29 materials with a 1000 K run and >= 1 lower temperature | see per-class table |
| S12 classes | 18 / 25 / 9 (52 of 55) | table membership by reduced formula: {'no_diffusion': 18, 'fast': 11, 'high_T_only': 26} | rule gap (no criterion); PI1 (52 of 55) |

## ionic_conductor_1000K extras (deposited flag) by paper class

| paper class (A) | flag True | flag False | flag missing |
|---|---|---|---|
| fast | 10 | 1 | 0 |
| high_T_only | 20 | 6 | 0 |
| no_diffusion | 9 | 9 | 0 |

Reading: the flag is not documented; it is reported, never keyed.

## Unit cells without trajectories or only at ~600 K

- no trajectory: Ba4LiGa5Se12, Li4CO4, Li4CO4, LiBeP, RbLi6BiO6
- only ~600 K (SIRIUS runs): CsLi2Cl3, KLiSe, Li2Ca2Ta3O10, Li2CdSnSe4, Li2HgO2, Li2P2PdO7, Li2Te2O5, Li5SiP3, Li7Te3O9F, LiAlS2, LiAuF6, LiInSe2, LiLuS2, LiYS2, LiZrS2, Na3Li3Ga2F12, Na3Li3Rh2F12
- formulas with several cells (polymorphs): Li4CO4, LiBeP

## Second route: D (ours, msd.py C2proc) against references at the same material and temperature

- pairs: 44; median log10(ours/ref) = -0.039; robust SD = 0.148 dex
- frozen tau_D = 0.295 dex (rule in the module docstring); keyable D (resolved and agreeing): 6 of 154 runs

| material | T (K) | D ours | D_se/D | reference route | D ref | log10 ratio | agree |
|---|---|---|---|---|---|---|---|
| Cs2Li3Br5 | 1000 | 6.74e-05 | 0.22 | printed_table3_sigma_fpmd_1000 (A) | 5.68e-05 | +0.07 | yes |
| Cs2Li3Br5 | 750 | 2.30e-05 | 0.26 | printed_table3_sigma_fpmd_750 (A) | 1.81e-05 | +0.11 | yes |
| Cs2Li3I5 | 1000 | 8.00e-05 | 0.17 | printed_table3_sigma_fpmd_1000 (A) | 9.43e-05 | -0.07 | yes |
| Cs2Li3I5 | 750 | 3.13e-05 | 0.23 | printed_table3_sigma_fpmd_750 (A) | 3.52e-05 | -0.05 | yes |
| Cs2Li3I5 | 500 | 3.76e-06 | 0.22 | printed_table3_sigma_fpmd_500 (A) | 6.83e-06 | -0.26 | yes |
| Cs2LiI3 | 1000 | 4.17e-05 | 0.24 | printed_table2_sigma_fpmd_1000 (A) | 4.93e-05 | -0.07 | yes |
| Cs3Li2Br5 | 1000 | 3.41e-05 | 0.18 | printed_table2_sigma_fpmd_1000 (A) | 6.51e-05 | -0.28 | yes |
| Cs3LiCl4 | 1000 | 5.03e-05 | 0.22 | printed_table3_sigma_fpmd_1000 (A) | 4.92e-05 | +0.01 | yes |
| Cs3LiCl4 | 750 | 1.05e-05 | 0.30 | printed_table3_sigma_fpmd_750 (A) | 1.46e-05 | -0.14 | yes |
| Cs3LiCl4 | 500 | 3.22e-06 | 0.24 | printed_table3_sigma_fpmd_500 (A) | 3.04e-06 | +0.03 | yes |
| CsLi3Br4 | 1000 | 7.62e-05 | 0.11 | printed_table3_sigma_fpmd_1000 (A) | 7.68e-05 | -0.00 | yes |
| CsLi3Br4 | 750 | 3.36e-05 | 0.11 | printed_table3_sigma_fpmd_750 (A) | 3.69e-05 | -0.04 | yes |
| CsLi3Br4 | 500 | 5.52e-06 | 0.24 | printed_table3_sigma_fpmd_500 (A) | 1.08e-05 | -0.29 | yes |
| CsLiI2 | 1000 | 5.29e-05 | 0.15 | printed_table3_sigma_fpmd_1000 (A) | 7.32e-05 | -0.14 | yes |
| CsLiI2 | 750 | 3.77e-05 | 0.19 | printed_table3_sigma_fpmd_750 (A) | 2.68e-05 | +0.15 | yes |
| CsLiI2 | 500 | 7.73e-06 | 0.13 | printed_table3_sigma_fpmd_500 (A) | 1.07e-05 | -0.14 | yes |
| Li10B14Cl2O25 | 1000 | 1.43e-06 | 0.45 | printed_table2_sigma_fpmd_1000 (A) | 1.56e-06 | -0.04 | yes |
| Li10BrN3 | 1000 | 9.49e-06 | 0.13 | printed_table2_sigma_fpmd_1000 (A) | 8.77e-06 | +0.03 | yes |
| Li10Si2PbO10 | 1000 | 3.42e-06 | 0.24 | printed_table2_sigma_fpmd_1000 (A) | 4.24e-06 | -0.09 | yes |
| Li2B2Se5 | 1000 | 1.30e-06 | 0.56 | printed_table2_sigma_fpmd_1000 (A) | 8.84e-07 | +0.17 | yes |
| Li2B3PO8 | 1000 | 3.67e-07 | 1.03 | printed_table2_sigma_fpmd_1000 (A) | 1.65e-06 | -0.65 | no |
| Li2BeF4 | 1000 | 3.97e-05 | 0.12 | printed_table2_sigma_fpmd_1000 (A) | 3.58e-05 | +0.04 | yes |
| Li2P2PdO7 | 600 | 1.06e-06 | 0.41 | printed_table2_sigma_fpmd_1000 (A) | 1.06e-06 | -0.00 | yes |
| Li2ZnBr4 | 1000 | 1.57e-05 | 0.38 | printed_table2_sigma_fpmd_1000 (A) | 1.67e-05 | -0.03 | yes |
| Li2ZnGeSe4 | 1000 | 1.66e-05 | 0.22 | printed_table2_sigma_fpmd_1000 (A) | 1.45e-05 | +0.06 | yes |
| Li3AuS2 | 1000 | 2.69e-07 | 0.45 | printed_table2_sigma_fpmd_1000 (A) | 1.47e-07 | +0.26 | yes |
| Li4CO4 | 1000 | 1.21e-05 | 0.21 | printed_table3_sigma_fpmd_1000 (A) | 8.09e-06 | +0.18 | yes |
| Li4CO4 | 750 | 4.01e-06 | 0.45 | printed_table3_sigma_fpmd_750 (A) | 4.60e-06 | -0.06 | yes |
| Li4CO4 | 500 | 8.86e-07 | 0.48 | printed_table3_sigma_fpmd_500 (A) | 1.31e-06 | -0.17 | yes |
| Li5Br2N | 1000 | 1.43e-06 | 0.40 | printed_table2_sigma_fpmd_1000 (A) | 5.15e-06 | -0.56 | no |
| Li7NbO6 | 1000 | 4.32e-06 | 0.16 | samos_deposited (S) | 4.38e-06 | -0.01 | yes |
| Li7NbO6 | 750 | 1.42e-06 | 0.17 | samos_deposited (S) | 1.49e-06 | -0.02 | yes |
| Li7NbO6 | 600 | 2.09e-07 | 0.48 | samos_deposited (S) | 1.65e-07 | +0.10 | yes |
| Li7NbO6 | 500 | 9.75e-08 | 0.82 | printed_table3_sigma_fpmd_500 (A) | 3.77e-07 | -0.59 | no |
| Li8Bi2(MoO4)7 | 1000 | 4.19e-07 | 0.86 | printed_table2_sigma_fpmd_1000 (A) | 4.76e-07 | -0.06 | yes |
| Li8SeN2 | 1000 | 1.20e-06 | 0.29 | printed_table2_sigma_fpmd_1000 (A) | 4.91e-06 | -0.61 | no |
| Li8TeN2 | 1000 | 3.25e-07 | 0.96 | printed_table2_sigma_fpmd_1000 (A) | 4.02e-06 | -1.09 | no |
| LiBeP | 1000 | 5.44e-06 | 0.21 | printed_table2_sigma_fpmd_1000 (A) | 7.45e-06 | -0.14 | yes |
| LiCS(OF)3 | 1000 | 2.23e-05 | 0.22 | printed_table2_sigma_fpmd_1000 (A) | 2.51e-05 | -0.05 | yes |
| LiGaSe2 | 1000 | 5.76e-06 | 0.66 | printed_table2_sigma_fpmd_1000 (A) | 8.55e-06 | -0.17 | yes |
| LiMoPO6 | 1000 | 9.84e-06 | 0.41 | printed_table2_sigma_fpmd_1000 (A) | 8.39e-06 | +0.07 | yes |
| LiP7 | 1000 | 2.02e-05 | 0.45 | printed_table2_sigma_fpmd_1000 (A) | 1.18e-05 | +0.23 | yes |
| LiY(MoO4)2 | 1000 | 5.32e-06 | 0.51 | printed_table2_sigma_fpmd_1000 (A) | 5.71e-06 | -0.03 | yes |
| Sr2LiBr5 | 1000 | 3.75e-05 | 0.25 | printed_table2_sigma_fpmd_1000 (A) | 3.63e-05 | +0.01 | yes |

## Arrhenius barrier: ours (>= 3 temperatures with D > 0, inverse-variance weighted) against printed (Table 3, A)

| material | temperatures | Ea ours (eV) | sd | Ea printed |
|---|---|---|---|---|
| Cs2Li3Br5 | [475, 600, 750, 800, 1000, 1100] | 0.249 | 0.022 | 0.18 |
| Cs2Li3I5 | [500, 600, 750, 1000] | 0.247 | 0.023 | 0.23 |
| Cs2LiI3 | [500, 600, 750, 1000] | 0.249 | 0.048 | - |
| Cs3Li2Br5 | [500, 600, 750, 1000] | 0.434 | 0.051 | - |
| Cs3LiCl4 | [500, 600, 750, 1000] | 0.238 | 0.028 | 0.23 |
| CsLi3Br4 | [475, 500, 600, 750, 800, 1000, 1100] | 0.213 | 0.014 | 0.17 |
| CsLiI2 | [500, 600, 750, 1000] | 0.173 | 0.017 | 0.16 |
| Li10BrN3 | [500, 750, 1000] | 1.164 | 0.363 | - |
| Li10Si2PbO10 | [600, 750, 1000] | 0.428 | 0.054 | - |
| Li2B3PO8 | [500, 600, 750, 1000] | 0.065 | 0.100 | - |
| Li2BeF4 | [500, 600, 750, 1000] | 1.377 | 0.298 | - |
| Li2Ti4O9 | [475, 600, 800, 1100] | 0.270 | 0.062 | - |
| Li2ZnBr4 | [500, 600, 750, 1000] | 0.885 | 0.068 | - |
| Li2ZnGeSe4 | [500, 600, 1000] | 0.991 | 0.191 | - |
| Li4CO4 | [500, 600, 750, 1000] | 0.234 | 0.044 | 0.15 |
| Li4Mo3O8 | [475, 600, 800, 1100] | 0.152 | 0.041 | 0.25 |
| Li5Br2N | [500, 600, 750, 1000] | 0.256 | 0.070 | - |
| Li7NbO6 | [500, 600, 750, 1000] | 0.333 | 0.042 | 0.21 |
| Li8Bi2(MoO4)7 | [500, 600, 1000] | 0.464 | 0.141 | - |
| Li8SeN2 | [500, 600, 750, 1000] | 0.320 | 0.092 | - |
| Li8TeN2 | [500, 600, 750, 1000] | 0.119 | 0.106 | - |
| LiBeP | [600, 750, 1000] | 0.438 | 0.124 | - |
| LiGaSe2 | [600, 750, 1000] | 1.641 | 0.323 | - |
| LiP7 | [500, 600, 750, 1000] | 0.976 | 0.134 | - |
| LiY2Ti2S2O5 | [600, 800, 1100] | 0.506 | 0.088 | - |
| NaLi5N2 | [475, 600, 800, 1100] | 0.334 | 0.032 | 0.28 |
| Sr2LiBr5 | [500, 600, 750, 1000] | 0.767 | 0.179 | - |

## Band gap: deposited direct_bandgap (S) against printed Table 2-3 gap (A)

- n = 37, median difference -0.002 eV, max |diff| 3.324 eV

## Engine route (pinball, PET-MAD, FPMD)

- pinball D/sigma deposited only for Li7NbO6 (provenance archive); PET-MAD trajectories (1c-13) cover 11+ materials outside the 55 FPMD set (LiGaBr3 is in KNOWN_77). Overlap FPMD x PET-MAD = 0 materials: no engine comparison table can be built from the deposits (reported, not imputed).

