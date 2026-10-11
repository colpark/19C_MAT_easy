#!/bin/bash
# Stage 3 model runs (V5_SPEC F.8): Sonnet active/validity on fault worlds k5 (280), Sonnet active on clean worlds k5 (140), Haiku active
# fault k3 (84), Opus active fault k1 (28); 4 concurrent
cd ~/Documents/harbor/v5/v5
export MCENV_URL=http://192.168.100.11:8770/call MCENV_RETRY_DIR=$PWD/runs/stage3/retries
~/v5env/bin/python -m mcenv.run_claude runs/stage3/plan_all.jsonl runs/stage3/episodes --conc 4 >> runs/stage3/run.log 2>&1
echo done >> runs/stage3/run.log
