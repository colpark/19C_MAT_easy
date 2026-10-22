# S-llm round G programs (V7-G2): measurement policy, identification rule, decision rule

Source: `programs_G/{R,H,T}{1..5}.py`, read only (not run). Line numbers refer to those files.
Budgets from the manuals: R and H 180 min, T 240 min shared by both samples; m0 (pre_m0/post_m0 for T) is free.
Lab facts used below, read from `mcenv/tools_common.py` (the lab code, not the programs): simulate and measure reject
any grid of more than 2000 points (`n = floor((stop-start)/step + 1e-9) + 1`); simulate accepts the spec either under
`spec` or as flat arguments (`a.get('spec', a)`); a neutron simulate ignores start/stop/step and always returns the full
fixed 2901-point pattern at the neutron dwell time. Where a program's outcome depends on these facts it is said so.
"Band" means the reliability margin m* (0.045 eV/atom for polymorph energy gaps, 0.02 eV/atom for hull distance).

## R family (claim: sample polymorph is the lowest-energy polymorph of its formula)

### R1
- Measures: X-ray only. Fits every same-formula polymorph to the X-ray m0, then up to 2 rounds (L92) while delta chi2 < 60 (L95) and budget >= 12 min (L99). Window: 20 deg (start 5..125 in 10 deg steps, stop start+19.99), step 0.01, optics standard or high_resolution, chosen by simulating the best fit against the next 3 rivals with fitted nuisances and taking the max of the per-point minimum discrimination (L48-77).
- Time: round 0 t = (0.55*left - 5)*60/2000 (L56); round 1 t = (left - 5)*60/2000*0.97 (L105), clamped 0.1-20 s. Never takes neutron.
- Does not measure if m0 already gives delta >= 60, budget < 12, or every simulation fails (cand None, L102); a measure error ends the loop (L110-112).
- Identification: lowest single-phase chi2; delta chi2 = runner-up minus best. identified_phase = best if delta >= 9, else "unknown" (L162).
- Decision: polymorph claim: gap = E(ident) - min E(other polymorphs); SUPPORTED if gap < 0, REFUTED if gap > 0, only when delta >= 25 and |gap| >= 0.045 (L153-155). Hull/meV claim branch: h vs 0.050 with band 0.02 (L133-141). Band-gap claim: CANNOT_TELL. delta < 25 forces CANNOT_TELL (L160).

### R2
- Measures: X-ray, and neutron as a scored option. Up to 4 measurements (L140) while delta < 60, budget >= 8 (L143) and best option score >= 5 (L149).
- X-ray options (L48-78): 4 optics/step combinations (standard or high_resolution, step 0.02 or 0.04), windows of 250/500/1000/1990 points placed where the summed discrimination of best vs next 3 rivals is largest, t = (avail - 5)*60/N (<= 20 s, option dropped if < 0.3 s). avail = 0.6*left in the first round, all of left afterwards (L146).
- Neutron: added as an option when avail >= 120 min (L79-88), scored by the full-pattern difference averaged over rivals; taken when it scores above every X-ray option. So with 180 min it can only be chosen from the second round on (first round avail = 0.6*180 = 108).
- Identification: lowest chi2 over the same-formula polymorphs, fitted on all measurements (m0 included whatever its radiation). identified_phase is always the best fit when any fit exists; the delta >= 9 test at L211 returns the best name on both branches.
- Decision: delta < 25 gives CANNOT_TELL (L164). Polymorph claim: gap = E(ident) - min E(others); |gap| < 0.045 gives CANNOT_TELL, else the sign (L199-205). Hull or "stable" claim: hull vs 0.050, band 0.02 (L173-184).

