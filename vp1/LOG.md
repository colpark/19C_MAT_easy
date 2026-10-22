# vP.1 log (table checks and run events)

Every table check (vp1/tablecheck_vp1.py) appends one line here: the in-memory table hashes of each vP.1 server against `TABLES_FROZEN.json` (FREEZE VP1-0), and the manipulated-arm manuals against the fm arm's. A batch starts only after a PASS.

- 2026-10-22T13:56Z node A2:8820 started from ~/vp1srv (code b01466903171b121 = sha256 of cat mcenv/*.py kit/ref/*.py), state ~/vp1_state.
- 2026-10-22T13:58Z determinism check (VP1-0 step 6, batch vp1-det, excluded from every analysis): PASS on all three families, 43 of 43 replayed calls with results equal to v7's logged sha (det/DET_8820.json).
- 2026-10-22T13:59Z TABLES_FROZEN.json computed in a fresh process on host A from the committed files; equal to node A2:8820's in-memory report on every key.
- 2026-10-22T13:59Z table check before batch `vp1-det`: PASS; 8820 pid 2971299 equal (21 tables)
- 2026-10-22T14:02Z table check before batch `vp1-1-preflight`: PASS; 8820 pid 2971299 equal (21 tables); 8821 pid 2975164 equal (21 tables); 8822 pid 2975179 equal (21 tables); 8823 pid 2975195 equal (21 tables)
