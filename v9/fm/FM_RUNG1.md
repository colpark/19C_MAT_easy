# Rung 1 (V9-7): rigid single points. Both gates failed.

**Cost held: 3,916 single points at 0.3585 s each, 1,404 s = 0.39 GPU hours against the 0.40
projected.** The first cost projection in three iterations that came in on target, because it was
measured on 3,916 distinct structures rather than extrapolated from a capped run.

**Interpretation, written by David before the run and binding in either direction:** a failure
here is **not** a verdict on the model. Unrelaxed ESMFold conformers scored rigidly on a rigid
slab is a crude docking score. Rung 1 could only have settled the question by passing.

## What was run

| | |
|---|---|
| peptides | 120 (60 top quartile, 60 bottom), the FM-blind subset frozen in V9-4 |
| conformers | 356 of 360 (3 per peptide; 4 refused, below) |
| placements | 10 per conformer, first 10 rows of the frozen scrambled Sobol table, seed 20261019 |
| complex evaluations | 3,560, **zero validity refusals** |
| slab | relaxed once: 8 steps, 15.4 s, final fmax 0.035; held rigid thereafter |
| model / head | `uma-s-1p2`, `oc20` |
| peptides still falling at the last evaluation | **0 of 120** |

**The validity check refused 4 of 360 conformers** (hard rule 3). Every one was conformer 0 — the
raw ESMFold output — with a heavy-atom pair at 0.9737, 0.9925, 0.7234 and 0.7006 Å. The noise +
relax conformers 1 and 2 had no clash in any of those cases, so no peptide lost all three and all
120 carry an energy. **ESMFold's raw output for a 10-mer carries a sub-1.0 Å heavy-atom clash about
3% of the time**, which is worth knowing independently of this benchmark.

**pLDDT over 120 peptides: mean 0.692, range 0.572 to 0.878.** Iteration 2 reported 0.690 (0.665
to 0.727) from 4 peptides; the mean held and the **range is four times wider** than the 4-peptide
sample suggested. The 4-peptide range was not a reliable guide and should not have been quoted as
if it were.

**One caveat on the protocol as specified.** 10 placements is not a power of two, so Sobol's
balance property does not hold. That is the same issue that took v8 from 30 placements to 64 in
amendment F. The count is pre-registered at 10, so it was run at 10 and the caveat reported rather
than changed mid-protocol.

## Gate M: FAILED

| Scorer | Accuracy on the 323 dev K pairs | 95% CI (bootstrap over 82 peptides) |
|---|---|---|
| **FM, UMA oc20** | **0.3901** | **[0.1996, 0.5822]** — includes 0.5 |
| mass | 0.5511 | [0.3797, 0.7532] |
| net charge at pH 7 | 0.7229 | [0.4872, 0.9241] |
| GRAVY | 0.5944 | [0.3566, 0.8144] |

The interval includes 0.5, so **Gate M failed**. The point estimate sits below chance.

## Gate N, restated form: FAILED, and the exclusion is on the wrong side

| Subset | n pairs | n peptides | ties excluded | FM accuracy | 95% CI | |
|---|---|---|---|---|---|---|
| **net charge wrong (primary)** | **70** | **50** | 39 | **0.2571** | **[0.0500, 0.4909]** | excludes 0.5 **from below** |
| GRAVY wrong (secondary) | 131 | 61 | 0 | 0.4656 | [0.1701, 0.7051] | includes 0.5 |
| mass wrong (diagnostic) | 145 | 58 | 0 | 0.4621 | [0.2121, 0.6842] | includes 0.5 |
| all three wrong | 4 | 7 | — | — | — | too thin for an interval |

**The primary subset's interval excludes 0.5 — from below.** Gate N as literally written says "the
FM picks the stronger binder with a 95 percent interval excluding 0.5", and that literal test is
met. But it is met because the FM reliably picks the **weaker** binder, which is not what the gate
asks. **Reported as FAILED.**

Two things follow and both are mine to own:

1. **My first implementation reported this as PASSED** (`lo > 0.5 or hi < 0.5`), a two-sided test
   of the gate's literal wording. The numbers were right and the label was wrong. Both Gate M and
   Gate N now record the side of the exclusion explicitly and never report an exclusion from below
   as a pass (V9-E5, together with a sibling defect in the head-to-head row, below).
2. **The pre-registered direction was not flipped.** Lower E_ads = stronger binder was fixed in
   V9-5 before any energy existed. Inverting it now would turn 0.2571 into 0.7429 and read as a
   strong pass. That is precisely the post-hoc estimator change this project has been guarding
   against for three iterations, and it is not done. The inversion is reported as an observation,
   not adopted as a predictor.

**A design note on the restated gate, for the next version of it.** The gate scores the FM on a
subset *defined by one descriptor being wrong*. Any model correlated with that descriptor will
land far from 0.5 there by construction, with no orthogonal information at all — so the gate could
read as informative when it is not. **It did not bite here**: FM-versus-net-charge pairwise
agreement is 0.5246 on 284 non-tied pairs, which is chance, so the FM is not a net-charge proxy and
the 0.2571 is the global sub-chance lean sharpened by a smaller n. The hazard is structural, not
hypothetical, and is worth closing in the wording.

