# PanelBench v5 stage 2: the FM advantage (V5-5, V5-6)

**Result: the pre-model gate failed in both rounds, so no stage 2 model episode was run** (David, 2026-10-11: run the frozen gate as designed, replace failing scenarios once under the frozen rule, report).

- The gate pits a scripted planner using MACE-MP-0 relaxations against the same planner using a volume-table placebo.
- Under the frozen design, the FM planner beat the placebo planner on 1 of 8 quiet scenarios tried (Ni3Sc order).
- The main finding is about accuracy: MACE-MP-0's structural errors on unfamiliar WBM chemistries are as large as the effects the quiet scenarios turn on.

**Limit.** The environment proves the mechanism inside a world we built, not that real science improves. Spend: $0.

## 1. Design (frozen before any FM call on a candidate: V5_SPEC Appendix B, commit ee21bf96)
- **Truth.** WBM relaxed structures (Matbench Discovery, figshare file 48169600, md5 4726643a…), outside MPtrj.
- **Agent's view.** The agent sees the composition and 12 generic prototypes. It builds hypotheses with `build` and relaxes them with `relax`.
- **relax arms.**
  - Placebo: an additive elemental-volume table, shown to the agent.
  - FM: MACE-MP-0 medium (`2023-12-03-mace-128-L1_epoch-199`, sha256 01bfe221…) on node A2's GPU.
  - Ceiling: the true DFT structure.
- **Selection.** Five shapes (loud polymorph control; tetragonality; trace phase; alloy vs mixture; L1_2 order). Selection rule v2 (charge balance, metal mixed sites) was frozen before any FM call. Candidates are ranked by the hash of their WBM id.
- **Constraints.** Section 3 constraints (C1, C2) pass on all 10 worlds in both rounds (`stage2/validation/CONSTRAINTS.md`, `stage2/validation_r/CONSTRAINTS.md`; tuning in `stage2/TUNING2.md`).
- **Gate (B.6).** A scripted planner:
  1. builds the claim-side and other-side hypotheses and relaxes them with the arm's relax;
  2. estimates crystallite size on m0;
  3. picks the cheapest grid measurement decisive between its own hypotheses, with lattice_scale free within ±1 % of the relaxed value;
  4. reads by likelihood ratio.
- **Gate rule.** The FM planner must beat the placebo planner by pair resolution (k = 1..5) on every quiet scenario. The loud control is reported, not gated (X15).

## 2. Hypothesis accuracy (stage2/FM_CHECK.md; volume per atom or a, against the DFT truth)
| round | structure | placebo | MACE-MP-0 |
|---|---|---|---|
| 1 | NiSeO3 perovskite | +33.0 % | +1.50 % |
| 1 | NiO2 rutile | +34.9 % | +5.69 % |
| 1 | AgRh B2 / AgRu B2 | −1.63 % / −1.11 % | −0.57 % / +0.20 % (mismatch −0.04 % vs true 0.72 %) |
| 1 | Ru3Ni L1_2 | −0.97 % | −0.17 % |
| 2 | TaCuO3 perovskite | +31.0 % | +0.18 % |
| 2 | TaO2 fluorite | +33.8 % | −1.68 % |
| 2 | PdGa B2 / PdV B2 | +3.89 % / −1.65 % | +0.46 % / −0.60 % (mismatch 1.85 % vs true 0.78 %) |
| 2 | Ni3Sc L1_2 | +4.12 % | −0.72 % |

- **Oxides.** MACE-MP-0 is far better than the placebo, but it often misses the ±1 % needed to start a fit (1.5 to 5.7 %).
- **Metals.** The placebo can already be within 1 to 2 %.
- **Small differences between isostructural phases.** FM gets these wrong: an alloy mismatch of 0.72 % came out as −0.04 %, and one of 0.78 % as 1.85 %.

## 3. Gate results (pairs resolved / 5, wrong conclusions in brackets)
| round | scenario | placebo | FM | ceiling | FM beats placebo |
|---|---|---|---|---|---|
| 1 | S2-A RbAsO3 polymorph (control) | 0/5 (5) | 0/5 (5) | 5/5 (0) | not gated |
| 1 | S2-B PbNbO3 tetragonality | 0/5 (0) | 0/5 (6) | 0/5 (10) | no |
| 1 | S2-C NiSeO3 + NiO2 trace | 0/5 (10) | 0/5 (10) | 5/5 (0) | no |
| 1 | S2-D Ag(Rh,Ru) alloy | 0/5 (0) | 0/5 (0) | 5/5 (0) | no |
| 1 | S2-E Ru3Ni order | 5/5 (0) | 5/5 (0) | 5/5 (0) | no (tie) |
| 2 | S2-B LaNbO3 tetragonality | 0/5 (0) | 0/5 (0) | 0/5 (7) | no |
| 2 | S2-C TaCuO3 + TaO2 trace | 0/5 (10) | 0/5 (5) | 5/5 (0) | no |
| 2 | S2-D Pd(Ga,V) alloy | 0/5 (10) | 0/5 (10) | 0/5 (6) | no |
| 2 | S2-E Ni3Sc order | 0/5 (0) | **5/5 (0)** | 5/5 (0) | **yes** |

Files: `stage2/validation/GATE.md` and `stage2/validation_r/GATE_round2.md`, with the planner's chosen windows.

**Reading.**
- **Where FM helped.** It helped where its error fell inside the fit's reach and the placebo's did not: Ni3Sc (FM −0.7 %, placebo +4.1 %).
- **Fewer wrong conclusions.** In TaCuO3 + TaO2, FM halved the planner's wrong conclusions (5 vs 10), because its window landed on the impurity peak. Its impurity lattice was still 1.7 % off, so it resolved no pair.
- **Even the loud control failed with FM.** Both FM and placebo polymorph structures were too far from the truth for the trust region, and the reading picked the wrong polymorph in one twin.
- **The planner's own limits, shown by the ceiling arm with true structures.** It fails tetragonality in both rounds and the round 2 alloy, by choosing plans that are decisive between its hypotheses but too cheap for the key. These cells say nothing about FM.

## 4. What was not done, and why
- **Stage 2 model runs.** Sonnet in four arms and Opus in two (220 episodes) were not run: the prompt requires the gate to pass first (6.5).
- **The S2 gate statistic.** FM minus placebo at least 15 points with the interval above zero, and blind plus FM at chance, was not computed for models, for the same reason.
- **The energy-as-verdict failure mode.** Not observable without model runs.
- **Further replacement rounds.** Not attempted (bounded at one round by David's choice). The FM_CHECK pattern suggests more candidates would mostly reproduce the same accuracy limit.

## 5. Options for David (each a design decision, not run)
1. **Treat the FM as a starting model for refinement** (trust region ±3 %, lattice refined on strong peaks), disclosed as post hoc after seeing FM outputs. FM would likely show an edge on oxides, where the placebo is about 33 % off, and none on metals.
2. **Choose scenarios where the decisive quantity is one an FM gets right** (internal coordinates, ordering energies, relative volumes of polymorphs), rather than absolute lattice parameters at below 1 % precision.
3. **Use a stronger or fine-tuned FM** (MACE-MPA-0, ORB v3, or r2SCAN-trained models), quoted under I11 if paid compute is needed.
4. **Fix the scripted planner's optimistic plans** before any rerun (tetragonality, alloy), validated on the ceiling arm.

## 6. Ledger
V5-E8 (census file committed), V5-E11 (planner bugs: identical pseudo-truths, collapsed two-phase hypothesis, P4/mmm seed), X15 (loud control not gated). Services: FM service stopped after the gate (restart: `~/start_fm.sh` on node A2).
