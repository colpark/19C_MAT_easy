# V9-8 — rung 2: converged relaxations on 59 peptides. Both gates FAILED.

Rung 1 (`FM_RUNG1.md`) failed both gates on a rigid score, which you had written in advance
was **not a verdict on the model**. Rung 2 is the verdict-bearing run: 3 conformers x 3
placements, every one relaxed to fmax <= 0.05 with LBFGS, step cap 1000.

**Headline: Gate M FAILED and Gate N FAILED on converged relaxations. The failure is not a
power failure — on the identical 265 pairs over 53 peptides, net charge at pH 7 scores 0.7509
with a 95 percent interval of [0.5312, 0.9196], which clears the Gate M bar that the FM at
0.5698 [0.3529, 0.7716] does not.** A free one-line descriptor passes where UMA-S-1p2 at
25 GPU hours lands on chance.

## Gate order disclosure (required in every report from here on)

You wrote the original Gate N as "the FM beats each null". The V9-4 null measurement showed
that phrasing mis-specified: net charge 0.6743 and GRAVY 0.6911 on dev K pairs mean the
original form asks whether the FM beats a one-line descriptor, when the question is whether
it knows something the descriptors do not. You restated Gate N as the orthogonal-information
form **before any FM accuracy existed**, so the change was made in ignorance of the outcome.
Both forms are reported side by side below and forever: the subset form is **the gate**, the
head-to-head paired difference against each of the three descriptors is **a diagnostic**.

## What ran

| | |
|---|---|
| peptides | **59 of the pre-registered 60** (30 top, 29 bottom) |
| why 59 | the 25 GPU-hour ceiling fired at a peptide boundary; `P119` (bottom) was not run |
| budget | 25.069 of 25.000 GPU h — **0.069 h over**, disclosed below |
| complex relaxations | 528 (59 x 9, less 3 for `P047`, whose conformer 0 was refused at the validity check) |
| conformer relaxations | 176 (one per surviving conformer, for the reference energy) |
| total | **704 relaxations, 128.19 s each, 90,246 s** |
| slab | 8 steps, 14.2 s, fmax 0.035, relaxed once and held rigid |
| validity refusals during the run | **0** |

Selection was `rung2_selection.json`, rule B, fixed and logged **before rung 1's scores were
looked at** (`PREREG_3_DECISIONS.md` section 2). The run order was interleaved top/bottom, so
the 59-peptide prefix is balanced by construction rather than by luck — that was the reason for
the interleave, and the ceiling firing one peptide early is why it mattered.

**The 0.069 GPU-hour overshoot.** `--budget-gpu-hours` checks the clock at a peptide boundary
and stops before starting the next peptide; it cannot stop mid-peptide without discarding work.
The 59th peptide started at 24.65 h and finished at 25.069. The overshoot is 0.28 percent and
is reported rather than rounded away.

## Cost: the projection held for the second time

| | Projected (V9-5/V9-9) | Realised |
|---|---|---|
| per converged relaxation | 167.1 s | **128.19 s** |
| steps to fmax <= 0.05 | 434 | mean 416.1, median 395, range 167–1000 |
| per peptide | — | 1,529.6 s mean (median 1,520.7, range 850–2,210) |
| 60 peptides | 25.07 GPU h | **25.069 GPU h at 59** (25.49 projected at 60) |

The per-relaxation cost came in 23 percent **under** projection because the V9-5 timing system
needed 434 steps and the median peptide needs 395. Rung 1's estimate also held. After three
iterations of optimistic estimates, two consecutive honest ones came from measuring a converged
relaxation on the real system instead of extrapolating from a capped one.

## Your three requirements

### Requirement 1 — trajectory minimum as well as final energy

**1 of 528 relaxations ended above its own trajectory minimum, by 0.015 eV** (−0.4546 against
−0.4696, 828 steps, no cap hit). No peptide's reported minimum changes: re-scoring every gate
on trajectory minima instead of final energies reproduces every number to four decimals
(`out/gates_rung2_traj_minima.json`).

This answers the concern that motivated the requirement, and the answer is the reassuring one.
The non-monotonic **force** path you identified is real and is not a UMA quirk — MACE-MH-1
wanders the same way (`MACE_RATE.md`) — but it does not propagate to the **energy** path. In
528 converged relaxations the energy descends monotonically. So a capped relaxation returns a
pessimistic energy, not an arbitrary one, which is a weaker failure mode than the force path
suggested. Both numbers are recorded per relaxation regardless.

