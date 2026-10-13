# v6 errors
| id | where | when | what | cause | class | fix | files | check |
|---|---|---|---|---|---|---|---|---|
| V6-E1 | V6-2 bar-1 script (exemplar/features_s1.py) | first run, before any feature was recorded | the pool came out empty (0 members) | the v6 copy of mcenv reads the WBM structures from v6/data/, which did not exist; the structure loader caught the error per entry and returned no key, so every formula dropped out silently | pipeline bug (path) | v6/data is a link to the v5 data folder (not in git, v6/.gitignore); the empty run is kept as exemplar/features/s1_empty_run.*; the script reran | exemplar/features_s1.py, v6/.gitignore | the rerun pool count |
