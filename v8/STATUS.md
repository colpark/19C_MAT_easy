# v8 status (updated at every push)

**v8 has ENDED, in the stop state amendment F item 7 pre-registers for a failed rod gate:
`v8/NEGATIVE_RESULT.md`.** Read that document; it is the result.

- **Gate F1 FAILED at every scale tested.** 0 of 4 dev systems at fragment scale under three
  estimator-protocol combinations (best 1.26 sigma); **1 of 4 at rod scale**, needing 3 of 4.
  `truth/F1_REESTIMATE.md`, `truth/F1_STEP2.md`, `truth/rod_runs_F1.json`, `NEGATIVE_RESULT.md`.
- **The direction is wrong as often as it is right.** Both Na+ rods prefer the registry 30 deg
  away from the carboxylate match. The cation decides, not the match.
- **Gate F1 item 5 scaling diagnostic**: holds for K+ (ratio 9.09), does not hold for Na+ (0.81).
- **Gate F2 never reached.** UMA was killed by the OOM killer on the 40,486-atom rod system; no
  energy was ever compared with truth.
- **Gate S PASSED.** Instrument (V8-2), graph, server and manual (V8-3), adapters and
  `validate_d` (all rows, hold included) all pass and are reusable.
- **FM blindness intact and complete**: no FM call and no LLM contact touched any dev or test
  system. **Spend $0.**
- Still open, unchanged: V8-X9, V8-X11, Q1 to Q6. None relaxes a gate; none explains the result.
- Machine: nothing of v8's running except the server on 8881 (demo worlds only). Host B1's GPU is
  still held by a 7-day vLLM process v8 did not start, checked once and never signalled.

Nothing further will be built. The next move is David's.
