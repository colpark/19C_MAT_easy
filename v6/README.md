# v6 kit (2026-10-13)

The contract for v6: how a claim becomes a typed subgoal graph, how the graph runs, what a trace log holds, what an agent's answer reports, and how a trace counts as valid. Unzip into `v6/` so that `v6/spec/` and `v6/graphexec/` exist. Change any file only through a logged deviation.

| File | Role |
|---|---|
| `spec/graph_schema.json` | JSON Schema of a subgoal graph: nodes, modules, typed ports with sources, null outputs, acceptance tests, triggers, roles |
| `spec/graph_R.json` | Graph for the relative-stability claim. S1 (identify) and S2 (FM energies) are independent and S3 joins them |
| `spec/graph_H.json` | Graph for the hull claim. S2 needs S1c's phase, so the decomposition is sequential |
| `spec/trace_schema.json` | JSON Schema of one execution log (gold or agent) |
| `spec/answer_schema.json` | Arguments of the v6 answer tool: the stage 4 fields plus the identified phase, the property values with their source, and the decision rule |
| `spec/render_template.md` | Rules for turning a log into a readable trace, and a skeleton |
| `graphexec/graphexec.py` | Reference executor, rules, interventions (prior flip and squeeze), number lock, validation suite, Mermaid export |
| `graphexec/test_graphexec.py` | Self-test on toy worlds: the exemplar suite passes, and four negative cases fail as they should |

## Use
```
python v6/graphexec/test_graphexec.py                       # must print ALL TESTS PASSED
python v6/graphexec/graphexec.py check v6/spec/graph_R.json   # order and schema
python v6/graphexec/graphexec.py mermaid v6/spec/graph_R.json # diagram
```

## What the builder adds
`graphexec/adapters_mcenv.py`: the five adapters (simulator, instrument, fit, fm, dft) on the v6 environment server. Each returns `dict(outputs=..., cost_min=..., calls=[...])`. They reach the world only through the server's tools with an episode token, and never read truth. The toy adapters in the test read toy truth directly. That shortcut is for the test only.

## Validation rows (graphexec.validate)
correctness, necessity per subgoal (ablating a node also ablates the fallback it triggers), measurement twin, prior twin, hold, escalation, sufficiency, non-bypass, faithfulness. A trace is an exemplar only if every row passes.
