# V9-4 the reserved benchmark split

**Pushed before the first FM call**, as hard rule 1 requires. Produced by
`v9/audit/split_and_pairs.py` from `~/v9_data/ds1_parsed/ds1.csv` (sha256 `2ccc2716…`).
Full record in `~/v9_data/split/split.json`.

## Rule

```
fraction = int(sha256(SALT + sequence).hexdigest()[:8], 16) / 2**32
fraction < 0.30  ->  dev        (may be touched by an FM in this iteration)
otherwise        ->  reserved   (never sees an FM)
```

`SALT = "v9-split-20261019"`, logged here and in the JSON. The rule is a pure function of the
sequence, so it is deterministic, order-independent, and reproducible by anyone with the salt. It
does not look at intensity, class, mass or any descriptor, so the split is **blind to truth as
well as to any model**.

## Counts

| Set | Peptides | Fraction | Top quartile | Bottom quartile | Middle |
|---|---|---|---|---|---|
| **dev** | **538** | 0.3128 | 135 | 133 | 270 |
| **reserved** | **1,182** | 0.6872 | 295 | 297 | 590 |
| total | 1,720 | 1.0000 | 430 | 430 | 860 |

The dev fraction lands at **0.3128** rather than exactly 0.30. That is ordinary hash-partition
sampling noise on 1,720 items, not a tuned boundary: the threshold was fixed at 0.30 before the
counts were computed and was not adjusted afterwards. **Disclosed rather than corrected**, because
moving the threshold to hit 0.3000 exactly would mean choosing a split after seeing its contents.

**Quartiles are cut on the full 1,720 before splitting**, so the class definition does not depend
on which peptides fell into dev. Dev and reserved each carry both classes in near-equal numbers.

## What this reserves

The 1,182 reserved peptides, including **295 top-quartile and 297 bottom-quartile**, are untouched
by any FM call in this iteration and will carry the benchmark. The unexposed-twin exclusion from
`v9/data/AUDIT_6_7.md` applies on top of this split when the task is designed; the two
restrictions are independent, so the next iteration must count their intersection before assuming
supply.
