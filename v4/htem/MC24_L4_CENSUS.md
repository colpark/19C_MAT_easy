# MC v2.4 MV1k: L4 v2.4 census and L8 v2.4 keys (HTEM_MC2_RULES_v24.md)

Scope: 483 non-dev fully cached libraries. 0 requests. **Disclosure:** the L4 redesign and the L8 stem follow the v2.3 Sonnet results (post hoc); no fresh HTEM data remains.

**L4 v2.4 includable: NO.**

| L4 v2.4 | count |
|---|---|
| SS critical (systems; test) | 5 (4; 1) |
| SS control available / in mix | 0 / 0 |
| NSS available / in mix (systems; test) | 9 / 2 (2; 0) |
| UND or dropped facts | 31 |
| mix (test) | 7 (1) |
| C2 on SS mix (pairs) | 1.0 (1) |
| C1 (Vegard fails every critical) | True |

**Library status:** {'P < 10': 109, None: 283, 'no x0': 11, 'ok': 31, 'no fallback: ground state': 40, 'no fallback: axial': 9}

**NSS by reason (all / mix):** {'slope': 9} / {'slope': 2}

**UND and dropped by reason:** {'N < 3': 13, 'r undefined (Vegard change < 4 tol)': 11, 'NSS dropped: Vegard within tol of an accepted value': 4, 'UND (neither SS nor NSS)': 3}

## Cheap rules (cap 35 % of the mix; v21 binomial form reported, c = SS control share)

| Rule | k/n | cap | v21 binomial p | SS critical | SS control | NSS |
|---|---|---|---|---|---|---|
| Vegard | 0/7 (0.00) | ok | 1.000 | 0/5 | 0/0 | 0/2 |
| always CANNOT DETERMINE | 2/7 (0.29) | ok | 0.150 | 0/5 | 0/0 | 2/2 |
| nearer end member | 2/7 (0.29) | ok | 0.150 | 1/5 | 0/0 | 1/2 |
| library median | 7/7 (1.00) | FAIL | 0.000 | 5/5 | 0/0 | 2/2 |

**Effect (SS critical, |Vegard − key|, Å):** median 0.1249 (p10 0.0422, p90 0.1869). **NSS r (mix):** {'median': -0.03351279231340573, 'min': -0.08906630847408811, 'max': 0.022040723847276653}.

## By system

| System | SS critical | SS control | NSS | UND/dropped |
|---|---|---|---|---|
| Ca-S-Sn | 0 | 0 | 0 | 2 |
| Co-Ni-O | 0 | 0 | 0 | 1 |
| Co-Ni-O-Zn | 0 | 0 | 0 | 5 |
| Co-O-Zn | 0 | 0 | 0 | 1 |
| Cr-Mn-O | 0 | 0 | 0 | 1 |
| Fe-In-O | 0 | 0 | 0 | 3 |
| H-In-Mn-O | 0 | 0 | 3 | 0 |
| In-Mn-O | 0 | 0 | 3 | 1 |
| Mn-O-Sn | 1 | 0 | 0 | 2 |
| Mn-O-Zn | 1 | 0 | 2 | 3 |
| Mn-Se-Te | 1 | 0 | 1 | 2 |
| Mn-Se-Te-Zn | 2 | 0 | 0 | 4 |
| S-Se-Sn | 0 | 0 | 0 | 1 |
| S-Sn-Te | 0 | 0 | 0 | 5 |

## Against MV1i (every MV1i L4 fact)

**Summary:** {'class': 31, 'kept as SS critical': 5, 'no fallback': 7, 'kept as NSS': 9}

**MV1i fallback facts** (MV1i pair differs from the v21 choice): 8

