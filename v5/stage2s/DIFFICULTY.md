# Stage 2s difficulty (V5_SPEC E.3, E.4)

Costs in minutes with the stage 2s cost model (10-min overhead per measurement, neutron 125 min). c_dec: cheapest plan with planning D >= 40 in both worlds (alternatives' lattices free within +-1 %). c_loc: cheapest 60-degree survey with 2 sigma(lattice_scale) <= 1 % (Cramer-Rao, every nuisance free). c_loc|dec: cheapest further plan after that survey. c_pla: the plan a placebo-quality hypothesis chooses within B, with its key D on each true world. Slack = B - c_dec.

| scenario | N | B | c_dec | c_dec plan | D_key of c_dec plan (worlds) | c_loc (survey) | default survey: cost, 2 sigma, D_key | c_loc + c_loc|dec | c_pla, D_key on true worlds | slack |
|---|---|---|---|---|---|---|---|---|---|---|
| 46 | 1000 | 30 | 10.085 | 28.45-30.45 deg at 0.04 deg, 0.10 s, standard | [695.297, 256.756] | 12.502 (5.00-65.00 deg at 0.04 deg, 0.10 s, standard) | 22.508, [0.000142, 0.000446], [8742.516, 7269.552] | 22.587000000000003 | (10.085, [19.625, 0.017]) | 19.91 |
| 47 | 10 | 66 | 54.33 | 55.57-57.57 deg at 0.01 deg, 13.23 s, standard | [111.369, 66.773] | 155.177 (20.00-80.00 deg at 0.04 deg, 5.80 s, standard) | 22.508, [0.041648, 0.037424], [2.848, 2.065] | 194.91199999999998 | (11.732, [0.0, 0.0]) | 11.67 |
| 48 | 200 | 20 | 16.513 | 30.35-32.35 deg at 0.01 deg, 1.94 s, standard | [90.703, 59.141] | 12.502 (5.00-65.00 deg at 0.04 deg, 0.10 s, standard) | 22.508, [0.002412, 0.002419], [23.906, 15.731] | 25.904 | none within B (spends nothing, D = 0) | 3.49 |
| 49 | 330 | 61 | 50.593 | 10.00-70.00 deg at 0.04 deg, 1.62 s, standard | [350.941, 40.0] | 12.502 (5.00-65.00 deg at 0.04 deg, 0.10 s, standard) | 22.508, [0.002585, 0.004464], [108.14, 12.326] | 26.495 | (50.796, [352.696, 40.2]) | 10.41 |
| 50 | 300 | 29 | 23.712 | 28.40-30.40 deg at 0.01 deg, 1.11 s, standard, Si standard | [323.036, 41.746] | 12.502 (5.00-65.00 deg at 0.04 deg, 0.10 s, standard) | 22.508, [0.000588, 0.000691], [70.051, 10.168] | 24.883000000000003 | (26.226, [127.908, 3.819]) | 5.29 |
