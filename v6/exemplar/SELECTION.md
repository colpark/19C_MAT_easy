# V6-2 exemplar selection (amendment A with the fast path, V6-X5, V6-X7, V6-X8)

**Disclosure.** The pick conditions on FM output (bar 3), which suits an exemplar, not a rate. The LLM does not gate selection (amendment A); its bypass is measured in V6-5. The full amendment A funnel over the whole pool keeps running in the background as a report (`features/`) and did not gate this pick (V6-X7, user decision).

Trace spec: `graph_R.json` with every validation row. Bars: (1) pattern similarity, N_q = the largest count rate with both twins' free scan below D 9 (exact, V6-X6); (2) the stage 4b heuristic panel fails the pair; (3) FM (MACE-MP-0) ranks P1 lowest with margin ≥ 0.090 eV/atom; (4) the cheapest decisive plan costs 36 to 108 min on the dearer twin and at most 108 on both, at the largest N ≤ N_q that meets it (V6-X8); (5) the blind FM planner resolves no pair (automatic for twins of one formula). Bar 1's threshold of 50 is lowered to the largest N_q reached (no candidate reached 50): the exemplar is quiet by low counts (V6-X7).

## Short list (fast path)
| candidate | polymorphs | DFT gap to nearest (eV/atom) | FM ranks P1 lowest | FM margin | panel fails | N_q | first failed bar |
|---|---|---|---|---|---|---|---|
| NbTlTe2 (stage 4b R pick) | 3 | 0.0486 | no | 0.0167 | yes (stage 4b) | 1.06 to 2.45 (stage 4b tuning) | bar 3 |
| SrInRh2 (stage 4b R pick) | 3 | 0.0053 | yes | 0.0368 | yes (stage 4b) | 1.06 to 2.45 (stage 4b tuning) | bar 3 |
| LiPbS2 (stage 4b R pick) | 4 | 0.0226 | yes | 0.0081 | yes (stage 4b) | 1.06 to 2.45 (stage 4b tuning) | bar 3 |
| TePdBr (stage 4b R pick) | 3 | 0.027 | yes | 0.0298 | yes (stage 4b) | 1.06 to 2.45 (stage 4b tuning) | bar 3 |
| ZrGaAg (stage 4b R pick) | 3 | 0.0239 | no | 0.0085 | yes (stage 4b) | 1.06 to 2.45 (stage 4b tuning) | bar 3 |
| ScGaFe2 (stage 4b R pick) | 3 | 0.1607 | yes | 0.0375 | yes (stage 4b) | 1.06 to 2.45 (stage 4b tuning) | bar 3 |
| MnSbS (stage 4, 63) | 4 known (stage 4 listed 2) | 0.088 | yes | 0.005 | - | - | bar 3 |
| BaIn3Ni (stage 4, 64) | 2 | - | yes | 0.119 | no (density and prototype rules right on both twins) | 5.6578 (linear estimate 0.6342) | bar 2 |
| BaSb2Pt (stage 4, 67) | 2 | - | yes | 0.100 | no (density and prototype rules right on both twins) | 2.3216 (linear estimate 0.2562) | bar 2 |

## Targeted search (fast path)
Stage 4b pool R pairs with two or three polymorphs, at most 24 sites, dev formulas excluded, DFT gap to the nearest polymorph ≥ 0.12 eV/atom: 1,521, in sha256 order of the twin ids (`fastpath/targeted_candidates.json`). Checked in order until the first full pass (`fastpath/targeted.jsonl`): 58 candidates; novelty: 55, bar 2: panel resolves the pair: 2, passed all: 1. A first try that evaluated bar 4 at N_q only is kept (`targeted_try1.jsonl`; ScPPd2 failed bar 4 there with plans of 8 and 7 min, which led to V6-X8).

## Pick: ScPPd2
- World A (claim true): wbm-4-29663, Immm (space group 71), DFT formation energy −0.817 eV/atom, the ground state of ScPPd2. World B: wbm-5-16590, Fm-3m (225, the Heusler-type ABC2 cell), −0.693 eV/atom. DFT gap 0.124 eV/atom. Library: these two polymorphs (every known ScPPd2 polymorph) and two distractors.
- Novelty: the anonymous formula with world A's key occurs 0 times in MP.
- Panel (bar 2): world A verdict False, world B verdict True (truth: true, false): density, prototype frequency and the nearest analog (ScAsPd2) all favour the Heusler polymorph; the panel is wrong on both twins.
- FM (bar 3): Immm -0.84406, Fm-3m -0.62586 eV/atom; P1 lowest with margin 0.2182 eV/atom (bar 0.090).
- Identification (bars 1, 4): N_q = 4.1112; at N = 1.34396 the cheapest decisive plans cost 38.5 and 20.95 min (window 36 to 108 on the dearer twin); the free scan shows about one count at the strongest peak, so the exemplar is quiet by low counts.
- Bar 5: twins of one formula, so a blind planner answers the same in both and resolves no pair.

The exemplar runs as v6 scenario 101 (worlds 1011 claim true, 1012) at N = 1.34396 (`exemplar/WORLDS6.json`).
