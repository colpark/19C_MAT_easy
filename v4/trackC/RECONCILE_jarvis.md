# RECONCILE_jarvis (C2)

Card: CARD_jarvis.json (C1). Deposit: figshare 21370572 (1,058 records). Parent: jarvis-tools dft_3d_2021 (55712 entries; 894 of 1,058 jids present, the rest from the 2025 dft_3d for B1 and atoms only).

## Stage counts

| Stage | Stated | Ours | Class |
|---|---|---|---|
| J0 entries with DOS | 55,723 | dft_3d_2021 holds 55712 entries | rounding / versioning (11 fewer) |
| (elastic tensors) | 17,419 | 17439 with a usable elastic tensor | rounding / versioning (+20) |
| J1 theta_D > 300 K | 5,618 | 8166 (jarvis-tools ElasticTensor.debye_temperature, VRH) | rule ambiguity: +2548 (45 %); J1 not keyable |
| J2 N(0) > 1 states/eV/Nelect | 1,736 | not recountable (no DOS-at-E_F field) | missing records |
| J3 n_atoms <= 5 | 1,058 | 864 of the 1,058 have <= 5 atoms as deposited | rule ambiguity (cell basis) + "as of now" subset |
| J4 EPC computed | 1,058 | 1058 | reconciles |
| J5 Tc >= 5 K | 283 (Fig. 1) | 283 | reconciles |
| J6 dynamically stable | 626 of 1,058 (text); 105 after J5 (Fig. 1) | stable 626; stable and Tc >= 5 K: 105 | reconciles |

Our theta_D on the 1,058 survivors: 1028 of 1044 above 300 K (the authors' own J1 survivors).

## Second route: lambda, omega_log, Tc recomputed from alpha2F (meV axis; eq. 6-8, mu* = 0.09, no f1 f2)

- records with a finite recomputation: 1047 of 1058
- Tc ours - deposited: median -0.035 K, robust SD 0.354 K, p95 |diff| 4.91 K, max 20.32 K
- lambda relative: median -0.0197, robust SD 0.0768
- frozen tau_Tc = max(0.707 K, 0.05 Tc); tau_lambda = 0.154; records where both routes agree: 643 of 1058

## Eliminating stage (frozen readings: Tc >= 5 K; a double failure is order-dependent and never keyed)

| eliminating stage | n | keyable (routes agree, not near 5 K) |
|---|---|---|
| J5_tc | 521 | 446 |
| J5|J6 (order-dependent) | 254 | 0 |
| J6_stability | 178 | 19 |
| survived | 105 | 0 |

Fate needs keyable rejects on at least 3 stages (skill C0). JARVIS keys rejects at J5 and J6 only (J1 fails reconciliation, J2 has no field, J3 is ambiguous): the Fate and Route families are not built (VC-E19, I5).

