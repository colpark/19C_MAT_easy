# Step 3: rod scoping — timing only, no production set started

Amendment E item 5. One 18-repeat U0 rod on K+ muscovite under the step 2 protocol, timed and stopped. **No production set was started, and no interaction energy was recorded**, so nothing here can be read as truth by any gate. The scoping script computes timings and sizes only.

**Headline: the rod protocol is cheap — about 1 GPU hour for a full set — so the amendment E item 6 stop rule does not trigger on cost. The blocker is geometry: 4 of the 5 units have no usable 18-repeat rod.**

## Timing and size, measured

| Quantity | Value |
|---|---|
| Rod | published 18-repeat U0 chain, capped (900 residues, 171 acidic, 6466 heavy atoms) |
| Slab | IFF mica15_single_layer tiled 9 × 6, 233.6 × 162.3 Å, 34,020 atoms, 1620 surface K+ |
| Box | 23.36 × 16.23 × 9.0 nm |
| Total atoms | **46,946** (rod 12,926 with hydrogens, slab 34,020) |
| Frozen framework atoms | 32,400 (mobile: 14,546, i.e. the rod plus 1620 surface cations) |
| Frozen-pair exclusions | 488,826 |
| θ0 from the rod's own geometry | 182° (the fragment gave 187°) |
| **Minimisation per placement** | **2.46 s** (median of 2; 2.7 and 2.2 s) |
| Set-up, once per system | θ0 scan 0.5 s, Modeller 3.9 s, createSystem 4.5 s, Context 1.6 s |
| Peak host memory (RSS) | 673 MiB |
| GPU memory held by the process | 247 MiB |

## Projected cost of a full rod set

At 30 placements per registry and 2 registries, one (unit, cation) system is 60 minimisations:

| Set | GPU hours | Wall hours across the two usable GPUs |
|---|---|---|
| One (unit, cation) system | 0.041 | — |
| 10 (unit, cation) systems (5 units × 2 cations) | **0.41** | **0.20** |
| The same at both rod lengths (14 and 18 repeats) | **0.82** | **0.41** |

Even multiplying by ten for more placements, longer minimisations or a solvated variant, the full set stays far below the 48 GPU hour threshold in amendment E item 6. Cost is not what stands in the way.

**Two caveats on these numbers.** First, 2.46 s is the time for a minimisation capped at 2000 iterations with a 1 kJ/mol/nm tolerance; because no energies were recorded, I cannot say whether 2000 iterations converges 14,546 mobile atoms, so the per-placement time is a **lower bound** and a converged protocol may need more. Second, the timing is from two placements on one system, so treat it as an order of magnitude rather than a calibrated rate.

## The real blocker: only U0 has a usable rod

The rods the instrument renders were built for **shape**, by tiling one repeat of the published 4H model with a rigid screw transform. That is fine for an AFM stamp and wrong for a force field. Measured on the 18-repeat tiled U0 rod:

- **102 atom pairs closer than 1.0 Å**, minimum separation **0.436 Å** (for example ARG568:CZ against VAL503:CG2, and the same contact recurring at 653/718 and 803/868, one per repeat layer).
- The energy at that geometry overflows, so OpenMM cannot even add hydrogens: "Energy or force at minimization starting point is infinite or NaN".

The clashes sit between side chains of *non-adjacent* repeats, about 65 residues apart. The screw transform reproduces the local repeat-to-repeat relationship to 0.011 Å RMSD, but it carries each repeat's side-chain rotamers along unchanged, and in the real assembly those rotamers adjust where repeat layers meet.

The published 18-repeat U0 chain used for this scoping is, by contrast, clean: **0 pairs below 1.0 Å, nearest-neighbour minimum 1.200 Å**. So:

| Unit | 18-repeat rod available as a force-field reference? |
|---|---|
| U0 (HRm-ea) | **yes** — the published design *is* an 18-repeat rod (20.4 × 4.0 nm, 171 acidic residues) |
| C1 to C4 (HRm-60, HRm-ef, HRm-5d, HRm-f1) | **no** — published only as 4H monomers (6.2 × 4.3 nm); the tiled rods clash and need side-chain repair |

A 14-repeat U0 rod can be cut from the published chain the same way, so U0 is available at both lengths. The four controls would each need a rebuilt rod — repacked side chains at the repeat junctions, then relaxed — before they could carry a reference energy. That is modelling work the v8 prompt did not scope, and amendment C item 4's "rigid screw transform, no new sequence" is exactly the method that produced the clashes.

## Why the rod is still the right direction

The physical argument from Gate F1 holds and the numbers sharpen it. One capped repeat presents **9** acidic residues; the 18-repeat rod presents **171**, about nineteen times as many, against cation rows repeating every 5.2 Å. The registry term should grow roughly with the number of engaged carboxylates while the lateral-offset term stays bounded by one surface unit cell, which is precisely the ratio that defeated the fragment. Nothing here tests that, because no rod energy was computed.

## Where this leaves v8, under amendment E

- Gate F1 **failed** at fragment scale under both estimators and both protocols (`F1_STEP2.md`, `F1_REESTIMATE.md`).
- Rod scoping shows the full set needs about **1 GPU hour**, far below 48, so the item 6 stop rule **does not** trigger and `NEGATIVE_RESULT.md` is not written.
- Item 5 says to time it and stop, so **no production set was started** and this is a stop for David.

The decision now is whether to spend the modelling effort to build four clash-free control rods, or to run the rod reference on U0 alone and accept one unit. U0 alone gives 2 (unit, cation) systems, which is below the 4 that amendment C item 7 requires and below Gate S's test-set requirement of 3 units, so U0 alone cannot carry the pilot as pre-registered.
