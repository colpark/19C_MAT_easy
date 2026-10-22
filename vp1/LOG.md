# vP.1 log (table checks and run events)

Every table check (vp1/tablecheck_vp1.py) appends one line here: the in-memory table hashes of each vP.1 server against `TABLES_FROZEN.json` (FREEZE VP1-0), and the manipulated-arm manuals against the fm arm's. A batch starts only after a PASS.

- 2026-10-22T13:56Z node A2:8820 started from ~/vp1srv (code b01466903171b121 = sha256 of cat mcenv/*.py kit/ref/*.py), state ~/vp1_state.
- 2026-10-22T13:58Z determinism check (VP1-0 step 6, batch vp1-det, excluded from every analysis): PASS on all three families, 43 of 43 replayed calls with results equal to v7's logged sha (det/DET_8820.json).
- 2026-10-22T13:59Z TABLES_FROZEN.json computed in a fresh process on host A from the committed files; equal to node A2:8820's in-memory report on every key.
- 2026-10-22T13:59Z table check before batch `vp1-det`: PASS; 8820 pid 2971299 equal (21 tables)
- 2026-10-22T14:02Z table check before batch `vp1-1-preflight`: PASS; 8820 pid 2971299 equal (21 tables); 8821 pid 2975164 equal (21 tables); 8822 pid 2975179 equal (21 tables); 8823 pid 2975195 equal (21 tables)
- 2026-10-22T14:03Z table check before batch `vp1-1-smoke`: PASS; 8820 pid 2971299 equal (21 tables); 8821 pid 2975164 equal (21 tables); 8822 pid 2975179 equal (21 tables); 8823 pid 2975195 equal (21 tables)
- 2026-10-22T14:07Z table check before batch `vp1-1-main`: PASS; 8820 pid 2971299 equal (21 tables); 8821 pid 2975164 equal (21 tables); 8822 pid 2975179 equal (21 tables); 8823 pid 2975195 equal (21 tables)
- 2026-10-22T14:10Z table check before batch `vp1-3-preflight`: PASS; 8824 pid 2984415 equal (21 tables); 8825 pid 2984555 equal (21 tables)
- 2026-10-22T14:11Z node A2:8824 and 8825 started for agent episodes (code hash f8a9ec23599d3781: the cat of mcenv/*.py now includes mcenv/run_claude_vp1.py, a host A runner the server never imports; server_vp1, tables_vp1, admin_vp1 and every imported module are unchanged since VP1-0, and the tables are equal).
- 2026-10-22T14:11Z table check before batch `plan_smoke.jsonl`: PASS; 8824 pid 2984415 equal (21 tables); 8825 pid 2984555 equal (21 tables)
