# V9-4 dev pairs, strata, and the three code-only null baselines

Truth and code only. No FM call and no model of any kind was involved in anything on this page.
Conventions were fixed in the script's docstring **before any number was computed** (hard rule 5).

## Dev pairs

A dev pair is one top-quartile and one bottom-quartile **dev** peptide. Near-isobaric is an
instrument property and is not required here, so the pool is every combination:

| Quantity | Value |
|---|---|
| dev top-quartile peptides | 135 |
| dev bottom-quartile peptides | 133 |
| **dev pairs** | **17,955** |
| **E** (panel picks the stronger binder) | **16,291** |
| **K** (panel wrong or tied) | **1,664** (9.27%) |
| distinct peptides appearing in a dev K pair | 195 |

The panel is the same code-only rule as V9-2, `count(W) - count(R)` from Janairo's published
rules. The K fraction here (9.3%) is lower than in the twin sets of V9-2 (15 to 28%), because
twins are additionally constrained to be near-isobaric and that constraint selects harder pairs.

## The FM subset, chosen FM-blind

120 peptides, 60 per quartile, selected by hash rank with salt `"v9-fmpick-20261019"` — again a
pure function of the sequence, so selection sees no intensity, no descriptor and no model.

| Quantity | Value |
|---|---|
| peptides | 120 (60 top, 60 bottom) |
| pairs | 3,600 |
| E | 3,277 |
| **K** | **323** |
| distinct peptides inside those K pairs | **82** (58 top, 24 bottom) |

Note the asymmetry: 58 of the 60 top-quartile peptides appear in a K pair but only 24 of 60
bottom-quartile ones. K pairs are where `W-R` fails, and failure is driven by strong binders that
the rule scores low, so the strong side is far more diverse. **Gate M's bootstrap is over
peptides, so its effective sample size is 82, not 323.** That is the honest denominator and it is
what makes the intervals below wide.

## The three null baselines

Pre-declared conventions:

- **Direction is not a free parameter after the fact.** Each descriptor is scored in both
  orientations and the null's accuracy is the **better** of the two, because an agent computing a
  free descriptor could fit its sign. Both orientations are reported.
- **Ties count as 0.5** and the tie count is reported.
- **Net charge at pH 7** = `(#R + #K) - (#D + #E)`. Histidine and the termini are ignored: the
  array peptides are surface-tethered, so a free C-terminus is not assumed.
- **GRAVY** = mean Kyte-Doolittle hydropathy.
- **Bootstrap over peptides**, 10,000 replicates, seed 29. Pairs are kept when both members
  survive a replicate, so the resampling unit is the peptide, not the pair.

### On all 1,664 dev K pairs (195 peptides)

| Null | Accuracy | Orientation | 95% CI | "higher wins" acc | Ties |
|---|---|---|---|---|---|
| monoisotopic mass | 0.5595 | higher wins | **[0.4221, 0.7072]** | 0.5595 | 0 |
| net charge pH 7 | **0.6743** | lower wins | **[0.5387, 0.8059]** | 0.3257 | 278 |
| GRAVY | **0.6911** | lower wins | **[0.5466, 0.8129]** | 0.3089 | 2 |
| *panel W−R, for reference* | 0.3395 | by construction | — | — | 1,130 |

### On the 323 FM-subset K pairs (82 peptides)

| Null | Accuracy | Orientation | 95% CI | "higher wins" acc | Ties |
|---|---|---|---|---|---|
| monoisotopic mass | 0.5511 | higher wins | [0.3796, 0.7508] | 0.5511 | 0 |
| net charge pH 7 | **0.7229** | lower wins | [0.4935, 0.9237] | 0.2771 | 39 |
| GRAVY | 0.5944 | lower wins | [0.3434, 0.8101] | 0.4056 | 0 |
| *panel W−R, for reference* | 0.3421 | by construction | — | — | 221 |

## What this means for Gate N, before any FM has run

**Two of the three nulls are not null.** On the full dev K set, net charge (0.674) and GRAVY
(0.691) both have intervals that **exclude 0.5**, so each is genuinely informative about which
peptide binds gold more strongly, in the stratum where the published rule fails. Only mass is
uninformative, as intended — mass is the instrument's axis, not a chemistry signal.

That makes **Gate N the harder of the two gates**, and it was right to require it. An FM that
reaches, say, 0.65 on dev K pairs would clear Gate M comfortably and still **fail** Gate N by
losing to a one-line GRAVY calculation. Gate N is also specified as a *paired* comparison, so it
will be evaluated as the bootstrap distribution of `accuracy(FM) - accuracy(null)` on identical
pairs rather than by eyeballing overlapping intervals.

Two observations worth carrying into the report:

1. **Lower charge and lower GRAVY both predict stronger binding** in this stratum. Arginine is the
   published low-binding marker and is both positively charged and the most hydrophilic residue on
   the Kyte-Doolittle scale, so these two nulls are not independent of each other, nor fully
   independent of the panel they are meant to control for. They should be read as one confound
   wearing three hats, not three separate hurdles.
2. **The intervals are wide** — net charge spans 0.49 to 0.92 on the FM subset — because the
   bootstrap unit is the peptide and only 82 peptides carry those 323 pairs. The FM evaluation
   inherits that width. If Gate M fails narrowly, low power on the K stratum will be a live
   explanation and must be reported as such rather than as a negative result.
