# v8 pre-registration addendum E (V8-X12)

Pushed before any new truth run. Verbatim from David's note below.

---

# PROMPT CHANGE: v8 amendment E (David, 2026-10-19), after Gate F1

To the v8 builder session. Log as V8-X12. Push v8/PREREG_ADDENDUM_E.md with
this note verbatim, regenerate PREREG_EFFECTIVE.md, and push before any new
truth run.

Good work overnight. Gate S, the instrument and the graph all stand, and FM
blindness is intact. This note answers Q7, changes how the Gate F1 quantity
is estimated, and sets a stop rule.

## 1. Q7: approved as you proposed
Make phase the registry label (matched or other) and keep the fitted angle
in angle_rel_deg. Do not edit any kit file and do not change a validate_d
row. Rerun all rows on the demo worlds and report.

## 2. Gate F1 keeps its threshold and changes its estimator
Disclosure first, and in every later report. I chose this estimator after
seeing the paired estimator fail, so it is post hoc. Report both estimators
side by side every time, and say which one came first and why the second
exists.

What was wrong. You paired placement i of theta0 with placement i of
theta0+30, took the signed difference, then averaged the three and used
their spread as the error. That pairing carries no physical meaning, and
lateral position is not noise. A rod diffuses laterally far faster than it
desorbs, so each registry reaches its own best lateral position.

New quantity. For each (unit, cation, registry), take the minimum
interaction energy over placements. The margin is
E_min(theta0+30) - E_min(theta0). Get its uncertainty from a bootstrap over
placements, 10,000 replicates. Gate F1 stays |margin| >= 3 SE. The
threshold does not move.

Also report, per system, the convergence of each minimum against the number
of placements. A minimum still falling at the last placement is not
converged, and that system is reported as undetermined rather than passed.

## 3. Step 1, free reanalysis before any new run
Recompute the margin from the 24 completed dev runs under the new
estimator, using the 3 placements you already have. Write
truth/F1_REESTIMATE.md with both estimators per system, note that 3
placements sample a minimum poorly, and push.

Proceed to step 2 either way. Step 1 is evidence, not a gate.

## 4. Step 2, match the reference protocol to the FM protocol
Today the reference runs solvated dynamics and the FM runs rigid
placements in vacuum, so two things differ at once and Gate F2 cannot
isolate the energy function. Make them differ in one thing only.

New reference protocol, fragment scale, both cations, dev and test:
1. Same IFF v1.5 muscovite slabs and same capped fragments.
2. 30 rigid placements per registry, sampled over the surface lateral unit
   cell with a logged quasi-random sequence and a fixed seed.
3. Per placement, minimize with the framework heavy atoms fixed and the
   surface cations plus the protein mobile. No water. No dynamics.
4. Keep the minimum per registry, then apply section 2.

The FM path keeps its own placement count and relaxation and differs only
by using UMA in place of IFF. Use the identical placement set for both
paths.

Disclose that the reference no longer includes explicit water, and state in
the manual and the report that interfacial water is known to matter at this
interface, so the reference is a self-consistent citable reference and not
a claim about experiment. This replaces the solvated protocol in
PREREG_EFFECTIVE.md for v8.

Keep the 24 solvated runs and their analysis as recorded. Nothing is
deleted.

Then report Gate F1 on the 4 dev systems. If it passes, run the test
systems, run the dev FM path, set the band, report Gate F2, and continue
into V8-4 as pre-registered.

## 5. Step 3, scope the rods, do not run them
Only if Gate F1 fails at fragment scale.

Build one 18-repeat U0 rod on K+ muscovite with the section 4 protocol.
Time it and stop. Report atom count, wall time per placement, projected
wall time for the full set across the two usable GPUs, and peak memory. Do
not start a production set. Write truth/ROD_SCOPE.md, push, and stop for
David.

## 6. Stop rule
v8 gets this one iteration. If Gate F1 fails at fragment scale and the rod
scoping shows the full set needs more than 48 GPU hours, stop and write
v8/NEGATIVE_RESULT.md: what was built, what the gates showed, why protein
to crystal registry energies resist this benchmark at reachable cost, and
what would change the answer. That document is a real v8 deliverable, not
a failure report.

## 7. Compute and housekeeping
1. Another process held about 68 GB on host B1's GPU all night. Check once,
   report what you see, and never signal it. If it clears, use B1.
2. Delete the leftover demo and adapter state under ~/v8_state that you
   flagged, and keep the server on 8881.
3. Isolation, credentials, anonymity, 2 concurrent episodes and the
   FM-blind rules all stay as in PREREG_EFFECTIVE.md.
4. Push after each step with STATUS.md updated, and at least every 90
   minutes while a job runs.

## 8. Stays open, not fixed now
V8-X9 partial instrument calibration, V8-X11 the two weak validate_d rows,
and Q1 to Q6. List each in the next report.
