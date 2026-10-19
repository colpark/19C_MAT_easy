# V7-3: family H selection. Gate H-supply FAILS: stopped for David

Truth, physics and heuristics only. No FM call and no LLM contact. Script: `v7/H/select_H.py`. Data: `v7/H/selection_H.json` (every frame row and its first failed bar) and `nq_H.json` (the bisection).

## Frame
- **Novel formulas** in `v6/exemplar/features/s1.jsonl` (R and H records, one per formula): 423.
- **Excluded:** v5 stage 4b dev formulas (0), every B1-built compound (48) and every T compound (24, all from the fresh set).
- **No twin pair:** 250 formulas lack a polymorph with hull ≤ 0.03 or one with hull ≥ 0.07.
- **Frame:** 101 formulas, 82 type E and 19 type M (V7-X5).
  - Type M needs two polymorphs with hull ≤ 0.03, since the lowest polymorph always has the lowest hull distance.
  - The prompt counted 109 E and 16 M. The difference comes from the exclusions and the M rule.

## Bars, in hash order (V6-8)
| bar | E | M |
|---|---|---|
| frame | 82 | 19 |
| quiet limit N_q < 1.5 | 0 | 1 |
| identification cost: dearer twin < 18 min (identification too cheap) | 56 | 4 |
| identification cost: dearer twin > 108 min | 3 | 5 |
| identification cost: no decisive plan within 180 min on a twin | 0 | 1 |
| diversity | 8 | 0 |
| **pass the bars** | **15** | **8** |

## Gate H-supply: FAILS
The gate needs at least 16 E-type and 5 M-type compounds through the bars. **E has 15**; M has 8.

Takes, if David lets H go ahead (all 23 survivors, no reserve):

| type | formula | polymorphs | hull A | hull B | N_q | N | cheapest decisive plan A, B (min) | H panel | oracle R-rank baseline resolves |
|---|---|---|---|---|---|---|---|---|---|
| M | PdCl3 | 3 | -0.1526 | 0.1327 | 4.628 | 3.2396 | 21.75, 8.37 | K | no |
| M | NbSnSe2 | 3 | -0.0216 | 0.1089 | 5.8028 | 4.062 | 94.0, 8.37 | K | no |
| M | Ca3(ZnGe)4 | 3 | 0.0004 | 0.1519 | 3.2862 | 2.3003 | 50.2, 11.7 | K | no |
| M | Ca2Ni3 | 3 | 0.0049 | 0.1524 | 4.4152 | 3.0906 | 18.37, 8.37 | K | no |
| M | Cd2Ni | 3 | 0.0085 | 0.1361 | 2.5456 | 1.7819 | 35.17, 8.37 | K | no |
| M | MgAlAu | 3 | 0.0265 | 0.1240 | 5.6774 | 3.9742 | 18.37, 9.25 | K | no |
| M | La3FeC4 | 3 | -0.0331 | 0.1326 | 3.9745 | 2.7821 | 38.5, 21.75 | K | no |
| M | AgS | 3 | 0.0250 | 0.3001 | 2.6873 | 1.8811 | 30.08, 8.37 | K | no |
| E | La3Tl3Pt2 | 2 | 0.0060 | 0.1214 | 4.1167 | 2.8817 | 9.25, 18.37 | K | yes |
| E | SrZn2In | 2 | 0.0238 | 0.1018 | 2.3149 | 1.6204 | 33.45, 8.37 | K | yes |
| E | Al5Ir | 2 | 0.0209 | 0.2046 | 3.5343 | 2.474 | 20.07, 11.7 | K | yes |
| E | LiZnSi | 2 | 0.0263 | 0.1765 | 3.1804 | 2.2263 | 21.75, 11.7 | K | yes |
| E | Pt2Se3 | 2 | 0.0171 | 0.1265 | 5.7805 | 4.0463 | 9.25, 20.95 | K | yes |
| E | InSnF4 | 2 | 0.0221 | 0.2247 | 1.8286 | 1.28 | 21.75, 9.25 | K | yes |
| E | HfAsO4 | 3 | 0.0010 | 0.0981 | 4.053 | 2.8371 | 13.42, 30.08 | K | yes |
| E | Na2Co2TeO6 | 2 | -0.0167 | 0.1674 | 8.5208 | 5.9646 | 18.37, 13.42 | K | yes |
| E | Mg(GePt)2 | 2 | -0.0104 | 0.0760 | 5.6836 | 3.9785 | 20.07, 20.07 | E | yes |
| E | BaSc2F8 | 3 | 0.0131 | 0.1505 | 2.3161 | 1.6213 | 21.75, 11.7 | K | yes |
| E | HfSi3Ni | 2 | 0.0024 | 0.2481 | 6.431 | 4.5017 | 9.25, 21.75 | K | yes |
| E | LaAlFe2 | 3 | -0.0012 | 0.0922 | 2.5842 | 1.8089 | 21.75, 13.42 | K | yes |
| E | NaAg | 3 | 0.0179 | 0.1026 | 3.1225 | 2.1858 | 21.75, 8.37 | K | yes |
| E | ZrAsSe | 2 | -0.0207 | 0.1267 | 5.4834 | 3.8384 | 9.25, 20.95 | K | yes |
| E | ScCuTe2 | 3 | 0.0234 | 0.4797 | 1.9787 | 1.3851 | 38.5, 8.37 | K | yes |

- **Panel labels:** the stage 4b H panel fails 22 of the 23 pairs (K). Only one E-type pair (Mg(GePt)2) is panel-resolved (E). The "panel stratum" of H is therefore almost all K.
- **The oracle R-rank baseline** ("SUPPORTED iff the sample is the lowest polymorph") resolves every type E pair and no type M pair, as designed.

## Options for David (none applied)
1. **Run H with the 23 survivors** (15 E, 8 M), with E one short of the gate. That would mean 46 worlds and 368 episodes at k = 4 instead of 384. It needs David's waiver of the gate, since gates are not relaxed (I5).
2. **Lower the H "too easy" bar** (dearer twin ≥ 18 min) to, for example, 9 min. 56 E pairs fail only because one cheap X-ray window identifies them; most of them would enter. That changes a V6-8 bar for H.
3. **Share compounds with T.** The 24 formulas excluded as T compounds are T's fresh K set. Letting H reuse some would add candidates at the cost of overlap between families.
4. **Widen the frame** beyond the V6-2 novel pool (s1.jsonl holds only 423 novel formulas), for example to non-novel formulas. That breaks B1's novelty convention.

Family T is unaffected and continues (V7-2).
