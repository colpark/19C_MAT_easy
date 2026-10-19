# v6 trace rendering rules

A rendered trace turns one execution log (trace_schema.json) into text a scientist can read in under a page. The log is the source of truth. The text adds wording only.

## Rules
1. One block per executed node, in log order. Skipped nodes get one line ("S2x skipped: the FM margin cleared the band").
2. Each block has four lines:
   - **Thought:** which subgoal, why it is needed, and which earlier outputs it uses.
   - **Action:** the module and the tool call with its key arguments.
   - **Observation:** the outputs.
   - **Check:** the acceptance test with its numbers, and the result.
3. Every numeral in the text must appear in the log or its constants, at the precision shown. `graphexec.number_lock` enforces this. Write small counts as words ("both polymorphs", "two measurements").
4. Name nodes by their graph ids (S1a, S1c, S2). `number_lock` also checks that every id exists.
5. State dependencies explicitly: "S3 joins S1c (the sample holds X) and S2 (Y lies lowest)".
6. Close with a **Verdict** line, then a **Why each step matters** paragraph that cites the validation results: ablation, measurement twin, prior twin and hold.
7. Plain sentences, active voice, no semicolons and no dashes as punctuation. Signed numbers keep their sign.
8. A Sonnet subagent may write the text from the log alone. It sees the log, the graph and these rules, nothing else. Code then runs the number lock. A failed lock means a rewrite, never an edit of the log.

## Skeleton (placeholders in braces come from the log)

**Claim.** {claim}

**Plan (S0).** The claim needs two answers: which polymorph this sample holds, and which polymorph of {formula} lies lowest. Measurement answers the first. The FM answers the second. S3 joins them.

**S1a predict window (simulator).**
Thought: The free scan cannot separate the polymorphs (D {S1c_m0_only.D} on the free scan alone), so I need the window where their patterns differ.
Action: simulate each library polymorph and search the plan grid.
Observation: window {S1a.window}, plan {S1a.plan}, predicted D {S1a.predicted_D} at {S1a.predicted_cost_min} min.
Check: predicted D {S1a.predicted_D} ≥ {D_accept}, accepted.

**S1b measure (instrument).** ...

**S1c identify (fit).** ...

**S2 infer energy (FM).** ...

**S2x escalate to DFT.** skipped: the FM margin {S2.margin} eV/atom cleared the band {band}.

**S3 decide (rule).** ...

**Verdict.** {verdict} (key {key}).

**Why each step matters.** Blanking S1a, S1b, S1c or S2 leaves CANNOT_TELL. The other twin's data flip S1c and the verdict. Flipping the FM ranking with the data fixed flips the verdict. Changing displacement, zero offset or crystallite size changes nothing.
