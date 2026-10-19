#!/bin/bash
# V7-4 (V7-X8, V7-X10): family T, Sonnet noprior and fm on 24 passing paired quads, k 1, 192 episodes, node A2:8784, 4 concurrent
cd ~/Documents/harbor/v7/v7
export MCENV_URL=http://192.168.100.11:8784/call MCENV_RETRY_DIR=$PWD/runs/T/v7_4/retries
mkdir -p runs/T/v7_4/retries runs/T/v7_4/episodes
~/v5env/bin/python -m mcenv.run_claude runs/T/v7_4/plan.jsonl runs/T/v7_4/episodes --conc 4 >> runs/T/v7_4/run.log 2>&1
echo "$(date -u +%FT%TZ) done" >> runs/T/v7_4/run.log
