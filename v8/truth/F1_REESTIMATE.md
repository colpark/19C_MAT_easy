# Step 1: Gate F1 re-estimated on the 24 completed solvated runs (free reanalysis)

Amendment E item 3. No new run was made for this. Evidence, not a gate: the iteration proceeds to step 2 either way.

**Disclosure of estimator order (amendment E item 2), to be repeated in every later report.** The **paired** estimator came first: it was pre-registered in V8-1 and produced the overnight Gate F1 failure. The **minimum-over-placements** estimator is second and **post hoc**: David chose it after seeing the paired estimator fail. Its rationale is physical, not statistical — pairing placement *i* of one registry with placement *i* of the other has no physical meaning, and lateral position is not noise, because a rod diffuses laterally far faster than it desorbs, so each registry reaches its own best lateral position. Both are reported side by side here and below.

## Both estimators, per dev system

| System | Paired margin (kJ/mol) | SE | n σ | Minimum margin (kJ/mol) | SE | 95 % CI | n σ | Minimum converged | Result |
|---|---|---|---|---|---|---|---|---|---|
| HRm-ea / K+ | +81.3 | 173.5 | 0.47 | −218.5 | 190.7 | −283 to +390 | 1.15 | yes | fail |
| HRm-ea / Na+ | +47.1 | 83.8 | 0.56 | −35.3 | 214.6 | −369 to +368 | 0.16 | yes | fail |
| HRm-60 / K+ | +110.7 | 181.0 | 0.61 | +67.8 | 128.1 | −230 to +371 | 0.53 | **no** | undetermined |
| HRm-60 / Na+ | −71.7 | 173.9 | 0.41 | −63.7 | 169.6 | −354 to +294 | 0.38 | **no** | undetermined |

Minimum-estimator uncertainty is a bootstrap over placements, 10,000 replicates, seed 19. Gate F1 keeps its threshold, |margin| ≥ 3 SE.

**Gate F1 under the minimum estimator: FAILED, 0 of 4 dev systems.** Two fail outright and two are reported undetermined rather than passed, because a minimum was still falling at the last placement.

## Three placements sample a minimum poorly, and the numbers show it

The running minimum per registry, in placement order:

| System | E(θ0) per placement | Running min | Still falling | E(θ0+30) per placement | Running min | Still falling |
|---|---|---|---|---|---|---|
| HRm-ea / K+ | −336, −315, −272 | −336, −336, −336 | no | −555, +53, −179 | −555, −555, −555 | no |
| HRm-ea / Na+ | −732, −508, −399 | −732, −732, −732 | no | −768, −364, −365 | −768, −768, −768 | no |
| HRm-60 / K+ | −441, −339, −143 | −441, −441, −441 | no | −70, −148, −373 | −70, −148, −373 | **yes** |
| HRm-60 / Na+ | −521, −45, −613 | −521, −521, −613 | **yes** | −319, −399, −677 | −319, −399, −677 | **yes** |

Three observations, all pointing the same way:

1. **Three placements is far too few for a minimum.** In three of the eight registry minima the last placement was still the lowest value seen, so the minimum had not stopped falling. A minimum over *n* samples is biased downward and its bias shrinks only as the sample grows; with *n* = 3 the estimate is dominated by which three offsets happened to be drawn. Amendment E item 4's 30 placements address exactly this.
2. **The spread among placements at one registry is as large as any registry effect.** Individual placements of one registry span 64 kJ/mol (HRm-ea / K+, θ0) up to 608 kJ/mol (HRm-ea / K+, θ0+30: −555 to +53). The claim's whole signal must be read off differences smaller than that.
3. **The two estimators disagree in sign on two of four systems.** HRm-ea / K+ goes from +81 (paired) to −219 (minimum), and HRm-ea / Na+ from +47 to −35. With the data this thin, the choice of estimator moves the answer more than the physics does — which is the honest reason this reanalysis settles nothing and step 2 is needed.

Every bootstrap interval spans zero, by a wide margin, under the minimum estimator.

## What this does and does not say

It does **not** say the registry margin is zero, and it does not say the new estimator is worse than the old one. It says the overnight data set — 3 placements per registry, solvated dynamics — cannot estimate a minimum over lateral position, under either estimator. The solvated runs stand as recorded and nothing was deleted; they remain the only solvated evidence v8 has, and they establish that the interface is strongly bound (−272 to −768 kJ/mol) with per-run sampling errors of 7 to 28 kJ/mol, so the individual runs were sound.

Proceeding to step 2: the rigid-placement reference protocol with 30 placements per registry and no water, which makes the reference differ from the FM path in one thing only.
