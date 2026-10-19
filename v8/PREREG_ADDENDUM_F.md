# v8 pre-registration addendum F (V8-X14)

Pushed before any new run. Verbatim from David's note below.

---

# PROMPT CHANGE: v8 amendment F (David, 2026-10-19), the rod test and the end of v8's first iteration

To the v8 builder session. Log as V8-X14, errors from V8-E17. Push `v8/PREREG_ADDENDUM_F.md` with this note verbatim, regenerate `PREREG_EFFECTIVE.md`, and push before any new run.

Excellent iteration. You were right that cost is not the blocker and that only U0 has a usable rod, and you caught your own Q7 error before it reached a gate. Two calls of mine were wrong and I am recording them: the minimum estimator did not recover a signal, and the rigid screw transform in amendment C item 4 is the wrong way to build a force field rod. Carry both in the report.

**This is v8's last iteration before I decide its future.** It answers one question and stops.

## 1. The question
Does the registry margin clear Gate F1 on a published rod, where 171 acidic residues engage the surface instead of 9?

## 2. Systems, dev only
U0 alone, from the published chain, at 14 and 18 repeats, on K+ and Na+ muscovite. That is 4 systems. Cut the 14-repeat rod from the published 18-repeat chain as you described.

**U0 sits in the dev split, so this touches no test system and FM blindness is unaffected.** Build no control rod. Do not repack anything.

## 3. Validity check before any force field run
For every structure you are about to hand to a force field, report the minimum heavy-atom pair distance and the count of pairs below 1.0 A. **Refuse to run any structure with a pair below 1.0 A** and report it instead. This rule is general from now on, and it is the check my amendment C should have demanded.

## 4. Protocol
The step 2 protocol, with three fixes.
1. **64 placements per registry**, not 30, from the same scrambled Sobol construction with a logged seed. 64 restores the power-of-two balance scipy asked for. The two registries share the identical placement set, as before.
2. **Record every energy.** The scoping run recorded none, which is why its timing is only a lower bound.
3. **Verify the minimisation converges.** Report the exit iteration count and final gradient norm per placement. If placements hit the 2000 iteration cap, raise the cap until they do not, apply the new cap uniformly, and log it.

Gate F1 is unchanged at `|margin| >= 3 SE`, minimum over placements, bootstrap over placements with 10,000 replicates. Report the running minimum against placement count, and mark a system **undetermined** if its minimum is still falling over the last quarter of placements.

Keep reporting both estimators side by side, keep the estimator-order disclosure, and keep the no-water disclosure.

## 5. One free diagnostic I want
Report the margin at 14 repeats beside the margin at 18 repeats for each cation. **If the physical story holds, the 18-repeat margin should exceed the 14-repeat margin in magnitude.** If it does not, say so plainly, because that would undercut the whole rod argument regardless of what the gate says. This is a reported diagnostic, not a gate.

## 6. Scope the next gate before we need it
Time **one** UMA single point and **one** UMA relaxation step on the 18-repeat K+ rod system. Report wall time, host and GPU memory, and whether it fits at all. **Do not record any energy as a margin and do not compute a matched angle from it.** This is a cost measurement on a dev system, nothing more. If UMA cannot hold a system of this size, that is the finding and it matters for Gate F2.

## 7. Budget and stop
Projected cost is about 0.35 GPU hours. If your own projection exceeds 4 GPU hours, stop and report before running.

Then stop for David in one of two states.

**If Gate F1 passes on at least 3 of the 4 rod systems:** write `truth/F1_ROD.md` with the table, the scaling diagnostic and the UMA timing, and stop. Build nothing further. The control rods are a separate decision with their own schedule.

**If Gate F1 fails on the rod:** write `v8/NEGATIVE_RESULT.md` and stop. v8 ends there. Cover what was built and verified, Gate S and Gate F1 across two estimators, two protocols and two length scales, the quantitative mechanism, which of my prescriptions were wrong and why, what would change the answer, and what a later attempt should do differently. Write it as a finding, not an apology. State plainly that the instrument, the graph, the server and the validation suite all pass and are reusable.

## 8. Unchanged
Isolation, credentials, anonymity, 2 concurrent episodes, FM-blind selection, and every open item in V8-X9, V8-X11 and Q1 to Q6. List them again in whichever document you write.
