#!/bin/bash
# V6-5 agent test: 54 Claude episodes (Sonnet 30, Haiku 18, Opus 6) on the v6 server (node A2:8776), 4 concurrent
cd ~/Documents/harbor/v6/v6
export MCENV_URL=http://192.168.100.11:8776/call MCENV_RETRY_DIR=$PWD/runs/agent_test/retries
mkdir -p runs/agent_test/retries runs/agent_test/episodes
~/v5env/bin/python -m mcenv.run_claude runs/agent_test/plan.jsonl runs/agent_test/episodes --conc 4 >> runs/agent_test/run.log 2>&1
echo done >> runs/agent_test/run.log
