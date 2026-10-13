# PanelBench v6: modular reasoning graphs and one exemplar trace (V6-0, 2026-10-13)

**Post hoc.** David decided v6 on 2026-10-13, after v5 (stage 4: with the FM accuracy rose, but the LLM's own chemistry already answered most pairs, so accuracy could not show whether the reasoning depended on the FM). v5 stage 4b is parked at V5-27 (9 of 12 P scenarios chosen, nothing frozen, no FM call on a P candidate, no LLM contact; `v5/STATUS.md`). Every v6 choice is made after v5. v5 stays as recorded.

**Limit.** The exemplar proves the method on one simulated case, not a rate, and not that real science improves.

## 0. Sources
- Branch `v6/2026-10-13`, worktree `~/Documents/harbor/v6`, folder `v6/`. `v6/mcenv/` is a copy of `v5/mcenv/` at the commit in `v6/MCENV_SOURCE`.
- Kit `v6_kit.zip` (sha256 0314a8b29689ad35a7842f8e11a42084999a65e4ec79b5ca2a29346764076deb) unzipped into `v6/`: `spec/` (graph_schema, graph_R, graph_H, trace_schema, answer_schema, render_template) and `graphexec/` (graphexec.py, test_graphexec.py). The kit is the contract; any change is a logged deviation (V6-X).
- Data and models: the cached Matbench Discovery files and the models v5 holds (MACE-MP-0 medium on node A2; the stage 4 and 4b energy tables). No new fetch. $0.

## 1. Method
1. **Subgoal graph.** A claim is a typed graph (`spec/graph_R.json`, `graph_H.json`). Nodes: S0 decompose (plan), S1a predict window (simulator), S1b measure (instrument), S1c identify (fit), S2 infer the property (FM), S2x escalate to DFT (priced, triggered when S2 is not accepted), S3 decide (rule). In R, S1 and S2 are independent and S3 joins them; in H, S2 needs S1c's phase. Each node has typed inputs and outputs, a null output and an acceptance test (S1a: predicted D ≥ D_accept; S1c: observed D ≥ D_accept; S2: margin ≥ band).
2. **Gold trace.** The reference executor (`graphexec.Executor`) runs the graph as a scripted agent. Its adapters reach the world only through the v6 environment server's tools with an episode token; the grader alone reads truth. A run logs every node in the `trace_schema.json` format.
3. **Interventions.** Ablation of a node (and the fallback it triggers), override of the prior node's outputs (`flip_R`/`flip_H`: the counterfactual ranking or side; `squeeze_R`/`squeeze_H`: the margin inside the band), and hold worlds (nuisance changes) show which steps carry the conclusion, first for the gold trace and then for an agent's trace.

## 2. Server, adapters and arms (V6-1)
- **v6 environment server** on node A2 (port 8776, own state), built from the stage 4 and 4b servers: the structured answer of `answer_schema.json` (the stage 4 grader keeps reading verdict, region and rationale; the other fields are stored for the step grader); a per-episode tool log with call ids (returned to the caller and logged); the arm `active-fm-flip`, whose FM tools pass their outputs through `graphexec.flip_R` / `flip_H` (the functions of the gold prior-twin test; the FM values for the whole library are flipped together, so every call is consistent).
- **Adapters** (`v6/graphexec/adapters_mcenv.py`), each returning `dict(outputs, cost_min, calls)`:
  - simulator (S1a): the cheapest plan on the stage 1 plan grid and the stage 4b plan search whose expected separation, free scan plus plan, reaches D_accept against every other library polymorph, computed from the simulator only (the server's `simulate`, as an agent would; noise-free library simulations at the lab's nominal scale with the free scan's fitted nuisances); returns window, plan, predicted D, cost.
  - instrument (S1b): `measure`.
  - fit (S1c): `fit` for every library polymorph on all measurements, the free scan included; phase = best fit; D = observed Δχ² of the best other polymorph minus the best.
  - fm (S2): `energy` (R) or `hull` (H).
  - dft (S2x): the priced DFT tool.
  - Every executor run opens a fresh episode token (budget, measurements and noise are per episode), so interventions never reuse spent budget (V6-X1 if the kit needs a hook for this).
- **Reproduction of stage 4:** the executor on the 16 stage 4 worlds with the frozen stage 4 server code, once with DFT serving S2 (the ceiling arm's tools) and once with the FM; verdicts must match the stage 4 scripted ceiling and FM planners on 16 of 16 worlds, and every log must validate against `trace_schema.json`.

## 3. The exemplar (V6-2 to V6-4)
**A good exemplar** is a gold trace on one pair of twins that passes every row of the validation suite and reads clearly in under a page, with an agent comparison that shows whether an agent's reasoning follows the same graph and depends on the FM.

**Candidates (V6-2):** stage 4 scenarios 63 (MnSbS), 64 (BaIn3Ni), 67 (BaSb2Pt); the six quiet R picks of stage 4b (NbTlTe2, SrInRh2, LiPbS2, TePdBr, ZrGaAg, ScGaFe2); the first 10 stage 4b pool candidates that pass the heuristic panel's failure condition (J.5.4a) with a library of two or three polymorphs, ranked by pattern similarity (smallest D on the free scan per unit count rate).

**Screen, in order** (every number in `v6/exemplar/SELECTION.md`):
1. FM ranks correctly with a margin of at least twice the band on both twins (R 0.090 eV/atom, H 0.040).
2. Identification, retuned with the stage 4b quiet machinery: D(m0) < 9 against every other polymorph; the cheapest decisive plan costs 0.2 to 0.6 of the budget on the dearer twin and at most 0.6 on both. Prefer quiet by subtlety (the free scan shows at least 50 counts at the strongest peak); otherwise the largest count rate that stays quiet, reported as quiet by low counts.
3. Shortcuts fail: the heuristic panel fails the pair, and the blind FM planner resolves no pair.
4. LLM probe: Sonnet active-noprior, k = 3 per twin, v6 manual and structured answer, resolves at most one of three pairs; at most 9 candidates are probed (those passing 1 to 3).
5. Pick the lowest probe score; ties by the larger FM margin, then the larger count rate.

**Disclosure:** the exemplar choice conditions on FM and LLM output; it suits a demonstration, not a rate.

**Gold trace (V6-3):** both twins with fresh tokens (`gold_A.json`, `gold_B.json`); rendering by `render_template.md` by a Sonnet subagent that sees only the log, the graph and the rules; `number_lock` must pass (at most three attempts per twin, then a code template); `GRAPH.md` with the Mermaid diagram and one line per node.

**Validation (V6-4)**, `graphexec.validate` with both twins, three hold worlds per twin (displacement +0.10 mm, zero offset +0.005°, crystallite size × 1.2), the non-bypass evidence of V6-2 and the rendered traces. Every row must pass:

| Row | Pass condition | Meaning |
|---|---|---|
| correctness | the key's verdict on both twins | the trace is right |
| necessity | ablating S1a, S1b, S1c, or S2 with its fallback S2x, leaves CANNOT_TELL on both twins | every subgoal carries the conclusion |
| measurement twin | the twins' data give different phases and opposite verdicts | the measurement decides which structure |
| prior twin | the same data with the FM ranking flipped give the opposite verdict | the prior decides the property |
| hold | the nuisance changes alter no acceptance, phase or verdict | the trace is not fragile to nuisances |
| escalation | with the FM margin squeezed inside the band, the graph buys DFT and returns the key or CANNOT_TELL, never a wrong verdict | the graph knows when not to trust the prior |
| sufficiency | FM margin at least twice the band, cost within budget | the case is clean |
| non-bypass | the panel fails, blind FM resolves nothing, the LLM probe resolves at most a third | no shortcut reaches the answer |
| faithfulness | the number lock passes on both rendered traces | the text says only what the log holds |

Also recorded per base trace: the grader's expected D on the executed measurements beside the observed D, and agreement of the key. A failed row returns to V6-2 with the next candidate; after three failed candidates, stop for David.

## 4. Agent test (V6-5; no gate; one scenario)
Arms, all with the structured answer and the v6 manual: active-noprior (lab tools), active-fm (+ `energy`, `hull`), active-fm-flip (FM outputs flipped; a disclosed diagnostic whose results never count as correctness). Runs: Sonnet all three arms k = 5 per twin (30), Haiku k = 3 (18), Opus k = 1 (6); seeds world × 100 + k; 4 concurrent.

Each episode becomes an agent trace (`trace_schema.json`, source agent): node statuses inferred from the tool log and the answer fields, with call ids as evidence. Metrics per model and arm:
- S1 agreement: identified phase = gold's; the grader's D on the agent's own measurements ≥ 25; the targeted window overlaps the gold S1a window.
- S2 agreement: FM values for every library polymorph (R) or the identified one (H), reported with source fm.
- S3 agreement: the verdict follows from the agent's own reported phase and values under the graph rule (internal consistency); the verdict equals the key.
- Causal reliance: in active-fm-flip, the share of verdicts equal to the gold prior-twin verdict (following the flipped FM).
- Override: the share keeping the unflipped verdict, and what the rationale cites (own knowledge, the stated error, a check).
- Bypass: correctness in active-noprior.
- Plan shape: the decisive window measured before the answer; the order of S1 and S2 (free for R).
`v6/exemplar/AGENT_TEST.md`: a node-by-node table of gold against each arm, and one representative agent trace per arm rendered beside the gold trace.

## 5. Manual (no hidden conventions)
The v6 manual carries the stage 4b manual conventions (DFT truth with MP2020 corrections; the claim thresholds; the library lists every known polymorph; the decisiveness rule; the stated error, the reliability band m* and its key rule; the DFT price) and describes every field of the structured answer.

## 6. Hard rules and budget
- v5 rules carried over: skill v1.7, I1 to I12, truth isolation, MCP-only agents, the sandbox, ledgers, a push after each label.
- The gold executor is a scripted agent: adapters use the server's tools with an episode token; only the grader reads truth. Node outputs hold only what an agent could see (no expected D, DFT truth or key in a node). Every number in a rendered trace comes from a log (number lock); the renderer never sees truth.
- Claude: Sonnet at most 54 probe episodes, 30 agent-test episodes, at most 6 renderer calls; Haiku 18; Opus 6; nothing else on Opus. No Qwen3-8B runs. No model writes a key.
- Disclosure in every report: the exemplar choice conditions on FM and LLM output; the fm-flip arm shows agents a counterfactual FM and never counts as correctness.

## 7. Deliverables (V6-6) and stop
`v6/exemplar/EXEMPLAR.md` (one page: the claim, the graph diagram, the rendered gold trace for the claim-true twin, the other twin in one line, the validation table, three lines of agent comparison, the limit), `V6_REPORT.md` (method, selection disclosure, results, what scales next: the same executor and validator across many worlds, keeping the traces where the FM step is critical, as supervised data and a step reward for Qwen3-8B). Stop for David after V6-6.

## 8. Deviations
| id | Deviation | Reason |
|---|---|---|
