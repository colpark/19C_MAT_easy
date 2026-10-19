# v7 errors (from V7-E1)
| label | where | when | what happened | cause | class | fix | files | check |
|---|---|---|---|---|---|---|---|---|
| V7-E1 | T gold harness (graphexec/adapters_mcenv.py fm adapter) | V7-2 first test compound (301, budget 240) | the executor stopped at S2: "hull: unknown structure 'None'" | the fm adapter served energies for claim R only and fell through to the hull path for claim T | pipeline bug | claim T takes the energies of every polymorph, as R; test rerun with fresh tokens | graphexec/adapters_mcenv.py | 301 selection rows pass |
