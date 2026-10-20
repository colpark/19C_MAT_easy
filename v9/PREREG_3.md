# v9 iteration 3 pre-registration (V9-7 to V9-9)

Pushed before any FM call. Verbatim from David's note below.

The decisions this note requires to be fixed in advance — the rung 2 selection rule and the
"best descriptor" of the restated Gate N — are in `v9/fm/PREREG_3_DECISIONS.md`, pushed in the
same commit, also before any FM call.

---

# v9 iteration 3: the FM ladder. Cheapest rung first.

To the v9 builder session. Continue the existing ledgers, labels V9-7 onward. Push `v9/PREREG_3.md` with this note verbatim before any FM call.

Good call firing the stop instead of scoring a gate on numbers you did not have. Three things you found are worth more than the gate would have been: that two of my three nulls are not null, that arginine makes them one confound wearing three hats rather than three hurdles, and that the fmax trajectory is non-monotonic so a capped relaxation returns a number depending on where it stopped. The 10x cost miss is mine, and it ran optimistic for the third time, from a figure that excluded convergence.

**Your ladder is approved: rung 1 then rung 2.** David approves raising the budget to **25 GPU hours** for rung 2, and only if rung 1 does not already settle it.

## A correction to Gate N, disclosed because I am changing a gate
I wrote Gate N as "the FM beats each null." Your measurement shows GRAVY at 0.691, so that phrasing asks whether the FM is better than a one-line descriptor, when the scientific question is whether it **knows something the descriptors do not**. A model can be individually weaker and still carry orthogonal information.

**Gate N is restated.** On the subset of dev K pairs **where the best descriptor is wrong**, the FM picks the stronger binder with a 95 percent interval excluding 0.5. Report n, since that subset is thin.

**The disclosure, required in every later report.** I wrote the original Gate N, your V9-4 measurement showed it mis-specified, and I restated it **before any FM accuracy existed**. So the change was made in ignorance of the outcome, not after seeing it. Report both forms side by side forever: the head-to-head against each of the three descriptors as a diagnostic, and the orthogonal-information form as the gate.

## Rung 1, V9-7. Rigid single points. 0.40 GPU hours
Relax the Au(111) slab **once** (14.9 s measured) and hold it rigid thereafter.

Per dev peptide, 3 conformers times 10 placements, **no relaxation**, single points only, keeping the minimum. 120 peptides, 60 from each quartile, from the FM-blind subset you already fixed. At your measured 0.398 s per single point that is **0.40 GPU hours**.

Then run `fm/fm_gates.py` unchanged on the 323 K pairs over 82 peptides you already froze, and report Gate M and the restated Gate N.

**Interpretation, written now.** A pass on both is decisive and we stop. A failure is **not** a verdict on the model, because unrelaxed ESMFold conformers scored rigidly on a rigid slab is a crude docking score. Say so plainly in either direction.

## Rung 2, V9-8. Converged relaxations. 25 GPU hours
Run this unless rung 1 passed both gates.

60 peptides, 30 from each quartile, drawn from rung 1's 120 by a logged rule fixed before you look at rung 1's scores. 3 conformers times 3 placements, **9 converged relaxations each**. LBFGS, fmax tolerance 0.05 eV/A, step cap 1000, and report every cap hit.

**Three requirements that come from your own findings.**
1. **Record the minimum energy over each trajectory as well as the final energy, and report both.** LBFGS does not guarantee a monotonic energy path, and you showed the force path wanders.
2. **Report the within-peptide spread** of adsorption energy across the 9 evaluations beside the between-peptide spread of the minima. If the within-peptide spread swamps the between-peptide signal, the minimum is noise and the gate result is unreliable whatever it says. That is what killed v8 and it costs nothing to check.
3. **Report the running minimum** against evaluation count, and mark a peptide undetermined if its minimum is still falling at the last evaluation. With only 3 placements this will be common, and saying so is better than hiding it.

## A small item, V9-9. Remove the next stop before it happens
Install **MACE-MH-1** and time **one** single point and **one** converged relaxation on the same 647-atom system. Nothing more. This exists so that if UMA fails Gate M we can try the second model without another budget stop, and so its rate is measured rather than assumed.

## Stop states, written now
1. **Rung 1 passes both gates.** Stop. The next prompt designs the task on the reserved split.
2. **Rung 1 fails, rung 2 passes both gates.** Stop. Same, with the relaxed protocol recorded as the one the design needs.
3. **Rung 2's within-peptide spread swamps the between-peptide signal.** Report it as a scoping finding, not an FM verdict, and stop.
4. **Rung 2 fails Gate M on UMA.** Run MACE-MH-1 only if its measured rate fits inside the remaining budget, and otherwise stop and report the rate. A failure on both, properly measured, is a real negative result about whether current foundation models predict experimental peptide binding to inorganic surfaces, and it is worth its own write-up.

In every state, write `v9/VERDICT_3.md` with each gate passed, failed or not reached, with its numbers.

## Carried unchanged
The reserved 1,182 peptides never see a model. No generative language model sees any sequence or class. Validity-check every structure. Record convergence and cost per unit of work from the first run. Disclose the Au(111) approximation to nanoparticle binding, the unmeasured single-measurement reproducibility, and the estimator and gate order. Keep every derived file inside the repository until the licence answer returns. Spend $0, no OpenRouter. Isolation and PID discipline as before.

## Out of scope
Any instrument, server, graph or world. Any FM call on a reserved peptide. Anything under `v6/`, `v7/` or `v8/`.
