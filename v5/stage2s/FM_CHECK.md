# FM check, stage 2s (gate rounds 1 and 2)

Relaxed structures from the gate planning episodes (node A2 states ~/v5_state_2s_gate and ~/v5_state_2s_gate_r2), compared with the DFT (WBM) truth. Volume error per atom and the sorted cell edges a, b, c. Extracted by stage2s/validation/fmcheck2s.py.

| round | scenario | arm | truth structure | space group (relaxed / truth) | volume error per atom | cell edges relaxed (A) | cell edges truth (A) |
|---|---|---|---|---|---|---|---|
| 1 | 46 | fm | SrPbO3 cubic perovskite | Pm-3m / Pm-3m | +0.29 % | [4.2901, 4.2901, 4.2901] | [4.2859, 4.2859, 4.2859] |
| 1 | 46 | fm | SrPbO3 ilmenite | R-3 / R-3 | -0.59 % | [5.9088, 5.9088, 16.2973] | [5.9092, 5.9092, 16.3924] |
| 1 | 46 | placebo | SrPbO3 cubic perovskite | Pm-3m / Pm-3m | +119.95 % | [5.5738, 5.5738, 5.5738] | [4.2859, 4.2859, 4.2859] |
| 1 | 46 | placebo | SrPbO3 ilmenite | R-3 / R-3 | +109.59 % | [7.8825, 7.8825, 19.3081] | [5.9092, 5.9092, 16.3924] |
| 1 | 47 | fm | SrOsO3 cubic perovskite | Pm-3m / Pm-3m | +0.33 % | [3.9967, 3.9967, 3.9967] | [3.9923, 3.9923, 3.9923] |
| 1 | 47 | fm | SrOsO3 orthorhombic perovskite | Pnma / Pnma | +0.17 % | [5.6308, 5.6323, 7.9636] | [5.6137, 5.6431, 7.9587] |
| 1 | 47 | placebo | SrOsO3 cubic perovskite | Pm-3m / Pm-3m | +146.45 % | [5.3926, 5.3926, 5.3926] | [3.9923, 3.9923, 3.9923] |
| 1 | 47 | placebo | SrOsO3 orthorhombic perovskite | Pnma / Pnma | +148.80 % | [7.6263, 7.6263, 10.7853] | [5.6137, 5.6431, 7.9587] |
| 1 | 48 | fm | MnPbO3 tetragonal perovskite | P4mm / P4mm | -0.67 % | [3.9194, 3.9194, 3.9537] | [3.9192, 3.9192, 3.9807] |
| 1 | 48 | fm | PbO2 rutile | P4_2/mnm / P4_2/mnm | +0.18 % | [3.5124, 5.0338, 5.0338] | [3.4449, 5.0784, 5.0784] |
| 1 | 48 | fm | MnO2 rutile | P4_2/mnm / P4_2/mnm | -0.05 % | [2.9782, 4.4586, 4.4586] | [2.9553, 4.477, 4.477] |
| 1 | 48 | placebo | MnPbO3 tetragonal perovskite | P4mm / P4mm | +110.99 % | [5.0361, 5.0361, 5.0865] | [3.9192, 3.9192, 3.9807] |
| 1 | 48 | placebo | PbO2 rutile | P4_2/mnm / P4_2/mnm | +98.04 % | [4.2047, 6.4688, 6.4688] | [3.4449, 5.0784, 5.0784] |
| 1 | 48 | placebo | MnO2 rutile | P4_2/mnm / P4_2/mnm | +135.87 % | [3.8937, 5.9903, 5.9903] | [2.9553, 4.477, 4.477] |
| 1 | 49 | fm | Pb3K L1_2 (2r) | Pm-3m / Pm-3m | +2.63 % | [5.1082, 5.1082, 5.1082] | [5.0642, 5.0642, 5.0642] |
| 1 | 49 | placebo | Pb3K L1_2 (2r) | Pm-3m / Pm-3m | +28.78 % | [5.5096, 5.5096, 5.5096] | [5.0642, 5.0642, 5.0642] |
| 1 | 50 | fm | CoMg B2 (2r) | Pm-3m / Pm-3m | +0.41 % | [3.0393, 3.0393, 3.0393] | [3.0352, 3.0352, 3.0352] |
| 1 | 50 | placebo | CoMg B2 (2r) | Pm-3m / Pm-3m | +22.75 % | [3.2498, 3.2498, 3.2498] | [3.0352, 3.0352, 3.0352] |
| 2 | 47 | fm | ScMnO3 cubic perovskite | Pm-3m / Pm-3m | -1.46 % | [3.784, 3.784, 3.784] | [3.8026, 3.8026, 3.8026] |
| 2 | 47 | fm | ScMnO3 orthorhombic perovskite | Pnma / Pnma | +7.48 % | [5.0124, 5.3303, 8.0986] | [5.0136, 5.4077, 7.4253] |

## Reading
- MACE-MP-0 places 8 of 11 volumes within 0.7 % of the DFT ones; the exceptions are Pb3K (+2.6 %) and the round 2 ScMnO3 polymorphs (cubic −1.5 %, Pnma +7.5 %); the placebo is 7 to 47 % off in volume per atom (6 to 36 % in lattice).
- The cell shape is where MACE fails the stage 2s scenarios:
  - SrOsO3 Pnma (round 1, 47): a and b split by 0.03 % against the DFT's 0.52 %, so MACE's Pnma is almost metrically cubic and its decisive splitting is missing; no plan within B separates the FM hypotheses (only the 125-min neutron pattern does).
  - MnPbO3 P4mm (48): c 3.954 A against 3.981 A (c/a 1.009 against 1.016); PbO2 rutile: c 3.512 A against 3.445 A (+2 %). With these shapes the FM main-phase hypothesis misfits the decisive window (chi2 about 5000 on 201 points), which swamps the 3 wt % impurity difference.
  - ScMnO3 Pnma (round 2, 47): c 8.10 A against 7.43 A (+9 %), volume +7.5 %.
- The design assumption "a good model returns the lattice to about 1 %" (E.2, the manual) holds for the volume of most structures but not for the distortions that decide the quiet polymorph and trace scenarios.
