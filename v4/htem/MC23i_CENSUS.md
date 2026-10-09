# MC v2.3 MV1i: L4 validity amendment (HTEM_MC2_RULES_v23i.md)

**Disclosure:** post-hoc change on seen data; no fresh HTEM data remains. 0 requests (cached COD search entries).

**Includable:** L8, L4, L7r. **Release label:** L8 confirmed on F2; L4 re-derived after VM-E10 and L7r new, both without fresh confirmation.

| L4 | MV1h | MV1i | MV1i without pinned |
|---|---|---|---|
| critical (systems) | 62 (16) | 46 (14) | 37 (14) |
| decided | 68 | 52 | 42 |
| C2 | 0.70 | 0.69 | 0.7 |
| Vegard k/n | 6/68 | 6/52 (p=0.979) | 5/42 |
| includable | True | True | True |

## 1. Consensus cells: end members shifted by more than 0.5 %

Cells compared as Niggli-reduced cells; an entry counts when its reduced cell is within 5 % per length and 3 deg per angle of the phase's own (VM-E11).

| Phase | Entries (same formula and sg / matched) | a | b | c |
|---|---|---|---|---|
| Co sg225 COD 1534891 | 5 / 5 | +3.63% | +3.63% | +3.63% |
| Fe sg225 COD 1534888 | 33 / 32 | +2.52% | +2.52% | +2.52% |
| Ni sg225 COD 1534892 | 51 / 51 | +2.42% | +2.42% | +2.42% |
| ZnO sg186 COD 2300116 | 14 / 14 | +1.69% | +1.69% | +1.98% |
| Ba sg165 COD 1525957 | 2 / 2 | +1.30% | +1.30% | -1.83% |
| ZnSe sg216 COD 1538613 | 3 / 3 | -1.83% | -1.83% | -1.83% |
| Mo sg225 COD 1534907 | 2 / 2 | +1.61% | +1.61% | +1.61% |
| Se sg152 COD 1534711 | 3 / 3 | +1.54% | +1.54% | +1.30% |
| Ti sg194 COD 1532765 | 5 / 5 | +1.50% | +1.50% | +0.41% |
| MnO2 sg62 COD 8103498 | 7 / 6 | -0.55% | +1.44% | +0.46% |
| TiO sg225 COD 1536851 | 2 / 2 | -1.36% | -1.36% | -1.36% |
| Cu2S sg225 COD 1530508 | 2 / 2 | +1.19% | +1.19% | +1.19% |
| Y sg194 COD 1531279 | 3 / 3 | -0.32% | -0.32% | -1.16% |
| Cr sg225 COD 1534885 | 2 / 2 | +1.11% | +1.11% | +1.11% |
| SnSe sg62 COD 1537675 | 4 / 4 | +1.10% | +0.10% | +0.47% |
| Cu2Se sg225 COD 1525030 | 4 / 4 | -1.03% | -1.03% | -1.03% |
| Ti4O7 sg2 COD 1008050 | 5 / 5 | -0.52% | -0.95% | +0.52% |
| Sb sg194 COD 1539203 | 3 / 2 | -0.58% | -0.58% | -0.94% |
| MgMn2O4 sg141 COD 1528844 | 2 / 2 | +0.23% | +0.23% | -0.82% |
| Fe sg229 COD 2300200 | 15 / 15 | +0.79% | +0.79% | +0.79% |
| Sb2Se3 sg62 COD 1537807 | 4 / 4 | +0.77% | -0.23% | +0.35% |
| SrO sg225 COD 1011328 | 7 / 7 | +0.70% | +0.70% | +0.70% |
| MnTe sg186 COD 9008873 | 2 / 2 | +0.68% | +0.68% | +0.02% |
| SnS2 sg164 COD 7038075 | 17 / 7 | +0.05% | +0.05% | +0.63% |
| TiCo3 sg221 COD 1523987 | 2 / 2 | -0.59% | -0.59% | -0.59% |
| ZnCr2O4 sg227 COD 1011278 | 12 / 12 | +0.57% | +0.57% | +0.57% |
| InCuS2 sg122 COD 1542205 | 3 / 3 | +0.10% | +0.10% | +0.54% |
| Ni sg194 COD 9008509 | 2 / 2 | -0.53% | -0.53% | -0.10% |
| Mn2Sn sg194 COD 1523342 | 3 / 3 | -0.27% | -0.27% | -0.52% |

End members: 219; with only their own entry matched: 113; entries of the same formula and sg not matched (other setting or polytype handled / excluded): 77.

**Critical/control flips against MV1h (7):**