## The original Gate N form, now a diagnostic

| | Paired difference | 95% CI | |
|---|---|---|---|
| FM − mass | −0.1610 | [−0.4699, +0.1107] | spans zero |
| FM − net charge | **−0.3328** | **[−0.5985, −0.0897]** | **entirely below zero: significantly worse** |
| FM − GRAVY | −0.2043 | [−0.5381, +0.1564] | spans zero |

**V9-E5, my error.** This table's label was computed as `"above zero" if lo > 0 else "spans zero"`,
so the net-charge row — an interval lying entirely *below* zero, meaning the FM is significantly
**worse** than a one-line descriptor — printed as "spans zero". The numbers were always right; the
label hid the single most pointed result in the table. Fixed to distinguish all three cases.

## Diagnostics

| | |
|---|---|
| Spearman(E_ads, intensity), 120 peptides | **+0.1171** (z = 1.27, p ≈ 0.21) |
| AUC, top against bottom quartile, 3,600 pairs | 0.4494 |
| accuracy on 3,277 dev E pairs | 0.4553 |
| within-peptide SD of E_ads | median 0.757 eV, IQR [0.336, 6.376], max 69.4 eV |
| within-peptide range of E_ads | median 3.54 eV, max 197.4 eV |
| between-peptide SD of the 120 minima | 1.032 eV |

A correct model gives a **negative** Spearman here, since lower E_ads should mean stronger binding
and higher intensity. **+0.1171 has the wrong sign.** Every one of the five measurements above
leans the same way, below chance — but they are **not independent evidence**: all five are
functions of the same 120 E_ads values, so there is no multiplicity gain, and the underlying
correlation is not significant on its own (p ≈ 0.21). The honest summary is **one weakly
anti-correlated quantity, not five confirmations.**

## Post-hoc diagnostics, labelled post hoc

Written after rung 1's numbers were seen.

**A size artefact exists in the score but does not explain the result.** Spearman(E_ads,
peptide atom count) = **+0.3093** and Spearman(E_ads, mass) = +0.3051, i.e. **bigger peptides get a
less negative E_ads** — backwards for physical adsorption, where more atoms means more contacts.
That is the signature of a rigid score dominated by repulsive contacts at the fixed 2.6 Å gap, with
no relaxation permitted to resolve a clash. This matters because **David's spec makes K pairs
size-unmatched on purpose** ("near-isobaric is an instrument property and is not required here"):
median |Δ atom count| within a K pair is 6 and median |Δ mass| is 88 Da, so the confound is live
inside the gate. It was tested and it is **not** the cause:

| Stratum | n pairs | n peptides | FM accuracy | 95% CI | FM picks the smaller peptide |
|---|---|---|---|---|---|
| \|Δ atoms\| ≤ 2 | 69 | 50 | 0.3913 | [0.1633, 0.6596] | 0.4038 |
| \|Δ atoms\| 3–8 | 130 | 64 | 0.4000 | [0.1829, 0.6250] | 0.6000 |
| \|Δ atoms\| ≥ 9 | 124 | 58 | 0.3790 | [0.1630, 0.6310] | 0.6048 |

Accuracy is ~0.39 in **every** stratum, including pairs matched to within 2 atoms where the artefact
cannot operate. The hypothesis was mine and it is wrong.

## The finding that bears on what to spend next: Gate M's bar rises as peptides fall

Gate M's bootstrap unit is the **peptide**, as pre-registered, and that — not the pair count — sets
the interval's width. The empirical anchor needs no simulation: **net charge scores 0.6743 on the
full dev K set and its interval excludes 0.5; it scores 0.7229 on rung 1's subset and its interval
includes 0.5.** Higher accuracy, wider interval, because 82 peptides carry it instead of 195.

A synthetic oracle (truth rank plus Gaussian noise, tuned by bisection to a target accuracy, then
put through the pre-registered peptide bootstrap — no FM value involved) gives the bar:

| Pair set | pairs | peptides | minimum accuracy that clears Gate M |
|---|---|---|---|
| full dev K set | 1,664 | 195 | **0.65** |
| rung 1, 120 peptides | 323 | 82 | **0.70** |
| rung 2, 60 peptides | 270 | 54 | **0.75** |

**Cutting to 60 peptides raises Gate M's bar from 0.70 to 0.75 — above the 0.74 that the best free
descriptor reaches on that very set.** Rung 2 as specified therefore demands that UMA beat every
free descriptor to clear Gate M, on a budget that would also buy 120 peptides × 4 evaluations at
22.3 GPU hours with the bar left at 0.70.

This is reported, not acted on. Rung 2 is being run at the pre-registered 60 peptides × 3
conformers × 3 placements, because that is the design David fixed and the budget he approved, and
because the choice only changes the outcome in the narrow band 0.70–0.75, which rung 1's 0.39 makes
unlikely. **If a stronger negative result is what rung 2 is for, more peptides and fewer
evaluations each is the better buy, and that is David's call to make.**

## State

Reserved split still untouched: **1,182 peptides have never been seen by any model.** Only the 120
dev peptides of the frozen FM subset have. $0 spent, no paid API call. Nothing was written outside
`~/Documents/harbor-v9` and `~/v9_data`. No process v9 did not start was signalled.
