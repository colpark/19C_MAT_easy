#!/usr/bin/env bash
# Start the PanelBench `plots` backend worker on 0.0.0.0:8103 (node 2, spark-0b70).
# Usage: ~/mcp/plots/start.sh            (lazy model loading)
#        PLOTS_PRELOAD=1 ~/mcp/plots/start.sh   (load all models at startup)
#        PLOTS_DEVICE=cpu ~/mcp/plots/start.sh  (force CPU)
set -euo pipefail
cd "$(dirname "$0")"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 CUBLAS_WORKSPACE_CONFIG=:4096:8
export PLOTS_PORT="${PLOTS_PORT:-8103}"
exec ./.venv/bin/python worker.py
