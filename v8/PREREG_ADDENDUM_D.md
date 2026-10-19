# v8 pre-registration addendum D (V8-X6)

Pushed before any truth run. Verbatim from David's note below.

---

# PROMPT CHANGE: v8 overnight run (David, 2026-10-19), addendum D

To the v8 builder session. David is offline until morning. Work unattended through as much of V8-1 to V8-7 as the rules allow, and never wait for a reply.

## 0. First, before any truth run
1. Log this note as V8-X6 and push `v8/PREREG_ADDENDUM_D.md` with it verbatim.
2. Regenerate `v8/PREREG_EFFECTIVE.md`, closing its open points with section 1 below, and push.
3. Every rule in `PREREG_EFFECTIVE.md` stays in force unless this note changes it.

## 1. Answers to the open points
1. **Count reading.**
   - A design belongs to the U0 family when at least one inner block lies within 2 mismatches of U0 (16 of 20, as amendment C states).
   - The strict reading (every inner block within 2) picks the rod source only: build U0 rods from mica18 if it passes the strict reading, else from the longest design that does.
   - Gate S is unaffected, since test uses only C2 to C4.
   - Record both counts in `SUPPLY.md`.
2. **Muscovite structure.**
   - Use the muscovite surface model shipped in the IFF v1.5 repository if it exists, with its charges, hydroxyl hydrogens and K+ layer.
   - If it does not exist, use COD 1100011. Place the OH hydrogens at 0.97 Å along the standard hydroxyl orientation, then relax only the hydrogens under IFF with every heavy atom fixed.
   - Either way, check the cell against the literature 2M1 values (a 5.19, b 9.03, c 20.1 Å, β 95.8°, each within 1 %) and the composition. Record the source, hash and checks in `SUPPLY.md`, and push.

## 2. Unattended operating rules
1. **Three tracks run in parallel** (section 3). A stop halts only its own track, and the other tracks continue.
2. **Feasibility problems** use the fallbacks in section 4 and get logged. They never stop the session.
3. **Scientific gates** (F1, F2, the exemplar rows, W and I) stop their track when they fail, as pre-registered. Report the failure, then continue the other tracks.
4. **Open questions.** When no rule settles a question, take the option that keeps FM blindness and the gates intact, log it in `v8/OPEN_QUESTIONS.md` as a deviation candidate, and continue.
5. **Pushes.** Push after every sub-step with `STATUS.md` updated, and at least every 90 minutes while any job runs.
6. **Rules that carry over.** Isolation, credentials, anonymity, pacing and FM-blind rules stay as in `PREREG_EFFECTIVE.md`. Never write a credential into any file. Use no Opus subagents.
7. **Morning brief.** When every track has finished or stopped, write `v8/MORNING.md`: one page with what ran, each gate's result, every deviation, the open questions and the next action for David. Push it last.

## 3. Tracks

### Track 1: truth and FM (GPU)
Use host A node 1, host A node 2 (reached from host A) and host B node 1, one v8 GPU job per node, each after the nvidia-smi check. Host B node 2 stays unused.
1. Build the K+ and Na+ muscovite (001) slabs, and push.
2. **Dev truth first:** U0 and C1 on K+ and Na+, with 2 registries and 3 placements each, as V8-1 specifies. Push after each run. Then report Gate F1 on U0 and C1 for both cations.
3. **Test truth:** C2, C3 and C4 on K+ and Na+. Push after each run, and apply amendment C item 7.
4. **FM path, on dev only** (UMA OMol head primary, OMat logged): ESMFold geometry, 30 rigid placements per registry, relax, keep the minimum. Then set the band m* and report Gate F2.
5. Write `TRUTH_TABLE.json`, `FM_DEV.json` and `F_REPORT.md`, and push V8-1.

**Throughput rule.** Measure ns per day on the first run. If the whole truth set would need more than 24 GPU hours across the three nodes, halve the production for every run (1 ns, averaging the last 0.5 ns) and log it. Never mix protocols between runs.

**Storage.** Write MD output as energies every 10 ps plus the final frame only.

### Track 2: instrument (CPU, host A node 1)
Run V8-2 in full and push after each sub-step:
- the sampler
- rendering: afmize renders the U0 rods from the section 1 source, and the C1 to C4 rods are tiled at 14 and 18 repeats
- the lattice scan
- calibration
- the cost model
- the fit statistic
- the simulator tool

### Track 3: graph, server, manual (CPU)
Run V8-3 in full, including the graph I tests. The manual holds placeholders for the band and the reliability table until Track 1 delivers them, then fills them in. Push.

### Joins
1. **V8-4 exemplar** starts once Track 1 has dev truth and dev FM values and Tracks 2 and 3 are done.
2. **V8-5** starts once V8-4 passes and test truth exists. The FM touches test systems only after the freeze.
3. **V8-6** runs only if every gate through V8-5 passes and the 4-episode smoke test passes, at 2 concurrent episodes. Then write the V8-7 report.

## 4. Pre-written fallbacks (feasibility)
1. **IFF assembly fails** within its one-day timebox: write the CHARMM-GUI sheet and stop Track 1. Tracks 2 and 3 continue.
2. **Na+ assembly fails:** finish the K+ truth, then apply amendment C item 7. Three test systems on K+ fall below four, so Track 1 stops after reporting the K+ results.
3. **Calibration data unreachable** from every node: use the instrument values reported in those papers' Methods as nuisance ranges, label the instrument "uncalibrated", log a deviation and continue.
4. **A world fails the bars:** redraw its hidden nuisances up to 3 times with logged seeds. This selection is truth-only and FM-blind. A rod system whose twins still fail leaves the pilot and the report lists it. Gate W passes when every remaining rod system has both twins through the bars and at least 8 rod systems (16 worlds) remain. Otherwise stop that track.
5. **A job dies** (out of memory or a node reboot): restart it once from scratch with the same seed and log it. After a second failure, move it once to another node. After a third, mark it failed and report it.

## 5. Out of scope tonight
Everything that `PREREG_EFFECTIVE.md` lists as out of scope, any change under `v6/` or `v7/`, and any change outside `v8/`, `~/v8env`, `~/v8_state` and `~/v8_data`.
