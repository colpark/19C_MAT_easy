#!/usr/bin/env bash
# Start the `science` family worker on 0.0.0.0:8104 (offline; GPU used for MACE/Orb/abTEM if available).
# Usage: ./start.sh            (foreground)   |  SCIENCE_DEVICE=cpu ./start.sh  (force CPU)
cd "$(dirname "$0")"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 MPLBACKEND=Agg SCIENCE_PORT=${SCIENCE_PORT:-8104}
exec ./.venv/bin/python worker.py
