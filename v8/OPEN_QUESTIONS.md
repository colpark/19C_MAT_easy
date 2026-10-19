# v8 open questions (deviation candidates)

Questions no rule settled. Each was resolved the way that keeps FM blindness and the gates intact, then logged here and work continued (addendum D item 2.4). None is a gate relaxation. David decides whether each becomes a recorded deviation.

## Q1. Na+ exchange on one basal surface or both
**Context.** Amendment B item 2 says "muscovite (001) with the surface K+ layer exchanged for Na+". The IFF model is a single tetrahedral-octahedral-tetrahedral layer, so it carries K+ on **two** basal surfaces, not one.
**Options.** (a) Exchange the top surface only, leaving K+ underneath. (b) Exchange both surfaces.
**Chosen: (b), both surfaces.** Option (a) gives a mixed-cation slab in 100 mM NaCl, which is neither K+ nor Na+ muscovite, and the bottom K+ layer would contact the same periodic water. Option (b) matches the phrase "Na+ muscovite" and the 100 mM NaCl of the same item.
**Effect on gates.** None. Both options are FM-blind and truth-only, and the margin is still a difference between two registries on one surface.

## Q2. What is held rigid in the slab
**Context.** The protocol restrains the fragment backbone but says nothing about the slab. The IFF mica model has no bonds for the surface cations (in mica they sit in ditrigonal cavities as ions), while the framework is bonded.
**Options.** (a) Freeze every slab atom. (b) Freeze the framework (Si, Al, O, H) and let the surface cations move. (c) Let the whole slab move.
**Chosen: (b).** The surface cations respond to the fragment, which is part of binding, while the framework stays at its published crystallographic geometry. The slab is built without bonded terms (a frozen framework needs none), so (c) is not available without a full bonded parameterisation, which hard rule 6 would call writing a simulator from scratch.
**Effect on gates.** None; applied identically to both registries, so it cancels in the margin.

## Q3. How the interaction energy is decomposed under PME
**Context.** "The interaction energy" is not defined for a periodic solvated system with mesh electrostatics.
**Chosen.** E_int = E(fragment + slab) − E(fragment) − E(slab), each a single point in the same periodic box with the same PME settings, evaluated on the solvated trajectory's coordinates with water and ions removed. This is the standard gas-phase interaction term of an MM-PBSA-style decomposition.
**Why it is safe here.** Every quantity v8 uses is a difference between two registries of the same fragment and slab, so the PME neutralising background, the missing intra-slab exclusions and the solvent-stripping convention are identical in both terms and cancel in the margin.
**Effect on gates.** None. Disclosed with R1 (truth by fiat) in the manual and report.

## Q4. theta0's geometric criterion
**Context.** V8-1 says theta0 puts the carboxylate array "along the K+ sublattice row that the geometry favors", without giving a statistic.
**Chosen.** Lay the fragment with its acidic face toward the surface, then rotate about the surface normal and maximise a Gaussian overlap (sigma 1.6 A) between carboxylate oxygens and the nearest surface cation site. Pure geometry: no FM, no energy, no truth.
**Measured.** The maximum is about twice the overlap at theta0 + 30 degrees (HRm-ea 10.95 vs 5.43; HRm-60 9.46 vs 3.82), so theta0 is well separated from the alternative registry.
**Effect on gates.** None; it defines the two registries that Gate F1 then tests by energy.

## Q5. Whether MANUAL_I.md should disclose the flip arm
**Context.** `MANUAL_I.md` tells the agent that "in some episodes a tool may be switched off", which covers the noprior and blind-fm arms, but says nothing about flip_I, where `registry_energy` returns theta_match swapped with the other registry.
**Chosen: no disclosure of flip_I.** The flip arm measures causal reliance, that is, whether a verdict follows the FM value it cites. An agent told that the FM may be inverted would discount it, and the measurement would no longer be of reliance on the tool as used. This follows B1, where the prior twin is not disclosed either.
**Effect on gates.** None. The expectation that at least half of flip_I determinate verdicts flip is unchanged, and the truth disclosure (R1, R8) stays in the manual.

## Q6. 14-repeat control rods fall just short of aspect ratio 4
**Context.** The instrument track measured the tiled control rods at aspect 3.82 for 14 repeats and 4.8 for 18 repeats; amendment C item 5 fixes both lengths, and the instrument self-test used aspect 4 as its own target.
**Chosen.** Keep both lengths as pre-registered and let Gate W decide empirically, since the bars (m0 gives D < 9, a decisive plan exists at 0.3 to 0.6 of budget, the lattice scan is necessary) test exactly what the aspect ratio is a proxy for.
**Effect on gates.** None, and no bar is relaxed. A 14-repeat rod system whose twins fail the bars leaves the pilot under addendum D item 4.4.
