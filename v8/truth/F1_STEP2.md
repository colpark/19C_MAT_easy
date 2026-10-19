# Step 2: Gate F1 on the matched reference protocol — FAILED

Amendment E item 4. **Gate F1 is reported as failed, not relaxed.** Its threshold, |margin| ≥ 3 SE, did not move. 0 of 4 dev systems pass.

**Disclosure of estimator order (amendment E item 2), repeated as required.** The **paired** estimator came first and was pre-registered in V8-1. The **minimum-over-placements** estimator is second and **post hoc**: David chose it after the paired estimator failed, on the physical ground that lateral position is not noise, since a rod diffuses laterally far faster than it desorbs, so each registry reaches its own best lateral position. Both are reported side by side throughout. This step uses the minimum estimator on a new protocol, so the comparison table below also carries the overnight solvated numbers under both estimators.

**Disclosure of the reference's water (amendment E item 4).** This reference carries **no explicit water**. Interfacial water is known to matter at a protein-mica interface, so this reference is a self-consistent citable reference, not a claim about experiment. It is also why the energies here (−1448 to −2576 kJ/mol) are far deeper than the solvated ones (−272 to −768): without water the carboxylate-to-cation attraction is unscreened. This disclosure belongs in `MANUAL_I.md` and in any later report.

## Protocol actually run

Same IFF v1.5 muscovite slabs (K+ and Na+) and the same capped fragments as before. 30 rigid placements per registry from a scrambled Sobol sequence over the surface lateral unit cell, `scipy.stats.qmc.Sobol(d=4, scramble=True)`, seed 20261019, columns (fractional offset along a, fractional offset along b, rotation about the surface normal within ±6°, height offset in −0.3 to +0.6 Å). **The two registries use the identical placement set, and the FM path will use the same table**, so reference and FM differ only in the energy function. Per placement: minimise with the mineral framework heavy atoms fixed and the surface cations plus the fragment mobile; no water, no dynamics. The interaction energy keeps the solvated runs' decomposition (Q3), E(fragment+slab) − E(fragment) − E(slab) at the minimised geometry, each a single point in the same box with identical PME, and with no frozen-pair exclusions in any of the three terms so the slab self-energy cancels exactly. Minimisation uses a separate complex system that does carry those exclusions, so single-precision force noise cannot drive the minimiser (V8-E11).

Scipy warns that Sobol balance wants a power of two; 30 placements are kept because amendment E fixes that number.

## Result

| System | θ0 | E_min(θ0) | E_min(θ0+30) | Margin (kJ/mol) | SE | 95 % CI | n σ | Converged | Result |
|---|---|---|---|---|---|---|---|---|---|
| HRm-ea / K+ | 187 | −2443.6 | −2271.4 | +172.2 | 160.4 | −214 to +413 | 1.07 | yes | fail |
| HRm-ea / Na+ | 187 | −2449.3 | −2576.3 | −127.0 | 153.5 | −538 to +74 | 0.83 | **no** | undetermined |
| HRm-60 / K+ | 190 | −1447.9 | −1533.6 | −85.7 | 109.0 | −323 to +176 | 0.79 | yes | fail |
| HRm-60 / Na+ | 190 | −1762.7 | −1540.9 | +221.8 | 176.3 | −289 to +393 | 1.26 | yes | fail |

30 placements per registry; bootstrap over placements, 10,000 replicates, seed 23. Every interval spans zero. HRm-ea / Na+ is reported **undetermined** rather than failed because its θ0+30 minimum fell within the last five placements (−2411 at 10, −2424 at 20, −2576 at 30), so that minimum had not settled.

**Gate F1: FAILED, 0 of 4 dev systems.** Best is 1.26 σ against the 3 σ required.

## Both estimators and both protocols, side by side

| System | Solvated, paired (n σ) | Solvated, minimum (n σ) | Rigid placements, minimum (n σ) |
|---|---|---|---|
| HRm-ea / K+ | +81.3 ± 173.5 (0.47) | −218.5 ± 190.7 (1.15) | +172.2 ± 160.4 (1.07) |
| HRm-ea / Na+ | +47.1 ± 83.8 (0.56) | −35.3 ± 214.6 (0.16) | −127.0 ± 153.5 (0.83) |
| HRm-60 / K+ | +110.7 ± 181.0 (0.61) | +67.8 ± 128.1 (0.53) | −85.7 ± 109.0 (0.79) |
| HRm-60 / Na+ | −71.7 ± 173.9 (0.41) | −63.7 ± 169.6 (0.38) | +221.8 ± 176.3 (1.26) |

Three of the four systems change the **sign** of their margin between the solvated and the rigid protocol, and two change sign between estimators on the same data. No protocol-estimator combination reaches 1.3 σ.

## What the 30 placements bought, and what still limits the gate

The new protocol did what it was meant to do. The minima are now well sampled in three of four systems: the running minimum is flat over the last ten placements for five of the eight registry minima, and the matched placement set removes the protocol mismatch that would have confounded Gate F2. The cost is trivial, 0.4 min per system against 16.4 min per single solvated run.

What did not change is the ratio of signal to placement sensitivity. Within one registry the interaction energy spans about 1000 to 1500 kJ/mol across the 30 offsets (HRm-ea / K+, θ0: −2444 to −870; HRm-60 / Na+, θ0: −1763 to −429). The registry margin that must be read off those minima is 86 to 222 kJ/mol, roughly a tenth of the spread. A minimum over 30 draws from a distribution that wide carries a bootstrap standard error of 109 to 176 kJ/mol, which is the same size as the margin. Taking more placements would shrink that error only slowly, and the undetermined system shows 30 is not yet enough even to settle one minimum.

The physical reading is unchanged from the overnight finding, and the matched protocol sharpens it: **a single capped 50-residue repeat does not carry enough carboxylates to make a registry preference that survives its own freedom to slide laterally.** One repeat presents about 9 acidic residues to a surface whose cation rows repeat every 5.2 Å; sliding the fragment by a fraction of that spacing changes the energy more than rotating it by the 30° the claim is about.

## Next, under the pre-registration

Gate F1 failed at fragment scale, so amendment E item 5 applies: scope one 18-repeat rod with this protocol, time it, and stop without starting a production set. That is `truth/ROD_SCOPE.md`. The stop rule in item 6 then decides whether v8 ends in `NEGATIVE_RESULT.md`.

The test systems, the dev FM path, the band and Gate F2 were **not** run, because each is downstream of a Gate F1 pass. **FM blindness remains intact and complete: no FM call and no LLM contact has touched any dev or test system.**
