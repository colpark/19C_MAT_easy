# Frozen constraints (V5_SPEC 3.3), checked by code

"Everything at best quality" (5-150 deg at 0.01 deg, high resolution, 20 s) needs 14501 points x 20 s = 4834 min > 180 min for every scenario (C2c, by arithmetic). C6 (twin input identity) is tests/test_v5.py::test_twin_inputs_identical.

| world | scen | D(m0) | cheapest D>=25 (min) | its D | best affordable D | best X-ray D | best 10-70 D | neutron D |
|---|---|---|---|---|---|---|---|---|
| 101 | 11 | 15554.75 | 0.0 | 15554.7479 | 985001.8 | 985001.8 | 985001.8 | 105430.0 |
| 102 | 11 | 15126.29 | 0.0 | 15126.2885 | 1252067.0 | 1252067.0 | 1171115.4 | 78781.1 |
| 103 | 12 | 7.87 | 5.842 | 27.2502 | 8375.2 | 984.6 | 450.4 | 8039.1 |
| 104 | 12 | 1.88 | 71.667 | 25.0034 | 13040.1 | 58.3 | 20.7 | 12940.2 |
| 105 | 13 | 1.07 | 30.117 | 27.0705 | 131.6 | 131.6 | 131.6 | 4.0 |
| 106 | 13 | 4.52 | 9.25 | 27.1864 | 531.4 | 531.4 | 531.4 | 19.2 |
| 107 | 14 | 0.68 | 8.367 | 32.7477 | 19753.9 | 752.1 | 62.5 | 19562.3 |
| 108 | 14 | 1.64 | 11.7 | 29.5361 | 17047.5 | 330.1 | 326.8 | 16937.7 |
| 109 | 15 | 8.86 | 6.675 | 26.0131 | 1052.1 | 1052.1 | 1044.9 | 50.1 |
| 110 | 15 | 0.61 | 50.2 | 28.0271 | 72.8 | 72.8 | 72.3 | 3.0 |

| check | world | rule | pass |
|---|---|---|---|
| C1 | 101 | D(m0) = 15554.7479 >= 25 | yes |
| C1 | 102 | D(m0) = 15126.2885 >= 25 | yes |
| C2a | 103 | D(m0) = 7.8724 < 9 | yes |
| C2b | 103 | cheapest D >= 25 plan costs 5.842 <= 90 min | yes |
| C2a | 104 | D(m0) = 1.8839 < 9 | yes |
| C2b | 104 | cheapest D >= 25 plan costs 71.667 <= 90 min | yes |
| C2a | 105 | D(m0) = 1.0749 < 9 | yes |
| C2b | 105 | cheapest D >= 25 plan costs 30.117 <= 90 min | yes |
| C2a | 106 | D(m0) = 4.5227 < 9 | yes |
| C2b | 106 | cheapest D >= 25 plan costs 9.25 <= 90 min | yes |
| C2a | 107 | D(m0) = 0.6794 < 9 | yes |
| C2b | 107 | cheapest D >= 25 plan costs 8.367 <= 90 min | yes |
| C2a | 108 | D(m0) = 1.6396 < 9 | yes |
| C2b | 108 | cheapest D >= 25 plan costs 11.7 <= 90 min | yes |
| C2a | 109 | D(m0) = 8.8637 < 9 | yes |
| C2b | 109 | cheapest D >= 25 plan costs 6.675 <= 90 min | yes |
| C2a | 110 | D(m0) = 0.6141 < 9 | yes |
| C2b | 110 | cheapest D >= 25 plan costs 50.2 <= 90 min | yes |
