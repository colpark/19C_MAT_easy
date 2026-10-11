# Stage 2r constraints (v5 section 3; D.3 r3, r4 amended X28), checked by code (`mcenv/tune2r.py --pairs`, v5 plan grid)

"Everything at best quality" exceeds 180 min by arithmetic (C2c).

| world | scen | D(m0) | cheapest D>=25 (min) | best affordable D | best 10-70 D | neutron D | checks |
|---|---|---|---|---|---|---|---|
| 401 | 41 | 8742.33 | 0.0 | 1131458.0 | 1131458.0 | 57877.0 | C1 yes |
| 402 | 41 | 7266.81 | 0.0 | 554019.6 | 554019.6 | 34441.2 | C1 yes |
| 403 | 42 | 4.22 | 8.367 | 62779.6 | 628.6 | 62577.2 | C2a yes, C2b yes, r4_strict no, r4 yes |
| 404 | 42 | 1.80 | 20.067 | 42014.4 | 260.9 | 41932.9 | C2a yes, C2b yes, r4_strict no, r4 yes |
| 405 | 43 | 0.78 | 38.5 | 1332.0 | 92.5 | 1304.4 | C2a yes, C2b yes |
| 406 | 43 | 0.62 | 72.0 | 1197.1 | 54.4 | 1181.8 | C2a yes, C2b yes |
| 407 | 44 | 8.52 | 8.367 | 770.2 | 770.2 | 333.5 | C2a yes, C2b yes |
| 408 | 44 | 0.56 | 72.0 | 49.9 | 49.9 | 22.0 | C2a yes, C2b yes |
| 409 | 45 | 5.21 | 8.367 | 928.7 | 928.7 | 15.8 | C2a yes, C2b yes |
| 410 | 45 | 0.36 | 50.2 | 65.8 | 65.8 | 0.9 | C2a yes, C2b yes |

All required checks pass (r4_strict, the frozen r4, fails for 42 and is reported only; X28).

Tunables: {"41": {"L": 100.0, "N": 1000.0, "bg": 20.0, "Nn": 1000.0, "bgn": 50.0}, "42": {"L": 100.0, "N": 4.0, "bg": 20.0, "Nn": 1000.0, "bgn": 50.0}, "43": {"L": 100.0, "N": 30.0, "bg": 20.0, "Nn": 1000.0, "bgn": 50.0}, "44": {"L": 100.0, "N": 70.0, "bg": 20.0, "Nn": 1000.0, "bgn": 50.0}, "45": {"L": 100.0, "N": 500.0, "bg": 20.0, "Nn": 1000.0, "bgn": 50.0}}