### Requirement 2 — within-peptide spread beside between-peptide spread

| | eV |
|---|---|
| within-peptide SD of the 9 E_ads values, median | **2.330** (IQR [1.651, 3.651], min 0.530 `P112`, max 6.743 `P033`) |
| between-peptide SD of the 59 minima | **3.319** |
| ratio within / between | **0.70** |
| ICC on the raw 9 values per peptide | 0.298 |

**Within does not swamp between.** Stop state 3 is **not** triggered: the minimum carries
signal above the placement scatter. This is the one number in rung 2 that came out in the
model's favour, and it is the number that killed v8 — worth saying plainly.

Two caveats on it. The ratio is 0.70, not 0.2: the placement scatter is 70 percent of the
between-peptide spread, so the minimum over 9 evaluations is a noisy statistic even though it
is not pure noise. And the ICC of 0.298 is computed on the raw values, not the minimum, so it
diagnoses the underlying scatter rather than the gate's statistic.

### Requirement 3 — running minimum against evaluation count, undetermined if still falling

**4 of 59 peptides are undetermined** — `P004`, `P020`, `P025`, `P117` — their running minimum
still fell during the last quarter of their 9 evaluations. Per-peptide running minima are in
`out/rung2_analysis.json`. 9 placements is few enough that this was expected to bite harder
than it did.

Gate scores with the undetermined peptides dropped, and with the two cap-hit peptides dropped,
are below. **Every variant fails both gates**, so no filtering choice is load-bearing:

| set | n peptides | n K pairs | FM accuracy | 95% CI | Gate M | Gate N primary |
|---|---|---|---|---|---|---|
| **all (pre-registered)** | **53** | **265** | **0.5698** | **[0.3529, 0.7716]** | **FAILED** | **FAILED** (0.5306) |
| determined only | 49 | 242 | 0.5785 | [0.3571, 0.7902] | FAILED | FAILED (0.5455) |
| no cap-hit peptides | 51 | 254 | 0.5630 | [0.3450, 0.7708] | FAILED | FAILED (0.5000) |
| both filters | 47 | 231 | 0.5714 | [0.3409, 0.7847] | FAILED | FAILED (0.5122) |
| trajectory minima | 53 | 265 | 0.5698 | [0.3529, 0.7716] | FAILED | FAILED (0.5306) |

(n peptides here is the K-pair bootstrap denominator, which is smaller than the 59 evaluated.)

**Cap hits: 2 of 528**, both `k=1 j=2` placements, `P011` at fmax 0.1054 and `P106` at 0.1569,
both at exactly 1000 steps. Those are the only two relaxations in the run that exited above the
0.05 target; the other 526 all converged.

## Gate M — FAILED

On 265 dev K-stratum pairs over 53 peptides, bootstrap over peptides, 10,000 replicates, seed 29:

| | accuracy | 95% CI | excludes 0.5 |
|---|---|---|---|
| **FM (UMA-S-1p2, oc20 head)** | **0.5698** | **[0.3529, 0.7716]** | **no → FAILED** |
| mass | 0.5547 | [0.3555, 0.7585] | no |
| **net charge at pH 7** | **0.7509** | **[0.5312, 0.9196]** | **yes, from above** |
| GRAVY | 0.5698 | [0.3559, 0.7735] | no |

**This is the decisive line of the iteration.** Your `gate_m_power.py` finding was that the
peptide count sets the interval width and that the bar at ~54 peptides is about 0.75, which
raised the possibility that a rung-2 failure would be a power failure rather than a model
failure. It is not. Net charge clears the bar **on the identical pairs and the identical
peptides** with the identical estimator. The FM had the same n available to it and landed on
0.5698, tied to four decimals with GRAVY and below net charge by 0.18.

So the honest statement is narrower and stronger than "underpowered": at this n a descriptor
that costs nothing passes, and the FM at 25 GPU hours does not.

## Gate N (restated, the gate) — FAILED

On the subset where the best descriptor is wrong, ties excluded with counts:

| subset | n pairs | n peptides | ties excl. | FM | 95% CI | result |
|---|---|---|---|---|---|---|
| **net charge wrong (PRIMARY)** | **49** | **32** | **34** | **0.5306** | **[0.1579, 1.0000]** | **FAILED** |
| GRAVY wrong (secondary) | 114 | 44 | 0 | 0.6579 | [0.4245, 0.8455] | failed |
| mass wrong (diagnostic) | 118 | 42 | 0 | 0.5763 | [0.3261, 0.8098] | failed |
| all three wrong | 4 | 7 | — | — | — | too thin, reported as a count |

