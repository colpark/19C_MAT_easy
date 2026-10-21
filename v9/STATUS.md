# v9 status (updated at every push)

## Iteration 3 (V9-7 to V9-9): the FM ladder ran. **Gates M and N both FAILED.** Stop state 4.
**Read `v9/VERDICT_3.md`.** This is a measured negative result, not an inconclusive one.

| Gate | Result | Numbers |
|---|---|---|
| **Gate M** | **FAILED** | rung 2 (relaxed): **0.5698** CI **[0.3529, 0.7716]**, 265 K pairs / 53 peptides. Rung 1 (rigid): 0.3901 CI [0.1996, 0.5822] |
| **Gate N** (restated) | **FAILED** | primary 0.5306 CI [0.1579, 1.0000] (n = 49/32); secondary 0.6579 [0.4245, 0.8455]. Rung 1: 0.2571 [0.0500, 0.4909] |
| Gate N original form (diagnostic) | not beaten | FM − net charge **−0.1811** [−0.4347, +0.0760]; FM − mass +0.0151; FM − GRAVY +0.0000. All span zero |

- **The failure is not a power failure.** On the identical pairs, peptides and estimator,
  **net charge at pH 7 scores 0.7509 CI [0.5312, 0.9196] and clears the bar**; the FM at 25 GPU
  hours ties GRAVY to four decimals (0.5698) and sits 0.18 below net charge. A free one-line
  descriptor passes where UMA-S-1p2 does not.
- **Gate order disclosure, required in every report:** David wrote the original Gate N, V9-4
  showed it mis-specified, and he restated it **before any FM accuracy existed**. Both forms are
  reported side by side forever — subset form as the gate, head-to-head as a diagnostic.
- **The ladder worked.** Rung 1 (0.39 GPU h against 0.40 projected) bought a protocol check and a
  cost calibration; rung 2 (25.069 against 25.000, a disclosed 0.28 percent overshoot) bought the
  verdict. **Both cost projections held** after three iterations of optimistic ones.
- **Rung 1's failure was not a verdict, as pre-registered.** Spearman(rigid, relaxed) over the
  same 59 peptides is **+0.2071**; minima moved from −1.47 to −6.92 eV median.
- **Within-peptide spread does NOT swamp between** (median 2.330 eV against 3.319 eV, ratio 0.70),
  so stop state 3 is not triggered and the 9-placement minimum carries signal. This is the number
  that killed v8.
- **4 of 59 peptides undetermined** (still falling). Dropping them, the 2 cap-hit peptides, or
  both leaves **both gates failing in every variant** — no filtering choice is load-bearing.
- **Spearman(E_ads, intensity) = +0.0717**, still the **wrong sign** (lower E_ads was
  pre-registered as the stronger binder). A null with a faint wrong-signed tilt.
- **Stop state 4, "otherwise" branch.** MACE-MH-1 float32 is **1.64× cheaper** than UMA and a
  rung-2-shape run would cost **about 15.3 GPU h** — but rung 2 spent 25.069 of the 25 approved,
  so **nothing remains and I stopped and reported the rate**. Approving a further ~15.3 h is
  David's call, not a budget v9 has.
- My reading, offered as a recommendation and not a finding: the **protocol** is the first thing
  to change, not the potential. A potential swap keeps rigid Au(111), no explicit water, a
  3-deep conformer ensemble at pLDDT 0.692, and the unpublished replicate error that bounds every
  accuracy number here including net charge's.
- Reserved split still **unseen by any model**. 4 structures refused at the validity check.
  **Spend $0, no OpenRouter, no API calls.**

## Iteration 2 (V9-4 to V9-6): the budget stop fired; Gates M and N NOT REACHED
- **V9-4 done** (`v9/split/SPLIT.md`, `DEV_PAIRS.md`): 538 dev / 1,182 reserved by salted hash;
  17,955 dev pairs (16,291 E / 1,664 K); FM subset of 120 chosen FM-blind.
- **Two of the three nulls are not null**: net charge 0.674 CI [0.539, 0.806] and GRAVY 0.691
  CI [0.547, 0.813] on dev K pairs. Only mass is uninformative. **Gate N is the harder gate.**
- **V9-5 stopped before production** (`v9/fm/FM_DEV.md`): the pre-registered protocol costs
  **83.6 GPU h at 60 peptides**, **167.1 at 120**, against an 8-hour limit. Converged LBFGS
  relaxation = **434 steps, 167 s**; the first 200-step run hit the cap on 6 of 6 evaluations
  (fmax 0.068-2.209), so hard rule 4 caught a 2.1x optimistic estimate before it was used.
- **V9-6**: `v9/VERDICT_2.md`. Gates M and N **not reached** — neither passed nor failed, because
  no FM accuracy exists. Four costed options for David; recommended ladder is rigid single points
  (0.40 GPU h) then 3x3 placements on 60 peptides (25.07 GPU h).
- Reserved split untouched by any model. Zero validity refusals. **Spend $0.**

## Iteration 1 (V9-0 to V9-3)

**V9-0 to V9-3 complete. All three gates PASSED. v9 stops here, as pre-registered.**
Read `v9/VERDICT.md`.

| Gate | Result | Numbers |
|---|---|---|
| **Gate T** (twin supply) | **PASSED** | 271 twins at 0.1 Da, 54 in the K stratum; needs 30 and 10. Also 420/70 at 0.5 Da and 799/122 at 1.0 Da |
| **Gate D** (truth separation) | **PASSED, second clause only** | the source reports discrete classes, reproduced 1720/1720. **No replicate error is published**, so the first clause is untested |
| **Gate A** (access) | **PASSED** | three datasets in hand on research-use terms; the benchmark-carrying one is CC BY-NC-ND 4.0 |

- **The benchmark is carried by dataset 1**, 1,720 gold-binding decapeptides, ACS Omega 2022 SI
  (`10.1021/acsomega.2c00640`) over the Tanaka et al. 2017 array (`10.1016/j.actbio.2016.11.037`).
- Two corrections to the prompt: the 1,720-peptide quartile dataset is **not** in the RSC Adv.
  2023 paper (that used 860), and **V9-E1** — the RSC data availability statement is unsatisfied,
  since only the R script is published and the `Q14.csv` it reads is absent.
- Datasets 2 to 5 carry no usable graded peptide affinity; dataset 3 needs an IEEE login
  (`v9/data/FETCH_SHEET.md`).
- Top blocker before a build: **the CC BY-NC-ND NoDerivatives licence** on the only dataset that
  carries the benchmark. Second: **contamination** — the data is published, so a model may recall
  it; this must be designed into the next iteration as a named check.
- **V9-X3** (after the stop, at David's instruction): datasets 6 and 7 audited the same way.
  **Neither is a second truth table** — dataset 7's 200 peptides are exactly ranks 1-200 of
  dataset 1 and dataset 6's 22 are ranks 11-180, with no bottom-quartile member in either, so
  Gate T fails structurally on both. Five papers in this cluster rest on one array, so no second
  truth table exists in it. See `v9/data/AUDIT_6_7.md`.
- **Contamination is now quantified**: about half of every twin set has its strong member
  re-published elsewhere as a known top-200 high binder, never its weak member. Excluding every
  exposed twin still leaves **136 twins and 32 in the K stratum at 0.1 Da**, so Gate T holds on a
  contamination-hardened set. Recommend building on the unexposed twins only.
- Nothing was built. No compute, no FM call, no LLM contact with any record. **Spend $0.**
