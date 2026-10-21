# v10 freeze ledger
| label | date | files and hashes | what |
|---|---|---|---|
| V10-0 | 2026-10-21 | PREREG.md 47e3b0e963e6ef42 (commit 9d4e9c25a, before any other v10 work); tests/test_neutron_scale.py 9bfaabcc37b30627 (passed) | pre-registration part 1; neutron scale |
| V10-1a | 2026-10-21 | pilot/recipes10.py dcf4679658447dcc; pilot/qual10.py d8470c1c24c28dca; pilot/frames10.py 53f588efde6b941b; pilot/pilot10.py 286e2565b340f22b; pilot/runjobs.py b3d16ef2e5f9cbae; mcenv cat e7b32384d41b7908; graphexec cat 4efac744f019effa | recipe suite and pilot code, hashed before the pilot |
| V10-1a amendment | 2026-10-21 | pilot/pilot10.py 39837e1fd2e90dde | orchestration only, during s0 (no job input, measurement or decision rule changed): remote mkdir before the job sync; host B's runner launched without waiting on its ssh session (waiting held host A back until host B finished); a live runner of a stage is adopted after an orchestrator restart; host B counts as done only on the last line of its log |
