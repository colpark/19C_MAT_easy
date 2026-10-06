# Held-out fidelity test sets (frozen before any F6 read)

Frozen 2026-10-05T22:39:49-05:00. Spec: fidelity/heldout_spec.py sha256 02bae8c44e1b553cff28410eb3fa2bbdb99c92f12cd21ad38f2fec450c1022a4; truths: fidelity/heldout_truth.json sha256 4c6273b90109e8cc497ae7522caf31e4a06a5e1544efe21d62574bd6aba7691a (250 rows).

## Selection (external)

Rule: Nature search result order (query "source data", materials science, 2025-2026, relevance; Communications Materials and Nature Communications pages saved under v32_host/fidelity/search), taking materials papers whose xlsx Source Data sheets are named by main-text figure and pass a printed-number check.

| order | article | outcome |
|---|---|---|
| commsmat 1 | 10.1038/s43246-026-01198-7 | skipped: 11 xlsx files with unnamed sheets |
| commsmat 2 | 10.1038/s43246-026-01347-y | **X2** (printed check below) |
| commsmat 3 | 10.1038/s43246-026-01193-y | **X1** |
| ncomms 1 | 10.1038/s41467-026-77390-7 | skipped: no printed number checkable (panels print none; article HTML holds the abstract only) |
| ncomms 2 | 10.1038/s41467-026-78108-5 | **X3** |
| ncomms 3 | 10.1038/s41467-026-77568-z | **X4** |
| ncomms (between) | 69825-y, 78109-4 (biology), 78091-x | 78091-x skipped: printed "cooling ~7.7 C" not reproducible as a maximum (8.4) |

| set | DOI | journal | printed-number check |
|---|---|---|---|
| X1 | 10.1038/s43246-026-01193-y | Communications Materials | Fig. 2a [Al] = 51 at.%, [N] = 47 at.% vs sheet Fig. 2a mean over 10-30 nm: 51.0, 47.0 |
| X2 | 10.1038/s43246-026-01347-y | Communications Materials | Fig. 10c marked point 1.2 m/s at 500 Pa vs sheet Fig. 10(c): p3(1.2 m/s) = 500 Pa |
| X3 | 10.1038/s41467-026-78108-5 | Nature Communications | Fig. 5d S1 = 0.17 mV/kPa, S2 = 0.0023 mV/kPa vs sheet Figure 5 linear fits: 0.170, 0.00234 |
| X4 | 10.1038/s41467-026-77568-z | Nature Communications | Fig. 4d bar label 12 % vs sheet Figure 4 xi_z/xi_y at alpha = 0: 0.1198 |

## Files (sha256; host only, never in git)

