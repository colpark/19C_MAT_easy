# v8 pre-registration addendum C (V8-X5)

Pushed before any truth run. Verbatim from David's note below.

---

# PROMPT CHANGE: v8 amendment C (David, 2026-10-19), supply at the repeat-unit level

To the v8 builder session. Log as V8-X5 (V8-X4 stays reserved for the fragment reading). Push `v8/PREREG_ADDENDUM_C.md` with this note verbatim before any truth run.

## Finding (count before commit)
Source: `pylesharley/DHR10micaX` at 09d10aa, `rosetta_models`, 20 PDBs. The repeat length is 50 residues.

- **One shared unit.** 16 of the 20 designs share one mica-facing repeat unit, U0, within 2 mismatches under cyclic alignment: mica18, mica18NC, mica14-checker, mica2NC, mica6NC, honeycomb 3H to 7H, TrimerV1, TrimerV5 and V1hb1 to V1hb4.
- **Four distinct units.** Only the four charge-pattern controls carry distinct units: 4H scrambled carb1, carb2, net1 and net2 (C1 to C4), each 3 to 8 mismatches from U0.
- **Rod shape.** Only U0 designs reach an aspect ratio of 4 or more. mica18 measures 19.7 × 3.7 nm and mica14-checker 15.6 × 3.7 nm. C1 to C4 exist only as 4H monomers of 5.6 × 3.6 nm (aspect 1.6), too round for AFM to orient.

**Consequence under amendments A and B.** The dev split (honeycomb series plus one control) shares U0 with most test designs, so dev FM calls reveal the test FM values. The test set also holds at most 4 distinct FM values per cation, and three of those belong to rods AFM cannot orient.

## Changes
1. **Verify the count** in `v8/truth/SUPPLY.md` with your own code. If your count differs, stop and report.
2. **A system is a (unit, surface cation) pair.** Designs that share a unit share one truth value and one FM value.
3. **Fragment (the V8-X4 reading).** Use one internal 50-residue repeat with neutral ACE and NME caps. Never include a design's own N or C cap in a truth or FM fragment, since the caps sit at the rod ends and do not set the registry.
4. **Rods for C1 to C4.** Build 14- and 18-repeat rods by tiling the internal repeat geometry of the published 4H model: a rigid screw transform taken from consecutive repeats, with no FM call and no new sequence beyond repeating the published unit. This follows the published series, which varies only the repeat count. **David's scope decision:** a repeat-count extension of a published unit counts as an input, not as sequence design.
5. **Split, with disjoint units.**
   - Dev: U0 and C1, with both cations.
   - Test: C2, C3 and C4 with both cations, which gives 6 (unit, cation) systems. Each appears at 14 and 18 repeats, so 12 rod systems, 24 worlds, scenarios 801 to 824.
   - The V8-4 exemplar comes from dev (U0 at 18 repeats, chosen on truth only).
6. **Gate S** passes when dev and test share no unit, dev holds at least 2 units and test at least 3. Gate F1 covers U0 and C1 on both cations.
7. **Truth must exist.** A test (unit, cation) system with |IFF margin| < 3 standard errors has no defined θ_match. It leaves the pilot, and the report lists it. If fewer than 4 test (unit, cation) systems remain, stop for David.
8. **Analysis.** Gate I's interval and every bootstrap resample the (unit, cation) clusters, not rod systems. With 6 clusters, report the interval whatever it shows.
9. Every other gate, expectation and isolation rule stays unchanged.