| MV1i fact | MV1i mix | MV1i class | MV1i pair | v2.4 pair | v2.4 |
|---|---|---|---|---|---|
| 10667|x0=0.2 | yes | control | Mn/Zn [1010117, 1538613] | Mn/Zn [1010117, 1538613] | class: r undefined (Vegard change < 4 tol) |
| 10667|x0=0.35 | yes | critical | Mn/Zn [1010117, 1538613] | Mn/Zn [1010117, 1538613] | class: r undefined (Vegard change < 4 tol) |
| 10668|x0=0.5 | yes | critical | Mn/Zn [1010117, 1538613] | Mn/Zn [1010117, 1538613] | class: N < 3 |
| 10668|x0=0.65 | yes | critical | Mn/Zn [1010117, 1538613] | Mn/Zn [1010117, 1538613] | class: N < 3 |
| 10670|x0=0.8 | yes | critical | Te/Se [1010538, 1538613] | Te/Se [1010538, 1538613] | kept as SS critical |
| 10674|x0=0.65 | yes | critical | Te/Se [1010538, 1538613] | Te/Se [1010538, 1538613] | kept as SS critical |
| 6663|x0=0.2 | yes | critical | Ca/Sn [1011236, 1537798] | Ca/Sn [1011236, 1537798] | class: r undefined (Vegard change < 4 tol) |
| 6663|x0=0.35 | yes | critical | Ca/Sn [1011236, 1537798] | Ca/Sn [1011236, 1537798] | class: N < 3 |
| 6715|x0=0.35 | yes | critical | Zn/Mn [2300116, 4117966] | Zn/Mn [2300116, 4117966] | kept as SS critical |
| 6715|x0=0.5 | yes | critical | Zn/Mn [2300116, 4117966] | Zn/Mn [2300116, 4117966] | class: r undefined (Vegard change < 4 tol) |
| 6725|x0=0.65 | yes | control | Ni/Co [1010093, 1533087] | Ni/Co [1010093, 1533087] | class: r undefined (Vegard change < 4 tol) |
| 6791|x0=0.5 | yes | control | Ti/Co [1532765, 9008492] | Ti/Sb [1532765, 1539203] | no fallback: ground state |
| 6811|x0=0.35 | yes | critical | Co/Zn [1533087, 1534836] | Co/Zn [1533087, 1534836] | class: r undefined (Vegard change < 4 tol) |
| 6821|x0=0.35 | yes | critical | Ti/Co [1532765, 9008492] | Ti/Sb [1532765, 1539203] | no fallback: ground state |
| 6821|x0=0.5 | yes | control | Ti/Co [1532765, 9008492] | Ti/Sb [1532765, 1539203] | no fallback: ground state |
| 6907|x0=0.8 | yes | critical | S/Te [1537798, 1539753] | S/Te [1537798, 1539753] | class: N < 3 |
| 6908|x0=0.35 | yes | critical | Co/Zn [1533087, 1534836] | Co/Zn [1533087, 1534836] | class: r undefined (Vegard change < 4 tol) |
| 6927|x0=0.65 | yes | critical | S/Te [1537798, 1539753] | S/Te [1537798, 1539753] | class: N < 3 |
| 6927|x0=0.8 | yes | critical | S/Te [1537798, 1539753] | S/Te [1537798, 1539753] | class: N < 3 |
| 6943|x0=0.5 | yes | critical | Ni/Co [1010093, 1533087] | Ni/Co [1010093, 1533087] | class: r undefined (Vegard change < 4 tol) |
| 6943|x0=0.65 | yes | critical | Ni/Co [1010093, 1533087] | Ni/Co [1010093, 1533087] | class: r undefined (Vegard change < 4 tol) |
| 6946|x0=0.65 | yes | critical | Mn/Zn [1514099, 1534836] | Mn/Zn [1514099, 1534836] | class: N < 3 |
| 6946|x0=0.8 | yes | critical | Mn/Zn [1514099, 1534836] | Mn/Zn [1514099, 1534836] | class: UND (neither SS nor NSS) |
| 6997|x0=0.5 | yes | critical | Se/Te [1010097, 1011352] | Se/Te [1010097, 1011352] | kept as SS critical |
| 7104|x0=0.8 | yes | critical | S/Se [1537798, 9008725] | S/Se [1011253, 1537675] | class: r undefined (Vegard change < 4 tol) (other pair) |
| 7161|x0=0.5 | yes | critical | Ti/Co [1532765, 9008492] | Ti/Sb [1532765, 1539203] | no fallback: ground state |
| 7167|x0=0.5 | yes | critical | Co/Zn [1533087, 1534836] | Co/Zn [1533087, 1534836] | class: N < 3 |
| 7177|x0=0.35 | yes | critical | S/Te [1537798, 1539753] | S/Te [1537798, 1539753] | class: N < 3 |
| 7221|x0=0.35 | yes | critical | Mn/Zn [1514099, 1534836] | Mn/Zn [1514099, 1534836] | kept as NSS |
| 7221|x0=0.65 | yes | critical | Mn/Zn [1514099, 1534836] | Mn/Zn [1514099, 1534836] | kept as NSS |
| 7378|x0=0.35 | yes | critical | Se/Te [1010097, 1011352] | Se/Te [1010097, 1011352] | kept as NSS |
| 7392|x0=0.2 | yes | critical | Ni/Co [1010093, 1533087] | Ni/Co [1010093, 1533087] | class: N < 3 |
| 7408|x0=0.65 | yes | critical | S/Te [1537798, 1539753] | S/Te [1537798, 1539753] | class: N < 3 |
| 7439|x0=0.5 | yes | critical | Cr/Mn [1516110, 2105790] | Cr/Mn [1516110, 2105790] | class: N < 3 |
| 7635|x0=0.35 | yes | critical | Se/Te [1010097, 1011352] | Se/Te [1010097, 1011352] | class: UND (neither SS nor NSS) |
| 7635|x0=0.5 | yes | critical | Se/Te [1010097, 1011352] | Se/Te [1010097, 1011352] | class: UND (neither SS nor NSS) |
| 8350|x0=0.5 | yes | critical | In/Fe [4343793, 5910082] | In/Fe [4343793, 5910082] | class: NSS dropped: Vegard within tol of an accepted value |
| 8352|x0=0.5 | yes | critical | In/Fe [4343793, 5910082] | In/Fe [4343793, 5910082] | class: NSS dropped: Vegard within tol of an accepted value |
| 8352|x0=0.65 | yes | control | In/Fe [4343793, 5910082] | In/Fe [4343793, 5910082] | class: NSS dropped: Vegard within tol of an accepted value |
| 8392|x0=0.65 | yes | critical | In/Mn [1010341, 1010586] | In/Mn [1010341, 1010586] | kept as NSS |
| 8392|x0=0.8 | yes | critical | In/Mn [1010341, 1010586] | In/Mn [1010341, 1010586] | kept as NSS |
| 8393|x0=0.8 | yes | critical | In/Mn [1010341, 1010586] | In/Mn [1010341, 1010586] | kept as NSS |
| 8394|x0=0.35 | yes | critical | In/Mn [1010341, 1010586] | In/Mn [1010341, 1010586] | kept as NSS |
| 8394|x0=0.5 | yes | control | In/Mn [1010341, 1010586] | In/Mn [1010341, 1010586] | class: NSS dropped: Vegard within tol of an accepted value |
| 8395|x0=0.65 | yes | critical | In/Mn [1010341, 1010586] | In/Mn [1010341, 1010586] | kept as NSS |
| 8395|x0=0.8 | yes | critical | In/Mn [1010341, 1010586] | In/Mn [1010341, 1010586] | kept as NSS |
| 8431|x0=0.5 | yes | critical | Sn/Mn [1000062, 2105790] | Sn/Mn [1000062, 2105790] | class: r undefined (Vegard change < 4 tol) |
| 8431|x0=0.65 | yes | critical | Sn/Mn [1000062, 2105790] | Sn/Mn [1000062, 2105790] | kept as SS critical |
| 8450|x0=0.2 | yes | critical | Sn/Mn [1000062, 2105790] | Sn/Mn [1000062, 2105790] | class: N < 3 |
| 9270|x0=0.5 | yes | critical | Ti/Co [1532765, 9008492] | Ti/Sb [1532765, 1539203] | no fallback: ground state |
| 9272|x0=0.5 | yes | critical | Ti/Co [1532765, 9008492] | Ti/Sb [1532765, 1539203] | no fallback: ground state |
| 9273|x0=0.5 | yes | critical | Ti/Co [1532765, 9008492] | Ti/Sb [1532765, 1539203] | no fallback: ground state |

