# Held-out fidelity gate (F6), result: STOP (accuracy fails)

Readers: frozen F6 (freeze check: PASS (entry 6)). Sets frozen before F6 (fidelity/HELDOUT.md); inputs set after F6, before the run (fidelity/heldout_inputs.json, pushed first).
Gate: coverage >= 80%, >= 90% of reads within 2u, |bias| <= 0.5u, |z| > 5 on at most 2% of reads.

| set / feature type | in scope | reads | coverage | within 2u | bias (u) | |z|>5 | verdict | status counts |
|---|---|---|---|---|---|---|---|---|
| external|peak_x | 20 | 0 | 0% | 0% | nan | 0.0% | **NO READS** | {'calibration failed': 20} |
| external|y_at_x | 65 | 0 | 0% | 0% | nan | 0.0% | **NO READS** | {'refused': 38, 'calibration failed': 27} |
| external|plateau | 8 | 0 | 0% | 0% | nan | 0.0% | **NO READS** | {'calibration failed': 8} |
| external|extremum | 34 | 11 | 32% | 100% | -0.22 | 0.0% | **ACCURACY PASS, COVERAGE < 80%** | {'calibration failed': 10, 'refused': 10, 'read': 11, 'miss': 3} |
| external|crossing | 12 | 0 | 0% | 0% | nan | 0.0% | **NO READS** | {'calibration failed': 12} |
| external|bar_top | 39 | 19 | 49% | 79% | -1.17 | 5.3% | **FAIL (accuracy)** | {'read': 19, 'calibration failed': 20} |
| external|x_end | 14 | 14 | 100% | 100% | -0.23 | 0.0% | **PASS** | {'read': 14} |
| internal|peak_x | 0 | - | - | - | - | - | no test case | |
| internal|y_at_x | 6 | 0 | 0% | 0% | nan | 0.0% | **NO READS** | {'unsupported': 6} |
| internal|plateau | 6 | 0 | 0% | 0% | nan | 0.0% | **NO READS** | {'calibration failed': 6} |
| internal|extremum | 5 | 4 | 80% | 75% | -0.88 | 0.0% | **FAIL (accuracy)** | {'read': 4, 'miss': 1} |
| internal|crossing | 12 | 0 | 0% | 0% | nan | 0.0% | **NO READS** | {'calibration failed': 12} |
| internal|bar_top | 22 | 0 | 0% | 0% | nan | 0.0% | **NO READS** | {'calibration failed': 10, 'miss': 12} |
| internal|x_end | 5 | 5 | 100% | 100% | -0.35 | 0.0% | **PASS** | {'read': 5} |
| all|peak_x | 20 | 0 | 0% | 0% | nan | 0.0% | **NO READS** | {'calibration failed': 20} |
| all|y_at_x | 71 | 0 | 0% | 0% | nan | 0.0% | **NO READS** | {'refused': 38, 'calibration failed': 27, 'unsupported': 6} |
| all|plateau | 14 | 0 | 0% | 0% | nan | 0.0% | **NO READS** | {'calibration failed': 14} |
| all|extremum | 39 | 15 | 38% | 93% | -0.40 | 0.0% | **ACCURACY PASS, COVERAGE < 80%** | {'calibration failed': 10, 'refused': 10, 'read': 15, 'miss': 4} |
| all|crossing | 24 | 0 | 0% | 0% | nan | 0.0% | **NO READS** | {'calibration failed': 24} |
| all|bar_top | 61 | 19 | 31% | 79% | -1.17 | 5.3% | **FAIL (accuracy)** | {'read': 19, 'calibration failed': 30, 'miss': 12} |
| all|x_end | 19 | 19 | 100% | 100% | -0.26 | 0.0% | **PASS** | {'read': 19} |

## Causes

1. **Calibration (coverage)**: on 27 of 33 external panels and 9 of 12 internal panel reads the axis calibration fails, mostly x. The OCR label bands are fixed in pixels (32 px below the x axis, 62 px left of the y axis), sized for the 300-600 px crops of the build papers; the held-out Nature figures are published at ~2000 px per figure (tick labels 30-40 px tall). S039 F16 subplots: x labels only on the bottom subplot and one subplot band is empty, which raises in OCR instead of returning None (a reader bug, not fixed here: the run stops).
2. **Refusals (by design, no read)**: X1 1a, 1c (open vs filled black markers), X2 8b (two black series), X2 11b (solid vs dashed red), X4 4b (ten graded series, adjacent Delta E < 15).
3. **Bar tops (accuracy)**: X3 3d - the two sample columns of a bar disagree (one hits a neighbouring bar or a cap), the spread enters u and hides gross errors (0M modulus read 273 vs 41.3 at z = 0.99; toughness 154 vs 88 at z = 0.82); toughness 1M read 223.8 vs 235.7 (z = -17, cap/dots region). X3 2f gradient bars read ~1 px low throughout (z ~ -2).
4. **Extremum (internal)**: S098 F5c T15@M10 strength 85.07 vs table 86.42 (z = -3.2); the table holds means over repeats, the curve is one representative test.
5. **x_end** passes in both sets (19 reads, 100% within 2u). Extremum (external) and bar tops on X4 4d (negative bar included) are accurate where read.

## Lessons for v3.3 (no reader change in v3.2 on this evidence)

- OCR label bands must scale with the frame size / measured glyph height, validated on replicas rendered at publication resolution (2000 px figures).
- Uncertainty must not absorb inconsistency: when the two bar sample columns (or any two independent estimates) disagree by more than 2 px, refuse instead of widening u.
- An empty OCR band must return None (bug).
- Gradient bar tops: the edge sits ~1 px inside the drawn top on these figures; replicas need the publisher rendering (PNG export, anti-aliased edge).

## Consequence

Accuracy fails for bar_top (both sets pooled: 79% within 2u, 5.3% gross) and for the internal extremum (75% within 2u). Per the instruction, the gate stops here; 5D is not run.
