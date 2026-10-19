# v7 code provenance (V7-0)

- **mcenv, spec and graphexec:** copied from `v6/` at a1751aaf (branch v6/2026-10-13).
  - `cat mcenv/*.py | sha256sum` = b9251227ee213370 for the v6 copy. The B1 server code deployed at node A2:8778 is 0ca269b543eedec0; the v6 tree adds `fm2_service.py` and the runners.
  - Kit B in the copy, byte-identical to v6: graphexec.py cf258f60e231c020, test_graphexec.py 49adca16ca14a6c5, graph_R_v2.json 3cc55075fa2b7510, graph_schema.json 771b8941574e8b92.
- **Kit D:** `v6_kit_D.zip` (zip ad87c7e000838624), unzipped over `v7/`. New files only: graphexec_d.py 0c463f0335ec25cd, test_graphexec_d.py 1a99b8a590c55356, graph_T.json 4961a797104c5eff, graph_H_v2.json bc090b97301b4f74, graph_R_v2_nodft.json d84949565367361a, graph_schema_d.json b9ecc5c5d0e79e0e, and README_kitD.md.
  - `test_graphexec.py`: ALL TESTS PASSED. `test_graphexec_d.py`: ALL KIT D TESTS PASSED.
- **v7 changes to the copied code** (new behaviour behind new arms, families and claim types; the one-sample B1 paths are unchanged):
  - `graphexec/adapters_mcenv.py`: per-sample free scans, fits, measurements and plans for T (node params `sample`); FM energies for claim T; make_task for T.
  - `mcenv/admin.py`: the V5_STAGE=7 hook.
- **New v7 files:** `mcenv/server7.py`, `family7.py`, `grade7.py`, `client7.py`; `spec/answer_schema_T.json`; `MANUAL_T.md`, `MANUAL_H.md`, `STATED7.json`.