### R3
- Measures: X-ray only, standard optics, step 0.02. Up to 3 tries (L325) while delta < 60 and budget >= 10 (L328). If status has no X-ray m0 it first takes 10-70 deg, 0.04, 0.5 s (L315-317).
- Window: 2000 points (about 40 deg) between 10 and 150 deg where best and runner-up (fitted nuisances, score (A-B)^2/(A+B+1)) differ most (L271-296, L332).
- Time: t = (left*frac - 5)*60/npts with frac 0.6 on tries 1-2 and 0.95 on try 3 (L339-341), <= 20 s; stops if t < 0.1 (L342). Never neutron.
- Identification: identified if delta >= 25 (L355), else identified_phase "unknown" (L415).
- Decision: polymorph claim: margin = min E(others) - E(ident); SUPPORTED if margin > 0, REFUTED if < 0, only when identified and |margin| >= 0.045 (L402-405). Hull claim: 0.050 with band 0.02 (L383-390). Not identified: CANNOT_TELL (L412-413).

### R4
- Measures: X-ray, and neutron as an alternative. Up to 4 rounds (L144) while delta < 60 and budget >= 6 (L150); only best vs runner-up are compared.
- X-ray plan (L61-110): optics standard or high_resolution, step 0.02/0.04/0.07, windows of 2000/1000/500 points over 5-150 deg, t = (B - 5)*60/npts (<= 20 s) with B = 0.7*budget in round 0 and the full budget later (L155).
- Neutron: if budget >= 120, the neutron gain is computed (L156) and the neutron pattern is taken when it exceeds the X-ray gain (L158-159). Note: plan_neutron sums two simulate calls (5-77, 77.05-150); per the lab code each returns the full pattern, so the neutron score is doubled.
- Does not measure if the X-ray plan has zero gain and the neutron is not chosen (L163-164); a failed measure ends the loop.
- Identification: lowest chi2 over same-formula polymorphs; identified_phase is always the best fit (L235 returns `ident` on both branches).
- Decision: requires delta >= 25 (L196). Hull/"convex" claim: band 0.02, negation words flip (L197-208). Polymorph claim only when the claim contains "lowest", "polymorph" or "stable" (L212): gap = min E(others) - E(ident), |gap| >= 0.045 gives the sign (L219-225). Otherwise CANNOT_TELL.

### R5
- Measures: X-ray only, standard optics, fixed 40 deg window (39.98 deg at step 0.02, 2000 points). Up to 3 rounds (L344) while delta < 300 and budget >= 15 (L346).
- Window: placed where top-2 simulations (nominal size 100 nm, no fitted nuisances, scale-matched) differ most, on a 0.07 deg scoring grid over 10-150 (L353-358).
- Time: t = (0.7*left - 5)*60/2000 in rounds 1-2 and (left - 6)*60/2000 in round 3 (L349), clamped 0.1-20 s; stops if the cost would exceed the budget (L351). Only RuntimeError from measure is caught (L363).
- Identification: STRONG = 30 (L262). identified_phase = best if delta >= 30, "unknown" if delta < 9, best otherwise (L408).
- Decision: always the polymorph-energy rule (does not read the claim type): margin = min E(others) - E(best); CANNOT_TELL if delta < 30 or |margin| < 0.045; else SUPPORTED if margin > 0, REFUTED if < 0 (L399-406).

## H family (claim: sample phase lies within 0.050 eV/atom of the hull)

### H1
- Measures: X-ray only. 2 rounds (L150). Round 0 always measures (if budget >= 7, L157); round 1 is skipped when delta >= 60 (L154).
- Window: optics standard (step 0.04) or high_resolution (step 0.02), 500/1000/1500/2000 points, chosen by the worst-case (min over the next 3 rivals) scale-matched discrimination over 5-150 deg (L75-107). Rival patterns are simulated with the best fit's nuisances, not their own (L86).
- Time: t = (B - 5)*60/npts (<= 20 s), B = 0.55*left in round 0 and all of left in round 1 (L159-161).
- Candidates: every library structure, not only the sample formula (L140).
- Identification: delta >= 25 identifies; identified_phase "unknown" if delta < 9, best otherwise (L217).
- Decision: threshold parsed from "N meV" in the claim, and the claim must mention "hull"; if not parsed, CANNOT_TELL (L110-117, L199). margin = h - thr; |margin| < 0.02 gives CANNOT_TELL; else SUPPORTED if h <= thr (sign flipped for "above the hull", "more than", "at least", "beyond") (L199-212).

