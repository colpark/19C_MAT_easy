# v9 verdict 3 (V9-7 to V9-9) — both gates FAILED on a measured, converged run

**Stop state 4.** Rung 1 failed both gates on a rigid score, rung 2 failed both gates on
converged relaxations, within-peptide spread did **not** swamp between-peptide spread, and
Gate M failed on UMA. Stop state 4's condition is "run MACE-MH-1 only if its measured rate
fits the remaining budget, otherwise stop and report the rate." **Nothing remains of the 25
GPU hours approved for rung 2 — 25.069 were spent — so I stopped and am reporting the rate.
MACE-MH-1 in float32 would cost about 15.3 GPU hours for a rung-2-shape run. That is a
decision for you, not a budget I have.**

This is the negative result you said was worth its own write-up.

## Every gate, with numbers

| Gate | Result | Numbers |
|---|---|---|
| **Gate M** (FM accuracy's 95% CI excludes 0.5, dev K pairs) | **FAILED** | rung 2: **0.5698**, CI **[0.3529, 0.7716]**, 265 pairs over 53 peptides. Rung 1 (rigid): 0.3901, CI [0.1996, 0.5822] — excluded 0.5 **from below**, which is not a pass |
| **Gate N restated** (FM on the subset where the best descriptor is wrong) | **FAILED** | rung 2 primary (net charge wrong): **0.5306**, CI **[0.1579, 1.0000]**, n = 49 pairs / 32 peptides, 34 ties excluded. Secondary (GRAVY wrong): 0.6579, CI [0.4245, 0.8455], n = 114 / 44. Rung 1 primary: 0.2571, CI [0.0500, 0.4909] |
| **Gate N original form** (now a diagnostic, reported side by side forever) | **not beaten** | FM − mass +0.0151 [−0.2722, +0.2946]; FM − net charge **−0.1811** [−0.4347, +0.0760]; FM − GRAVY +0.0000 [−0.3376, +0.3404]. All three span zero |
| Gate T, Gate D, Gate A (iteration 1) | PASSED, PASSED second clause only, PASSED | unchanged; `VERDICT.md` |

**Gate order disclosure, as required.** You wrote the original Gate N as "the FM beats each
null". The V9-4 null measurement showed it mis-specified: net charge 0.6743 and GRAVY 0.6911 on
dev K pairs mean the original form asks whether the FM beats a one-line descriptor, when the
question is whether it knows something the descriptors do not. You restated it **before any FM
accuracy existed**, so the change was made in ignorance of the outcome. Both forms appear above
and in every report from here on: the subset form is the gate, the head-to-head is a diagnostic.

## The failure is not a power failure

On the **identical** 265 K pairs over the **identical** 53 peptides with the **identical**
bootstrap estimator:

| | accuracy | 95% CI | clears the bar |
|---|---|---|---|
| **FM (UMA-S-1p2, oc20)** | **0.5698** | **[0.3529, 0.7716]** | **no** |
| net charge at pH 7 | **0.7509** | **[0.5312, 0.9196]** | **yes** |
| GRAVY | 0.5698 | [0.3559, 0.7735] | no |
| mass | 0.5547 | [0.3555, 0.7585] | no |

My `gate_m_power.py` finding was that the bootstrap unit is the peptide, so the peptide count
sets the interval width, and the bar at ~54 peptides is about 0.75. That raised the real
possibility that a rung-2 failure would be an artefact of the 60-peptide design rather than a
statement about the model. **It is not.** A descriptor that costs nothing clears the bar at this
n. The FM, at 25 GPU hours and 704 converged relaxations, lands tied to four decimals with
GRAVY and 0.18 below net charge.

The narrow, defensible claim: at 53 peptides' power, net charge passes and the FM does not.

## Your three rung-2 requirements, answered

1. **Trajectory minimum as well as final energy.** 1 of 528 complex relaxations ended above its
   own trajectory minimum, by 0.015 eV. No peptide's minimum changes; re-scoring every gate on
   trajectory minima reproduces every number. The non-monotonic **force** path you identified is
   real and is not UMA-specific — MACE wanders the same way — but it does not reach the **energy**
   path. A capped relaxation returns a pessimistic energy, not an arbitrary one.
2. **Within-peptide spread beside between-peptide spread.** Within-peptide SD of the 9 values,
   median **2.330 eV** (IQR [1.651, 3.651]); between-peptide SD of the 59 minima **3.319 eV**;
   ratio **0.70**. **Within does not swamp between, so stop state 3 is not triggered** and the
   minimum is not noise. It is the one number that came out in the model's favour, and it is the
   number that killed v8. Caveat: 0.70 is not 0.2 — the minimum over 9 placements is noisy even
   though it carries signal.
3. **Running minimum against evaluation count, undetermined if still falling.** **4 of 59
   peptides undetermined**: P004, P020, P025, P117. Dropping them, dropping the two cap-hit
   peptides, or dropping both leaves accuracy at 0.5785 / 0.5630 / 0.5714 and **both gates
   failing in every variant**. No filtering choice is load-bearing.

## What ran, and what it cost

| | |
|---|---|
| rung 1 (V9-7) | 3,916 rigid single points, 0.3585 s each, **0.39 GPU h against 0.40 projected** |
| rung 2 (V9-8) | **704 converged relaxations, 128.19 s each, 25.069 GPU h** over **59 of 60 peptides** (30 top, 29 bottom); the ceiling fired at a peptide boundary and P119 was not run |
| cap hits | 2 of 528 complex relaxations, fmax 0.1054 and 0.1569 at exactly 1000 steps; the other 526 converged to fmax ≤ 0.05 |
| validity refusals | 4 at conformer build, all conformer 0 (raw ESMFold), heavy-atom pairs 0.70–0.99 Å; no peptide lost all three. **Zero** during either FM run |
| V9-9 (MACE-MH-1) | installed and timed on the identical 647-atom system. UMA 0.3585 s single point, 434 steps / 167.1 s relaxation. MACE float64 1.1525 s / 230 steps / 254.2 s. **MACE float32 0.4804 s / 238 steps / 102.1 s — 1.64× cheaper than UMA** |
| total spend | **$0. No OpenRouter. No API calls.** |

Both cost projections held. Rung 1's was exact and rung 2's came in 23 percent under, because
the V9-5 timing system needed 434 steps and the median rung-2 peptide needed 395. That followed
from measuring a converged relaxation on the real system instead of extrapolating from a capped
one — the correction you made after the 10× miss.

**Disclosed overshoot:** 25.069 against 25.000 GPU hours, 0.28 percent. `--budget-gpu-hours`
stops before starting a peptide and cannot stop mid-peptide without discarding work.

## Rung 1 was a crude score, as you said in advance

You wrote before rung 1 ran that a failure there "is not a verdict on the model, because
unrelaxed ESMFold conformers scored rigidly on a rigid slab is a crude docking score." The data
agrees: **Spearman between the rigid and the relaxed minimum over the same 59 peptides is
+0.2071.** Binding energies moved from a −1.47 eV median to −6.92 eV, and the size artefact in
the rigid score (Spearman with atom count +0.1964, the wrong sign for adsorption) weakened to
+0.1582. Rung 2 is a different measurement, not the same one refined — so rung 1's failure
carries no weight against the model and rung 2's does.

The ladder worked exactly as designed: the 0.40-hour rung bought a protocol check and a cost
calibration, and the 25-hour rung bought the verdict.

## Where the FM's ranking actually points

Spearman(E_ads_min, measured intensity) = **+0.0717** over 59 peptides. Lower E_ads was
pre-registered in V9-5 as the stronger binder, so a positive correlation means the ranking
points slightly the **wrong** way. Rung 1 was +0.1171, so relaxation moved it toward zero
without reaching the negative value the model would need. AUC top-vs-bottom quartile 0.4678.
Accuracy on dev E pairs 0.4231 over 605 pairs.

This is a null with a faint wrong-signed tilt, not a result pointing the right way too weakly
to resolve.

## What this is and is not evidence about

**It is** evidence that UMA-S-1p2 with the oc20 head, 3 ESMFold conformers and 9 relaxed
placements on a rigid Au(111) slab cannot rank these decapeptides by gold-binding strength at
53 peptides' power, while net charge at pH 7 can.

**It is not** evidence that no foundation model can. Every confound named in iteration 2 is
still in place and still disclosed:

- **Au(111) approximates the nanoparticle** the assay actually measures. Facets, edges, vertices
  and curvature are absent.
- **No explicit water.** Peptide–gold binding in the assay is a displacement reaction against
  solvent, and this protocol does not model the displacement.
- **The conformer ensemble is 3 deep** from a single ESMFold prediction, pLDDT mean 0.692, range
  0.572–0.878. Iteration 2's 4-peptide range of 0.665–0.727 was four times too narrow.
- **Single-measurement reproducibility in the source data is unmeasured**, because no replicate
  error is published. This is Gate D's open first clause and it bounds any accuracy claim from
  above — including net charge's 0.7509.
- **The 9-placement minimum carries placement scatter at 70 percent** of the between-peptide
  spread.
- **10 placements in rung 1 is not a power of two**, so Sobol's balance property fails there.
  The count was pre-registered and was not changed after the fact.
- Estimator and gate order: the paired head-to-head form came first and was pre-registered; the
  subset form replaced it as the gate before any FM accuracy existed; the sensitivity filters in
  `FM_RUNG2.md` are post hoc and labelled.

My reading is that the **protocol**, not the potential, is the first thing a next iteration
should change — because a potential swap keeps all six items above and only moves the first one.
That is a recommendation, not a finding, and the measurement does not distinguish the two.

## MACE-MH-1: the rate, as stop state 4 requires

`mace-torch 0.3.16`, checkpoint `mace-mh-1.model` (59,208,139 bytes, sha256 `a522eb7f59c7879963d41586528f4980baf33e086c94aa92e3eafdeccad3be47`)
from the ACEsuit `mace-foundations` release, head **`oc20_usemppbe`**, installed `--no-deps` into
`~/v9_data/macenv` reusing v8's torch 2.13.0+cu130 read-only through a `.pth` file. Nothing was
written into v8env.

On the identical 647-atom system (560 Au, 87 peptide atoms, 280 fixed):

| | single point | relaxation to fmax ≤ 0.05 | s/step |
|---|---|---|---|
| UMA-S-1p2 (oc20) | 0.3585 s | 434 steps, 167.1 s | 0.385 |
| MACE-MH-1 float64 | 1.1525 s | 230 steps, 254.2 s | 1.105 |
| **MACE-MH-1 float32** | **0.4804 s** | **238 steps, 102.1 s** | **0.429** |

MACE float32 is slower per step and converges in 46 percent fewer steps, netting **1.64× cheaper
per converged relaxation**. Scaled onto rung 2's realised cost, a rung-2-shape MACE float32 run
is **about 15.3 GPU hours**. **That fits inside a 25-hour allowance but there is no unspent
allowance: rung 2 consumed 25.069 of the 25 approved.** So I stopped and reported the rate, which
is the "otherwise" branch of stop state 4.

**V9-E4** (mine, found and fixed): my first MACE "single point" of 0.0005 s was an ASE
`check_state` cache hit. The first fix still had one, because scrambled Sobol's placement 0
equals the cold call's structure; the loop now starts at placement 1.

MACE's fmax path also wanders non-monotonically (0.0721 at step 150, 0.0910 at 200, 0.0482 at
238), so the force-path behaviour you flagged is a property of LBFGS on this class of system,
not a UMA quirk.

