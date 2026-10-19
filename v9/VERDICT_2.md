# v9 iteration 2 verdict: the budget stop fired. Gates M and N were not reached.

**Gate M and Gate N are NOT REACHED — neither passed nor failed.** No FM accuracy exists, because
the pre-registered budget stop in V9-5 fired before any production run: the protocol costs **83.6
GPU hours at 60 peptides** and **167.1 at 120**, against an 8-hour limit. Reporting a gate as
failed would mean claiming a negative result about foundation models that this iteration did not
measure, and reporting one as passed is obviously unavailable. The stop rule is the finding.

What *was* established is in V9-4, and it is substantive: **two of the three null baselines are
not null**, which makes Gate N considerably harder than it looks and matters whoever runs it next.

## The three gates

### Gate M, the FM is informative — **NOT REACHED**

Requires FM accuracy on dev K-stratum pairs whose 95% interval excludes 0.5. No FM accuracy was
computed. `v9/fm/fm_gates.py` is written, tested against the data layout, and will produce the
gate from a completed run without modification. The evaluation set it would use is fixed and
pushed: **323 K pairs over 82 peptides**, from the FM-blind 120-peptide subset.

### Gate N, not a confound — **NOT REACHED**, and harder than specified

Requires the FM to beat each null with the paired difference's interval above zero. The nulls are
measured and pushed (`v9/split/DEV_PAIRS.md`), on all 1,664 dev K pairs over 195 peptides:

| Null | Accuracy | Orientation | 95% CI | Excludes 0.5? |
|---|---|---|---|---|
| monoisotopic mass | 0.5595 | higher wins | [0.4221, 0.7072] | no |
| **net charge pH 7** | **0.6743** | lower wins | **[0.5387, 0.8059]** | **yes** |
| **GRAVY** | **0.6911** | lower wins | **[0.5466, 0.8129]** | **yes** |

**An FM at 0.65 would clear Gate M comfortably and still fail Gate N to a one-line hydrophobicity
calculation.** Mass is the only genuine null, which is as intended — mass is the instrument's
axis, not a chemistry signal.

One qualification on these three, carried from V9-4: arginine is the published low-binding marker
and is simultaneously positively charged and the most hydrophilic residue on the Kyte-Doolittle
scale. Net charge and GRAVY are therefore **not independent of each other, nor fully independent
of the `W-R` panel they are meant to control for**. They are closer to one confound wearing three
hats than to three separate hurdles, and Gate N should be read that way.

### Gate A and Gate D from iteration 1 — unchanged

Gate A passed. Gate D passed on its second clause, with the single-measurement reproducibility
unmeasured and disclosed, per your decision 2.

## The cost measurement, and the error it caught

Full detail in `v9/fm/FM_DEV.md`. The short form:

| Measurement | Value |
|---|---|
| system | 647 atoms (560 Au in `fcc111(14,10,4)` + 87 peptide atoms), one GB10 |
| **converged relaxation (LBFGS)** | **434 steps, 167.1 s**, final fmax 0.0415 |
| FIRE, same start | **did not converge in 800 steps**, fmax 0.0773, 303.5 s |
| first timing run, 200-step cap | **6 of 6 evaluations hit the cap**, fmax 0.068 to 2.209 |
| rigid single point, no relaxation | 0.398 s |
| slab relaxation, once | 8 steps, 14.9 s |

**Hard rule 4 earned its place.** The first run's 78 s per evaluation was a lower bound on an
unfinished calculation; the true converged cost is **2.1x** that. Had I projected from the capped
figure, as v8's rod scoping did, I would have reported 39 GPU hours at 60 peptides instead of 84 —
still over budget, but wrong, and wrong in the same optimistic direction as both of your v8
estimates.

A second observation for whoever scopes this next: the fmax trajectory is non-monotonic (0.064 at
step 200, 0.129 at 350, 0.042 at 434). The optimiser is crossing between shallow local minima of a
flexible molecule on a surface. So a cap below ~400 steps returns a number that depends on where
it stopped, and **the minimum over 30 placements is a noisy statistic even when every member has
converged**. That bears on the "undetermined" rule more than the budget does.

## Why the gap cannot be closed inside the protocol

8 GPU hours spread over 1,800 relaxations allows **16 s each**. The measured cost is 167 s, a
factor of **10.4**. The three obvious levers do not reach:

- **A smaller slab**: the slab is 87% of the atoms, so halving it leaves roughly 40 GPU hours, and
  the cell cannot shrink much below 40 A without the 29.3 A peptide seeing its own periodic image.
- **Both GPUs**: halves wall time, leaves GPU hours unchanged. GPU hours is the budgeted quantity.
- **MACE-MH-1**: the ladder says to try it only if UMA sits at chance, which cannot be established
  without the run that does not fit. It is also not installed.

**This is a protocol-scoping mismatch, not an implementation problem.** 1,800 converged
relaxations of a few-hundred-atom system is intrinsically a tens-of-GPU-hours job on one GB10.

## What David chooses between

Measured numbers, with what each costs scientifically. My recommendation is first.

1. **Raise the budget to ~25 GPU hours and cut to 3 conformers x 3 placements on 60 peptides**
   (25.07 GPU h, about 13 wall hours across both GB10s). Keeps converged relaxations, keeps the
   60-peptide bootstrap that Gate M's power depends on, and keeps a real minimum over placements.
   Loses placement coverage, so `E_ads` is a weaker minimum — which is disclosable and
   quantifiable by reporting the running minimum, as the protocol already requires.
2. **Keep 8 hours and accept a 100-step cap** on 60 peptides at 9 evaluations (6.09 GPU h). Fits,
   but every evaluation stops at fmax ~0.18 in a non-monotonic landscape, so the energies are
   order-dependent. I do not recommend scoring a gate on these.
3. **Rigid single points, no relaxation**: 120 peptides x 30 placements for **0.40 GPU h**. Three
   orders of magnitude cheaper, and it fits any budget. It is a crude docking score on unrelaxed
   ESMFold conformers, so a failure would not be informative about UMA — but a **pass** would be
   decisive and very cheap, and it is a defensible first rung precisely because it is the cheapest
   thing that could possibly work. Worth running before option 1 for that reason alone.
4. **Abandon the FM path for this truth layer** and record it as a negative scoping result. I do
   not recommend this yet, because nothing has yet tested whether UMA is informative — only that
   the pre-registered way of asking costs ten times its budget.

**Options 3 then 1 is the ladder I would run**: 0.4 GPU hours to see whether a signal is visible
at all, then 25 to measure it properly if it is.

## State at the stop

Nothing was built: no instrument, no server, no graph, no world. Every FM call touched **dev
peptides only** — 4 peptides folded, 12 conformers relaxed, 1 slab, and 8 complexes — and the
**1,182 reserved peptides have not been seen by any model**. No generative language model saw any
sequence or class. No record-level data entered the builder's context. Validity-checked every
structure: **zero refusals**. **Spend $0.** Writes stayed under `~/Documents/harbor-v9` and
`~/v9_data`; the UMA and ESMFold weights were copied into `~/v9_data` so no cache write lands
outside v9's roots (**V9-X4**). B1's GPU was never touched.

The six adsorption energies that exist are unconverged, from one peptide, and are **timing data
only**. No FM accuracy is claimed in either direction.