### H2
- Measures: X-ray, and neutron as an option. Up to 4 rounds (L449) while delta < 60; rivals are the next 3 within 200 chi2 of the best (L451).
- X-ray options (L364-376): standard step 0.03 or high_resolution step 0.01, windows of 500/1000/2000 points over 5-150 deg at 1/5-window strides, scored by the minimum over rivals of the discrimination. Time is set to reach need = max(60 - delta, 20) with 20% margin (L394-395), capped by budget and 20 s.
- Neutron: offered when left >= 120 (L378-385), cost 120. Policy: the cheapest option whose expected gain reaches need (L404-406); otherwise the most informative option if its gain >= 5 (L407-418). Note: per the lab code the neutron score is overstated (two full-pattern chunks, L307-322, then multiplied by 120*60/2901, L380-382), which favours the neutron.
- Does not measure when no option is affordable or the best gain < 5 (L418).
- Identification: delta >= 25. identified_phase is always the best fit (L529 returns `ident` on both branches).
- Decision: fixed threshold 0.050 (claim text not parsed). CANNOT_TELL if delta < 25 or |h - 0.050| < 0.02; else SUPPORTED if h < 0.050, REFUTED otherwise (L507-511). If every fit fails: CANNOT_TELL, "unknown" (L477-481).

### H3
- Measures: one X-ray, then possibly the neutron, both rule-based. X-ray only if delta < 40 and budget > 20 (L130): spend = min(left - 1, 55) when left >= 140, else left - 1 (L131); t = (spend - 5)*60/2000 (L133).
- Window: 40 deg (39.98 deg at step 0.02) with start in {5, 25, 45, 65, 85, 105, 110}, optics standard or high_resolution, chosen to maximise the minimum expected chi2 of best vs the next 3 rivals (L88-110). With 180 min: 55 min X-ray, about 125 min left.
- Neutron: taken if, after that, delta < 25 and left >= 120 (L148-150).
- Candidates: same reduced formula (L39-48); each phase is fitted at size 30 and 100 nm and the lower chi2 kept (L51-61).
- Identification: delta >= 25 (GAP_OK, L18). Otherwise answers CANNOT_TELL with identified_phase "unknown" (L161-180).
- Decision: fixed threshold 0.050, band 0.02: |h - 0.050| < 0.02 gives CANNOT_TELL; h < 0.050 SUPPORTED; else REFUTED (L191-201). Claim text not parsed.

### H4
- Measures: X-ray, or neutron by rule. Up to 3 rounds (L328) while delta < 50 (THRESH_ID).
- X-ray design (L280-306): optics standard or high_resolution, step 0.01/0.02/0.04, always a 2000-point window, placed where the minimum over the next 3 rivals of the scale-matched discrimination is largest; rivals simulated with the best fit's nuisances; t = (avail - 5)*60/2000 with avail = 0.55*left in round 1 and all of left later (L335).
- Neutron: used when left >= 120 and the design fails or its expected delta < 25 (L342-345).
- simulate is called with a flat spec, not under `spec` (L258). Per the lab code (`a.get('spec', a)`) this is accepted; if it were rejected, the X-ray design would fail and the program would take only the neutron when left >= 120. Uncertain in that sense.
- Identification: delta >= 25. identified_phase is always the best fit (L416).
- Decision: fixed 0.050, band 0.02: CANNOT_TELL if delta < 25, no hull value, or |h - 0.050| < 0.02; else SUPPORTED below, REFUTED above (L396-407).

### H5
- Measures: as written, X-ray windows or neutron, up to 4 rounds (L136) while delta < 37.5 (1.5*25, L140) and budget >= 8 (L143), comparing best vs runner-up only.
- X-ray options (L89-115): standard or high_resolution, step 0.02/0.04/0.06, 2000-point windows from 10 deg at half-window strides. But each X-ray option first simulates 10-150 deg at step 0.07 (L98), which is 2001 points; the lab rejects it, the `except` skips the option (L99-100), so no X-ray option is ever formed.
- Effective policy: only the neutron option, offered when left >= 120 (L77-85). With 180 min the program takes the neutron pattern once (unless m0 already gives delta >= 37.5); afterwards left is about 60, plan returns None and it stops. It never takes an X-ray scan beyond m0.
- Identification: delta >= 25 identifies; otherwise identified_phase "unknown" (L157, L204).
- Decision: fixed 0.050, band 0.02: CANNOT_TELL if not identified or |h - 0.050| < 0.02; SUPPORTED if h <= 0.050, else REFUTED (L176-187).

