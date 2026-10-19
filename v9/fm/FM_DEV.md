# V9-5 the FM path on dev peptides: cost measured, production not run

**The budget stop rule in V9-5 fired. The pre-registered protocol costs 83.6 GPU hours at 60
peptides and 167.1 at 120, against the 8-hour limit, so nothing was run in production and no FM
accuracy exists.** This document is the cost measurement that decision rests on.

Every FM call reported here touched **dev peptides only**. The 1,182 reserved peptides
(`v9/split/SPLIT.md`) have not been seen by any model.

## What was built and fixed before any number was seen

| Element | Choice | Why |
|---|---|---|
| Structure predictor | ESMFold `facebook/esmfold_v1` | per the prompt |
| Conformers | 3 per peptide: ESMFold output, plus 2 with Cartesian Gaussian noise sigma **0.15 A** (seeds **910001**, **910002**) each followed by a 15-step UMA `omol` relaxation | the relaxation is what makes a perturbation a conformer rather than a rattled copy |
| Surface | ASE `fcc111('Au', size=(14,10,4), vacuum=12.0, orthogonal=True)` — **560 Au atoms, cell 40.39 x 24.99 x 31.07 A**, bottom **2 of 4** layers fixed | the longest ESMFold conformer measured **29.3 A**, so this leaves ~11 A margin along x and ~10 A along y |
| UMA head | **`oc20`** | of the seven heads (`oc20`, `oc22`, `oc25`, `odac`, `omat`, `omc`, `omol`) it is the only one trained on **molecular adsorbates on metal slabs**, which is this geometry exactly |
| Placements | 10 per conformer, scrambled Sobol d=4 (frac x, frac y, rotation 0–360 deg, dz in −0.3 to +0.7 A), **seed 20261019**, nominal gap 2.6 A | |
| Estimator | per peptide, `E_ads = min` over all 30 evaluations of `E(complex) − E(slab) − E(conformer in the same cell)`; **lower E_ads = stronger binder** | fixed before any energy was computed (hard rule 5) |
| Validity check | every complex screened for a heavy-atom pair below 1.0 A before it reaches the FM | hard rule 3 |

**Disclosures required by the prompt and kept here.** ESMFold confidence on a 10-mer is
**moderate: pLDDT mean 0.690, range 0.665 to 0.727** across the peptides folded, which is the
expected result for a short flexible peptide and means the conformers are a coarse sample of an
ensemble rather than a structure. And **the experiment measured binding to gold nanoparticles**,
which carry facets, edges and vertices; a flat Au(111) slab has none of those, so the surface
model is an approximation of the thing that was actually measured. The Au(100) sensitivity check
was not reached.

Structures built: 4 peptides, **12 of 12 conformers written, zero validity refusals**. The full
120-peptide conformer build was not run, because the stop rule fired first; it costs about 21
minutes (ESMFold 1.47 s per peptide, perturb-and-relax 9 s per peptide).

## The convergence measurement, which is the whole finding

A first timing run of one peptide used a 200-step cap. **All 6 evaluations hit it**, with final
fmax between **0.068 and 2.209 eV/A** against the 0.05 target — so not one had converged, and the
78 s per evaluation it reported was a lower bound on an unfinished calculation. This is precisely
the error hard rule 4 names, and recording convergence from the first run is what caught it.

A second probe took one identical starting structure to a high cap with two optimisers:

| Optimiser | Steps | Converged | Final fmax | Wall | s/step |
|---|---|---|---|---|---|
| **LBFGS** | **434** | **yes** | 0.0415 | **167.1 s** | 0.385 |
| FIRE | 800 (cap) | **no** | 0.0773 | 303.5 s | 0.379 |

LBFGS is the right optimiser and **a converged evaluation costs 167 s, not 78**. The fmax
trajectory is markedly non-monotonic — 0.064 at step 200, 0.078 at 250, 0.055 at 300, 0.129 at
350, 0.073 at 400, 0.042 at 434 — which says the optimiser is crossing between shallow local
minima of a flexible molecule on a surface. Two consequences worth carrying: a cap chosen
anywhere below ~400 steps returns a number that depends on where it stopped, and the "minimum
over 30 placements" is itself a noisy statistic even when each member has converged.

Note also that the probed placement was one of the **easier** ones: at step 200 it stood at fmax
0.068, while two placements of the same peptide were at 0.955 and 2.209. The 167 s figure is
therefore optimistic as a per-evaluation average.

## Cost, measured on a 647-atom system (560 Au + 87 peptide atoms), one GB10

| Protocol per evaluation | Cost | 120 peptides x 30 evals | 60 peptides x 30 evals |
|---|---|---|---|
| **converged LBFGS (434 steps)** | **167.1 s** | **167.1 GPU h** | **83.6 GPU h** |
| 200-step cap (fmax 0.07–2.2) | 78.7 s | 78.7 | 39.4 |
| 100-step cap (fmax ~0.18) | 40.6 s | 40.6 | 20.3 |
| 50-step cap (fmax ~0.37) | 21.5 s | 21.5 | 10.8 |
| rigid single point, no relaxation | **0.398 s** | 0.40 | 0.20 |

The slab relaxes in 8 steps and 14.9 s, once, so it is not the cost. The cost is 1,800 to 3,600
relaxations of a few-hundred-atom system.

### What the 8-hour budget actually buys

| Protocol | Evaluations in 8 GPU h | Peptides at 30 evals | at 9 evals | at 3 evals |
|---|---|---|---|---|
| converged LBFGS | 172 | **5.7** | 19.2 | 57.5 |
| 200-step cap | 366 | 12.2 | 40.7 | 122 |
| 100-step cap | 709 | 23.6 | 78.8 | 237 |
| 50-step cap | 1,340 | 44.7 | 149 | 447 |
| rigid single point | 72,390 | 2,413 | 8,043 | 24,130 |

**No configuration that keeps the pre-registered protocol fits.** The nearest miss is 60 peptides
at 1 conformer x 3 placements with converged relaxations, **8.36 GPU h** — which fits the budget
to within 5% but abandons the 3-conformer, 10-placement minimum that gives `E_ads` its meaning.

## Why this is a protocol-scoping problem, not an implementation one

8 GPU hours over 1,800 relaxations allows **16 seconds per relaxation**. The measured converged
cost is 167 s, so the budget and the protocol differ by a factor of **10.4**. Nothing available
closes that gap: a smaller slab scales roughly with atom count and the slab is 87% of the atoms,
so even halving it leaves ~40 GPU h; running both idle GB10s halves **wall** time and leaves GPU
hours unchanged, which is the budgeted quantity; and MACE-MH-1 was not tried because the ladder
says to try it only if UMA sits at chance, which cannot be established without the run.

## Pre-registered stop

> "If the projection exceeds 8 GPU hours, cut to 60 peptides and report the cut. If it exceeds 8
> hours even at 60, stop and report before running."

At 60 peptides the projection is **83.6 GPU hours**. The second branch applies. **Stopped before
running, and reporting.** The six adsorption energies from the capped timing run exist in
`~/v9_data/fm/probe/fm_dev.json` and are **timing data only**: one peptide yields no accuracy, and
every one of them is unconverged. **No energy from this iteration is used as a result, and no FM
accuracy is claimed.** `v9/fm/FM_DEV.json` is not written, because there is no dev FM result to
write.