The primary subset's interval reaches 1.0000 because 32 peptides supporting 49 pairs is very
thin — that is the cost of defining the subset by one descriptor's errors, and it was visible
in advance (`PREREG_3_DECISIONS.md` section 1 fixed the subset sizes before any FM call: 70
pairs over 50 peptides was the rung-1 projection; rung 2's smaller peptide set gives 49 over 32).
The secondary subset is better powered and also fails, at 0.6579 [0.4245, 0.8455].

**The design note I raised in rung 1 still stands and still does not bite.** The restated gate
scores the FM on a subset defined by one descriptor being wrong, so any model correlated with
that descriptor looks informative there by construction. FM-against-net-charge pairwise
agreement is **0.5628 on the 231 non-tied rung-2 K pairs** (rung 1: 0.5246 on 284), so the FM
tracks net charge barely above chance and the subset is not doing hidden work for it. It is not
doing hidden work against it either.

## Original Gate N form, now a diagnostic — all three span zero

Paired difference FM − null on all 265 K pairs, FM and null scored on the identical replicate:

| | difference | 95% CI | |
|---|---|---|---|
| FM − mass | +0.0151 | [−0.2722, +0.2946] | spans zero |
| FM − net charge | **−0.1811** | [−0.4347, +0.0760] | spans zero |
| FM − GRAVY | +0.0000 | [−0.3376, +0.3404] | spans zero |

Relaxation changed this picture from rung 1, where FM − net charge was −0.3328 [−0.5985,
−0.0897], entirely below zero: the FM was **significantly worse** than net charge on the rigid
score and is now merely worse. That is the direction of improvement, and it stops short of
parity.

## Diagnostics

| | rung 1 (rigid) | rung 2 (relaxed) |
|---|---|---|
| Spearman(E_ads_min, intensity), 59–120 peptides | **+0.1171** | **+0.0717** |
| AUC top vs bottom quartile | 0.4494 | 0.4678 |
| accuracy on dev E pairs | 0.4553 (3,277) | 0.4231 (605) |
| E_ads_min median | −1.473 eV | **−6.917 eV** |
| E_ads_min range | [−8.238, −0.587] | [−15.258, −0.935] |
| Spearman(E_ads_min, peptide atom count) | +0.1964 | +0.1582 |

**The sign is still wrong.** Lower E_ads was pre-registered in V9-5 as the stronger binder, so
a positive Spearman against measured intensity means the FM's ranking points slightly the wrong
way. It is now +0.0717 against +0.1171 — closer to zero, which is the improvement relaxation
bought, and still not the negative correlation the model would need.

**Relaxation did real work and rung 1 was a poor proxy for it.** Spearman between the rigid and
the relaxed minimum over the same 59 peptides is **+0.2071**. The rigid score barely predicts
the relaxed one, binding energies moved from a −1.5 eV median to −6.9 eV, and the size artefact
weakened from +0.1964 to +0.1582. Your advance interpretation of rung 1 was right: it was a
crude docking score and its failure was not a verdict. Rung 2's failure is a different
measurement, not the same one refined.

## What this is and is not evidence about

It is evidence that **UMA-S-1p2 with the oc20 head, 3 ESMFold conformers, 9 relaxed placements
on a rigid Au(111) slab, cannot rank these decapeptides by gold-binding strength** at 53
peptides' worth of statistical power, while net charge can.

It is **not** evidence that no foundation model can, and the confounds are all still in place
and all still disclosed: Au(111) is an approximation to the nanoparticle surface the assay
measures; there is no explicit water; the conformer ensemble is 3 deep from a single ESMFold
prediction with pLDDT mean 0.692; single-measurement reproducibility in the source data is
unmeasured because no replicate error is published (Gate D's first clause, still open); and the
9-placement minimum carries scatter at 70 percent of the between-peptide spread.

The one confound rung 2 removes is the one rung 1 could not: this is a converged relaxation, not
a rigid score.

## Files

- `out/gates_rung2.json` — the pre-registered scoring, all 59 peptides
- `out/gates_rung2_{determined_only,no_cap_hit_peptides,determined_and_no_cap,traj_minima}.json`
- `out/rung2_analysis.json` — the three requirements, per-peptide running minima, cap hits
- `rung2_analysis.py` — post hoc, so labelled in its docstring
- `~/v9_data/fm/rung2/fm_dev.json` — per-relaxation records, kept inside v9's roots
