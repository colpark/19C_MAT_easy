# v8 negative result: registry claim I has no measurable energy signature under CHARMM36+IFF

**Written under amendment F item 7. Gate F1 failed on the rod — 1 of 4 systems pass against the 3 of 4 required — so v8 ends here.**

v8 asked whether a protein foundation model and a materials foundation model can be made to
compose at a protein-on-crystal interface, with simulated AFM as the lab and registry claim I
as the claim: *protein rods lie in the registry where their carboxylate array matches the
surface cation sublattice.* Everything the benchmark needs around that claim was built and
passes. The claim's **truth layer** does not exist: under CHARMM36 + INTERFACE FF v1.5 the
interaction energy does not distinguish the matched registry from the registry 30 degrees
away, at any scale v8 could reach, under either estimator, under either protocol.

This is a finding about the force field and the claim, not about the benchmark machinery.

## 1. The result in one table

Gate F1 is `|margin| >= 3 SE`. A **positive** margin means the matched registry theta0 is
favoured, which is what registry claim I predicts. Margins in kJ/mol.

| Scale | System | Solvated, paired | Solvated, minimum | Rigid, minimum | Rigid rod, minimum | Rigid rod, paired |
|---|---|---|---|---|---|---|
| fragment, 9 acidic | HRm-ea / K+ | +81.3 +/- 173.5 (0.47) | -218.5 +/- 190.7 (1.15) | +172.2 +/- 160.4 (1.07) | - | - |
| fragment, 9 acidic | HRm-ea / Na+ | +47.1 +/- 83.8 (0.56) | -35.3 +/- 214.6 (0.16) | -127.0 +/- 153.5 (0.83) | - | - |
| fragment, 9 acidic | HRm-60 / K+ | +110.7 +/- 181.0 (0.61) | +67.8 +/- 128.1 (0.53) | -85.7 +/- 109.0 (0.79) | - | - |
| fragment, 9 acidic | HRm-60 / Na+ | -71.7 +/- 173.9 (0.41) | -63.7 +/- 169.6 (0.38) | +221.8 +/- 176.3 (1.26) | - | - |
| rod 14, 131 acidic | HRm-ea / K+ | - | - | - | **+223.9 +/- 415.7 (0.54)** | +338.8 +/- 183.8 (1.84) |
| rod 14, 131 acidic | HRm-ea / Na+ | - | - | - | **-1194.2 +/- 681.2 (1.75, undetermined)** | -1075.5 +/- 208.5 (5.16) |
| rod 18, 171 acidic | HRm-ea / K+ | - | - | - | **+2036.1 +/- 482.0 (4.22, PASS)** | -107.0 +/- 272.7 (0.39) |
| rod 18, 171 acidic | HRm-ea / Na+ | - | - | - | **-961.8 +/- 402.2 (2.39, undetermined)** | -501.4 +/- 294.2 (1.70) |

**Gate F1: FAILED.** 0 of 4 at fragment scale under three estimator-protocol combinations;
**1 of 4 at rod scale**, needing 3 of 4.

**Disclosure of estimator order (amendment E item 2).** The **paired** estimator came first and
was pre-registered in V8-1. The **minimum over placements** estimator is **post hoc**, adopted
after the fragment failure on the physical argument that lateral position is not noise. Both
appear side by side everywhere a margin appears, here and in every earlier report.

**Disclosure of protocol (amendment E item 4).** The rigid-placement reference carries **no
explicit water**. The solvated protocol is the one pre-registered in V8-1; the rigid one was
added to match what an FM path could see. `MANUAL_I.md` states this.

## 2. Three ways the rod result fails, beyond the gate count

**2.1 The sign is not consistent, and Gate F1 cannot see that.** Gate F1 tests magnitude,
`|margin| >= 3 SE`. It is a detection test, not a direction test. Both Na+ rods prefer the
registry 30 degrees **away** from the carboxylate match, and the 14-repeat Na+ rod does so at
**5.16 sigma** under the pre-registered paired estimator. Had the gate been evaluated on the
paired estimator and magnitude alone, that system would have been scored a pass **while
contradicting the claim it was built to test.** The cation, not the carboxylate match, decides
which registry wins: K+ favours theta0, Na+ favours theta0+30, at both lengths.

