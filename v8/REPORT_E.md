# Amendment E iteration report (2026-10-19)

Every item of amendment E is addressed. **Gate F1 failed at fragment scale under both estimators and both protocols. Rod scoping shows cost is not the obstacle; rod geometry is.** The item 6 stop rule does not trigger, so `NEGATIVE_RESULT.md` is not written, and v8 stops for David under item 5.

**Disclosure of estimator order (item 2), as required in every report.** The **paired** estimator came first and was pre-registered in V8-1; it produced the overnight failure. The **minimum-over-placements** estimator is second and **post hoc**, chosen after that failure, on the physical ground that lateral position is not noise: a rod diffuses laterally far faster than it desorbs, so each registry reaches its own best lateral position. Both are reported side by side wherever a margin appears.

## Item by item

| Item | What was done | Result |
|---|---|---|
| 1. Q7 | `phase` is now the identified candidate registry; the fitted angle stays in `angle_rel_deg`. No kit file, no `validate_d` row edited. All rows rerun on the demo worlds. | **All rows PASS, hold included** |
| 2. Estimator | Minimum over placements, bootstrap over placements with 10,000 replicates, threshold unmoved at 3 SE, convergence reported per system. | applied in steps 1 and 2 |
| 3. Step 1, free reanalysis | `truth/F1_REESTIMATE.md` from the 24 completed solvated runs, both estimators. | **Gate F1 FAILED**, 0 of 4 |
| 4. Step 2, matched protocol | Rigid placements, no water, 30 per registry from a shared Sobol set, identical for both registries and reserved for the FM path. `truth/F1_STEP2.md`. | **Gate F1 FAILED**, 0 of 4 |
| 5. Step 3, rod scoping | One published 18-repeat U0 rod timed on K+ muscovite. No production set, no energies. `truth/ROD_SCOPE.md`. | ~1 GPU hour for a full set; **geometry blocks it** |
| 6. Stop rule | Rod set needs about 1 GPU hour, far below 48. | **not triggered**, no `NEGATIVE_RESULT.md` |
| 7. Housekeeping | B1 checked once and never signalled; leftover demo and adapter state deleted; server kept on 8881. | done |
| 8. Stays open | Listed below. | listed |

## Item 1: all rows pass, including hold

`validate_d` with every row, on the demo A and demo B worlds, with an azimuth hold and a noise hold:

| Row | Result |
|---|---|
| correctness | yes (A SUPPORTED, B REFUTED, both matching key) |
| necessity S1a+S1d, S1b+S1e, S1c+S1d+S1e+S1f, S2a, S2b | yes (each ablation gives CANNOT_TELL in both worlds) |
| measurement factorial | yes (A identified row_1, B identified row_2) |
| **hold** | **yes** (all four verdicts and all four identified registries equal their base) |
| prior flip | yes (both verdicts flip) |
| abstention | yes |
| sufficiency | yes (margin 0.4, cost 65.467 min) |
| non-bypass | yes (blind-fm resolves 0, constant prior resolves 0) |
| faithfulness | yes |

The fix took two attempts, and the first was wrong in an instructive way (V8-E15). Labelling the registry as "along a lattice row" or "30° off it" assumed the two registries sit at 0° and 30° from a row. They do not: they sit at θ and θ+30 for an offset θ set by the design's carboxylate spacing, drawn at random in the demo worlds and fixed at 12° in the toy tests. With that assumption one hold of four still failed, because world B's angle moved from 44° to 49° across the 45° midpoint. The correct label names the **candidate registry nearest the fitted angle**, using the candidate *angles* only. Those angles are geometric and identical in both twins, so the label never sees an energy or a ranking: an intervention on the FM's ranking flips the verdict and leaves the label alone, which is why the prior-flip row still passes. Changes were confined to `mcenv/world8.py`, `mcenv/server8.py` and `graphexec/test_graph_I.py`. All three suites pass and every kit file still verifies byte-identical.

Two rows remain weaker than they read, unchanged from V8-X11: non-bypass's panel clause is asserted rather than measured, since no panel run exists for demo worlds, and faithfulness uses a templated rendering rather than a renderer. Both need redoing on real worlds.

## Items 3 and 4: Gate F1, both estimators, both protocols

