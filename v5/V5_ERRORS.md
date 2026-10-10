# v5 error ledger

| id | source | stage | symptom | root cause | class | fix | files | regression |
|---|---|---|---|---|---|---|---|---|
| V5-E1 | Materials Project | V5-0 setup | `MP_API_KEY` not set on host A or node A2; no key in any config file | approved fetch needs a key that is not on the nodes | environment gap | fallback per prompt 1.1: pymatgen-built structures from published lattice parameters, sources in `scenarios/structures/SOURCES.md`; MP fetch can run later if David provides the key | V5_SPEC.md 1.1 | n/a |
