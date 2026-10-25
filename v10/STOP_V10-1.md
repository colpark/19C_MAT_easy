# Stop for David: V10-1 pilot, no tuning unit qualifies (2026-10-25)

The pilot's stage s2 finished at 15:15Z (126 of 126 jobs, rc 0 on every one). κ is final at **0.2**: the final median D(neutron, κ=1)/D(R1)
is 6.22 over 252 worlds (deciles 1.43, 6.20, 11.48), so the final median ratio is 0.2 × 6.22 = **1.24**, inside 0.5 to 2.
`v10/KAPPA.json` is written.

**Qualification: 0 of 126 tuning units qualify** (R 0 of 99, H 0 of 27). Every unit fails the first condition, N_plan ≤ N_rec;
26 also fail the plan check (23) or the free-scan bar (7). T draws its candidates from R qualifiers, so T has none and stage s4
has no job.

PREREG V10-1: continue only if every family's projected supply reaches 1.25 × the Gate V10-supply minima; otherwise widen the frame to
every WBM and MP formula that passes the v7 novelty rule and rerun the projection; if it still falls short, stop for David. With a
qualification rate of 0, the projected supply is 0 on any frame, so the widened projection falls short too. **This is that stop.**
Nothing after V10-1 has run: no selection, no world built, no FM call, no episode. Stage s3 (v7 bars for the pilot controls) is still
running at $0 so that PILOT.md can report the control shares; s4 has no job.

## Why (s2 outputs, `pilot/run/s2/out`)
| | R (99) | H (27) |
|---|---|---|
| N_plan / N_rec: min, p10, median, p90, max | 1.02, 1.12, 1.79, 2.94, 5.36 | 1.08, 1.10, 1.43, 2.13, 4.41 |
| planner's worst-case D over the best recipe's D on the hard twin, at N_rec (qualifying needs 50 / 15 = 3.33) | 0.62, 1.12, 1.87, 2.94, 3.26 | 0.76, 1.55, 2.33, 2.99, 3.09 |
| recipe that sets N_rec (the best on the hard twin) | R3c 50, R5 33, R3b 14, R3a 2 | R3c 20, R5 5, R3b 2 |
| decisive-plan kind at N_plan | pair 60, window > 35° 22, 25-35° 12, neutron 3, Si 1, < 25° 1 | pair 21, window > 35° 5, 25-35° 1 |

N_rec is set by the hard twin (the easy twin's recipe D is often in the thousands). There, qualification asks the planner's worst
case (over size, displacement and zero offset) to beat the best fixed recipe by 3.33 at the same counts. It does so by about 2 (median),
3.26 at best. The binding recipes are the narrow fixed windows R3a to R3c (20° windows at 0.02° over the whole budget) and R5 (the
neutron, which κ = 0.2 makes as strong as R1 on the median world).

## What would change it (approximate, for David's decision; not applied)
Counts of units with N_plan ≤ N_rec under one change each, with expected D taken as linear in N (only this condition; the plan check
and the free-scan bar would remove some more):

| change | R (of 99) | H (of 27) |
|---|---|---|
| as registered | 0 | 0 |
| plan target 25 instead of 50 | 60 | 20 |
| N_rec threshold D < 25 instead of 15 | 44 | 19 |
| N_rec without R3a-c | 21 | 10 |
| N_rec without R5 | 8 | 1 |
| N_rec without R3a-c and R5 | 54 | 18 |

Gate V10-supply minima (×1.25 for the projection): R 16 (20), H 12 (15) with 5 of type M, T 12 (15), 6 controls per family (8). The
tuning split is about a quarter of each frame, so a pilot rate p projects to about 4p × frame on the bench side.

Every one of these is a change to the registered selection rule and needs David's written amendment. Nothing else is waiting on the
pilot except PILOT.md (after s3) and the PREREG part 2 append of these numbers.
