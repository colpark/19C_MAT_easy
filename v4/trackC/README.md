# v4/trackC: DiscoveryQA kit (v4.4 Track C pilot)

The computed tier works like this. A screening pipeline paper supplies the rules and its open deposit supplies per-material outcomes. Code applies the frozen rules to the deposited values and writes every key at level S. Open foundation models (FMs) serve only as demonstrators. Governed by `../SKILL_discoveryqa_v0.2.md`, with invariants from `../SKILL_panelbench_v1.6.md`. Data, archives and task folders live in `~/Documents/harbor/v4_host/trackC/` (host B) and stay out of git (I9).

## Pipeline (run order; freeze labels in `../FREEZE.md`)

| Step | Tool | Output | Freeze |
|---|---|---|---|
| C0 fetch | `mc_fetch.py` (Materials Cloud API, figshare, arXiv; polite, .bad bodies, md5), `fetch_all.sh`, `exp_fetch.py` (Addendum B hosts), `manifest.py` | `MANIFEST_trackC.json` | C0 |
| C0 inventory | `inventory.py` (AiiDA groups: node types, arrays, dict keys, exit states; never values) | `inventory/*.json` | C0 |
| C0 cards | (hand-filled from the deposits) | `CARD_SOURCE_liion.json`, `CARD_SOURCE_jarvis.json` | C0 |
| B1, B2 | `bridge.py origin`, `known.py` | `B1_origin_liion.json`, `KNOWN_77.json` | C0 |
| B2 pre-registration | — | `MATCH_RULE_B2.json`, `BRIDGE_METRICS_B2.md` | B2pre |
| C1 | `card.py` (+ `card_jarvis.py`), `card.py audit-packet` | `CARD_liion.json`, `CARD_jarvis.json`, `AUDIT_PACKET_C1.md` | C1pre, C1pre_jarvis, C1 |
| procedures | `msd.py`, `arrhenius.py`, `nernst_einstein.py`, `allen_dynes.py`, `synth_md.py`, `validate_procedures.py` | `VALIDATION_procedures_summary.json` | C2proc |
| C2 | `reconstruct.py` (+ `reconstruct_jarvis.py`), `reconcile.py`, `paper_tables.py` | `RECONCILE_*.md`, `TOLERANCES_trackC.json`, `materials*.jsonl` | C2 |
| C2b | `match_exp.py`, `bridge.py table/metrics` | `b2_matches.jsonl`, `BRIDGE_liion.csv`, `BRIDGE_B2_results.json` | C2 |
| C3 | `splits.py`, `demonstrators.py` (jobs, liion-md, jarvis-phonon, registry, validate) | `SPLITS.json`, `fm_registry.json`, `fm_errors.json` | C3split_rule, C3split, C3spec, C3 |
| C4 | `decisions.py` | `decisions.jsonl`, `DECISIONS_counts.json` | C4 |
| C5 | `PRIOR_RULES_trackC.md`, `generate_c.py` (prep on host B, then file-only), `render_c.py` | `items.jsonl`, panels, structures | C5prior, C5 |
| C6 | `gates_c.py`, `determinism_c.sh` | gated items, gate report, determinism hashes | C6 |
| C7 | `export_c.py` (A0, B0f, B2, R0 tasks; T-FM spec; cascade scored in gates) | `v4_host/trackC/c7/tasks-*` | C7 |
| C8 | — | `TRACKC_PILOT_REPORT.md`, `../COST_QUOTE_trackC.md` | C8 |

## Hosts
- Host A (spark-112b) holds git and runs only the low-priority determinism check (Track H runs there).
- Host B (wcs-180522) is the builder. Its GPU runs the JARVIS phonons and two MACE shards.
- Host A node 2 (spark-0b70) runs the demonstrator MD.
- Host B node 2 is unreachable (VC-E02).

## Tests
`pytest tests/` covers the procedures on synthetic data and published reference values (the JVASP-19821 Debye temperature) and the B2 matching (an exact pair, a doped family pair, a polymorph that must not match). `validate_procedures.py` runs the full synthetic validation.
