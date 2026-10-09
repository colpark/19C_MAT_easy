# VG: S4mc6 v2 real gate (v4.5 MC v2.1)

Rules: HTEM_MC2_RULES_v21.md section 3 (MV1c). Code: mc2/iv_classes.py and mc2/vg_mc2.py (VG freeze; VM-E05 fixed before any output). Data: the 260 fully cached libraries, with no fetch. Output: VG_S4MC6.json.

**VG: PASS.**

| Step | Result | Gate |
|---|---|---|
| 1 Synthetic, fresh base 915300, 200 curves per class | valid 1.00, beyond range 1.00, non-ohmic 1.00, fault 1.00; false fault flags 0.00 | ≥ 0.90 each; ≤ 0.05 false fault: **pass** |
| 2 Replicate agreement (5 replicate groups, 233 matched positions; matched by grid index and |Δx| ≤ s) | valid/not-valid agreement 0.970; 4-class agreement 0.970 (201 both valid, 25 both fault, 7 split) | ≥ 0.90: **pass** |
| 3 Threshold sensitivity (share of positions whose valid call flips) | r² 0.995: 0.31 %; r² 0.99: 0.39 % | reported |
| 4 Database consistency (level A, validation only) | Spearman of our Rs against fpm_sheet_resistance on valid positions: 1.000 (n = 1,317) | target 0.9: met |

**The real-world trap.**
- 826 positions that we call fault (602) or beyond range (224) still list a finite fpm_sheet_resistance in the database.
- A user who trusts the database column takes these as readings.
- On valid positions the database Rs is the same quantity as ours (ρ = 1.000), so the database simply applies no validity screen.

**Classes over 2,564 positions with I-V points:**

| Class | Positions | Detail |
|---|---|---|
| valid | 1,339 | |
| fault | 911 | erratic 498, fewer than 4 points 170, degenerate 157, reversed polarity 86 |
| beyond range | 257 | |
| non-ohmic | 57 | |

**Caveats.**
- The synthetic generator is easy: 5-point sweeps at the real current levels, with clean curvature. Step 1 therefore shows that the class definitions work as coded, not that they are hard to fool.
- The replicate evidence comes from 5 groups. By the split of the first library in each pair, 125 positions are train, 71 test and 37 dev. VG is a pass/fail check of a frozen reader, with nothing tuned, so all splits are used.
