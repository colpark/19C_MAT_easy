#!/bin/bash
# V7-4: family H, 368 Sonnet episodes (46 worlds x noprior, fm x k 1-4) on node A2:8783, 4 concurrent
cd ~/Documents/harbor/v7/v7
export MCENV_URL=http://192.168.100.11:8783/call MCENV_RETRY_DIR=$PWD/runs/H/v7_4/retries
mkdir -p runs/H/v7_4/retries runs/H/v7_4/episodes
~/v5env/bin/python -m mcenv.run_claude runs/H/v7_4/plan.jsonl runs/H/v7_4/episodes --conc 4 >> runs/H/v7_4/run.log 2>&1
echo "$(date -u +%FT%TZ) done" >> runs/H/v7_4/run.log
