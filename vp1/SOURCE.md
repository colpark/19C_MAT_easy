# vP.1 code and data provenance (VP1-0 step 4)

Branch `vp1/2026-10-22`, created from `origin/v7/2026-10-18` at 21fce6e556f7333c87f1ebbe35ef7980573878b2. Worktree `~/Documents/harbor/vp1` on host A.
Everything below was copied unchanged by `vp1/tools/build_source.py`. v5, v6 and v7 are never edited. Hashes are sha256 prefixes (16 hex characters).

- **Server chain.** Every file the deployed v7 servers carry (node A2 `~/v7srv` for H and T; `~/v6srv_b1` for B1's `bench/`), from the first of `v7/`, `v6/`, `v5/` whose sha256 equals the deployed file.
- **Deployed copies that differ.** Where no repository file equals the deployed one, the frozen repository file is used; the table gives both.
- **vP.1 code** (new, not copied) is listed in FREEZE.md, not here.

| part | vp1 path | source | hash | note |
|---|---|---|---|---|
| server | `H/TOOL_TABLES_H.json` | `v7/H/TOOL_TABLES_H.json` | d081ef363206811d | equal to deployed |
| server | `H/WORLDS_H.json` | `v7/H/WORLDS_H.json` | c7916260949f7438 | deployed copy differs (deployed cd30dbcec3970413) |
| server | `H/library_structures_H.json` | `v7/H/library_structures_H.json` | 95b5b2b1bad27a16 | equal to deployed |
| server | `MANUAL_H.md` | `v7/MANUAL_H.md` | 44e4fb3d4d054f1f | equal to deployed |
| server | `MANUAL_T.md` | `v7/MANUAL_T.md` | c6840bce1f90e504 | equal to deployed |
| server | `STATED7.json` | `v7/STATED7.json` | 1e97fe6241fff93c | equal to deployed |
| server | `T/TOOL_TABLES_T.json` | `v7/T/TOOL_TABLES_T.json` | 5bdb99ac0c37ad94 | equal to deployed |
| server | `T/WORLDS_T.json` | `v7/T/WORLDS_T.json` | 5fc8bb45cb8f46cd | deployed copy differs (deployed 26923fd3b148d81f) |
| server | `T/library_structures_T.json` | `v7/T/library_structures_T.json` | 2e3c2f1dd3f3eec5 | equal to deployed |
| server | `bench/MANUAL_B1.md` | `v6/bench/MANUAL_B1.md` | 208ec7116086e112 | equal to deployed |
| server | `bench/TOOL_TABLES_B1.json` | `v6/bench/TOOL_TABLES_B1.json` | c07e88ab7649be3f | equal to deployed |
| server | `bench/WORLDS_B1.json` | `v6/bench/WORLDS_B1.json` | daefed4167b85c10 | equal to deployed |
| server | `bench/grade_b1.py` | `v6/bench/grade_b1.py` | 7af5017604d02084 | equal to deployed |
| server | `bench/library_structures_b1.json` | `v6/bench/library_structures_b1.json` | 33e8bfec923f097c | equal to deployed |
| server | `exemplar/AGENT_TEST.md` | `v6/exemplar/AGENT_TEST.md` | 1a65d0c317590d3f | equal to deployed |
| server | `exemplar/EXEMPLAR.md` | `v6/exemplar/EXEMPLAR.md` | 0b04c886c495283e | equal to deployed |
| server | `exemplar/GRAPH.md` | `v6/exemplar/GRAPH.md` | 3377898f81145083 | equal to deployed |
| server | `exemplar/MANUAL.md` | `v6/exemplar/MANUAL.md` | fff0c87076fadd7d | equal to deployed |
| server | `exemplar/SELECTION.md` | `v6/exemplar/SELECTION.md` | 3d4ac2fbe4fce57e | equal to deployed |
| server | `exemplar/STATED.json` | `v6/exemplar/STATED.json` | 4db9a947b58676ab | equal to deployed |
| server | `exemplar/TOOL_TABLES.json` | `v6/exemplar/TOOL_TABLES.json` | 7a780d89c416a891 | equal to deployed |
| server | `exemplar/VALIDATION.md` | `v6/exemplar/VALIDATION.md` | 739579ba5d09fe1e | equal to deployed |
| server | `exemplar/WORLDS6.json` | `v6/exemplar/WORLDS6.json` | 34c6fc764c2499b6 | equal to deployed |
| server | `exemplar/agent_test.json` | `v6/exemplar/agent_test.json` | 9e9b5f7985a047b7 | equal to deployed |
| server | `exemplar/agent_test.py` | `v6/exemplar/agent_test.py` | 3ce4e6639d89e38d | equal to deployed |
| server | `exemplar/count_scenarios.py` | `v6/exemplar/count_scenarios.py` | f89c95ae6bc587a6 | equal to deployed |
| server | `exemplar/features_s1.py` | `v6/exemplar/features_s1.py` | 2ddecb0a0843dd7a | equal to deployed |
| server | `exemplar/gold_A.json` | `v6/exemplar/gold_A.json` | 04fcb7247ecf3dd0 | equal to deployed |
| server | `exemplar/gold_B.json` | `v6/exemplar/gold_B.json` | 5a3c63c06b1a640f | equal to deployed |
| server | `exemplar/gold_tokens.json` | `v6/exemplar/gold_tokens.json` | 9be55d41b28c93ac | equal to deployed |
| server | `exemplar/library_structures.json` | `v6/exemplar/library_structures.json` | 4ae6f1c1f85158fa | equal to deployed |
| server | `graphexec/KIT_B_README.md` | `v7/graphexec/KIT_B_README.md` | 9d37b70fcd3a85ae | equal to deployed |
| server | `graphexec/adapters_mcenv.py` | `v7/graphexec/adapters_mcenv.py` | 7a4982770f5f3acb | deployed copy differs (deployed 64ecd741dbbb0fea) |
| server | `graphexec/graphexec.py` | `v7/graphexec/graphexec.py` | cf258f60e231c020 | equal to deployed |
| server | `graphexec/graphexec_d.py` | `v7/graphexec/graphexec_d.py` | 0c463f0335ec25cd | equal to deployed |
| server | `graphexec/run_gold.py` | `v7/graphexec/run_gold.py` | 872f54ecd3020984 | equal to deployed |
| server | `graphexec/run_repro.py` | `v7/graphexec/run_repro.py` | 8bf869a505b856ee | equal to deployed |
| server | `graphexec/run_validate.py` | `v7/graphexec/run_validate.py` | 7c3d143efae0c102 | equal to deployed |
| server | `graphexec/test_graphexec.py` | `v7/graphexec/test_graphexec.py` | 49adca16ca14a6c5 | equal to deployed |
| server | `graphexec/test_graphexec_d.py` | `v7/graphexec/test_graphexec_d.py` | 1a99b8a590c55356 | equal to deployed |
| server | `mcenv/admin.py` | `v7/mcenv/admin.py` | 268c83fc71f4add8 | equal to deployed |
| server | `mcenv/agents.py` | `v7/mcenv/agents.py` | 3e949f0709b48653 | equal to deployed |
| server | `mcenv/agents3.py` | `v7/mcenv/agents3.py` | bb25ee1ea85684d8 | equal to deployed |
| server | `mcenv/agents4.py` | `v7/mcenv/agents4.py` | 0480e5160ca59259 | equal to deployed |
| server | `mcenv/agents4b.py` | `v7/mcenv/agents4b.py` | c57e7a849552ce48 | equal to deployed |
| server | `mcenv/analyze_stage1.py` | `v7/mcenv/analyze_stage1.py` | c70ba0ef0ffeaf68 | equal to deployed |
| server | `mcenv/analyze_stage1b.py` | `v7/mcenv/analyze_stage1b.py` | d9f47992d9977463 | equal to deployed |
| server | `mcenv/analyze_stage2r.py` | `v7/mcenv/analyze_stage2r.py` | 26b1f28d2767f097 | equal to deployed |
| server | `mcenv/analyze_stage2s.py` | `v7/mcenv/analyze_stage2s.py` | 8c7bda8fbab9cbe2 | equal to deployed |
| server | `mcenv/analyze_stage3.py` | `v7/mcenv/analyze_stage3.py` | 17571d91903a7d28 | equal to deployed |
| server | `mcenv/analyze_stage4.py` | `v7/mcenv/analyze_stage4.py` | 1c1453ebfd97756e | equal to deployed |
| server | `mcenv/analyze_stage4b.py` | `v7/mcenv/analyze_stage4b.py` | f9c87d1d29d1942c | equal to deployed |
| server | `mcenv/bench6.py` | `v7/mcenv/bench6.py` | 669a6b7519d1e7d0 | equal to deployed |
| server | `mcenv/client.py` | `v6/mcenv/client.py` | 5dcc83fff6c76282 | equal to deployed |
| server | `mcenv/client7.py` | `v7/mcenv/client7.py` | 34370658fbc72a08 | equal to deployed |
| server | `mcenv/determinism.py` | `v7/mcenv/determinism.py` | f21590f190f8f917 | equal to deployed |
| server | `mcenv/determinism_v52.py` | `v7/mcenv/determinism_v52.py` | 882c22ab33a35101 | equal to deployed |
| server | `mcenv/difficulty2s.py` | `v7/mcenv/difficulty2s.py` | 4637a8b6b850d8c2 | equal to deployed |
| server | `mcenv/energy4.py` | `v7/mcenv/energy4.py` | b9da6cf05780ddf1 | equal to deployed |
| server | `mcenv/export_worlds.py` | `v7/mcenv/export_worlds.py` | 00ad3dc4fdca8c6d | equal to deployed |
| server | `mcenv/family7.py` | `v7/mcenv/family7.py` | c4bded0ab5858699 | equal to deployed |
| server | `mcenv/fm2_service.py` | `v7/mcenv/fm2_service.py` | 3679d9b81f1799f3 | equal to deployed |
| server | `mcenv/fm_service.py` | `v7/mcenv/fm_service.py` | 0d583ceb6b8ac796 | equal to deployed |
| server | `mcenv/gate_report.py` | `v7/mcenv/gate_report.py` | 5f47d2820631bab7 | equal to deployed |
| server | `mcenv/gate_report2r.py` | `v7/mcenv/gate_report2r.py` | 73040807ecd96184 | equal to deployed |
| server | `mcenv/gate_report2s.py` | `v7/mcenv/gate_report2s.py` | 1c42658e841740d9 | equal to deployed |
| server | `mcenv/grade.py` | `v7/mcenv/grade.py` | a6e0dda9e970b901 | equal to deployed |
| server | `mcenv/grade2s.py` | `v7/mcenv/grade2s.py` | b6ecaab14bb79ad8 | equal to deployed |
| server | `mcenv/grade3.py` | `v7/mcenv/grade3.py` | 57783186af8a36e0 | equal to deployed |
| server | `mcenv/grade4.py` | `v7/mcenv/grade4.py` | 7b708554ace7a3b3 | equal to deployed |
| server | `mcenv/grade4b.py` | `v7/mcenv/grade4b.py` | a86c5fbd38205fc5 | equal to deployed |
| server | `mcenv/grade7.py` | `v7/mcenv/grade7.py` | 35592e37982a8c35 | equal to deployed |
| server | `mcenv/heuristics4b.py` | `v7/mcenv/heuristics4b.py` | ed047809801158f0 | equal to deployed |
| server | `mcenv/merge1b.py` | `v7/mcenv/merge1b.py` | 72bce9345210241d | equal to deployed |
| server | `mcenv/oracle1b.py` | `v7/mcenv/oracle1b.py` | 6d48211abb790a1b | equal to deployed |
| server | `mcenv/oracle_plans.py` | `v7/mcenv/oracle_plans.py` | cd8122ffd89e9179 | equal to deployed |
| server | `mcenv/physics.py` | `v7/mcenv/physics.py` | f11d3fa76119d29e | equal to deployed |
| server | `mcenv/plangrid.py` | `v7/mcenv/plangrid.py` | 5870c3009373cbf6 | equal to deployed |
| server | `mcenv/planner2.py` | `v7/mcenv/planner2.py` | b23fc98ace5b3a8e | equal to deployed |
| server | `mcenv/planner2r.py` | `v7/mcenv/planner2r.py` | 5daa6fe75c9ffca9 | equal to deployed |
| server | `mcenv/planner2s.py` | `v7/mcenv/planner2s.py` | 282a97d73a594ed6 | equal to deployed |
| server | `mcenv/rulef3.py` | `v7/mcenv/rulef3.py` | 7e89e313cf669d1e | equal to deployed |
| server | `mcenv/run_claude.py` | `v7/mcenv/run_claude.py` | 8c527f3a4f04be35 | deployed copy differs (deployed 67cb95416aaf5177) |
| server | `mcenv/run_qwen.py` | `v6/mcenv/run_qwen.py` | 5d3ea69496e94b92 | equal to deployed |
| server | `mcenv/sandbox.py` | `v7/mcenv/sandbox.py` | e002ef2a4ff513ed | equal to deployed |
| server | `mcenv/scenarios.py` | `v7/mcenv/scenarios.py` | 55bfba3d30e01c05 | equal to deployed |
| server | `mcenv/separation.py` | `v7/mcenv/separation.py` | 694543259f41145c | equal to deployed |
| server | `mcenv/server.py` | `v7/mcenv/server.py` | abf2ba1105eadfe3 | equal to deployed |
| server | `mcenv/server2.py` | `v7/mcenv/server2.py` | d06154dc43d218df | equal to deployed |
| server | `mcenv/server2r.py` | `v7/mcenv/server2r.py` | 795fb4455c681b94 | equal to deployed |
| server | `mcenv/server2s.py` | `v7/mcenv/server2s.py` | 204a863d2a1e5942 | equal to deployed |
| server | `mcenv/server3.py` | `v7/mcenv/server3.py` | 4f0c722320a7f4ad | equal to deployed |
| server | `mcenv/server4.py` | `v7/mcenv/server4.py` | 1608481e473333ac | equal to deployed |
| server | `mcenv/server4b.py` | `v7/mcenv/server4b.py` | 9e505caf3b9ce746 | equal to deployed |
| server | `mcenv/server6.py` | `v7/mcenv/server6.py` | d44bfe4a9d86a5be | equal to deployed |
| server | `mcenv/server7.py` | `v7/mcenv/server7.py` | 36722d32c0c09ae9 | equal to deployed |
| server | `mcenv/shadow_plans_v52.py` | `v7/mcenv/shadow_plans_v52.py` | 193d8f6b88edd8d1 | equal to deployed |
| server | `mcenv/shadow_plans_v53.py` | `v7/mcenv/shadow_plans_v53.py` | 6d819dbe519f37c9 | equal to deployed |
| server | `mcenv/stage1b.py` | `v7/mcenv/stage1b.py` | b52802b26fa5b42b | equal to deployed |
| server | `mcenv/stage2.py` | `v7/mcenv/stage2.py` | e538a0e7ae3ad2ad | equal to deployed |
| server | `mcenv/stage2r.py` | `v7/mcenv/stage2r.py` | c584cd570388bd34 | equal to deployed |
| server | `mcenv/stage2s.py` | `v7/mcenv/stage2s.py` | 9915ffcb53f6510d | equal to deployed |
| server | `mcenv/stage3.py` | `v7/mcenv/stage3.py` | 808d20026e492545 | equal to deployed |
| server | `mcenv/stage4.py` | `v7/mcenv/stage4.py` | b7cc606c18a16f5c | equal to deployed |
| server | `mcenv/stage4b.py` | `v7/mcenv/stage4b.py` | fb0932e00081ea89 | equal to deployed |
| server | `mcenv/stage6.py` | `v7/mcenv/stage6.py` | d53270b488c13f8d | equal to deployed |
| server | `mcenv/structures.py` | `v7/mcenv/structures.py` | 4f2bae8e015b66e6 | equal to deployed |
| server | `mcenv/survey2s.py` | `v7/mcenv/survey2s.py` | 8ef69e4ea7625f4d | equal to deployed |
| server | `mcenv/tasks.py` | `v7/mcenv/tasks.py` | 786a75c6922f2210 | equal to deployed |
| server | `mcenv/tools_common.py` | `v7/mcenv/tools_common.py` | b6dc270f90a1baaf | equal to deployed |
| server | `mcenv/tune.py` | `v7/mcenv/tune.py` | 131d08dff3bc1381 | equal to deployed |
| server | `mcenv/tune1b.py` | `v7/mcenv/tune1b.py` | 92109ffb9c94e635 | equal to deployed |
| server | `mcenv/tune2r.py` | `v7/mcenv/tune2r.py` | 1c3aa4a877a772fc | equal to deployed |
| server | `mcenv/tune2s.py` | `v7/mcenv/tune2s.py` | 725ce472bb164411 | equal to deployed |
| server | `mcenv/tune4.py` | `v7/mcenv/tune4.py` | a1d46b46a907e83c | equal to deployed |
| server | `scenarios/MANUAL.md` | `v5/scenarios/MANUAL.md` | a68091a88ae15ae3 | equal to deployed |
| server | `scenarios/TUNING.md` | `v5/scenarios/TUNING.md` | 75dba713172e7a35 | equal to deployed |
| server | `scenarios/WORLDS.json` | `v5/scenarios/WORLDS.json` | 58d33f463dcfe816 | equal to deployed |
| server | `scenarios/peak_tables.json` | `v5/scenarios/peak_tables.json` | 5c87f919940c13d0 | equal to deployed |
| server | `scenarios/peak_tables.pkl` | `v5/scenarios/peak_tables.pkl` | 4bf0ae2078f0aa54 | equal to deployed |
| server | `spec/answer_schema.json` | `v7/spec/answer_schema.json` | a3b7d5478647c0ad | equal to deployed |
| server | `spec/answer_schema_T.json` | `v7/spec/answer_schema_T.json` | 3177a42121826680 | equal to deployed |
| server | `spec/graph_H.json` | `v7/spec/graph_H.json` | 60bb28be27993338 | equal to deployed |
| server | `spec/graph_H_v2.json` | `v7/spec/graph_H_v2.json` | bc090b97301b4f74 | equal to deployed |
| server | `spec/graph_R.json` | `v7/spec/graph_R.json` | d98a34a70892281b | equal to deployed |
| server | `spec/graph_R_v2.json` | `v7/spec/graph_R_v2.json` | 3cc55075fa2b7510 | equal to deployed |
| server | `spec/graph_R_v2_nodft.json` | `v7/spec/graph_R_v2_nodft.json` | d84949565367361a | equal to deployed |
| server | `spec/graph_T.json` | `v7/spec/graph_T.json` | 4961a797104c5eff | equal to deployed |
| server | `spec/graph_schema.json` | `v7/spec/graph_schema.json` | 771b8941574e8b92 | equal to deployed |
| server | `spec/graph_schema_d.json` | `v7/spec/graph_schema_d.json` | b9ecc5c5d0e79e0e | equal to deployed |
| server | `spec/render_template.md` | `v7/spec/render_template.md` | b211e03ec1a26a48 | equal to deployed |
| server | `spec/trace_schema.json` | `v7/spec/trace_schema.json` | 704cae90b4cb639c | equal to deployed |
| server | `stage1b/DIFFICULTY.md` | `v5/stage1b/DIFFICULTY.md` | 90183254410b7d60 | equal to deployed |
| server | `stage1b/MANUAL.md` | `v5/stage1b/MANUAL.md` | a68091a88ae15ae3 | equal to deployed |
| server | `stage1b/TUNING.md` | `v5/stage1b/TUNING.md` | 24ee69ef99b6496c | equal to deployed |
| server | `stage1b/WORLDS.json` | `v5/stage1b/WORLDS.json` | 44f16cbe3bf10b6b | equal to deployed |
| server | `stage1b/peak_tables.json` | `v5/stage1b/peak_tables.json` | 5c87f919940c13d0 | equal to deployed |
| server | `stage4/DISTRACTORS.json` | `v5/stage4/DISTRACTORS.json` | 876c576d2cdb9928 | equal to deployed |
| server | `stage4/ENERGY_TABLES.json` | `v5/stage4/ENERGY_TABLES.json` | cefe8f5233aacf97 | equal to deployed |
| server | `stage4/FM_CHECK.md` | `v5/stage4/FM_CHECK.md` | d7cb3cfb580f3e2c | equal to deployed |
| server | `stage4/MANUAL.md` | `v5/stage4/MANUAL.md` | 85fea166a40eae5d | equal to deployed |
| server | `stage4/SELECTION.json` | `v5/stage4/SELECTION.json` | 314a456c5476984a | equal to deployed |
| server | `stage4/SELECTION.md` | `v5/stage4/SELECTION.md` | a42fdadc75b04e6f | equal to deployed |
| server | `stage4/STATED_ERRORS.json` | `v5/stage4/STATED_ERRORS.json` | f43e84ac2f72f8f8 | equal to deployed |
| server | `stage4/TUNING.md` | `v5/stage4/TUNING.md` | 1bf6dbec57a16f07 | equal to deployed |
| server | `stage4/WORLDS.json` | `v5/stage4/WORLDS.json` | c849075f6dac801e | equal to deployed |
| server | `stage4/build_tables.py` | `v5/stage4/build_tables.py` | cca04f98fbfb4052 | equal to deployed |
| server | `stage4/census.py` | `v5/stage4/census.py` | 261a0764a258a66d | equal to deployed |
| server | `stage4/distractors.py` | `v5/stage4/distractors.py` | bf10a9bde1fcdcc6 | equal to deployed |
| server | `stage4/fm_dev.py` | `v5/stage4/fm_dev.py` | f9b2121177519125 | equal to deployed |
| server | `stage4/fm_library.json` | `v5/stage4/fm_library.json` | de10da4588a20ec3 | equal to deployed |
| server | `stage4/fm_library.py` | `v5/stage4/fm_library.py` | f6ac1cce01f601ba | equal to deployed |
| server | `stage4/library_structures.json` | `v5/stage4/library_structures.json` | 6e2c3cfaa3ae3a68 | equal to deployed |
| server | `stage4/noprior_table.py` | `v5/stage4/noprior_table.py` | 06f5442541149eb5 | equal to deployed |
| server | `stage4/peak_tables.json` | `v5/stage4/peak_tables.json` | cabc86e90b8ca279 | equal to deployed |
| server | `stage4/placebo_model.json` | `v5/stage4/placebo_model.json` | a099916a309edb4f | equal to deployed |
| server | `stage4/select4.py` | `v5/stage4/select4.py` | 325d396e78ee9a03 | equal to deployed |
| runner/analysis | `F/sllm/PROGRAMS_G.md` | `v7/F/sllm/PROGRAMS_G.md` | 6adde1cd22cb9ada | unchanged |
| runner/analysis | `F/sllm/audit_authors.py` | `v7/F/sllm/audit_authors.py` | 48baa9f84fea3314 | unchanged |
| runner/analysis | `F/sllm/audit_run.py` | `v7/F/sllm/audit_run.py` | a149d6ab3f13c3d8 | unchanged |
| runner/analysis | `F/sllm/author.py` | `v7/F/sllm/author.py` | c0bf172e4f17f432 | unchanged |
| runner/analysis | `F/sllm/dev_tokens_G_HT.txt` | `v7/F/sllm/dev_tokens_G_HT.txt` | bfc81ddecb784bb3 | unchanged |
| runner/analysis | `F/sllm/dev_tokens_G_R.txt` | `v7/F/sllm/dev_tokens_G_R.txt` | 483fe048057d9b9d | unchanged |
| runner/analysis | `F/sllm/inputs_G/H/INSTRUCTION.txt` | `v7/F/sllm/inputs_G/H/INSTRUCTION.txt` | 3a3eda72027197dd | unchanged |
| runner/analysis | `F/sllm/inputs_G/H/client.py` | `v7/F/sllm/inputs_G/H/client.py` | 63d14e1a55d883b9 | unchanged |
| runner/analysis | `F/sllm/inputs_G/H/manual.md` | `v7/F/sllm/inputs_G/H/manual.md` | 931ad21a51ad84f3 | unchanged |
| runner/analysis | `F/sllm/inputs_G/H/tools.json` | `v7/F/sllm/inputs_G/H/tools.json` | 9640864c82a2e0d7 | unchanged |
| runner/analysis | `F/sllm/inputs_G/R/INSTRUCTION.txt` | `v7/F/sllm/inputs_G/R/INSTRUCTION.txt` | 3a3eda72027197dd | unchanged |
| runner/analysis | `F/sllm/inputs_G/R/client.py` | `v7/F/sllm/inputs_G/R/client.py` | 63d14e1a55d883b9 | unchanged |
| runner/analysis | `F/sllm/inputs_G/R/manual.md` | `v7/F/sllm/inputs_G/R/manual.md` | e205b4661d4344b6 | unchanged |
| runner/analysis | `F/sllm/inputs_G/R/tools.json` | `v7/F/sllm/inputs_G/R/tools.json` | 8bf86abf4358fcb7 | unchanged |
| runner/analysis | `F/sllm/inputs_G/T/INSTRUCTION.txt` | `v7/F/sllm/inputs_G/T/INSTRUCTION.txt` | 3a3eda72027197dd | unchanged |
| runner/analysis | `F/sllm/inputs_G/T/client.py` | `v7/F/sllm/inputs_G/T/client.py` | 63d14e1a55d883b9 | unchanged |
| runner/analysis | `F/sllm/inputs_G/T/manual.md` | `v7/F/sllm/inputs_G/T/manual.md` | 5d9e9a7dcf1b3ac4 | unchanged |
| runner/analysis | `F/sllm/inputs_G/T/tools.json` | `v7/F/sllm/inputs_G/T/tools.json` | 3db06d3573c20bf3 | unchanged |
| runner/analysis | `F/sllm/inputs_G/tokens_inputs.txt` | `v7/F/sllm/inputs_G/tokens_inputs.txt` | 104ac131cebedf60 | unchanged |
| runner/analysis | `F/sllm/programs_G/H1.py` | `v7/F/sllm/programs_G/H1.py` | 6c9806cc56aea351 | unchanged |
| runner/analysis | `F/sllm/programs_G/H2.py` | `v7/F/sllm/programs_G/H2.py` | 0f77d8ddb97e03cf | unchanged |
| runner/analysis | `F/sllm/programs_G/H3.py` | `v7/F/sllm/programs_G/H3.py` | 13b7ed546a846eb8 | unchanged |
| runner/analysis | `F/sllm/programs_G/H4.py` | `v7/F/sllm/programs_G/H4.py` | d5c8cfb3fdd2aa66 | unchanged |
| runner/analysis | `F/sllm/programs_G/H5.py` | `v7/F/sllm/programs_G/H5.py` | 8d4bb04671cdad24 | unchanged |
| runner/analysis | `F/sllm/programs_G/R1.py` | `v7/F/sllm/programs_G/R1.py` | d9449fdad6e23af0 | unchanged |
| runner/analysis | `F/sllm/programs_G/R2.py` | `v7/F/sllm/programs_G/R2.py` | 194ac666c18f30a9 | unchanged |
| runner/analysis | `F/sllm/programs_G/R3.py` | `v7/F/sllm/programs_G/R3.py` | f3762bb196f42716 | unchanged |
| runner/analysis | `F/sllm/programs_G/R4.py` | `v7/F/sllm/programs_G/R4.py` | b350578539f9a4a4 | unchanged |
| runner/analysis | `F/sllm/programs_G/R5.py` | `v7/F/sllm/programs_G/R5.py` | 1928feb8203499f1 | unchanged |
| runner/analysis | `F/sllm/programs_G/T1.py` | `v7/F/sllm/programs_G/T1.py` | 129081b93dade3fe | unchanged |
| runner/analysis | `F/sllm/programs_G/T2.py` | `v7/F/sllm/programs_G/T2.py` | 2df76c1901bb9418 | unchanged |
| runner/analysis | `F/sllm/programs_G/T3.py` | `v7/F/sllm/programs_G/T3.py` | f67e76a086f17406 | unchanged |
| runner/analysis | `F/sllm/programs_G/T4.py` | `v7/F/sllm/programs_G/T4.py` | 6903ae5346818174 | unchanged |
| runner/analysis | `F/sllm/programs_G/T5.py` | `v7/F/sllm/programs_G/T5.py` | d43d106c1d29adcb | unchanged |
| runner/analysis | `F/sllm/run/worlds_B1_H.txt` | `v7/F/sllm/run/worlds_B1_H.txt` | 471249685d146ca6 | unchanged |
| runner/analysis | `F/sllm/run_sllm.py` | `v7/F/sllm/run_sllm.py` | 60f82fec31e7cafc | unchanged |
| runner/analysis | `v7ref/FREEZE.md` | `v7/FREEZE.md` | ec52fdef4eb899f6 | unchanged |
| runner/analysis | `H/FM_CHECK.md` | `v7/H/FM_CHECK.md` | 127c981b4ebc3dc6 | unchanged |
| runner/analysis | `P/audit.py` | `v7/P/audit.py` | d3c32b4f66c7a1fd | unchanged |
| runner/analysis | `P/core.py` | `v7/P/core.py` | 0c5822dd46cc449e | unchanged |
| runner/analysis | `P/replay7.py` | `v7/P/replay7.py` | 1b8f1fa313a30047 | unchanged |
| runner/analysis | `T/fm/fm_check.json` | `v7/T/fm/fm_check.json` | b973fcc902f3cc7e | unchanged |
| runner/analysis | `T/run_subsets.json` | `v7/T/run_subsets.json` | 72d25b55b27d5860 | unchanged |
| runner/analysis | `analyzeF.py` | `v7/analyzeF.py` | 0edceee787f01e47 | unchanged |
| runner/analysis | `analyzeG.py` | `v7/analyzeG.py` | cd827aebdface15d | unchanged |
| runner/analysis | `b1/ROWS_NODFT.md` | `v7/b1/ROWS_NODFT.md` | d8982b37305e258b | unchanged |
| runner/analysis | `evidence7.py` | `v7/evidence7.py` | 5fbda604953b7d60 | unchanged |
| runner/analysis | `figG.py` | `v7/figG.py` | ddb37ce5d174aea8 | unchanged |
| runner/analysis | `gatesF.py` | `v7/gatesF.py` | 0c2860750858f68f | unchanged |
| runner/analysis | `run_qwen7.py` | `v7/run_qwen7.py` | afb2f93ea2df2988 | unchanged |
| runner/analysis | `bench/fm/fm_check.json` | `v6/bench/fm/fm_check.json` | 4c3d5fcfef003a31 | unchanged |
| runner/analysis | `.claude/agents/v5-sonnet-v6-active-fm.md` | `v7/.claude/agents/v5-sonnet-v6-active-fm.md` | 6ad54d3e7230c865 | unchanged |
| runner/analysis | `.claude/agents/v5-sonnet-v7h-fm.md` | `v7/.claude/agents/v5-sonnet-v7h-fm.md` | b04808658512419b | unchanged |
| runner/analysis | `.claude/agents/v5-sonnet-v7t-fm.md` | `v7/.claude/agents/v5-sonnet-v7t-fm.md` | 5c1b26191cd4c3cb | unchanged |
| runner/analysis | `.claude/agents/v5-haiku-v7h-fm.md` | `v7/.claude/agents/v5-haiku-v7h-fm.md` | 1edadd4062034b34 | unchanged |
| runner/analysis | `.claude/agents/v5-haiku-v7t-fm.md` | `v7/.claude/agents/v5-haiku-v7t-fm.md` | d3d7b8154c7ae163 | unchanged |
| runner/analysis | `.claude/agents/v5-haiku-v6-active-fm.md` | `v6/.claude/agents/v5-haiku-v6-active-fm.md` | ba3d12cfe63880fa | unchanged |
| runner/analysis | `.claude/agents/v5-sonnet-active.md` | `v7/.claude/agents/v5-sonnet-active.md` | 4a9f35056e36d2fd | unchanged |

## The four files that differ from the deployed copies

- `H/WORLDS_H.json`, `T/WORLDS_T.json`: the deployed files are the drafts copied before the freeze. They differ from the frozen files (FREEZE V7-3a c7916260949f7438, V7-2a 5fc8bb45cb8f46cd) only in bookkeeping fields the server never reads (`status`, and per world `in_bench`, `selection_rows_pass`, `bench_note`); every field `family7` reads is equal (checked by a JSON comparison, VP1-0). vP.1 serves the frozen files.
- `graphexec/adapters_mcenv.py`: the repository copy adds V7-E2's measure rule to the executor's client (`Env.call`), which no server path runs.
- `mcenv/run_claude.py`: host A's runner, not part of the server; the repository copy carries V7-X17's slot gate.
