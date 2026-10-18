# V6-14: the second energy model on the dev split. Gate A0 FAILS (C3)

The rule of `fm2/PREREG.md` was applied once to the v5 stage 4b dev split (`v5/stage4b/dev/dev4b_v2.json`: 637 entries, 491 polymorph pairs, removed from candidacy).

- **Candidates:** sources, versions and weight hashes are in `fm2/CANDIDATES.md`.
- **Protocol:** the MACE protocol (`mcenv/fm2_service.py`).
- **Data:** `fm2/dev/dev_second_fm.json` (script `fm2/dev_second_fm.py`), with the relaxations in `fm2/dev/relax_*.json`.

## The rule

| | CHGNet 0.3.0 | SevenNet-0 | M3GNet-MP-2021.2.8 |
|---|---|---|---|
| relaxed without error (R1 needs ≥ 98 %) | 637 of 637 (100 %) | 637 of 637 (100 %) | 637 of 637 (100 %) |
| converged within 500 steps (diagnostic) | 636 of 637 | 636 of 637 | 493 of 637 |
| energy convention (lower formation-energy MAE) | as_given (0.2277 corrected, 0.0533 as given) | corrected (0.0418 corrected, 0.2045 as given) | corrected (0.0654 corrected, 0.2111 as given) |
| formation-energy MAE, eV/atom | 0.0533 | 0.0418 | 0.0654 |
| polymorph-gap MAE, 491 pairs (R2 cap 0.0458) | 0.0469 | 0.0398 | 0.0551 |
| R1 / R2 | pass / fail | pass / pass | pass / fail |
| Pearson with MACE, signed polymorph-gap error (R3) | 0.8582 | 0.5375 | 0.7817 |
| own band m* for claim R (J.4 rule) | 0.05 | 0.035 | 0.075 |

- **MACE** on the same pairs: polymorph-gap MAE 0.0427 eV/atom.
- **R2:** the best candidate MAE is 0.0398 (SevenNet), so the cap is min(1.15 × 0.0398, 0.064) = 0.0458. CHGNet misses it narrowly (0.0469); M3GNet misses it clearly (0.0551).
- **R3:** SevenNet-0 is the only candidate that passes R1 and R2, so it wins without needing R3. Its error correlation with MACE is 0.5375.
- **Convergence:** M3GNet relaxed every entry without error but converged within 500 steps on only 493. Read as "converges", it would fail R1 as well, which changes nothing.

**Winner's stated errors (`fm2/STATED2.json`):** formation energy MAE 0.0418, polymorph gap MAE 0.0398, hull MAE 0.0418 eV/atom; m*_2 (claim R) = 0.035; m* (hull) = 0.015.

## Baseline: MACE on the 162 dev pairs with a DFT gap of at least 0.075 eV/atom

Re-derived exactly as the prompt states:
- 119 outside MACE's band of 0.045 eV/atom, 3 of them wrong.
- 43 inside the band: 19 wrong and 1 tie.

## Joint classes on the 162 (each model against its own band)

| candidate | AGREE (wrong) | SPLIT | SOFT | catch rate (of MACE's 3 outside-band errors) | false alarms on MACE's 116 outside-band correct pairs | false alarms on all 139 MACE-correct pairs |
|---|---|---|---|---|---|---|
| chgnet | 99 (1) | 0 | 63 | 2 of 3 | 18 of 116 | 41 of 139 |
| sevennet | 114 (2) | 0 | 48 | 1 of 3 | 4 of 116 | 27 of 139 |
| m3gnet | 65 (1) | 0 | 97 | 2 of 3 | 52 of 116 | 75 of 139 |

## Gate A0: FAILS

The winner, SevenNet-0, yields **0 SPLIT pairs** among the 162. The gate needs at least 5, so **C3 fails on the dev split**. The dev SPLIT rate is 0.0, and the expected SPLIT count for a 60-compound extension is 0.0.

No candidate yields any SPLIT on the 162, so the outcome does not depend on which model won.

Expectations of the pre-registration:
- The winner yields 3 % to 10 % SPLIT pairs: **not met** (0 %).
- Its errors correlate with MACE's above 0.5: **met** (0.5375).

## Why: the models disagree, but almost only inside a band (diagnostic, not part of the rule)

| candidate | sign disagreements with MACE, 162 pairs | of those, MACE outside its band | of those, candidate outside its band | SPLIT on all 491 pairs | SPLIT with MACE wrong |
|---|---|---|---|---|---|
| chgnet | 12 | 5 | 0 | 0 | 0 |
| sevennet | 10 | 1 | 3 | 1 | 0 |
| m3gnet | 21 | 8 | 0 | 1 | 0 |

- **The two models disagree in sign on 10 to 21 of the 162 pairs.** In almost every such pair one model sits inside its band, so the pair is SOFT, not SPLIT. Where both models are confident, they agree.
- **MACE's three confident errors:** SevenNet repeats two of them, confidently (AGREE-wrong). It turns the third into SOFT.
- **In R3 terms:** a strict consensus rule would mostly escalate or abstain where MACE is unsure, which the band rule already does with MACE alone. It would almost never catch a confident MACE error.
- **The 30 B1 compounds** include one FM-wrong compound (202 ZrTeP) and nine in band. Part A can only observe a SPLIT on the first, and only if model 2 is confident and right there. That is not known without an FM call on a B1 compound, which this stop does not make.

## Options for David (none applied)

1. **Close Part A on C3 as pre-registered.** Read the dev result as evidence that MP-trained universal potentials share MACE's confident errors; the second opinion adds abstention, not correction. Then move to the B audit (V6-18, truth only), which does not depend on A.
2. **Test a second opinion of a different kind** (out of this prompt's scope): for example a model trained on other data (excluded here by the rule), or a non-MLIP prior such as a composition or prototype model. Pre-register a new rule first.
3. **Keep MACE plus SevenNet as a SOFT detector only:** the "both" arm abstains or escalates where either model is unsure. Measure coverage and DFT value without the C3 claim. This needs a new pre-registration, since C3 is part of Gate A.

Stopped for David. Nothing after V6-14 has run: no kit C1, no model-2 call on a B1 compound, no episode.
