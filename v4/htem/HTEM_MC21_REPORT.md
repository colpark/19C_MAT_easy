# HTEM MC v2.1: census report (MV1c to MV1d)

Branch v4.5/2026-10-08. Rules: HTEM_MC2_RULES.md (MV0) amended by HTEM_MC2_RULES_v21.md (MV1c 3ca1adbb). Census: MC21_CENSUS.md and .json.

**Outcome.**
- **Formally GO** under the v2.1 rules, but one group rests on a rule gap.
- **The gap (VM-E07):** the structural group's keys (L4, L6) rest on chemically implausible COD reference phases. Under I8 that group is held for David.
- **Without the structural group,** the electrical and optical groups still meet every go criterion: 2 groups, 4 types (L2, L7, L3, L8), 142 critical items, 23 in test, fresh confirmation passed.
- **Not started:** MV2-MV6, pending David's call.
- **Spend:** $0.

## Steps
| Step | Result |
|---|---|
| MV1c | v2.1 amendments frozen. I_floor = 5e-8 A from dev I-V amplitude levels, the same value as the frozen validity floor. |
| VG | S4mc6 v2 **pass**. Synthetic recovery 1.00 for every class, false fault 0.00. Replicate valid/not-valid agreement 0.970 over 233 matched positions. Flips at r² 0.995/0.99: 0.31 %/0.39 %. Database Rs Spearman 1.000. **Trap: 826 fault or beyond-range positions still carry a finite database Rs.** VG_S4MC6.md. |
| F1 | 87 libraries, 3,841 requests (cap 4,500), 0 errors, 75 min; 86 now fully cached. |
| CO1 | 174 searches and 697 CIFs, 891 COD requests in total (cap 1,000). 678 phases with sticks, 321 L4 pairs, 19 CIF parse failures dropped. VM-E06 (pymatgen API name) fixed with no extra requests. |
| MV1d | Census (a)/(b)/(c). (a) reproduces MV1b **byte for byte**. |

## Side by side (critical items, with systems in brackets)
| Type | (a) old rules, MV1b scope (260) | (b) old rules, enlarged (346) | (c) v2.1 rules, enlarged | (c) includable |
|---|---|---|---|---|
| L1 best conductor | 6 (3) | 9 (5) | 8 (4) | no: "thickest" 6/11 breaks the cap |
| L2 resistivity trend | 6 (2) | 9 (4) | 9 (4) | yes |
| L3 most transparent at E | 10 (5) | 16 (7) | 16 (7) | yes |
| L4 lattice or d at x0 | 6 (1) | 6 (1) | 39 (16) | yes, but VM-E07 |
| L5 temperature at matched composition | 4 (2) | 5 (3) | 5 (3) | no: too few items, and "always no decided difference" 4/7 breaks the cap |
| L6 single-phase range | 1 (1) | 3 (2) | 25 (14) | yes, but VM-E07 |
| L7 valid Rs readings | 39 (20), built | 83 (35), built | 73 (33) | yes |
| L8 impossible optical data | 34 (16) | 44 (21) | 44 (21) | yes |
| **Round** | NO-GO | NO-GO | GO | |

**What changes from (b) to (c), and why:**
- **L2:** the binomial cheap-rule gate. "Zero slope" scores 6/13, p = 0.45, so it no longer fails on one item.
- **L8:** the T > 1.05 count is no longer a cheap rule (approved). It is reported as the single-constraint baseline, which scores 0.81. The L8-deep subset (the T + R balance decides) has 12 critical items over 6 systems.
- **L4, L6:** the CO1 sticks.
- **Robustness:** it removes 10 L7 libraries and 2 L1 libraries.

## Groups under (c)
| Group | Includable types | Critical | Systems | In test | Builds |
|---|---|---|---|---|---|
| electrical | L2, L7 | 82 | 33 | 15 | yes |
| optical | L3, L8 | 60 | 24 | 8 | yes |
| structural | L4, L6 | 64 | 25 | 11 | yes, **held (VM-E07)** |

**Fresh confirmation** (F1 libraries only):
- **Pass:** L2 (6 items), L3 (8), L6 (9), L7 (50) and L8 (14).
- **Unconfirmed** (fewer than 6 fresh items): L1, L4 and L5.

## VM-E07: rule gap in the CO1 selection
The CO1 rule keeps every ambient, ordered COD entry over element subsets of size 1 to 3 of the system. It never asks whether a phase fits the library's chemistry. With 678 candidate phases, coincidental stick hits decide many calls.

**L4 critical items by pair:**

| Pair | Chemistry | Critical items |
|---|---|---|
| SnS/SnTe rocksalt (S-Sn-Te) | plausible | 5 |
| MnZnSe₂/MnZnTe₂ (Mn-Se-Te-Zn) | plausible | 4 |
| wurtzite ZnO/MnO (Mn-O-Zn) | plausible | 4 |
| fcc Cr/Mn metals in an oxide library (Cr-Mn-O-Zn) | implausible | 3 |
| fcc Ta/Sn (Co-Sn-Ta) | implausible | 2 |
| fcc Cu/Sb metals in sulfide and selenide libraries (Cu-S-Sb, Cu-Sb-Se) | implausible | 2 + 2 |
| others | mixed | the rest |

**L6 main-phase calls include:**
- O₂ (Co-O)
- elemental S (Cu-S-Sb)
- fcc Mn (Mn-Se-Te-Zn)
- fcc Sn (Cu-S-Sn)
- a bcc Zn-Cu alloy (Cu-O-Zn)

These are not credible for these films.

**Not done (I4, I8):** the rule was not tightened after seeing these results.

**Possible amendment for David (not applied):** a phase must contain the library's anion or anions. Elemental phases are allowed only in anion-free libraries. This would be frozen with fresh confirmation on libraries not yet seen, which needs F2.

## Options for David
1. **Proceed to MV2-MV6 with the electrical and optical groups (recommended).**
   - Types: L2, L7, L3 and L8.
   - These meet the round go without the structural group: 142 critical items, 23 in test, fresh confirmation passed.
   - VM-E07 does not touch them.
   - The structural group stays out until a chemistry-consistent COD rule is frozen.
2. **Amend CO1 first,** with a chemistry-consistent phase rule, then rerun the structural part. Under the disclosure rule, its fresh confirmation needs libraries not yet seen, which means F2.
3. **F2:** the other 218 uncached libraries, about 9,600 requests, about 3.5 h. It would also give L1, L4 and L5 fresh confirmation. Not approved, sized here.

## Ledger
- Errors: VM-E04 (MV1b), VM-E05 (VG crash, before output), VM-E06 (pymatgen API), VM-E07 (rule gap, open).
- Freezes: MV1c, VG, F1, CO1, MV1d code.
- Commands, hosts and request counts: LOG.md.