- 10667|x0=0.2 Mn/Zn [1010117, 1538613]: critical -> control (key 5.7028 -> 5.7028)
- 6725|x0=0.65 Ni/Co [1010093, 1533087]: critical -> control (key 4.2088 -> 4.2088)
- 6791|x0=0.5 Ti/Co [1532765, 9008492]: critical -> control (key 2.9417 -> 2.0836)
- 6821|x0=0.5 Ti/Co [1532765, 9008492]: critical -> control (key 2.9366 -> 2.0794)
- 6908|x0=0.35 Co/Zn [1533087, 1534836]: control -> critical (key 4.2806 -> 4.2806)
- 7104|x0=0.8 S/Se [1537798, 9008725]: control -> critical (key 2.8530 -> 5.9030)
- 9270|x0=0.5 Ti/Co [1532765, 9008492]: control -> critical (key 2.9645 -> 2.1047)

**Facts gone (16):** ['10793|x0=0.2', '10793|x0=0.35', '6679|x0=0.65', '6706|x0=0.2', '6760|x0=0.35', '7118|x0=0.2', '7118|x0=0.35', '7161|x0=0.35', '7345|x0=0.65', '7345|x0=0.8', '7412|x0=0.65', '7579|x0=0.5', '8506|x0=0.5', '8507|x0=0.35', '8507|x0=0.5', '8508|x0=0.5']

**Facts added (0):** []

## 2. Axial ratio

| Pair | c/a A | c/a B | difference |
|---|---|---|---|
| Sn/V (SnO2 sg136 COD 1000062 / VO2 sg136 COD 1537412) | 0.6727 | 0.6333 | 6.2% |
| Ti/V (Ti6O11 sg2 COD 1008195 / V6O11 sg2 COD 1530102) | 5.8055 | 5.5182 | 5.2% |
| Ti/V (Ti8O15 sg2 COD 1008197 / V8O15 sg2 COD 8103815) | 7.9730 | 7.5074 | 6.2% |
| Te/Se (Te sg152 COD 1011098 / Se sg152 COD 1534711) | 1.3294 | 1.1345 | 17.2% |
| S/Se (Sb2S3 sg62 COD 1011154 / Sb2Se3 sg62 COD 1537807) | 0.3414 | 0.9873 | 65.4% |
| S/Se (SnS sg62 COD 1011253 / SnSe sg62 COD 1537675) | 2.8091 | 0.3880 | 624.0% |
| Sn/In (SnS sg62 COD 1011253 / InS sg62 COD 9008787) | 2.8091 | 0.8870 | 216.7% |
| Ti/Mo (Ti2N sg141 COD 1100029 / Mo2N sg141 COD 1541975) | 2.1221 | 1.9048 | 11.4% |
| Ag/Zn (Ag sg194 COD 1509145 / Zn sg194 COD 9008522) | 1.6348 | 1.8563 | 11.9% |
| Sn/Ta (CoSn2 sg140 COD 1524261 / Ta2Co sg140 COD 1524529) | 0.8573 | 0.8125 | 5.5% |
| Ta/Zr (Ta2Co sg140 COD 1524529 / Zr2Co sg140 COD 1524514) | 0.8125 | 0.8671 | 6.3% |
| Ti/Nb (Ti6Sn5 sg71 COD 1528270 / Nb6Sn5 sg71 COD 2310946) | 0.3387 | 2.9779 | 88.6% |
| Mn/Cr (MgMn2O4 sg141 COD 1528844 / MgCr2O4 sg141 COD 1533115) | 1.6042 | 1.4115 | 13.6% |
| Ti/Co (TiSb sg194 COD 1531830 / CoSb sg194 COD 1541039) | 1.5268 | 1.3262 | 15.1% |
| V/Fe (V2O3 sg15 COD 1532125 / Fe2O3 sg15 COD 2108027) | 0.7627 | 1.4297 | 46.7% |
| Ti/Zn (Ti sg194 COD 1532765 / Zn sg194 COD 9008522) | 1.5885 | 1.8563 | 14.4% |
| In/Sn (In sg139 COD 1538014 / Sn sg139 COD 1540069) | 1.5212 | 1.8329 | 17.0% |
| In/Sb (In sg139 COD 1538014 / Sb sg139 COD 9013010) | 1.5212 | 1.6478 | 7.7% |
| Sb/Zn (Sb sg194 COD 1539203 / Zn sg194 COD 9008522) | 1.5764 | 1.8563 | 15.1% |
| Sn/Ga (Sn sg139 COD 1540069 / Ga sg139 COD 9012723) | 1.8329 | 1.5876 | 15.4% |
| Sn/Sb (Sn sg139 COD 1540069 / Sb sg139 COD 9013010) | 1.8329 | 1.6478 | 11.2% |
| Ti/Mn (TiO2 sg62 COD 1544349 / MnO2 sg62 COD 8103498) | 0.6035 | 0.3086 | 95.6% |
| Se/S (SnSe2 sg164 COD 1548805 / SnS2 sg164 COD 7038075) | 1.6102 | 1.4422 | 11.7% |
| Mg/Zn (Mg sg194 COD 1575875 / Zn sg194 COD 9008522) | 1.6236 | 1.8563 | 12.5% |
| Mn/V (MnO2 sg62 COD 8103498 / VO2 sg62 COD 9000071) | 0.3086 | 0.5992 | 48.5% |
| Mn/Fe (MnO2 sg62 COD 8103498 / FeO2 sg62 COD 9011412) | 0.3086 | 0.6601 | 53.2% |
| Co/Zn (Co sg194 COD 9008492 / Zn sg194 COD 9008522) | 1.6271 | 1.8563 | 12.3% |
| Cr/Zn (Cr sg194 COD 9008493 / Zn sg194 COD 9008522) | 1.6256 | 1.8563 | 12.4% |
| Ni/Zn (Ni sg194 COD 9008509 / Zn sg194 COD 9008522) | 1.6409 | 1.8563 | 11.6% |
| Zn/Y (Zn sg194 COD 9008522 / Y sg194 COD 1531279) | 1.8563 | 1.5740 | 17.9% |
| Zn/Sr (Zn sg194 COD 9008522 / Sr sg194 COD 1540836) | 1.8563 | 1.6357 | 13.5% |
| Zn/Zr (Zn sg194 COD 9008522 / Zr sg194 COD 9008523) | 1.8563 | 1.5925 | 16.6% |
| Se/Te (Se sg154 COD 9008579 / Te sg154 COD 9008580) | 1.1365 | 1.3301 | 14.6% |
| Mn/Cr (MnHO2 sg62 COD 9009153 / CrHO2 sg62 COD 9010009) | 0.6277 | 0.6621 | 5.2% |

