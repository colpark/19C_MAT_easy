#!/bin/bash
# Stage 4 Claude runs (V5_SPEC I.14): 528 episodes, 4 concurrent, frozen server on node A2:8773
cd ~/Documents/harbor/v5/v5
export MCENV_URL=http://192.168.100.11:8773/call MCENV_RETRY_DIR=$PWD/runs/stage4/retries
mkdir -p runs/stage4/retries runs/stage4/episodes
~/v5env/bin/python -m mcenv.run_claude ${PLAN:-runs/stage4/plan_all.jsonl} runs/stage4/episodes --conc ${CONC:-4} >> runs/stage4/run.log 2>&1
echo done >> runs/stage4/run.log
