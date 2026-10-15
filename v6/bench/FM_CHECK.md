# B1 FM check (V6-9, after the world freeze; no compound changes)

- **FM:** MACE-MP-0 relaxation on node A2 of all 122 library structures of the 30 bench compounds. All 122 converged (`bench/fm/relax.log`).
- **FM values:** as the exemplar computes them (MACE energy plus the entry's MP2020 correction, then formation energy and hull against the fixed DFT hull). Table: `bench/TOOL_TABLES_B1.json` (fm per scenario), data: `bench/fm/fm_check.json`.
- **FM margin:** the FM gap from the FM's lowest polymorph to the next, against the band 0.045 eV/atom.
- **FM status:** right = the FM's lowest is the DFT ground state with margin at least the band; in band = margin below the band; wrong = another polymorph lowest with margin at least the band.
- **FM-path gold:** arm v6-gold (S2 from the FM; when it is not accepted, S2x buys DFT at 60 min per structure within the budget). Graph kit B, planner v3.
- **Prior twin:** S2's output reflected by flip_R.

| scen | stratum | formula | FM lowest | DFT lowest | FM margin | FM status | FM-path gold A / B (key SUPPORTED / REFUTED) | S2x | cost A / B | prior twin A / B | prior twin row |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 201 | K | AsPbAu2 | AsPbAu2 (Pm) | AsPbAu2 (Pm) | 0.17511 | right | SUPPORTED / REFUTED | skipped | 120.0 / 120.0 | REFUTED / SUPPORTED | pass |
| 202 | K | ZrTeP | ZrTeP (Pnma) | ZrTeP (Immm) | 0.12796 | wrong | REFUTED / SUPPORTED | skipped | 71.833 / 71.833 | SUPPORTED / REFUTED | pass |
| 203 | K | ZrInFe2 | ZrInFe2 (Pmma) | ZrInFe2 (Pmma) | 0.11185 | right | SUPPORTED / REFUTED | skipped | 120.0 / 120.0 | REFUTED / SUPPORTED | pass |
| 204 | K | MgZn2Sb | MgZn2Sb (P-1) | MgZn2Sb (P-1) | 0.02238 | in band | CANNOT_TELL / CANNOT_TELL | ran | 180.0 / 180.0 | CANNOT_TELL / CANNOT_TELL | fail |
| 205 | K | CuSO3 | CuSO3 (C2/m) | CuSO3 (C2/m) | 1.56915 | right | SUPPORTED / REFUTED | skipped | 120.0 / 120.0 | REFUTED / SUPPORTED | pass |
| 206 | K | ZrSi3Pt | ZrSi3Pt (P2/m) | ZrSi3Pt (P2/m) | 0.07669 | right | SUPPORTED / REFUTED | skipped | 105.167 / 105.167 | REFUTED / SUPPORTED | pass |
| 207 | K | SiNiOs | SiNiOs (P4/nmm) | SiNiOs (P2_1/m) | 0.01106 | in band | CANNOT_TELL / CANNOT_TELL | ran | 180.0 / 180.0 | CANNOT_TELL / CANNOT_TELL | fail |
| 208 | K | MnWN3 | MnWN3 (P2_1/m) | MnWN3 (Cmcm) | 0.01561 | in band | CANNOT_TELL / CANNOT_TELL | ran | 132.0 / 132.0 | CANNOT_TELL / CANNOT_TELL | fail |
| 209 | K | TiPPd2 | TiPPd2 (Immm) | TiPPd2 (Immm) | 0.24039 | right | SUPPORTED / REFUTED | skipped | 120.0 / 120.0 | REFUTED / SUPPORTED | pass |
| 210 | K | LiRu3 | LiRu3 (Cm) | LiRu3 (Cm) | 0.27186 | right | SUPPORTED / REFUTED | skipped | 120.0 / 120.0 | REFUTED / SUPPORTED | pass |
| 211 | K | ZrGe2Ir | ZrGe2Ir (C2/m) | ZrGe2Ir (C2/m) | 0.02735 | in band | CANNOT_TELL / CANNOT_TELL | ran | 180.0 / 180.0 | CANNOT_TELL / CANNOT_TELL | fail |
| 212 | K | Al5Rh | Al5Rh (I4/mcm) | Al5Rh (I4/mcm) | 0.11375 | right | SUPPORTED / REFUTED | skipped | 71.833 / 71.833 | REFUTED / SUPPORTED | pass |
| 213 | K | Fe3Sb2 | Fe3Sb2 (R-3m) | Fe3Sb2 (Ibam) | 0.03162 | in band | CANNOT_TELL / CANNOT_TELL | ran | 180.0 / 180.0 | CANNOT_TELL / CANNOT_TELL | fail |
| 214 | K | LiNb2In | LiNb2In (P2/m) | LiNb2In (P2/m) | 0.22261 | right | SUPPORTED / REFUTED | skipped | 177.166 / 71.833 | REFUTED / SUPPORTED | pass |
| 215 | K | ScNiGe3 | ScNiGe3 (Cm) | ScNiGe3 (P2/m) | 0.01938 | in band | CANNOT_TELL / CANNOT_TELL | ran | 131.833 / 131.833 | CANNOT_TELL / CANNOT_TELL | fail |
| 217 | E | Hf3Mn2In3 | Hf3Mn2In3 (P-62m) | Hf3Mn2In3 (P-62m) | 0.12352 | right | SUPPORTED / REFUTED | skipped | 38.5 / 38.5 | REFUTED / SUPPORTED | pass |
| 219 | E | FeNiBC | FeNiBC (P2_1/m) | FeNiBC (P2_1/m) | 0.02343 | in band | CANNOT_TELL / CANNOT_TELL | ran | 131.833 / 131.833 | CANNOT_TELL / CANNOT_TELL | fail |
| 220 | E | In5Pd | In5Pd (C2/m) | In5Pd (C2/m) | 0.05855 | right | SUPPORTED / REFUTED | skipped | 120.0 / 120.0 | REFUTED / SUPPORTED | pass |
| 221 | E | In(GePt)2 | In(GePt)2 (C2/m) | In(GePt)2 (C2/m) | 0.06577 | right | SUPPORTED / REFUTED | skipped | 71.833 / 71.833 | REFUTED / SUPPORTED | pass |
| 222 | E | Si3Ni2 | Si3Ni2 (P6_3/mmc) | Si3Ni2 (P6_3/mmc) | 0.27273 | right | SUPPORTED / REFUTED | skipped | 120.0 / 120.0 | REFUTED / SUPPORTED | pass |
| 223 | E | TaBPt2 | TaBPt2 (P1) | TaBPt2 (P1) | 0.05753 | right | SUPPORTED / REFUTED | skipped | 120.0 / 120.0 | REFUTED / REFUTED | fail |
| 224 | E | Pt2S3 | Pt2S3 (R-3m) | Pt2S3 (R-3m) | 0.03432 | in band | CANNOT_TELL / CANNOT_TELL | ran | 180.0 / 180.0 | CANNOT_TELL / CANNOT_TELL | fail |
| 225 | E | SrZnPO | SrZnPO (C2/m) | SrZnPO (C2/m) | 0.10178 | right | SUPPORTED / REFUTED | skipped | 120.0 / 120.0 | REFUTED / SUPPORTED | pass |
| 226 | E | TlSnF4 | TlSnF4 (P-1) | TlSnF4 (P-1) | 0.05796 | right | SUPPORTED / REFUTED | skipped | 38.417 / 38.417 | REFUTED / SUPPORTED | pass |
| 227 | E | BaSn(PtSe2)2 | BaSn(PtSe2)2 (C2) | BaSn(PtSe2)2 (C2) | 0.04197 | in band | CANNOT_TELL / CANNOT_TELL | ran | 131.833 / 131.833 | CANNOT_TELL / CANNOT_TELL | fail |
| 228 | E | Mg5Nb | Mg5Nb (P-1) | Mg5Nb (P-1) | 0.06661 | right | SUPPORTED / REFUTED | skipped | 105.167 / 105.167 | REFUTED / SUPPORTED | pass |
| 229 | E | LaGaFe2 | LaGaFe2 (Pmma) | LaGaFe2 (Pmma) | 0.09258 | right | SUPPORTED / REFUTED | skipped | 105.167 / 105.167 | CANNOT_TELL / CANNOT_TELL | fail |
| 230 | E | Ni3Ge2 | Ni3Ge2 (Cmcm) | Ni3Ge2 (Cmcm) | 0.08781 | right | SUPPORTED / REFUTED | skipped | 120.0 / 120.0 | REFUTED / SUPPORTED | pass |
| 241 | E | CrFe5 | CrFe5 (Cmmm) | CrFe5 (Cmmm) | 0.26092 | right | SUPPORTED / REFUTED | skipped | 120.0 / 120.0 | REFUTED / SUPPORTED | pass |
| 242 | E | CrIr5 | CrIr5 (Cmmm) | CrIr5 (Cmmm) | 0.58548 | right | SUPPORTED / REFUTED | skipped | 71.833 / 71.833 | REFUTED / SUPPORTED | pass |

## Counts

- **FM status by stratum:** K right 8, in band 6, wrong 1; E right 12, in band 3, wrong 0.
- **FM-path gold:** correct on both twins of the 20 FM-right compounds.
  - The 9 in-band compounds end CANNOT_TELL: the measurement took 72-120 min, so the DFT escalation (60 min per structure) does not fit in the budget.
  - The FM-wrong compound 202 ZrTeP gives the wrong verdict on both twins (REFUTED / SUPPORTED).
- **Prior twin:** passes on 19 compounds, the 18 FM-right two-polymorph compounds and ZrTeP. It fails on the 9 in-band compounds (no determinate verdict to flip) and on two three-polymorph FM-right compounds: 223 TaBPt2 (twin B stays REFUTED: after the reflection a third polymorph is lowest) and 229 LaGaFe2 (the reflected margin falls inside the band). The flip test reflects all polymorph energies together, so with three polymorphs it does not always reverse the verdict.
- **The stratum design confounds FM status.** 7 of the 15 K compounds are in band or wrong, against 3 of the 15 E compounds. V6-11 reports the gap by FM status within each stratum for this reason.
- **Prior FM contact (V6-X13).** ZrTeP's V6-2 MACE values were not reused; this check recomputed them from scratch.