**2.2 The two estimators disagree on sign, on identical data.** On the 18-repeat K+ rod the
minimum estimator reads **+2036.1 (4.22 sigma)** and the paired estimator **-107.0 (0.39
sigma)**. Both are correct about different questions: theta0 has the single deepest well of the
128 placements, while averaged over lateral offsets theta0+30 is marginally lower. The one
system that passes the gate passes on an estimator chosen after seeing a failure, and the
pre-registered estimator on the same run shows no signal and the opposite sign. I do not treat
that as evidence for the claim.

**2.3 The minimum is still not saturated for Na+.** 64 placements per registry, zero cap hits,
every placement converged on tolerance. Yet both Na+ systems are **undetermined** under the
pre-registered convergence rule: the running minimum of the theta0+30 registry last improved at
placement 48 of 64 (rod 14) and 52 of 64 (rod 18). More placements would move those margins.

## 3. The quantitative mechanism

The claim fails because **a lateral slide costs more energy than the 30 degree rotation the
claim is about**, and this does not improve with rod length.

| Scale | acidic residues | within-registry energy span | margin | span/margin |
|---|---|---|---|---|
| one capped 50-residue repeat | 9 | 1000 to 1500 | 86 to 222 | ~7x |
| 14-repeat rod | 131 | 4471 to 5701 | 224 to 1194 | ~5 to 22x |
| 18-repeat rod | 171 | 4514 to 8975 | 962 to 2036 | ~3 to 7x |

Surface cation rows are **5.2 A** apart. Sliding the adsorbate by a fraction of that spacing
changes the interaction energy by thousands of kJ/mol; rotating it by 30 degrees changes it by
hundreds. Going from 9 to 171 acidic residues — a factor 19 — raised the margin by 1.5x to 13x
but raised the bootstrap error on a minimum over a wide distribution by 3x to 4x, because the
error tracks the width of the within-registry distribution. The mean `|margin|/SE` across
systems went from **0.99** at fragment scale to **2.23** at rod scale. The rod helps. It does
not help enough, and it does not fix the direction.

**The geometric premise is satisfied; the energy simply does not follow it.** The theta0 scan is
not degenerate and it does discriminate the two registries: the carboxylate-cation Gaussian
overlap score is **102.4 at theta0 against 81.4 at theta0+30 (79%)** for the 14-repeat rod and
**124.5 against 95.3 (77%)** for the 18-repeat rod. So the structure really does sit in a
geometrically better match at theta0, by about a quarter in overlap, and the force field still
ranks the registries by cation identity instead. That is the sharpest form of the negative
result: **registry claim I is geometrically true of these structures and energetically invisible
to this force field.**

## 4. The item 5 scaling diagnostic, reported plainly

If the physical story held, `|margin(18)|` should exceed `|margin(14)|`.

| Cation | &#124;margin(14)&#124; | &#124;margin(18)&#124; | ratio | same sign | verdict |
|---|---|---|---|---|---|
| K+ | 223.9 | 2036.1 | **9.09** | yes (both +) | **holds** |
| Na+ | 1194.2 | 961.8 | **0.81** | yes (both -) | **does not hold** |

**It holds for K+ and fails for Na+.** This is one of two, not a confirmation. As you said, a
failure here undercuts the rod argument regardless of the gate, and for Na+ it failed: a longer
rod with 40 more acidic residues produced a *smaller* preference, and a preference for the wrong
registry at both lengths. The honest reading of this diagnostic is that length is not the
controlling variable; cation identity is.

## 5. What was built, verified, and is reusable

Nothing below depends on registry claim I being true. All of it stands.

