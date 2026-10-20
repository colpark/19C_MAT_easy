#!/bin/bash
# V7-4 (V7-X8, V7-X10): T Haiku noprior/fm (96, 4 concurrent), then T Sonnet fm-planner (48, 2 concurrent, 5400 s limit), node A2:8784
cd ~/Documents/harbor/v7/v7
export MCENV_URL=http://192.168.100.11:8784/call
MCENV_RETRY_DIR=$PWD/runs/T/haiku/retries ~/v5env/bin/python -m mcenv.run_claude runs/T/haiku/plan.jsonl runs/T/haiku/episodes --conc 4 >> runs/T/haiku/run.log 2>&1
echo "$(date -u +%FT%TZ) haiku done" >> runs/T/haiku/run.log
MCENV_RETRY_DIR=$PWD/runs/T/planner/retries ~/v5env/bin/python run_long7.py runs/T/planner/plan.jsonl runs/T/planner/episodes 2 5400 >> runs/T/planner/run.log 2>&1
echo "$(date -u +%FT%TZ) planner done" >> runs/T/planner/run.log
