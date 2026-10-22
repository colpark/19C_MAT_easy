# B1 without DFT: gold traces and validation rows (V7-0 step 6)

- **Graph:** `graph_R_v2_nodft.json` (kit D: graph R v2 without S2x; inside the band the rule answers CANNOT_TELL).
- **Path:** the FM adapters (planner v3; MACE through the B1 server's FM path, node A2:8778, arm v6-gold, budget 180; no DFT call).
- **Worlds:** the 30 B1 compounds, both twins and the six B1 hold worlds.
- **Rows:** `validate_d` with rows = all.
  - `accept` is the key; on the 9 FM in-band compounds it is the key and CANNOT_TELL (B1's band rule).
  - **Non-bypass evidence:** the V6-8 panel stratum, blind-FM pairs resolved 0, constant prior resolved 0.
  - **Faithfulness** is not run: these are training traces, not rendered exemplars. The row reads "no rendered trace given" on every compound.
- **Data:** traces in `v7/b1/gold_nodft/` (gold, logs, rows); script `v7/b1/run_b1_nodft.py`. These are training traces in the 19C scope.

| scen | formula | stratum | FM status | verdict A / B (key) | correctness | necessity S1a+S1d | necessity S1b+S1e | necessity S1c+S1d+S1e+S1f | necessity S2 | measurement factorial | hold | prior flip | abstention | sufficiency | non-bypass |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 201 | AsPbAu2 | K | right | SUPPORTED / REFUTED (S/R) | pass | pass | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| 202 | ZrTeP | K | wrong | REFUTED / SUPPORTED (S/R) | **fail** | pass | pass | pass | pass | **fail** | pass | pass | pass | pass | pass |
| 203 | ZrInFe2 | K | right | SUPPORTED / REFUTED (S/R) | pass | pass | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| 204 | MgZn2Sb | K | in band | CANNOT_TELL / CANNOT_TELL (S/R) | pass | pass | pass | pass | pass | **fail** | pass | **fail** | pass | **fail** | pass |
| 205 | CuSO3 | K | right | SUPPORTED / REFUTED (S/R) | pass | pass | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| 206 | ZrSi3Pt | K | right | SUPPORTED / REFUTED (S/R) | pass | pass | pass | pass | pass | pass | pass | pass | pass | **fail** | pass |
| 207 | SiNiOs | K | in band | CANNOT_TELL / CANNOT_TELL (S/R) | pass | pass | pass | pass | pass | **fail** | pass | **fail** | pass | **fail** | pass |
| 208 | MnWN3 | K | in band | CANNOT_TELL / CANNOT_TELL (S/R) | pass | pass | pass | pass | pass | **fail** | pass | **fail** | pass | **fail** | pass |
| 209 | TiPPd2 | K | right | SUPPORTED / REFUTED (S/R) | pass | pass | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| 210 | LiRu3 | K | right | SUPPORTED / REFUTED (S/R) | pass | pass | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| 211 | ZrGe2Ir | K | in band | CANNOT_TELL / CANNOT_TELL (S/R) | pass | pass | pass | pass | pass | **fail** | pass | **fail** | pass | **fail** | pass |
| 212 | Al5Rh | K | right | SUPPORTED / REFUTED (S/R) | pass | pass | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| 213 | Fe3Sb2 | K | in band | CANNOT_TELL / CANNOT_TELL (S/R) | pass | pass | pass | pass | pass | **fail** | pass | **fail** | pass | **fail** | pass |
| 214 | LiNb2In | K | right | SUPPORTED / REFUTED (S/R) | pass | pass | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| 215 | ScNiGe3 | K | in band | CANNOT_TELL / CANNOT_TELL (S/R) | pass | pass | pass | pass | pass | **fail** | pass | **fail** | pass | **fail** | pass |
| 217 | Hf3Mn2In3 | E | right | SUPPORTED / REFUTED (S/R) | pass | pass | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| 219 | FeNiBC | E | in band | CANNOT_TELL / CANNOT_TELL (S/R) | pass | pass | pass | pass | pass | **fail** | pass | **fail** | pass | **fail** | pass |
| 220 | In5Pd | E | right | SUPPORTED / REFUTED (S/R) | pass | pass | pass | pass | pass | pass | pass | pass | pass | **fail** | pass |
| 221 | In(GePt)2 | E | right | SUPPORTED / REFUTED (S/R) | pass | pass | pass | pass | pass | pass | pass | pass | pass | **fail** | pass |
| 222 | Si3Ni2 | E | right | SUPPORTED / REFUTED (S/R) | pass | pass | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| 223 | TaBPt2 | E | right | SUPPORTED / REFUTED (S/R) | pass | pass | pass | pass | pass | pass | pass | **fail** | pass | **fail** | pass |
| 224 | Pt2S3 | E | in band | CANNOT_TELL / CANNOT_TELL (S/R) | pass | pass | pass | pass | pass | **fail** | pass | **fail** | pass | **fail** | pass |
| 225 | SrZnPO | E | right | SUPPORTED / REFUTED (S/R) | pass | pass | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| 226 | TlSnF4 | E | right | SUPPORTED / REFUTED (S/R) | pass | pass | pass | pass | pass | pass | pass | pass | pass | **fail** | pass |
| 227 | BaSn(PtSe2)2 | E | in band | CANNOT_TELL / CANNOT_TELL (S/R) | pass | pass | pass | pass | pass | **fail** | pass | **fail** | pass | **fail** | pass |
| 228 | Mg5Nb | E | right | SUPPORTED / REFUTED (S/R) | pass | pass | pass | pass | pass | pass | pass | pass | pass | **fail** | pass |
| 229 | LaGaFe2 | E | right | SUPPORTED / REFUTED (S/R) | pass | pass | pass | pass | pass | pass | pass | **fail** | pass | pass | pass |
| 230 | Ni3Ge2 | E | right | SUPPORTED / REFUTED (S/R) | pass | pass | pass | pass | pass | pass | pass | pass | pass | **fail** | pass |
| 241 | CrFe5 | E | right | SUPPORTED / REFUTED (S/R) | pass | pass | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| 242 | CrIr5 | E | right | SUPPORTED / REFUTED (S/R) | pass | pass | pass | pass | pass | pass | pass | pass | pass | pass | pass |

## Rows passed, by FM status

| FM status | n | correctness | necessity S1a+S1d | necessity S1b+S1e | necessity S1c+S1d+S1e+S1f | necessity S2 | measurement factorial | hold | prior flip | abstention | sufficiency | non-bypass |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| right | 20 | 20 | 20 | 20 | 20 | 20 | 20 | 20 | 18 | 20 | 13 | 20 |
| in band | 9 | 9 | 9 | 9 | 9 | 9 | 0 | 9 | 0 | 9 | 0 | 9 |
| wrong | 1 | 0 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 |

## Reading the rows

- **FM right (20):** the gold gives the key on both twins in all 20. The rows that fail on some of them:
  - **sufficiency** needs the decision margin at least twice the band (0.09 eV/atom), which several FM-right compounds miss;
  - **prior flip** fails on three-polymorph compounds, where the reflected energies need not reverse the verdict (as in V6-9).
- **FM in band (9):** the gold answers CANNOT_TELL on both twins, which the band rule accepts, so the correctness row passes. Three rows fail by construction:
  - the **measurement factorial** asks for determinate verdicts equal to the key;
  - the **prior flip** asks for a reversed determinate verdict;
  - **sufficiency** asks for a margin above twice the band.
- **FM wrong (202 ZrTeP):** the gold follows the wrong FM and gives the wrong determinate verdict on both twins.