## T family (two samples; claim: treatment left the material in a lower-energy polymorph)

### T1
- Measures: X-ray, and neutron as an option, per sample. Loop picks the sample with the smaller delta among those with delta < 60 and fewer than 4 rounds (L359-362); stops when budget < 5.5. share = left/len(todo) (L363).
- X-ray options (L301-323): step 0.02, standard or high_resolution, windows of 250/500/1000/1500/2000 points over 10-150 deg at 50-point strides, t in {1, 2, 5, 10, 20} s, cost <= share. Neutron option if share >= 120 (L324-331); with 240 min and both samples pending, share is exactly 120 at the start.
- Choice: the cheapest option with expected delta >= 60 (L334-336); otherwise the most informative if its gain > 3 (L337-338). Note: the neutron score uses three simulate chunks (L271-278 with chunk 1400); per the lab code each returns the full pattern, so the neutron score is about tripled.
- Identification: per sample, lowest chi2 over same-formula polymorphs; identified_phase "unknown" if delta < 9 (L384).
- Decision: OK = 30: CANNOT_TELL if min delta < 30 (L414); same polymorph in both gives REFUTED (L417); diff = E(post) - E(pre), |diff| < 0.045 CANNOT_TELL, diff < 0 SUPPORTED, else REFUTED (L424-433).

### T2
- Measures: X-ray only, fixed step 0.03, 2000-point window (about 60 deg). Up to 4 outer rounds (L154); each round measures every sample with delta < 40 (L156), weakest first, while budget >= 15 (MIN_SHARE).
- Window: chosen over 10-150 deg where best and runner-up differ most, both simulated with the best fit's nuisances and scale (L91-118); optics standard or high_resolution (flux 0.25 applied).
- Time: share = left/len(need)/1.5 (L160), t = (share - 5)*60/2000, clamped 0.1-20 s (L95-96). Stops if a round makes no measurement (L185).
- simulate is called with a flat spec (L77); per the lab code this is accepted. If it were not, design() would return None and no measurement would be taken.
- Identification: identified_phase "unknown" if delta < 9 (L196).
- Decision: CANNOT_TELL if min delta < 25 (L215); same polymorph REFUTED; diff = E(post) - E(pre), band 0.045, sign decides (L218-234).

### T3
- Measures: X-ray or neutron, one sample per round, up to 8 rounds (L390) while min delta < 40 and budget >= 6 (L392); the sample with the smaller delta is measured (L394). Starts from hard-coded ids pre_m0/post_m0 (L380), which match the lab's T ids.
- Neutron: if left >= 120, the neutron score is compared with the best X-ray plan at a 120-min spend; the neutron is taken if it is more than 1.2 times larger (L400-407).
- X-ray (L338-350): step 0.02, standard or high_resolution, windows of 200/400/800/1400/2000 points over 5-150 deg; spend = min(left, 60) (all of left if less than 8 would remain) (L409-411); t = (spend - 5)*60/W, <= 20 s.
- Identification: identified_phase "unknown" if delta < 9 (L478-479).
- Decision: CANNOT_TELL if min delta < 25 (L450); same polymorph REFUTED; diff band 0.045, sign decides (L454-468).

### T4
- Measures: X-ray only. 3 rounds (L181); each round measures every sample with delta < 40 (L183), weakest first, while budget >= 6.5.
- Plan (L141-160): step 0.02, standard or high_resolution, windows of 200-2000 points over 5-150 deg, scored against up to 3 rivals within 400 chi2 (L196); t = (share - 5)*60/n, <= 20 s.
- Budget split: share = left/(samples still to measure in this round), halved in rounds 0 and 1 (L189-191).
- Identification: identified_phase is the best fit unless its chi2 is infinite (L219); no "unknown" for low delta.
- Decision: CANNOT_TELL if either phase is unknown or min delta < 25 (L248); same polymorph REFUTED; |E(post) - E(pre)| < 0.045 CANNOT_TELL, else sign (L251-264).