| Component | State |
|---|---|
| **Gate S (supply)** | **PASSED**. `truth/SUPPLY.md`. Family reading 16 of 20 designs, strict reading 10 of 20, both recorded; dev (U0, C1) and test (C2, C3, C4) disjoint; dev 2 units, test 3. |
| **Truth pipeline** | A Materials Studio IFF v1.5 CAR/MDF model turned into a running OpenMM system: `truth/iff_slab.py`, both `<NonbondedForce>` and `<LennardJonesForce>` blocks (V8-E7), net charge 0.0000, cell within 0.3% of 2M1 literature. K+ and Na+ muscovite slabs at two sizes. |
| **CHARMM36 caps** | `truth/caps_charmm36.xml`, neutral ACE/NME built from charmm36.xml's own NMA residue split at the amide bond, each half exactly neutral (V8-E8). |
| **Solvated protocol** | `truth/run_truth.py`: clash-aware solvation (V8-E10), frozen-pair exclusions (V8-E11), 1 fs. 24 of 24 dev runs completed. |
| **Rigid reference** | `truth/run_ref.py`: shared Sobol placement set, per-placement convergence recording, 20,000 cap. 0.4 min per fragment placement against 16.4 min per solvated run. |
| **Validity check** | `truth/validity.py` (amendment F item 3), general from now on. Refuses any structure with a heavy-atom pair below 1.0 A. It refuses the tiled rods and passes all four production structures. |
| **Instrument (V8-2)** | Complete. `ALL WORLD TESTS PASSED`. von Mises world sampler, afmize rendering, Villarrubia tip dilation, cost model, fitter. Partly uncalibrated (V8-X9). |
| **Graph, server, manual (V8-3)** | Complete. `spec/graph_I.json`, `mcenv/server8.py`, `MANUAL_I.md`. All suites pass. |
| **Validation suite** | `validate_d` **passes on every row**, hold included, on the demo worlds — after the Q7 fix. Two rows remain weaker than they read (V8-X11). |
| **Kit integrity** | Kit B, kit D and graph I tests pass; every kit file byte-identical to v6 at `a1751aaff`. |
| **Adapters** | Graph I executes end to end against the server; gold gives SUPPORTED on demo A and REFUTED on demo B, matching keys. |

**The instrument, the graph, the server and the validation suite all pass and are reusable.**
What is missing is a claim whose truth layer has a signal. Point this machinery at a different
claim and the benchmark works.

**FM blindness is intact and complete.** No FM call and no LLM contact touched any dev or test
system at any point. The only FM calls in v8 are the V8-0 install probes, on a water box and a
public lysozyme sequence. Gate F2 was never reached, so no FM energy was ever compared to truth.

**Spend: $0.** No paid API call was made.

## 6. Which prescriptions were wrong, and why

**Yours, the two you recorded, both confirmed by this iteration.**

1. **The minimum-over-placements estimator did not recover a signal.** It changed the sign of
   two of four fragment margins without crossing threshold, and at rod scale it disagrees in
   sign with the pre-registered estimator on the one system that passes. The estimator was a
   reasonable response to the failure — lateral position genuinely is not noise — but the
   problem was never the estimator. It was that the within-registry distribution is 3 to 20
   times wider than the quantity to be read off its edge, so a minimum over any affordable
   number of draws carries an error the size of the margin.
2. **The rigid screw transform of amendment C item 4 is the wrong way to build a force-field
   rod.** It reproduces the local repeat relationship to 0.011 A RMSD and still produces 102
   heavy-atom pairs below 1.0 A (minimum 0.436 A, between side chains of repeats about 65
   residues apart), because it carries side-chain rotamers along unchanged. The energy overflows
   and OpenMM cannot add hydrogens (V8-E14). Amendment F item 3's validity check is the rule
   that should have governed amendment C, and it now does.

A third, smaller one: **amendment B's fluorophlogopite** had no IFF parameters at all, so Gate
F1 on that substrate was reported FAILED and not patched. Na+ muscovite replaced it. That
decision was yours and it was right.

**Mine.**

