#!/usr/bin/env bash
# Start the PanelBench MCP `vision` worker on 0.0.0.0:8101 (node 2). Foreground; use nohup/tmux for background.
set -euo pipefail
cd "$HOME/mcp/vision"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 CUBLAS_WORKSPACE_CONFIG=:4096:8
export CELLPOSE_LOCAL_MODELS_PATH="$HOME/mcp/vision/weights/cellpose"
export PORT="${PORT:-8101}"
exec "$HOME/mcp/vision/.venv/bin/python" worker.py
