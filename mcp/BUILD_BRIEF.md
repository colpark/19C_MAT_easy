# Build brief for environment agents (PanelBench MCP toolset v1)

Node 2 = `ssh -i ~/.ssh/node11 aid1@192.168.100.11` (hostname spark-0b70; aarch64; NVIDIA GB10, CUDA driver 580.82.09; 20 cores,
119 GB RAM; Python 3.12.3; `uv` at ~/.local/bin/uv; internet available for installs). A working torch reference env exists:
~/panels/.venv (torch 2.14.0+cu130, CUDA works) - you may copy its torch wheel choice, do not modify it.

Rules (from the owner's prompt, binding):
1. Work only under node 2 `~/mcp/<family>/` (your family folder) and host A `~/Documents/harbor/mcp/env_logs/<family>.md`. Do not touch
   other folders on either machine, other agents' folders, task folders, or anything under ~/Documents/harbor/v0*.
2. One Python environment per family: `~/mcp/<family>/.venv` made with uv. Pin every version; record `pip freeze` into
   `~/mcp/<family>/freeze.txt` and copy it to the host A log folder.
3. For every cloned repo: record URL, commit hash, LICENSE file name and license (or "no LICENSE file"). For every weight file: path,
   size, sha256, source URL, license. NEVER copy weights into ~/Documents/harbor/mcp (that folder goes to git). Weights stay in
   `~/mcp/<family>/weights/` on node 2.
4. Time box: GPU builds 1 hour each; if CUDA does not work in time, fall back to CPU and say so. OmniXAS: 2 hours.
5. Verify each model with a tiny smoke inference (synthetic image or tutorial input), report timing and device.
6. Never write credentials or tokens into any file. Do not use sudo. Do not stop or kill processes you did not start.
7. Write a backend worker for your family: `~/mcp/<family>/worker.py`, a small HTTP/JSON server (FastAPI + uvicorn, or stdlib) bound to
   0.0.0.0:<port given to you>, endpoints GET /health, GET /version (tool versions + weight sha256s), POST /<tool> taking
   {"image_b64": <PNG/JPEG bytes base64>, "args": {...}, "seed": int} (or {"args": ...} for non-image tools), returning JSON
   {"values": ..., "units": ..., "confidence": ..., "warnings": [...], "provenance": {"tool", "tool_version", "backing_model",
   "weights_sha256", "seed", "device"}, "images": {"name": "<png base64>"} (optional)}. Deterministic: fixed seeds,
   torch.use_deterministic_algorithms(True, warn_only=True). Log each request (tool, sha256 of input, args, duration) to
   ~/mcp/<family>/requests.log. No outbound network calls at request time (set HF_HUB_OFFLINE=1, TRANSFORMERS_OFFLINE=1).
   Copy worker.py (code only) to host A `~/Documents/harbor/mcp/backends/<family>/` for git, with a short README of how to start it.
8. Do NOT start long-lived services yet beyond a quick test; leave a `start.sh` that starts the worker.
9. Final reply: per tool - status (works GPU / works CPU / unavailable + exact error), versions, commit, license, weight sha256s, smoke
   result; anything that needs an owner decision.