### T5
- Measures: as written, X-ray only, step 0.02, 2000-point window, optics standard or high_resolution, up to 6 rounds while delta < 60 and budget >= 12.
- Never measures in practice: best_window() simulates 10-150 deg at step 0.02 in one call (L351-352, called from L408), which is 7001 points; the lab rejects it, the `except` (L410-411) leaves no option and the loop breaks (L412-413). The program answers from m0 alone.
- Budget split as written: alloc = left/2 when both samples need data, at least 12 min (L398-399); t = (alloc - 5)*60/2000.
- Identification: identified_phase is the best fit whenever fits exist (L434); no "unknown" for low delta.
- Decision: SAFE = 30: CANNOT_TELL if min delta < 30 (L447); same polymorph REFUTED; band 0.045, sign of E(post) - E(pre) (L450-463).

## Summary tables

R family

| program | measures | neutron | main window rule | identification threshold |
|---|---|---|---|---|
| R1 | conditional (delta < 60, budget >= 12; max 2) | no | 20 deg window, step 0.01, best vs 3 rivals simulated | delta >= 25 (unknown < 9) |
| R2 | conditional (delta < 60, budget >= 8, gain >= 5; max 4) | yes (option when avail >= 120) | 250-1990 point windows, 4 optics/step combos, best vs 3 rivals | delta >= 25 |
| R3 | conditional (delta < 60, budget >= 10; max 3) | no | 2000 points at 0.02 (40 deg), best vs runner-up | delta >= 25 |
| R4 | conditional (delta < 60, budget >= 6; max 4) | yes (if budget >= 120 and gain beats X-ray) | 500-2000 point windows, step 0.02/0.04/0.07, best vs runner-up | delta >= 25 |
| R5 | conditional (delta < 300, budget >= 15; max 3) | no | fixed 40 deg at 0.02, nominal-parameter simulations | delta >= 30 |

H family

| program | measures | neutron | main window rule | identification threshold |
|---|---|---|---|---|
| H1 | yes (round 0 always if budget >= 7; max 2) | no | 500-2000 points, worst case over 3 rivals | delta >= 25 (unknown < 9) |
| H2 | conditional (delta < 60; max 4) | yes (cheapest option reaching target, left >= 120) | 500-2000 points, step 0.03/0.01, min over rivals | delta >= 25 |
| H3 | conditional (X-ray if delta < 40; neutron if delta < 25 after) | yes (rule) | 40 deg window, 7 fixed starts | delta >= 25 |
| H4 | conditional (delta < 50; max 3) | yes (rule: left >= 120 and expected delta < 25) | 2000 points, step 0.01-0.04, min over rivals | delta >= 25 |
| H5 | conditional, neutron only (X-ray options always fail on 2001 points) | yes (once, when left >= 120) | none effective | delta >= 25 |

T family

| program | measures | neutron | main window rule | identification threshold |
|---|---|---|---|---|
| T1 | conditional (per sample delta < 60; max 4 each) | yes (option when share >= 120) | 250-2000 points at 0.02, cheapest reaching expected 60 | min delta >= 30 |
| T2 | conditional (delta < 40, share >= 15; max 4 rounds) | no | 2000 points at 0.03 (60 deg), best vs runner-up | min delta >= 25 |
| T3 | conditional (min delta < 40; max 8) | yes (if left >= 120 and score > 1.2 x X-ray) | 200-2000 points at 0.02, spend <= 60 min | min delta >= 25 |
| T4 | conditional (delta < 40; 3 rounds) | no | 200-2000 points at 0.02, up to 3 rivals | min delta >= 25 |
| T5 | never (7001-point simulate rejected) | no | intended 2000 points at 0.02 | min delta >= 30 |
