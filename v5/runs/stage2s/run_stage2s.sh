#!/bin/bash
# Stage 2s model runs (V5_SPEC E.7): Sonnet placebo/fm/ceiling k5 (150), Opus placebo/fm k1 (20), Haiku fm/placebo k3 (60); 4 concurrent
cd ~/Documents/harbor/v5/v5
export MCENV_URL=http://192.168.100.11:8769/call MCENV_RETRY_DIR=$PWD/runs/stage2s/retries
~/v5env/bin/python -m mcenv.run_claude runs/stage2s/plan_all.jsonl runs/stage2s/episodes --conc 4 >> runs/stage2s/run.log 2>&1
echo done >> runs/stage2s/run.log