3. **The 0.35 GPU hour projection in amendment F item 7 came from my own bad number.** My rod
   scoping recorded no energies and used a 2000-iteration cap, so its 2.46 s per placement was
   a lower bound on an unconverged minimisation. The real figure is 21 s per placement and
   **3.24 GPU hours** for the four systems, inside your 4-hour limit but ten times the estimate
   I gave you. Rod minimisations need 1,126 to 7,640 iterations; the 2000 cap truncated all of
   them.
4. **V8-E17**: my cap test was off by one (`>= cap` rather than `>= cap - 1`), so it reported
   zero cap hits when every rod placement had hit the cap. This is the error that would have
   let an unconverged rod result reach a gate. Amendment F item 4.3 is what forced me to look.
5. **V8-E15**: my first Q7 registry label assumed the registries sit at 0 and 30 degrees from a
   lattice row. They sit at theta and theta+30 for a design-dependent theta. Caught before it
   reached a gate.
6. **V8-E4**: I read a README download on a gated HF repo as access when the checkpoint still
   403'd.
7. **V8-E18**: the logged placement count was hardwired to 30 in the run headers while the runs
   drew 64. Results unaffected; code fixed.

## 7. What would change the answer

In rough order of how much I believe in it.

1. **A different claim on the same instrument.** Binding *orientation* relative to the lattice
   is measurable by AFM and has a large energy signature — adsorbed versus not, or along versus
   across a step edge. Registry claim I asks the force field to resolve a 30 degree rotation
   against a lateral-slide landscape an order of magnitude deeper. The instrument does not care
   which claim it images.
2. **A free-energy difference rather than a minimised interaction energy.** The quantity the
   claim is really about is `Delta G` between two registry basins with the adsorbate free to
   slide within each. That is umbrella sampling or metadynamics along the lateral coordinate,
   not a minimum over placements: 10 to 100x the compute, and it would integrate out exactly the
   nuisance that defeats this measurement instead of sampling its edge.
3. **Many more placements.** Both Na+ systems are undetermined with the running minimum still
   falling at placement 48 to 52 of 64. 256 to 1024 placements per registry would settle the
   minima, at 1.2 to 5 GPU hours per system. I expect this to sharpen the margins and leave the
   direction inconsistency standing, because the direction is set by the cation.
4. **A different force field.** The result is a statement about CHARMM36 + IFF v1.5 with these
   charges. A polarisable water and ion model, or a *ab initio*-level treatment of the
   carboxylate-cation contact, could rank the registries differently. This is also exactly what
   UMA was supposed to test, and Gate F2 was never reached.
5. **Clash-free control rods.** Needed for a pilot of the pre-registered size, but they would
   not change the physics: U0's own rods already fail.

## 8. What a later attempt should do differently

1. **Measure the nuisance before pre-registering the signal.** One afternoon of fragment
   placements would have shown the within-registry span is 10x the margin, before any of the
   instrument, graph or server was built. A one-line pre-flight — *compute the spread of the
   quantity you intend to take an extremum of* — would have redirected v8 at the start.
2. **Make every gate a direction test when the claim has a direction.** `|margin| >= 3 SE`
   scored a system as a pass while it contradicted the claim. Write the gate as
   `margin >= 3 SE` with the sign fixed by the claim, and report the two-sided magnitude
   separately.
3. **Fix the estimator before seeing data, and if you change it, report both forever.** Doing
   so here is what let the sign disagreement in section 2.2 be visible rather than flattering.
4. **Validity-check every structure at the point of construction, not at the point of use.**
   Amendment F item 3 is cheap, general, and would have caught V8-E14 three stages earlier.
5. **Verify convergence by recording it, never by assuming a cap is generous.** Record exit
   iteration and gradient norm per placement from the first run. Both of my cost estimates were
   wrong in the same direction because the first runs recorded neither.
6. **Build the truth layer before the benchmark around it.** v8's instrument, graph, server and
   validation suite are good work spent on a claim that had no signal. The order should be
   truth, then gate, then instrument.

## 9. UMA timing (amendment F item 6)

A cost measurement on a dev system. **No energy was recorded as a margin and no matched angle
was computed from it.**

**UMA cannot hold a system of this size on this hardware. It was killed by the kernel OOM
killer before the first single point completed.** That is the item 6 finding.

