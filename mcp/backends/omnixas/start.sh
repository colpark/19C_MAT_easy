#!/usr/bin/env bash
# Start the omnixas worker (CPU) on 0.0.0.0:8105. Run on node 2 from ~/mcp/omnixas.
set -euo pipefail
cd "$(dirname "$0")"
export DGLBACKEND=pytorch HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 CUDA_VISIBLE_DEVICES=""
# matgl mkdirs $HOME/.cache/matgl on import; keep it inside the family folder
export HOME="$PWD/home"; mkdir -p "$HOME"
export OMNIXAS_PORT="${OMNIXAS_PORT:-8105}"
exec ./.venv/bin/python worker.py
