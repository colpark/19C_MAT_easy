# vision backend (PanelBench MCP toolset v1)

Runs on node 2 (spark-0b70) from `~/mcp/vision`. Code only here; venv, repos and weights live on node 2.

Start (foreground):  `ssh -i ~/.ssh/node11 aid1@192.168.100.11 ~/mcp/vision/start.sh`
(for background: `nohup ~/mcp/vision/start.sh > ~/mcp/vision/worker.out 2>&1 &`). Binds 0.0.0.0:8101 (override with PORT).

Endpoints: GET /health, GET /version, POST /segment, /segment_microstructure, /grain_size_astm, /grain_boundary_map
(returns status "unavailable"), /classify_modality_embed, /find_atoms. Body: {"image_b64": ..., "args": {...}, "seed": 0}.
Models load lazily on first call (cold call adds ~1-6 s; SAM ViT-H ~2.5 GB). Requests are serialized by a lock and logged
to ~/mcp/vision/requests.log. smoke.py / atoms_sweep.py are the smoke tests (run on node 2 with the family venv).
Provenance and licenses: ../../env_logs/vision.md.
