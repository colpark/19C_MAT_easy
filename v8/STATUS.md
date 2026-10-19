# v8 status (updated at every push)

**Stopped for David at the end of the amendment E iteration.** Read `v8/REPORT_E.md`.

- **Gate F1 FAILED at fragment scale** under both estimators and both protocols (0 of 4 dev systems, best 1.26 sigma). `truth/F1_REESTIMATE.md` (step 1), `truth/F1_STEP2.md` (step 2).
- **Q7 done** (E item 1): `phase` is the identified candidate registry; `validate_d` with **all rows PASSES** on the demo worlds, hold row included. No kit file or validate_d row edited.
- **Rod scoping done** (E item 5): a full rod set is about 1 GPU hour, far below 48, so the E item 6 stop rule does not trigger and no NEGATIVE_RESULT.md is written. The blocker is geometry: only U0 has a usable 18-repeat rod, since the tiled control rods clash (V8-E14). No production set started.
- Gate S passed; V8-2 instrument and V8-3 graph/server/manual stand; adapters stand.
- FM blindness intact and complete: no FM call has touched any dev or test system.
- Still open (E item 8): V8-X9, V8-X11, Q1 to Q6.
- Machine: nothing of v8's running except the server on 8881 (demo worlds only); host B1's GPU still held by a 7-day vLLM process, never signalled.

David's decision: build four clash-free control rods so a rod reference can carry a pilot of the pre-registered size, or narrow v8's scope to what U0 alone supports.
