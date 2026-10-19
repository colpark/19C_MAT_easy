# v8 pre-registration addendum A (V8-X2)

Pushed before any V8-1 truth or FM work. Verbatim from David's note below.

---

# PROMPT CHANGE: v8 amendment A (David, 2026-10-18), replaces Change 1

To the v8 builder session. Log this as deviation V8-X2. Push
v8/PREREG_ADDENDUM_A.md with this note verbatim before any V8-1 truth or
FM work. If V8-1 work has already started, first report exactly what ran,
listing the systems and any FM call on a test fragment. Gates and
expectations stay as pre-registered except where this note changes them.

1. Withdraw Change 1. UMA access was granted at 01:17Z. Keep uma-s-1p2 as
   pre-registered, with the OMol head primary and the OMat head as the
   logged alternative. Do not switch to MACE-MH-1 or Orb. If any part of
   Change 1 was applied, revert it and log the revert.

2. v7 provenance (record only, no rebuild). Log the following as V8-X2:
   - v8's base is the V7-0 commit 10aee1e18, and the kit files came from
     the v7 working tree.
   - Every kit B file in v8/ is byte-identical to v6/ at a1751aaff, and
     every kit D file matches the kit D hash prefixes.
   - From now on, v8/spec and v8/graphexec are v8's own frozen copy. Never
     read, copy, import or wait on anything from v7 again: its files,
     branch, working tree, servers or state. No rebase, no merge.

3. Runtime isolation from v7 (v7 runs in parallel), for the rest of v8:
   - Run the kit tests under ~/v8env (install jsonschema>=4.18 there), and
     stop using ~/v5env.
   - Write only under v8/, ~/v8env, ~/v8_state and ~/v8_data. Servers use
     ports 8881 to 8889, each checked free first.
   - Use PID files. Never signal or renice a process v8 did not start.
   - Before each GPU job, check nvidia-smi. If another process holds over
     half the GPU memory, wait and poll every 10 minutes from a background
     job. Run at most one v8 GPU job per node, and launch every v8 compute
     job with nice -n 10.
   - Pace Claude episodes at 2 concurrent (this replaces 4). v7 shares the
     subscription.
   - Git. Never run gc, prune or repack, and never check out or commit in
     another worktree. Log v8's working path and git dir once in LOG.md.

4. FM-blind fix. Hard rule 1 forbids FM contact with a system before its
   freeze, while V8-1 runs the FM on test fragments. Resolve the
   contradiction in favor of hard rule 1:
   - Before the freeze, run the FM path on dev fragments only, and write
     v8/truth/FM_DEV.json.
   - Gate F2 becomes: outside m*, the FM's sign agrees with IFF on at least
     80 % of dev points. Drop the clause "at least one test system falls
     outside m*", and report that count after the freeze instead.
   - V8-4 exemplar: pick the dev system with the largest |IFF margin| in
     standard errors, chosen on truth only, and run the FM-adapter rows on
     that dev system.
   - V8-5: run the FM path on the test systems only after the freeze, then
     write v8/truth/FM_TEST.json and report FM status per system.
   - If an FM call already touched a test fragment, keep its output sealed
     and unread until the freeze, and disclose it.

5. Gate S (supply) and the band rule.
   - List the designs and their repeat units in v8/truth/SUPPLY.md. Dev is
     the honeycomb series plus one charge-control variant, and test is all
     the others. Stop for David unless test holds at least 6 designs and
     dev at least 2 distinct repeat units.
   - σ_FM is the RMS of (FM margin minus IFF margin) over the dev points
     (fragment, substrate and placement).
   - m* = max(2 σ_FM, the empirical bound). Compute the empirical bound
     only if at least 10 dev points exist. Report n and the bootstrap
     interval.

6. Sequences. Take sequences from the design PDB files on GitHub.
   Supplementary Table 2 is a cross-check only.

7. Disclosure. This amendment came after V8-0 and before any truth, world
   or FM output. Cite V8-X2 in the report.
