# B1 selection (V6-8)

The frame is selected using truth, physics and the stage 4b heuristic panel only. No FM call and no LLM contact touched these compounds in B1 before this freeze; see the prior-contact note below. Script: `bench/select_b1.py`. Output: `bench/selection_b1.json` (every frame row with its first failed bar) and `bench/nq_b1.json` (the bisection). Logs: `bench/select_b1.log`, plus the crashed first run `bench/select_b1_run1.log` (V6-E3). Selection ran on host A (V6-X11).

**Disclosure (stratified design).** B1 is stratified on the heuristic panel. Stratum K is 15 compounds where the panel fails the pair; stratum E is 15 where it resolves it. Every B1 result is reported per stratum and as the stratified overall. None of it is a population rate for the frame.

## Frame

- The novel R pairs of the V6-2 pool (`exemplar/features/s1.jsonl`), with a library of 2 or 3 polymorphs and a DFT gap E_form(B) − E_form(A) ≥ 0.075 eV/atom, ScPPd2 excluded.
- In hash order (rank).
- **416 pairs.** All 416 were evaluated.

## Bars, in order

| bar | rule | removed | left |
|---|---|---|---|
| quiet limit | N_q = the largest X-ray count rate with D(m0) < 9 on both twins (bisection on log N, 30 steps); N_q ≥ 1.5 | 6 | 410 |
| set point | N = 0.7 N_q (D(m0) at N is below 5 on every take: max 4.88) | 0 | 410 |
| identification cost | at N, the cheapest decisive plan (stage 1 plan grid, X-ray or neutron, singles and pairs, cost cap 180) costs 18 to 108 min on the dearer twin and ≤ 108 on both | 202 (188 dearer twin < 18, too easy; 12 dearer twin > 108; 2 no decisive plan within 180 on a twin) | 208 |
| panel | stage 4b panel (density, prototype frequency, nearest analog, oxidation): E if verdicts are A True and B False, otherwise K | (171 K, 37 E) | 208 |
| diversity | no two compounds share an anonymous formula with the same structure-type pair (first in hash order kept) | 45 (31 K, 14 E) | 163 (140 K, 23 E) |
| strata | 15 takes + 10 reserve per stratum in hash order | K: 115 beyond the reserve; E: all 23 kept | 25 K, 23 E |

N_q over the frame: min 1.05, median 4.30, max 10.08. Every cheapest decisive plan of the 30 takes is X-ray.

**E reserve shortfall (V6-X12).** The frame holds only 23 E compounds after diversity. So E has 15 takes and a reserve of **8, not 10**. If V6-9 replaces more than 8 E compounds, B1 runs with fewer than 15 E. That would be logged; no bar would be relaxed.

**Prior FM contact (V6-X13).** Three selected compounds had MACE values computed in V6-2, during the exemplar's fast-path search (`exemplar/fastpath/targeted.jsonl`), before B1 existed: **ZrTeP** (K take), **TePdBr** and **ScGaFe2** (K reserve). The selection script never reads those files; the bars use truth, physics and the panel only. They stay in. The V6-9 FM check recomputes FM for every compound from scratch and does not reuse those values.

## Selected compounds

Columns:
- D(m0): the expected free-scan Δχ² at N, per twin.
- cheapest: the cheapest decisive plan in minutes, per twin.
- panel: the panel's verdict on the claim for twin A (claim true) and twin B (claim false). The correct pair is True, False.

