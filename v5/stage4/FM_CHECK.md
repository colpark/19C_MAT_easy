# Stage 4 FM check (V5_SPEC I.12; V5-24)

After the V5-23 freeze and the gate: MACE-MP-0 medium (`2023-12-03-mace-128-L1_epoch-199.model`, MPtrj only) relaxed every library structure on node A2 (`stage4/fm_library.py` with `mcenv.fm_service.relax`: FIRE, FrechetCellFilter, FixSymmetry, fmax 0.02 eV/Å, at most 500 steps; all 32 converged, `stage4/fm_library.json`). FM formation energies take the MP2020 correction the DFT truth entry carries (X49, V5-E23) and the MP elemental references; hull distances against the fixed MP patched phase diagram. These numbers are the expected ceiling of the FM arm; they change no world.

Stated errors (manual, measured on the 500-entry WBM dev split before V5-23): FM 0.055 eV/atom, placebo 0.322 eV/atom.

## Formation energy per polymorph (eV/atom)
| scenario | world | polymorph | DFT | FM | FM − DFT | placebo |
|---|---|---|---|---|---|---|
| 61 | 601 | Y3Zn (Cmcm) | -0.153 | -0.201 | -0.049 | -0.722 |
| 61 | 602 | Y3Zn (I4/mmm) | -0.004 | -0.029 | -0.024 | -0.722 |
| 62 | 603 | TiPPt (P-62m) | -0.923 | -0.958 | -0.034 | -0.797 |
| 62 | 604 | TiPPt (P6_3/mmc) | -0.755 | -0.811 | -0.056 | -0.797 |
| 63 | 605 | MnSbS (P2_1/c) | -0.545 | -0.526 | +0.018 | -0.521 |
| 63 | 606 | MnSbS (Pca2_1) | -0.457 | -0.522 | -0.065 | -0.521 |
| 64 | 607 | BaIn3Ni (I4mm) | -0.293 | -0.336 | -0.043 | -0.236 |
| 64 | 608 | BaIn3Ni (I-4m2) | -0.157 | -0.217 | -0.060 | -0.236 |
| 65 | 609 | Ca2Ni (Pnma) | -0.131 | -0.109 | +0.022 | -0.889 |
| 65 | 610 | Ca2Ni (I4/mmm) | -0.026 | -0.014 | +0.012 | -0.889 |
| 66 | 611 | CaS2 (C2/c) | -1.655 | -1.731 | -0.076 | -1.624 |
| 66 | 612 | CaS2 (P4/nmm) | -1.379 | -1.430 | -0.052 | -1.624 |
| 67 | 613 | BaSb2Pt (Cmcm) | -0.825 | -0.835 | -0.011 | -0.496 |
| 67 | 614 | BaSb2Pt (P4/nmm) | -0.674 | -0.735 | -0.061 | -0.496 |
| 68 | 615 | ScTiN2 (R-3m) | -2.004 | -1.988 | +0.016 | -0.460 |
| 68 | 616 | ScTiN2 (P4/nmm) | -1.516 | -1.552 | -0.037 | -0.460 |

Mean absolute FM error over the 16 polymorphs: 0.040 eV/atom (dev split 0.055).

## R scenarios: ranking of the two polymorphs
| scenario | formula | DFT gap E(P2) − E(P1) | FM gap | FM ranks P1 lower | gap within 2 × stated error |
|---|---|---|---|---|---|
| 61 | Y3Zn | 0.148 | 0.173 | yes | no |
| 62 | TiPPt | 0.169 | 0.147 | yes | no |
| 63 | MnSbS | 0.088 | 0.005 | yes | yes |
| 64 | BaIn3Ni | 0.136 | 0.119 | yes | no |
| 65 | Ca2Ni | 0.105 | 0.095 | yes | yes |

## H scenarios: side of 50 meV/atom
| scenario | world | polymorph | DFT hull distance | FM hull distance | FM on the correct side | within 2 × stated error of 0.050 |
|---|---|---|---|---|---|---|
| 66 | 611 | CaS2 (C2/c) | -0.055 | -0.131 | yes | no |
| 66 | 612 | CaS2 (P4/nmm) | 0.221 | 0.170 | yes | no |
| 67 | 613 | BaSb2Pt (Cmcm) | -0.017 | -0.028 | yes | yes |
| 67 | 614 | BaSb2Pt (P4/nmm) | 0.134 | 0.072 | yes | yes |
| 68 | 615 | ScTiN2 (R-3m) | -0.009 | 0.007 | yes | yes |
| 68 | 616 | ScTiN2 (P4/nmm) | 0.480 | 0.443 | yes | no |

## Scripted FM planner (ceiling planner with FM energies), k = 1 to 5
Pair resolution per scenario: 61: 5/5, 62: 5/5, 63: 5/5, 64: 5/5, 65: 5/5, 66: 5/5, 67: 5/5, 68: 5/5; total 40/40 (ceiling planner 40/40).

## Reading
- The FM ranks every R pair correctly and places every H world on the correct side of 50 meV/atom, so the FM arm can in principle resolve every pair.
- MnSbS (63) is the narrow case: the FM gap is 0.005 eV/atom against a DFT gap of 0.088, well inside twice the stated error; an agent that weighs the stated error should hedge there. BaSb2Pt (67, world 614) sits 0.072 above the hull under the FM, 0.022 from the threshold, also inside twice the stated error.
- The FM errors on these polymorphs are of the size the dev split predicts; nothing here selected on the FM (the selection was frozen at V5-23 before these calls).