**Facts new in v2.4:** []

**Space-group check of the standardized end members:** {'Ag2O sg201 COD 1010604': {'sg_cod': '201', 'sg_detected': 224}, 'Ba sg165 COD 1525957': {'sg_cod': '165', 'sg_detected': 193}, 'MgCr2O4 sg141 COD 1533115': {'sg_cod': '141', 'sg_detected': 227}, 'Cu2O sg201 COD 9005769': {'sg_cod': '201', 'sg_detected': 224}, 'Sr sg165 COD 4123971': {'sg_cod': '165', 'sg_detected': 193}}

## L8 v2.4 keys (threshold 3 sigma_s)

Items 124; critical 87; keys moved against MV1h 12; critical/control flips 0; naive zero correct 0.298.

sigma_s by system: {'Ag-O-V': 0.032, 'Ba-Co-Fe-O-Zr': 0.032, 'Ba-Co-Fe-Y-Zr': 0.032, 'Ba-Cr-O': 0.032, 'Ba-Cu-S': 0.032, 'Ba-Fe-O-Y-Zr': 0.032, 'Co-Ni-O': 0.032, 'Co-Ni-O-Zn': 0.032, 'Co-Sn-Ta': 0.032, 'Cr-Cu': 0.032, 'Cr-Mg-O': 0.032, 'Cr-Mn-O': 0.032, 'Cr-O-Zn': 0.032, 'Cu-Ge-S': 0.032, 'Cu-In-S': 0.032, 'Cu-N': 0.098, 'Cu-N-Sn': 0.032, 'Cu-N-Ta': 0.032, 'Cu-O-S-Zn': 0.032, 'Cu-O-Se-Zn': 0.032, 'Cu-O-Zn': 0.032, 'Cu-S-Sb': 0.032, 'Cu-S-Sn': 0.032, 'Cu-S-Sr': 0.032, 'Fe-In-O': 0.032, 'Fe-N': 0.032, 'Ga-H-O-Zn': 0.032, 'Ga-O-Zn': 0.032, 'Ga-Sn': 0.032, 'Ge-N-Zn': 0.032, 'H-In-Mn-O': 0.032, 'H-Mn-O-Sn': 0.032, 'H-O-Ti-Zn': 0.032, 'In-Mn-O': 0.032, 'In-O-Sn-Zn': 0.032, 'In-S': 0.032, 'Mg-O-Zn': 0.032, 'Mn-O': 0.026, 'Mn-O-Sn': 0.032, 'Mn-O-Zn': 0.032, 'Mn-Se-Te-Zn': 0.038, 'N-Sb': 0.032, 'N-Sb-Zn': 0.032, 'N-Sn-Zn': 0.027, 'N-Ta': 0.032, 'N-Ti': 0.032, 'O-Sn-Sr': 0.032, 'O-Sn-Ti-Zn': 0.032, 'O-Sn-Zn': 0.032, 'O-Ti-Zn': 0.032, 'Sn-Ti-Zn': 0.032, 'Sn-Zn': 0.032}