| System | Solvated, paired | Solvated, minimum | Rigid placements, minimum |
|---|---|---|---|
| HRm-ea / K+ | +81.3 ± 173.5 (0.47 σ) | −218.5 ± 190.7 (1.15 σ) | +172.2 ± 160.4 (1.07 σ) |
| HRm-ea / Na+ | +47.1 ± 83.8 (0.56 σ) | −35.3 ± 214.6 (0.16 σ) | −127.0 ± 153.5 (0.83 σ, undetermined) |
| HRm-60 / K+ | +110.7 ± 181.0 (0.61 σ) | +67.8 ± 128.1 (0.53 σ, undetermined) | −85.7 ± 109.0 (0.79 σ) |
| HRm-60 / Na+ | −71.7 ± 173.9 (0.41 σ) | −63.7 ± 169.6 (0.38 σ, undetermined) | +221.8 ± 176.3 (1.26 σ) |

Nothing reaches 1.3 σ against the 3 σ required. Three of four systems change the margin's **sign** between protocols, and two change sign between estimators on the same data. Every bootstrap interval spans zero.

The matched protocol did its job: the minima are now well sampled in three of four systems, the placement set is shared so Gate F2 would have isolated the energy function, and a system costs 0.4 min against 16.4 min per single solvated run. What did not change is the ratio that matters. Within one registry the interaction energy spans 1000 to 1500 kJ/mol across the 30 lateral offsets; the margin to be read off the minima is 86 to 222 kJ/mol, about a tenth of that. A minimum over 30 draws from so wide a distribution carries a bootstrap error of 109 to 176 kJ/mol — the size of the margin itself.

**One capped 50-residue repeat presents 9 acidic residues to cation rows spaced 5.2 Å apart. Sliding it by a fraction of that spacing changes the energy more than rotating it by the 30° the claim is about.** That is the finding, and it is now established under two protocols and two estimators.

## Item 5: rod scoping — cost is fine, geometry is not

Published 18-repeat U0 rod (900 residues, 171 acidic, 6466 heavy atoms) on a 9×6 IFF slab: 46,946 atoms, 2.46 s per placement minimisation, 673 MiB host and 247 MiB GPU memory. A full set is **0.41 GPU hours** for 10 (unit, cation) systems, **0.82** at both rod lengths, so 0.2 to 0.4 wall hours across hosts A1 and A2. Caveat: no energies were recorded, so convergence within 2000 iterations is unverified and the per-placement time is a lower bound.

**The blocker is that only U0 has a usable rod.** The rods the instrument renders were tiled from one repeat by a rigid screw transform, which is right for an AFM stamp and wrong for a force field: the 18-repeat tiled rod has 102 atom pairs below 1.0 Å, minimum 0.436 Å, between side chains of repeats about 65 residues apart, and its energy overflows so OpenMM cannot even add hydrogens (V8-E14). The published 18-repeat U0 chain is clean (0 pairs below 1.0 Å). U0 is therefore available at both lengths from the published model, while C1 to C4 exist only as 4H monomers and would each need a rebuilt, repacked rod. The screw transform that amendment C item 4 prescribes is exactly what produced the clashes.

U0 alone gives 2 (unit, cation) systems — below amendment C item 7's four and below Gate S's three test units — so U0 alone cannot carry the pilot as pre-registered.

## Item 8: still open, not fixed

- **V8-X9** — instrument calibration is partial. Both calibration DOIs resolved; the raw AFM images of 10.1038/s41467-026-76923-4 set the noise scale (0.003 to 0.09 nm), but 10.1038/s41467-026-69170-0 supplied no raw images, tip radius, line rate or drift, so those are assumed and the instrument is labelled partly uncalibrated in `world/CALIBRATION.md`.
- **V8-X11** — two `validate_d` rows are weaker than they read: non-bypass's panel clause is asserted, and faithfulness is templated.
- **Q1** Na+ exchanged on both basal surfaces, not one. **Q2** framework frozen with mobile surface cations. **Q3** the PME interaction-energy decomposition. **Q4** θ0's geometric criterion. **Q5** the flip arm is not disclosed in the manual. **Q6** 14-repeat control rods reach aspect 3.82, not 4. All in `OPEN_QUESTIONS.md`; none relaxes a gate.

## State and what David decides

FM blindness is intact and complete: **no FM call and no LLM contact has touched any dev or test system**; the only FM calls in v8 remain the V8-0 install probes. The 24 solvated runs and their analysis are kept as recorded; nothing was deleted. Kit B, kit D and graph I all pass and every kit file is byte-identical. Nothing of v8's is running except the server on port 8881, which holds demo worlds only. `MANUAL_I.md` now states that the reference carries no explicit water.

The decision is whether to build four clash-free control rods — repacking side chains at repeat junctions, then relaxing — so the rod reference can carry a pilot of the pre-registered size, or to narrow v8's scope to what U0 alone supports. The compute is an hour either way; the modelling is the cost, and the v8 prompt did not scope it.