| # | stratum | slot | rank (hash) | formula | polymorphs | gap eV/atom | N_q | N | D(m0) A, B | cheapest decisive min A, B | panel A, B |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | K | take | 01dfc5a9f7 | AsPbAu2 | 2 | 0.1051 | 2.1116 | 1.4781 | 0.989, 4.822 | 38.5, 8.37 | False, True |
| 2 | K | take | 05521ed639 | ZrTeP | 2 | 0.1831 | 4.2803 | 2.9962 | 4.611, 3.892 | 9.25, 20.07 | False, True |
| 3 | K | take | 0730a22895 | ZrInFe2 | 2 | 0.1678 | 1.9801 | 1.3861 | 1.131, 4.884 | 38.5, 8.37 | False, True |
| 4 | K | take | 0870325c4b | MgZn2Sb | 2 | 0.0813 | 1.5112 | 1.0578 | 0.928, 4.788 | 38.5, 8.37 | False, True |
| 5 | K | take | 0b07a23dd9 | CuSO3 | 2 | 1.4816 | 3.3343 | 2.334 | 2.467, 4.726 | 21.75, 8.37 | False, True |
| 6 | K | take | 0cbc1ed6d9 | ZrSi3Pt | 2 | 0.1844 | 3.2509 | 2.2756 | 4.381, 4.572 | 11.7, 21.75 | False, False |
| 7 | K | take | 103ee8d23c | SiNiOs | 2 | 0.105 | 2.8751 | 2.0126 | 2.141, 4.637 | 20.95, 9.25 | False, False |
| 8 | K | take | 121825c62d | MnWN3 | 2 | 0.1101 | 4.6581 | 3.2607 | 4.636, 3.474 | 11.7, 21.75 | False, False |
| 9 | K | take | 122a0fe734 | TiPPd2 | 2 | 0.2664 | 5.4407 | 3.8085 | 1.872, 4.633 | 38.5, 20.07 | False, True |
| 10 | K | take | 143bb1607a | LiRu3 | 2 | 0.1566 | 2.1343 | 1.494 | 1.656, 4.752 | 31.78, 8.37 | False, True |
| 11 | K | take | 163716ac92 | ZrGe2Ir | 2 | 0.1285 | 2.7281 | 1.9097 | 3.799, 4.563 | 13.42, 20.07 | False, False |
| 12 | K | take | 17e2888ec0 | Al5Rh | 2 | 0.1619 | 3.1783 | 2.2248 | 3.916, 4.644 | 20.95, 11.7 | False, True |
| 13 | K | take | 191383784b | Fe3Sb2 | 3 | 0.3196 | 2.6576 | 1.8603 | 2.1, 4.674 | 21.75, 8.37 | False, False |
| 14 | K | take | 191385574e | LiNb2In | 2 | 0.2583 | 2.51 | 1.757 | 1.599, 4.783 | 21.75, 8.37 | False, True |
| 15 | K | take | 1932dd8bcd | ScNiGe3 | 2 | 0.1145 | 5.4279 | 3.7995 | 4.676, 3.144 | 9.25, 20.07 | False, False |
| 16 | K | reserve | 19ae83033a | NbCd2P | 2 | 0.1025 | 4.1992 | 2.9394 | 4.638, 2.485 | 8.37, 21.75 | False, False |
| 17 | K | reserve | 1b6359d5ae | SrRu3 | 2 | 0.0986 | 2.7539 | 1.9277 | 2.574, 4.629 | 18.37, 11.7 | False, False |
| 18 | K | reserve | 1e98f5c544 | TePdBr | 3 | 0.1235 | 4.2676 | 2.9873 | 4.645, 1.658 | 11.7, 38.5 | False, False |
| 19 | K | reserve | 1fa04051a3 | TiMnC2 | 2 | 0.0913 | 7.22 | 5.054 | 4.817, 1.838 | 8.37, 21.75 | False, False |
| 20 | K | reserve | 204cdce8d6 | Pt2O3 | 3 | 0.1396 | 4.9617 | 3.4732 | 4.67, 2.849 | 11.7, 20.07 | False, False |
| 21 | K | reserve | 20df5ac1f4 | ScGaFe2 | 3 | 0.1607 | 4.0877 | 2.8614 | 2.541, 4.685 | 21.75, 9.25 | False, False |
| 22 | K | reserve | 22ba7d9e91 | NiB2 | 3 | 0.1374 | 3.1076 | 2.1753 | 2.248, 4.746 | 21.75, 9.25 | False, True |
| 23 | K | reserve | 23096cee6d | InTe2Pb | 2 | 0.1215 | 5.1575 | 3.6102 | 1.643, 4.654 | 30.12, 13.42 | False, True |
| 24 | K | reserve | 247528bed0 | CrBi2 | 2 | 0.1702 | 7.9954 | 5.5968 | 4.604, 4.16 | 28.45, 13.42 | False, False |
| 25 | K | reserve | 24edbb3e90 | RbCuS | 3 | 0.0997 | 3.5168 | 2.4618 | 2.655, 4.772 | 20.07, 8.37 | False, True |
| 1 | E | take | 00f8680d20 | TePtI | 3 | 0.1099 | 4.1103 | 2.8772 | 4.631, 2.275 | 11.7, 33.45 | True, False |
| 2 | E | take | 01eb52ae82 | Hf3Mn2In3 | 2 | 0.1597 | 4.293 | 3.0051 | 4.668, 2.394 | 8.37, 20.07 | True, False |
| 3 | E | take | 08e3071c42 | TePtBr | 3 | 0.1199 | 5.1103 | 3.5772 | 4.649, 2.457 | 11.7, 21.75 | True, False |
| 4 | E | take | 3210a8555f | FeNiBC | 2 | 0.1624 | 3.9028 | 2.732 | 4.488, 4.585 | 11.7, 18.37 | True, False |
| 5 | E | take | 3833d073ac | In5Pd | 2 | 0.1121 | 1.7936 | 1.2555 | 1.872, 4.689 | 30.12, 8.37 | True, False |
| 6 | E | take | 4f2ad210ee | In(GePt)2 | 2 | 0.1036 | 3.1912 | 2.2338 | 3.399, 4.633 | 20.07, 11.7 | True, False |
| 7 | E | take | 5e2ddec9c2 | Si3Ni2 | 2 | 0.3636 | 3.8222 | 2.6755 | 4.674, 3.088 | 8.37, 20.07 | True, False |
| 8 | E | take | 5fb2e12602 | TaBPt2 | 3 | 0.1598 | 2.5386 | 1.777 | 2.186, 4.646 | 33.45, 11.7 | True, False |
| 9 | E | take | 637089ce2e | Pt2S3 | 2 | 0.1267 | 4.9389 | 3.4572 | 4.677, 4.175 | 11.7, 18.37 | True, False |
| 10 | E | take | 7f7ec42d77 | SrZnPO | 2 | 0.1279 | 2.1861 | 1.5303 | 2.807, 4.648 | 33.45, 11.7 | True, False |
| 11 | E | take | 8482d16fcf | TlSnF4 | 2 | 0.0894 | 2.7809 | 1.9466 | 3.324, 4.622 | 18.37, 9.25 | True, False |
| 12 | E | take | a17d36a279 | BaSn(PtSe2)2 | 2 | 0.1228 | 2.6434 | 1.8504 | 3.247, 4.616 | 20.95, 11.7 | True, False |
| 13 | E | take | a6ea650460 | Mg5Nb | 2 | 0.1222 | 2.756 | 1.9292 | 2.496, 4.663 | 21.75, 9.25 | True, False |
| 14 | E | take | a7f909d515 | LaGaFe2 | 3 | 0.1055 | 4.3536 | 3.0475 | 4.651, 3.818 | 11.7, 20.95 | True, False |
| 15 | E | take | b3553b6527 | Ni3Ge2 | 2 | 0.128 | 3.1533 | 2.2073 | 2.317, 4.743 | 20.95, 8.37 | True, False |
| 16 | E | reserve | ba4ebb46a9 | CrFe5 | 2 | 0.3064 | 7.3019 | 5.1113 | 4.86, 2.09 | 8.37, 21.75 | True, False |
| 17 | E | reserve | ba58d28d83 | CrIr5 | 2 | 0.656 | 8.5973 | 6.0181 | 4.657, 4.557 | 20.95, 9.25 | True, False |
| 18 | E | reserve | ba700f1083 | CsNiHgSe2 | 2 | 0.1043 | 5.4571 | 3.82 | 4.659, 3.462 | 9.25, 20.07 | True, False |
| 19 | E | reserve | db08ec75e5 | RbIr(SO4)2 | 2 | 0.0814 | 4.2409 | 2.9686 | 4.6, 3.425 | 13.42, 20.95 | True, False |
| 20 | E | reserve | e73c964500 | MnPb5 | 2 | 0.1982 | 2.4816 | 1.7371 | 2.587, 4.591 | 20.07, 18.37 | True, False |
| 21 | E | reserve | edcbed8f1b | SiNi5 | 2 | 0.2356 | 3.3215 | 2.325 | 2.334, 4.717 | 18.37, 9.25 | True, False |
| 22 | E | reserve | f6136022db | MnIr5 | 2 | 0.8548 | 7.1689 | 5.0182 | 4.733, 2.194 | 11.7, 21.75 | True, False |
| 23 | E | reserve | fa284523a2 | SrLiPb | 3 | 0.0928 | 4.2312 | 2.9618 | 4.641, 3.014 | 11.7, 20.07 | True, False |

K panel patterns among the takes: 9 are (False, True), wrong on both twins; 6 are (False, False), right on twin B only.