| Item | System | sigma_A | stated 3 sigma_s | key MV1h | key v2.4 |
|---|---|---|---|---|---|
| 7079 | In-O-Sn-Zn | 0.0324 | 0.096 | 42 | 43 |
| 7461 | In-O-Sn-Zn | 0.0324 | 0.096 | 33 | 36 |
| 7219 | In-O-Sn-Zn | 0.0324 | 0.096 | 33 | 34 |
| 8338 | Ga-O-Zn | 0.0324 | 0.096 | 23 | 25 |
| 6638 | Ga-O-Zn | 0.0324 | 0.096 | 18 | 19 |
| 8350 | Fe-In-O | 0.0324 | 0.096 | 28 | 30 |
| 9859 | H-O-Ti-Zn | 0.0324 | 0.096 | 26 | 27 |
| 7192 | In-O-Sn-Zn | 0.0324 | 0.096 | 7 | 18 |
| 6839 | Ga-O-Zn | 0.0324 | 0.096 | 10 | 12 |
| 7373 | Ga-O-Zn | 0.0324 | 0.096 | 33 | 34 |
| 7879 | Cu-O-Zn | 0.0324 | 0.096 | 2 | 3 |
| 11915 | Ge-N-Zn | 0.0324 | 0.096 | 0 | 1 |
