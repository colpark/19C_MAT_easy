#!/bin/bash
# V7-G1: Sonnet fm and fm-hint on the 30 fresh T quads, k 1; host-wide Claude cap 4 shared with v10 (V7-X17)
cd ~/Documents/harbor/v7/v7
R=runs/G/fresh
PLAN=${1:-$R/plan.jsonl}
MCENV_HOST_CAP=4 MCENV_URL=http://192.168.100.11:8784/call MCENV_RETRY_DIR=$PWD/$R/retries ~/v5env/bin/python -m mcenv.run_claude $PLAN $R/episodes --conc 3 >> $R/run.log 2>&1
echo "$(date -u +%FT%TZ) $PLAN done" >> $R/run.log
