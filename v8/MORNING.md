# v8 morning brief (2026-10-19)

Unattended overnight run under addendum D. Branch `v8/2026-10-19`, base V7-0 `10aee1e18`.

**Headline: Gate S passed, Gate F1 FAILED, tracks 2 and 3 finished.** The registry margin does not exist at one-repeat fragment scale (risk R2), so the truth and FM track stopped as pre-registered. Nothing was relaxed anywhere. One decision is waiting for you (Q7) and one question of scope (how to get a margin at all).

## Each gate

| Gate | Result | Where |
|---|---|---|
| Gate S (supply) | **PASSED** | `truth/SUPPLY.md` |
| Gate F1 on fluorophlogopite | **FAILED** (no IFF parameters), not patched | amendment B item 1 |
| Gate F1 on K+ and Na+ muscovite | **FAILED**, 0 of 4 dev systems, none above 0.61 sigma | `truth/F_REPORT.md` |
| Gate F2 (FM informative) | not reached; stopped with Track 1 | `truth/F_REPORT.md` |
| V8-4 exemplar rows | not reached; `validate_d` on demo worlds fails the hold row only | Q7 |
| Gate W, Gate I | not reached | |

Kit B, kit D and graph I tests pass, and every kit file is still byte-identical to v6 at `a1751aaff`.

## What ran

- **V8-0** (earlier): install checks on hosts A1 and B1; UMA access granted at 01:17Z and `uma-s-1p2` verified on both.
- **Gate S**: my own count reproduces amendment C exactly, 16 of 20 designs in the U0 family, 10 under the strict reading; both recorded. mica18 passes strict, so it is the U0 rod source. Dev (U0, C1) and test (C2, C3, C4) share no unit.
- **Muscovite structure**: the IFF v1.5 distribution zip *does* ship mica surface models with charges, hydroxyl hydrogens and the K+ layer, so the first branch of your item 1.2 applied and COD 1100011 was not used. Cell within 0.3 % of 2M1 literature on every parameter; net charge 0.0000.
- **Track 1**: K+ and Na+ slabs built, five capped fragments cut, theta0 fixed geometrically, then **24 of 24 dev truth runs completed** and Gate F1 evaluated. Test truth stopped after 2 runs; the FM path never ran.
- **Track 2 (V8-2)**: instrument complete, `ALL WORLD TESTS PASSED`, verified by me.
- **Track 3 (V8-3)**: graph I, server (port 8881), manual complete; all suites pass, verified by me.
- **Adapters**: graph I executes end to end against the server; gold gives SUPPORTED on a demo A world and REFUTED on a demo B world, matching keys.

**FM blindness is intact and complete.** No FM call and no LLM contact has touched any dev or test system. The only FM calls in v8 are the V8-0 install probes, on a water box and a public lysozyme sequence.

## Why Gate F1 failed (the one scientific finding)

The three in-plane placements of a system disagree in **sign**, not just in size:

| System | Margin per placement (kJ/mol) | Margin | SE | n sigma |
|---|---|---|---|---|
| HRm-ea / K+ | −219, +369, +93 | +81.3 | 173.5 | 0.47 |
| HRm-ea / Na+ | −35, +143, +33 | +47.1 | 83.8 | 0.56 |
| HRm-60 / K+ | +371, +191, −230 | +110.7 | 181.0 | 0.61 |
| HRm-60 / Na+ | +202, −354, −64 | −71.7 | 173.9 | 0.41 |

So theta_match is not badly measured at this scale; by this protocol it is **not well defined**. Which registry is lower depends more on a lateral shift of a third of a lattice vector than on the 30 degree rotation the claim is about. The error is dominated by placement spread (52 to 178 kJ/mol), not by sampling within a run (33 to 67), so longer production would not rescue it. Individual runs are well behaved and the interface is strongly bound (−264 to −315 kJ/mol on K+, about −732 on Na+), and the geometric criterion prefers theta0 about 2:1. It is only the energy difference between registries that vanishes.

## Two things I need from you

1. **Q7, which blocks V8-4** (`OPEN_QUESTIONS.md`). `validate_d` with all rows fails the **hold row only**, on demo worlds. The verdicts held under both perturbations; the row compares the *identified phase*, and graph I stores the fitted rod angle there as text because the frozen schema has no field for a continuous identification (V8-X7). A 5 degree shift under a 17 degree azimuth hold therefore fails string equality while the registry call is unchanged. My recommendation: make `phase` the registry label (matched or other) and leave the angle in `angle_rel_deg`, which maps the kit's existing meaning onto this family rather than editing a row. It is a design change, so I did not make it.
2. **Scope after Gate F1.** Options are in `truth/F_REPORT.md`. My recommendation is to define truth on **rods of 14 or 18 repeats rather than single repeats**: many carboxylates then engage coherently, the registry term adds while the placement term largely cancels, and the truth object becomes the same object the instrument renders. That is a change of scope, not of gate, so it is yours to make.

## Deviations and errors logged tonight

`LOG.md` has all of them. The ones that matter:

- **V8-X8**: a 1 fs timestep is needed at the fragment-slab interface (V8-E11), so the full set would have exceeded 24 GPU hours; your throughput rule triggered and production is 1 ns averaged over the last 0.5 ns, applied uniformly to all 24 runs. No protocol mixed.
- **V8-E10, V8-E11**: the first 12 run attempts all died with NaN. Two causes: `addSolvent` places water on top of fragment hydrogens (0.8 to 1.2 A), and 2 fs is unstable at the interface. Both fixed and verified.
- **V8-E12**: my first drivers were launched so that the PID file named a wrapper, so one survived a stop and briefly ran a second GPU job on host A1. Found, stopped by verified PID, never by pattern. No production run had completed, so nothing was contaminated. Drivers now write their own PID files.
- **V8-E8**: OpenMM's CHARMM36 ships no ACE/NME caps; added from the shipped NMA residue, each cap exactly neutral, no kit file touched.
- **V8-X9**: instrument calibration is partial. Both DOIs resolved, but one paper gave no raw images, tip radius, line rate or drift, so those are assumed and the instrument is labelled partly uncalibrated.
- **V8-X7, V8-X11**: graph I declares `claim_type` "R" because the frozen schema has no "I"; and two `validate_d` rows (non-bypass's panel clause, faithfulness) are weaker than they read and need redoing on real worlds.
- **Q1 to Q6** in `OPEN_QUESTIONS.md`: Na+ exchanged on both basal surfaces; framework frozen with mobile surface cations; the PME interaction-energy decomposition; theta0's criterion; no disclosure of the flip arm; 14-repeat control rods at aspect 3.82. None relaxes a gate.

## Machine state

- Nothing of v8's is running. All drivers and queues exited or were stopped by their own PID files. No process v8 did not start was ever signalled.
- Host B1's GPU was held by another process (about 68 GB) all night, so B1 ran nothing and its test slice never started.
- The v8 server is still up on port 8881 with state in `~/v8_state/server8`; it holds demo worlds only. Leftover test state from the build sits under `~/v8_state/server8` and `~/v8_state/adapters8_*` and can be deleted.
- Data under `~/v8_data`: 26 completed runs in `runs/` and `runs_all/`, slabs, fragments, rods, stamps, calibration downloads. No credential is written anywhere.

## Next action for David

Answer Q7, then choose the scope after Gate F1. Until the second is settled there is no truth for v8, so V8-4 onward cannot start and the 144 episodes of V8-6 are not reachable.