- X1 `43246_2026_1193_Fig1_HTML.png` 781393 B 9f843dda98e9659c1dc8b15ac86f46417e49428bcd537e44bb4d7b8e390efcfa
- X1 `43246_2026_1193_Fig2_HTML.png` 1196627 B dabd6fe14beaaff13abe0c79aa8abde2c79708dc4eccbe9948e2a3daa6f14677
- X1 `43246_2026_1193_Fig3_HTML.png` 704896 B 554369b7758065cbc6d02e7c4e672d52909321127bd206733aa918e67e94b24c
- X1 `43246_2026_1193_Fig4_HTML.png` 1388246 B 793153567c52516266bd040789dd4659f7a08ae1f8caaf717adfcb2df7899dc4
- X1 `43246_2026_1193_Fig5_HTML.png` 676690 B 1555879a15e9ba931da857bf92e8f768f8a8b04dacee3648c5199efa0499d992
- X1 `43246_2026_1193_MOESM4_ESM.xlsx` 2578436 B b6fd59c3c1b3e75ff59ab4d70488be1dbacd98812900768bb97256e5732d616a
- X2 `43246_2026_1347_Fig10_HTML.png` 511941 B aa6846e6f19616a1b123e5a1aa11777e0503cb76b2a6ef4fc5c7727511c9133f
- X2 `43246_2026_1347_Fig11_HTML.png` 656605 B 760b6b4865c860db6a936aeb601381cd4db5dde378c92e511c1c015e4bbcc524
- X2 `43246_2026_1347_Fig12_HTML.png` 530119 B c943f07df587aebf464c34b1896f059c7490ce01eaec4e1296343c940016c689
- X2 `43246_2026_1347_Fig1_HTML.png` 2342730 B 3c7f879a778f79403705b11a712403e334b687a63c2bd4fc1c1539c3cc2c2354
- X2 `43246_2026_1347_Fig2_HTML.png` 615424 B 6270c29882866983ba7f5d4a36d16c80c5a71d9f8cf184857b4d4a08287af0bc
- X2 `43246_2026_1347_Fig3_HTML.png` 1164383 B 65304ac4e54ef257f7d64bda713288bdfc9a67c0c51031b7810f7408d764d582
- X2 `43246_2026_1347_Fig4_HTML.png` 341182 B fb304c92ce4769de71d01e178fbcb98db5fcca8f859a1400c8af2efe73521bd9
- X2 `43246_2026_1347_Fig5_HTML.png` 1003611 B ffd8bcbf9fed485edbc0b77da6544a3ad379544ae6779cf90ef48a0d653a6571
- X2 `43246_2026_1347_Fig6_HTML.png` 1048711 B 468f06745171acb4ab2882efb41e81bcc360db1f50986de96ad1574fff97902a
- X2 `43246_2026_1347_Fig7_HTML.png` 1247892 B 82f791b95f4f857df45470127ecf2db527cdf8dfe975349d9866a8dcc660ac95
- X2 `43246_2026_1347_Fig8_HTML.png` 1078545 B ce279e57437d7407da655ef4172894691f160d81d55ce17756602588fc73b864
- X2 `43246_2026_1347_Fig9_HTML.png` 764769 B 70ac284d72e1f541c7d8ba2ded7cc182a2495483bb59e4249ce7cf5209d9d3bf
- X2 `43246_2026_1347_MOESM2_ESM.xlsx` 235762 B bfe0e5f055981d5b29a0c4de2dce6a7a8c240343769d6a4d086f0270f7989d18
- X2 `43246_2026_1347_MOESM3_ESM.xlsx` 35012 B cb7f1273c91f8435efc8f81f02d36c16f49d62ee8fff734ffd9f62c65a0b36da
- X2 `43246_2026_1347_MOESM4_ESM.xlsx` 9155 B 5b02fff837682dcbcb61f437127fafcfca09c96b35f210d0cf938d64fd74e388
- X2 `43246_2026_1347_MOESM5_ESM.xlsx` 30370 B 5e239465c4c693c73c2640e605956a6e58fe644bfcc9546e32cbbb30d81a87ca
- X3 `41467_2026_78108_Fig1_HTML.png` 1570385 B 3e3e1bc20b2205c65497687bba3e5caef2a6b2573aee97ff6fb6f5fa1695bf6e
- X3 `41467_2026_78108_Fig2_HTML.png` 2850463 B e44bb46dc27ae37f7dc14d66ed8ac51dee7cee3adcf9bc5671ee76c3053f915d
- X3 `41467_2026_78108_Fig3_HTML.png` 2340740 B 1a5a67380526dde770615d0fab6fcddc4221ee06af6744197bd9f5b40277378e
- X3 `41467_2026_78108_Fig4_HTML.png` 1219463 B 7350b429808cf0b7c019bf9cdd2f310f2aca5cc2d0472300c0fc289075282673
- X3 `41467_2026_78108_Fig5_HTML.png` 1008935 B cb1c71276d091353f7356a0f08bf748f60cff805dc0090672bac2a2f6e3ddd1d
- X3 `41467_2026_78108_MOESM3_ESM.xlsx` 13353119 B c6164e7309f9cf3167d54da6e5e1bb1d955e51a5d2daa1a59318d100b44dd434
- X4 `41467_2026_77568_Fig1_HTML.png` 242799 B af5fabc56d077d73080d6cec1630826f61722ef101409f2a083a5179a6585f9d
- X4 `41467_2026_77568_Fig2_HTML.png` 145387 B 02ef13442bb4646f408e3f73cce046b9aff9b60df1df3654eaaee77ce8a7bc08
- X4 `41467_2026_77568_Fig3_HTML.png` 402095 B ad4dd765dc3a12e2a9b4fee66b1d4fc0064757dd874c168ae6a09d6c8b30cd0a
- X4 `41467_2026_77568_Fig4_HTML.png` 182235 B 76f5e610eee5a60b01c94b6d8117c0e5f417168b6ee10fd9d12ac4f3a78e4585
- X4 `41467_2026_77568_Fig5_HTML.png` 48262 B bc33a5d097a04b99350cec8bae46cd9dd4f9bd0565142df48e7a89b45e13cae6
- X4 `41467_2026_77568_MOESM3_ESM.xlsx` 61211 B 17cffe4f96af944408ace2b9208ce03b82c34a619c2eb25d9844a409849dc4ec

## Internal set (test only, never keys)

S098 F5b, F5c (Table 1), F6a (Table 2), F7h (Table 3); S039 F16 (Table 4), F8 (Table 1 D_DS). Crops:
- s098 F5b 41ed8042ea80669f004c27419e2359449f8239a834a5002d094490c365fb259f
- s098 F5c f59515efcfb5ab5339df586b236c59c5eedf88ed995a9915febb54e53b005e3b
- s098 F6a 843709e55d1fbf719780727af8692dd734a7a547e523d298c64d8173f33563dd
- s098 F7h c08961f5c0b6c51422f83a771cdd1d8f6fc6cdae5e8e7e2c58cd2d07128e7f56
- s039 F16 f16d2264751b3e1a5aa5707f26d54583fe34c6df8319b2a7255cfc963eb00d16
- s039 F8 fb818b29ee6efe4c1525ca28f26e287e348c18fa016b091ab1de680ca31f7426

## Test cases per set and feature type

| feature type | external | internal |
|---|---|---|
| peak_x | 22 | 0 |
| y_at_x | 65 | 6 |
| plateau | 8 | 6 |
| extremum | 34 | 5 |
| crossing | 12 | 12 |
| bar_top | 39 | 22 |
| x_end | 14 | 5 |

Reader inputs (colours, legend/inset boxes, declared ticks, sub-frame crops) are set after the F6 freeze, before the run, and logged in fidelity/heldout_inputs.json.