| Quantity | Value |
|---|---|
| System | 18-repeat U0 rod on K+ muscovite, heavy atoms only |
| Atoms | **40,486** (34,020 slab + 6,466 rod) |
| Model | `uma-s-1p2`, OMol head, device `cuda` |
| Build time | 0.74 s |
| Outcome | **killed, rc 137 (SIGKILL)** after 6 min 52 s |
| Kernel record | `Out of memory: Killed process 3871571 (python) total-vm:138195220kB` |
| Machine memory | 125,489,512 kB total (GB10 unified, so host and GPU share it) |
| Single point | **never completed** |
| Relaxation step | never attempted |
| Energy recorded | **none** — and none would have been used as a margin |

The process reached 138 GB of virtual address space against 125 GB of total unified memory and
was killed during the first forward pass, after `torch.compile` finished. It died by signal, so
the script's own exception handler never ran and no JSON was written; the log and the kernel
record are the evidence. The same OOM event also killed an unrelated browser process belonging
to the user session — collateral from a global OOM, not anything v8 signalled. **v8 signalled no
process it did not start, here or anywhere.**

Two notes for whoever reaches Gate F2:

- **The slab dominates.** 34,020 of the 40,486 atoms are substrate. The adsorbate is 16% of the
  system, so the cost is set almost entirely by how much mica the reference needs. An FM path at
  this scale needs a smaller slab, a cutoff-based decomposition, or an embedding scheme — not a
  bigger machine.
- **This is a hardware and system-size finding, not a verdict on UMA's accuracy.** Gate F2 was
  never reached and no UMA energy was ever compared with truth. Whether UMA ranks these
  registries correctly remains untested, and section 7 item 4 is where that question lives.
- **The atom count differs from the OpenMM one** (40,486 against 46,946) because the FM path
  takes heavy atoms only while the force-field system carries hydrogens.

## 10. Still open, not fixed

- **V8-X9** — the instrument is **partly uncalibrated**. Both calibration DOIs resolved; the raw
  AFM images of 10.1038/s41467-026-76923-4 set the noise scale (0.003 to 0.09 nm), but
  10.1038/s41467-026-69170-0 supplied no raw images, tip radius, line rate or drift, so those
  are assumed. `world/CALIBRATION.md` labels it so.
- **V8-X11** — two `validate_d` rows are weaker than they read: non-bypass's panel clause is
  asserted rather than measured, since no panel run exists for the demo worlds, and faithfulness
  uses a templated rendering rather than the renderer. Both need redoing on real worlds.
- **Q1** Na+ exchanged on both basal surfaces, not one. **Q2** framework frozen with mobile
  surface cations. **Q3** the PME interaction-energy decomposition. **Q4** theta0's geometric
  criterion. **Q5** the flip arm is not disclosed in the manual. **Q6** 14-repeat control rods
  reach aspect 3.82, not 4. All in `OPEN_QUESTIONS.md`. **None of them relaxes a gate, and none
  of them explains this result** — Q1 to Q4 would shift margins by tens of kJ/mol against a
  nuisance span of thousands.
- Isolation, credentials, anonymity, 2 concurrent episodes and FM-blind selection were held
  throughout and are unchanged.

## 11. Machine state at the stop

- Nothing of v8's is running except the server on port 8881, which holds **demo worlds only**.
- Host B1's GPU is still held by a 7-day vLLM process that v8 did not start. It was checked
  once, reported, and **never signalled**.
- All 24 solvated runs, the fragment rigid runs and the four rod runs are kept as recorded.
  Nothing was deleted. Writes stayed under `v8/`, `~/v8env`, `~/v8_state` and `~/v8_data`.
  No file under `v6/` or `v7/` was changed, and no v7 artefact was read after amendment A.

**v8 ends here, as amendment F item 7 pre-registers.** The registry margin does not exist at
fragment scale, does not exist consistently at rod scale, and points the wrong way for Na+. The
benchmark machinery is sound and waits for a claim with a signal.
