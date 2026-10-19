# V8-1 feasibility report: Gate F1 FAILED, Track 1 stopped

**Gate F1 is reported as failed, not relaxed.** No bar, threshold or protocol was adjusted after seeing these numbers. Track 1 (truth and FM) stops here under addendum D item 2.3; tracks 2 and 3 finished and are reported separately.

## Result

Gate F1 requires `|IFF margin| >= 3 standard errors` for the dev units (U0 = HRm-ea, C1 = HRm-60) on both surface cations (amendment C item 6, amendment B item 2). All four dev systems fail, none above 0.61 sigma.

| System | theta0 | Margin (kJ/mol) | SE | SE from placements | SE from blocks | n sigma | Truth exists |
|---|---|---|---|---|---|---|---|
| HRm-ea / K+ | 187 | +81.3 | 173.5 | 169.7 | 36.3 | 0.47 | no |
| HRm-ea / Na+ | 187 | +47.1 | 83.8 | 52.0 | 65.7 | 0.56 | no |
| HRm-60 / K+ | 190 | +110.7 | 181.0 | 178.0 | 32.6 | 0.61 | no |
| HRm-60 / Na+ | 190 | −71.7 | 173.9 | 160.5 | 66.8 | 0.41 | no |

24 of 24 dev runs completed (2 units x 2 cations x 2 registries x 3 placements). Fluorophlogopite's Gate F1 was already reported as failed for lack of IFF parameters (amendment B item 1), so that line stands unchanged.

## Why it failed: the margin's sign is not stable across placements

This is risk R2 realised, and more sharply than the risk was written. The three in-plane placements of one system do not merely scatter around a common margin; they disagree in sign:

| System | Margin per placement (kJ/mol) |
|---|---|
| HRm-ea / K+ | −219, +369, +93 |
| HRm-ea / Na+ | −35, +143, +33 |
| HRm-60 / K+ | +371, +191, −230 |
| HRm-60 / Na+ | +202, −354, −64 |

Three of the four systems contain both signs. So at one-repeat scale, theta_match is not a poorly-measured quantity: by this protocol it is **not well defined**. Which registry is lower depends more on where the fragment sits laterally, shifted by a third of a surface lattice vector, than on the 30 degree rotation that defines the claim.

The error decomposition says the same thing. The standard error is dominated by the spread over placements (52 to 178 kJ/mol), not by the sampling error within a run (33 to 67 kJ/mol from 5 blocks over the last 0.5 ns). Longer production would therefore not rescue the gate: it shrinks the smaller of the two terms. The individual runs are well behaved, with per-run interaction energies stable to 7 to 28 kJ/mol.

Two further observations, recorded because they bear on any redesign:

- **Binding strength is cation-dependent and large.** At theta0, HRm-ea gives E_int about −264 to −315 kJ/mol on K+ and about −732 kJ/mol on Na+. The interface is strongly bound; it is only the *difference between registries* that is unresolvable.
- **The geometric criterion that defines the two registries is sound.** The carboxylate-to-cation overlap at theta0 is about twice that at theta0 + 30 degrees (HRm-ea 10.95 against 5.43, HRm-60 9.46 against 3.82; `v8/OPEN_QUESTIONS.md` Q4). The geometry prefers theta0 clearly; the IFF energy of a single capped repeat does not follow it.

## What was not done, and why

- **Test truth** (C2, C3, C4 on both cations): stopped. 2 runs of the HRm-ef slice had completed when Gate F1 was evaluated; they are kept in `~/v8_data/runs` but are not analysed, since a test margin is only meaningful once dev truth exists. Amendment C item 7, which drops a test system below 3 SE, was never reached.
- **The FM path and Gate F2**: stopped before any FM call touched any system. Gate F2 compares the FM's sign against the IFF sign on dev points; with no IFF sign resolved, that comparison would be noise against noise. **FM blindness is therefore intact and complete: no FM call and no LLM contact has touched any dev or test system.** The code is written and benchmarked (`truth/fm_path.py`, 0.82 s per UMA force call on 2877 atoms, about 3.3 GPU hours for the four dev systems) and can run as soon as a truth definition exists.
- **V8-4, V8-5, V8-6, V8-7**: not reached. V8-4 is additionally blocked by `v8/OPEN_QUESTIONS.md` Q7.

## Protocol actually run

As pre-registered except where noted. IFF v1.5 surface model with full charges (muscovite 2M1, cell within 0.3 % of literature on a, b, c and beta, net charge 0.0000), CHARMM36 for the fragment with neutral ACE/NME caps added from the shipped NMA residue (V8-E8), TIP3P water, 100 mM KCl or NaCl of the surface cation. One internal 50-residue repeat per unit, never a design's own cap (the V8-X4 reading). Two registries (theta0 and theta0 + 30 degrees) by the geometric criterion, three in-plane placements each. Minimise, 100 ps equilibration, then NVT at 300 K with the fragment backbone restrained at 5 kcal/mol/A^2; mineral framework frozen, surface cations mobile (Q2). Interaction energy every 10 ps as E(fragment+slab) − E(fragment) − E(slab) on solvent-stripped coordinates in the same box with identical PME (Q3).

Deviations: production is 1 ns averaged over the last 0.5 ns rather than 2 ns over the last 1 ns, under the pre-registered throughput rule, because a 1 fs timestep is required at the fragment-slab interface (V8-E11) and the full set would otherwise exceed 24 GPU hours (V8-X8). Applied uniformly to all 24 runs; no protocol was mixed. Water placed on top of fragment hydrogens by `addSolvent` is deleted before the run (V8-E10), and nonbonded pairs between two frozen framework atoms within 4.5 A are excluded, which changes no force on any mobile atom (V8-E11).

## Options for David (none applied)

Gate F1 failed, so the pre-registered action is to stop and report, which is what this is. If v8 is to continue, the design question is how to make a registry margin that exists at all. In rough order of how directly each addresses the finding above:

1. **Use rods, not single repeats.** The published designs bind as long rods, where many carboxylates engage the lattice coherently and the registry term adds up while the placement term largely cancels. A 14 or 18 repeat rod is what the instrument already renders, so the truth object and the imaged object would also finally be the same thing.
2. **Make the placement average part of the definition.** Define the margin as an average over a proper sample of in-plane offsets, with many more than three, and report its standard error. This is honest but expensive, and with signs flipping it may converge on a margin near zero, which is itself a publishable answer about the fragment scale.
3. **Let the fragment relax laterally** instead of restraining it to a fixed placement, so each registry finds its own best offset. That changes what the margin means and needs a new statement of the claim.
4. **Keep v8 and drop the registry claim** in favour of a claim the fragment scale can support.

I recommend 1, and note it is a change of scope, not a change of gate.
