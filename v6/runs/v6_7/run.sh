#!/bin/bash
# V6-7: 114 Claude episodes (agent test at N 4.1, sweep N 3 and 30, planner arm) on the v6 server (node A2:8776), 4 concurrent
cd ~/Documents/harbor/v6/v6
export MCENV_URL=http://192.168.100.11:8776/call MCENV_RETRY_DIR=$PWD/runs/v6_7/retries
mkdir -p runs/v6_7/retries runs/v6_7/episodes
~/v5env/bin/python -m mcenv.run_claude runs/v6_7/plan.jsonl runs/v6_7/episodes --conc 4 >> runs/v6_7/run.log 2>&1
echo done >> runs/v6_7/run.log