## Errors I made this iteration

- **V9-E5.** `fm_gates.py` reported rung 1's Gate M as PASSED when its interval excluded 0.5
  **from below** (the test was `lo > 0.5 or hi < 0.5`), and labelled an FM − net-charge interval
  lying entirely below zero as "spans zero". The numbers were right and the labels were wrong.
  Fixed to record the side of every exclusion and never call an exclusion-from-below a pass. The
  pre-registered direction fixed in V9-5 was **not** flipped; flipping it would have turned
  rung 1's 0.2571 into 0.7429, and that is exactly why it was fixed in advance.
- **V9-E4.** The MACE cache-hit timing, above.
- **V9-X5.** The first conformer launch died with `torch.AcceleratorError: CUDA error: out of
  memory` at `model.cuda()` with 108 GB host memory free and the GPU at 2 percent utilisation.
  An identical relaunch succeeded. Unexplained; it motivated `--resume`, which is why the budget
  ceiling could stop rung 2 at a peptide boundary safely.

## Constraints held

The reserved 1,182 peptides have **never been seen by any model**. No generative language model
saw any sequence or class. Every structure was validity-checked and 4 were refused. Convergence
and cost per unit of work were recorded from the first run. Every derived file is inside the
repository or `~/v9_data`, pending the licence answer. All writes were under `~/Documents/harbor-v9`
and `~/v9_data`. v9 owned its own PID files and signalled no process it did not start. Nothing
under `v6/`, `v7/` or `v8/` was modified; v8's site-packages were read, never written. **Spend $0.**

## Open, carried forward

- The **CC BY-NC-ND licence** answer on dataset 1 — still the top blocker on anything published.
- **Gate D's first clause**: no replicate error is published. `FETCH_SHEET.md` item 3 (Tanaka et
  al. 2017 replicate structure) is paywalled and still unfetched. This bounds every accuracy
  number here, net charge's included.
- The **uncounted intersection** of the reserved split with the unexposed-twin exclusion list.
- v8's partial instrument calibration and two weak `validate_d` rows.
