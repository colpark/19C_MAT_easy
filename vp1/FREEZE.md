# vP.1 freeze ledger

Hashes are sha256 prefixes (16 hex characters). Nobody changes a file after its row; a change needs a new row and a deviation.

| label | date | files and hashes | what |
|---|---|---|---|
| VP1-0 | 2026-10-22 | PREREG.md 4b979bf55eb08e81 (kit PREREG_vP1.md verbatim, first commit 615ee79dd); vp1_kit.zip 13c1804a5378bc50 (kit/ref/manip.py 57c03d7c3ed1650e, folds.py 6b56e79df846e729, crossfit.py 20b48140ae78691e, qwen_author.py 97e179fb1fa7a69d; tests/test_ref.py 6c4542b74ee3654d, 9 of 9 pass; spec/arms_vp1.json c7bc37b397304254, runs_vp1.json 38c2e7ff8e02f4cd); SOURCE.md 7f23ccaa26c5a20b (tools/build_source.py 89fe80f5b6b84895); server code b01466903171b121 (sha256 of cat mcenv/*.py kit/ref/*.py; server_vp1.py 62ef4975aa74822b, tables_vp1.py 779d54609e0aa5d7, admin_vp1.py 40b6c29a2e6b58b6; tests/test_server_vp1.py d66270befadcb2b9, 7 of 7 pass); ops/start_server.sh c3e01a3084d48d1c; ops/determinism_vp1.py fa825c27bf7f0b74 (det/DET_8820.json bee819f954fb7feb, PASS); TABLES_FROZEN.json ea46822a35142af3 (tablecheck_vp1.py 2b918ad7ac9fe5ee); folds.json 1131f17073e60952 (folds_vp1.py 10600cf74df5e00b; B1 15/15, H 12/11, T 12/12) | setup: server, table check and folds hashed before any vP.1 score is read and before any bench episode |