Facts of MV1h on dropped pairs: ['10793|x0=0.2', '10793|x0=0.35', '6679|x0=0.65', '6706|x0=0.2', '6760|x0=0.35', '7118|x0=0.2', '7118|x0=0.35', '7161|x0=0.35', '7345|x0=0.65', '7345|x0=0.8', '7412|x0=0.65', '8506|x0=0.5', '8507|x0=0.35', '8507|x0=0.5', '8508|x0=0.5'].

**Sn/Ta (CoSn2/Ta2Co) c/a:** [{'pair': 'Sn/Ta', 'ca_A': 0.8573448546739983, 'ca_B': 0.8124591236102029, 'ca_diff': 0.055246756125210794}]

## 3. Pinned (report only): {'facts': 10, 'critical': 9, 'libraries': ['10668', '6821', '7221', '8392', '8395']}

## L4 critical by pair (MV1i): {'Ni/Co [1010093, 1533087]': 3, 'S/Te [1537798, 1539753]': 5, 'Mn/Zn [1514099, 1534836]': 4, 'Ti/Co [1532765, 9008492]': 5, 'Co/Zn [1533087, 1534836]': 3, 'Mn/Zn [1010117, 1538613]': 3, 'Te/Se [1010538, 1538613]': 2, 'S/Se [1537798, 9008725]': 1, 'Ca/Sn [1011236, 1537798]': 2, 'In/Fe [4343793, 5910082]': 2, 'In/Mn [1010341, 1010586]': 6, 'Sn/Mn [1000062, 2105790]': 3, 'Cr/Mn [1516110, 2105790]': 1, 'Se/Te [1010097, 1011352]': 4, 'Zn/Mn [2300116, 4117966]': 2}

## L4 critical by system (MV1i): {'Mn-O-Zn': 6, 'Co-Ni-O-Zn': 5, 'S-Sn-Te': 5, 'Co-Sb-Ti': 5, 'Mn-Se-Te-Zn': 5, 'Mn-Se-Te': 4, 'In-Mn-O': 3, 'H-In-Mn-O': 3, 'Mn-O-Sn': 3, 'Ca-S-Sn': 2, 'Fe-In-O': 2, 'Co-O-Zn': 1, 'S-Se-Sn': 1, 'Cr-Mn-O': 1}

## Probe statement

L1 probe: the naive answer is invalid in only 4 of 22 libraries, so it cannot carry an intention claim (diagnostic only).
