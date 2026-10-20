# V9-9: MACE-MH-1 installed and timed. It is cheaper than UMA per converged relaxation.

David's scope: "Install MACE-MH-1 and time one single point and one converged relaxation on the
same 647-atom system. Nothing more." This exists so stop state 4 turns on a measured rate rather
than an assumed one.

## Install

`mace-torch 0.3.16`, checkpoint `mace-mh-1.model` (59,208,139 bytes, sha256 `a522eb7f59c7879963d4…`)
from the ACEsuit `mace-foundations` release. Installed into a **separate** interpreter at
`~/v9_data/macenv` with `--no-deps`, with v8's `site-packages` added read-only by a `.pth` file so
torch 2.13.0+cu130 is reused rather than a second 5 GB copy downloaded. **Nothing was installed
into, or written to, the v8 environment** (V9-X4 holds).

**Head: `oc20_usemppbe`.** MACE-MH-1's six heads are `matpes_r2scan`, `mp_pbe_refit_add`,
`spice_wB97M`, `oc20_usemppbe`, `omol`, `omat_pbe`. The OC20 head is chosen for exactly the reason
UMA's `oc20` was chosen in V9-5 — it is the only one trained on molecular adsorbates on metal slabs
— and carries the same disclosure, that OC20's adsorbates are small molecules so a 10-residue
peptide extrapolates adsorbate size.

## The rates, on the identical 647-atom system (560 Au + 87 peptide atoms, P000 conformer 1, placement 0)

| Model | dtype | steps to fmax ≤ 0.05 | wall | s/step | single point |
|---|---|---|---|---|---|
| UMA `uma-s-1p2` / `oc20` | float32 | 434 | **167.1 s** | 0.385 | 0.3585 s (realised over 3,916) |
| MACE-MH-1 / `oc20_usemppbe` | float64 | 230 | 254.2 s | 1.105 | 1.1525 s |
| MACE-MH-1 / `oc20_usemppbe` | float32 | **238** | **102.1 s** | 0.429 | 0.4804 s |

**MACE-MH-1 in float32 is 1.64× cheaper than UMA per converged relaxation**, not because its steps
are faster — they are about the same — but because it needs **238 steps against UMA's 434**. In
float64 it is 1.52× more expensive than UMA. float32 cost essentially nothing in convergence here:
238 steps against float64's 230, final fmax 0.0482 against 0.0465.

Projections at rung 2's shape (60 peptides × 9 converged relaxations):

| Model | GPU hours | inside the 25-hour budget? |
|---|---|---|
| UMA | 25.1 | just fits |
| MACE-MH-1 float64 | 38.1 | **no** |
| MACE-MH-1 float32 | **15.3** | **yes, with 9.7 h spare** |

So stop state 4's condition — "run MACE-MH-1 only if its measured rate fits inside the remaining
budget" — **is satisfied, in float32**.

**MACE's fmax path wanders too**: 0.0721 at step 150, 0.0910 at step 200, 0.0482 at step 238. The
non-monotonic force path David identified from UMA is **not a UMA quirk**; it reproduces on a
different architecture on the same system, so a capped relaxation returns a where-it-stopped number
for either model.

## V9-E4, my error, caught before it reached a report

The first version of this probe timed its second single point on an `Atoms` object holding the
**same positions** with the **same calculator**, so ASE's `check_state` found nothing changed and
returned the cached result: **0.0005 s**, which is a cache hit and not a computation. Taking it at
face value would have projected MACE single points as 2,000× cheaper than they are.

The fix times the rate on structures that genuinely differ, which is what a production run
evaluates. The first fix was still wrong in a smaller way — placement 0 of the timing table *is*
the structure the cold call used, because a scrambled Sobol sequence starts at the same point for
any n, so one cache hit survived at 0.0002 s and dragged the mean down. The loop now starts at
placement 1 and all ten timings are 0.42 s or above with ten distinct energies.

**UMA's figures are unaffected.** Its 0.3585 s was realised over 3,916 genuinely distinct
structures in the rung 1 production run, and its 167.1 s came from a real converged trajectory.

No energy from this probe is used as a margin or a prediction. It is a rate measurement only.
