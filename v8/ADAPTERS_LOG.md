# Adapters log (v8 executor adapters for graph I)

Files added: graphexec/adapters_v8.py, graphexec/run_gold_I.py, this log. Scratch: ~/v8_data/adapters/ (gold/, validate1/, validate2/, server logs).
No existing file in spec/, graphexec/ or mcenv/ changed. No git command run. No GPU, no FM call beyond the server's stand-in tools.

## Design
- Adapters follow adapters_mcenv.py: Env (HTTP POST {token, tool, args, rid}), token minted per run on the Context. Deviation from the old adapter:
  minting is a local subprocess `server8.py admin new` with V8_SERVER8_STATE set (no ssh). Token hashes only are written to disk.
- simulator S1a/S1d: server `simulate` over a grid of (one AFM scan + one lattice scan), cheapest first (cost formulas from `status`),
  cheapest plan with predicted_D >= 2 x D_accept inside the budget left, else the most separating. instrument: afm_scan/lattice_scan.
  fit S1c/S1f: server `fit` on m0 + measurements. fm S2a: `structure` (sequence read from the sample text); S2b: `registry_energy`.
  S3: rule_I_registry_match via RULES_I. A tool refusal (noprior arm, budget) becomes null outputs plus an error record, not a crash.
- Ceiling set (CEILING = ADAPTERS): graph I needs no reference value served free, so it uses the server's tools only.
- run_gold_I.py: gold (trace + gold answer in answer_schema_I shape, both schema-validated), prephold, validate.

## Servers (own instances, ports free-checked with `ss -ltn` before start, PID files, stopped by their PID files)
8882 state ~/v8_state/adapters8_base (base); 8883 ~/v8_state/adapters8_hold_azimuth; 8884 ~/v8_state/adapters8_hold_noise. After kill, `ss -ltn` shows
only 8881 (the pre-existing server, untouched).
Hold worlds: copies of the demo worlds with the SAME ids in a hold server's state dir (so the noise stream, seeded by world id, k and scan number, is the
same): azimuth = hidden sample azimuth +17 deg; noise = rod and lattice scatter x1.2.

## Commands
    run_gold_I.py gold --world demo_A_101 --k 1 --state ~/v8_state/adapters8_base --out ~/v8_data/adapters/gold      (and demo_B_102)
    run_gold_I.py validate --worlds demo_A_101,demo_B_102 --state ... --hold azimuth=URL=STATE --hold noise=URL=STATE --out ~/v8_data/adapters/validate1

## Results
Gold: demo_A_101 SUPPORTED (key SUPPORTED), demo_B_102 REFUTED (key REFUTED), cost 65.467 min each, no remeasure path. Gold answers validate; `--submit`
smoke test of the answer tool: recorded.

validate_d, both holds (validate1): correctness yes; necessity S1a+S1d, S1b+S1e, S1c+S1d+S1e+S1f, S2a, S2b all yes; measurement factorial yes
(A identified 58, B 44); **hold NO**; prior flip yes; abstention yes; sufficiency yes (margin 0.4, cost 65.467); non-bypass yes (see caveat); faithfulness yes.
Overall FAIL because of hold.
Hold diagnosis (logs in validate1/logs): all four hold verdicts equal the base verdicts. The failing comparison is the identified phase string (the
fitted angle rounded to a degree): azimuth hold B gives 49 against 44 (A 58 = 58; noise hold A 58 = 58, B 44 = 44). Cause in the stand-in world: the
isotropic rods are not shifted with the azimuth, so a +17 deg azimuth changes m0's concentration, S1a then plans a cheaper lattice scan (128 px, 1 s: SE 5.05
against 1.68) and the rounded angle moves 5 degrees. Nothing weakened. Run validate2 with the noise hold only: all rows PASS (a subset, not a substitute).
The parent should decide the hold design (phase granularity or the hold perturbation) when real worlds exist.
Non-bypass caveat: blindfm_pairs_resolved (blind-fm arm, both CANNOT_TELL) and constant_prior_resolved (S2b fixed to world A's output: A SUPPORTED, B
CANNOT_TELL, so the pair is not resolved) are measured; panel_fails is ASSERTED (no panel exists for demo worlds), so that row's pass is partly vacuous.
Faithfulness uses a plain templated rendering of the gold trace, not a real renderer.

## Frozen-kit checks (after all work)
test_graphexec.py: ALL TESTS PASSED; test_graphexec_d.py: ALL KIT D TESTS PASSED; test_graph_I.py: ALL GRAPH I TESTS PASSED.
