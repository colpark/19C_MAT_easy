# BRIDGE_METRICS_B2 (pre-registered 2026-10-07, before any matching)

Addendum B, B2 C2b. Bridges report beside the go criteria and never gate them. Every experimental value is level A and never keys an item (I2, I2c). Match classes follow `MATCH_RULE_B2.json` v1; exact and family are reported apart in every metric.

## Frozen constants
- Experimental fast conductor: room-temperature sigma >= 0.1 mS/cm (Addendum B). Room temperature as in the match rule (20 to 30 °C).
- Bootstrap: 2,000 resamples over matched pairs, seed 23, percentile 95 % interval.
- Computed routes and their own class thresholds:
  - pinball: sigma(1000 K) >= 1 mS/cm (CARD_liion S8 frozen reading)
  - FPMD (xm-46): diffusive at 1000 K per S10 frozen reading, and the room-temperature Arrhenius extrapolation (300 K, L4) where a ladder exists
  - PET-MAD (1c-13): its own deposited trajectories, D per temperature from msd.py, Arrhenius extrapolation to 300 K where >= 3 temperatures are resolved
  - outside MLIPs (C3): the same procedure on their trajectories

## M1 Recall against experiment
Of the experimental fast conductors that exact-match a structure in the funnel, how many survive each gate, and which gate removes each one. The denominator is the exact matches whose funnel stage is known. When a stage outcome is not deposited for a material, its fate is reported as "unknown at stage X", never inferred.

## M2 Ranking
Spearman rho between pinball sigma(1000 K) and experimental room-temperature sigma on exact matches, with the bootstrap 95 % CI. Family matches get a separate line. Report n. With n < 8, report rho and its CI but state "underpowered". Source of pinball sigma: only values deposited or printed by the authors (Tables 2 and 3); printed values are labelled A (author output) in the table.

## M3 Classification
For each computed route: agreement with the experimental class (fast or not at 0.1 mS/cm RT). Report the confusion counts, precision, recall and, where the route gives a 300 K extrapolation, bias and spread (SD) of log10(sigma_route / sigma_exp). A route without an RT value is classified at its own threshold, and the report states that 1000 K and room temperature differ.

## M4 Temperature
Direct log-sigma comparison only where the route extrapolates to 300 K. Otherwise ranks only (M2), and the 1000 K vs room-temperature mismatch is stated in the report.

## Reporting
- B1 origin counts per stage.
- KNOWN_77 reconciliation (count against 77, gaps logged).
- Match yields by class and reasons for every no-match.
- M1 to M4 tables, the contamination note (literature conductivities are recallable, one more reason never to key them), and the VC-E08 rule-gap note for David.
