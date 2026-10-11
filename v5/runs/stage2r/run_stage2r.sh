#!/bin/bash
# Stage 2r model runs (V5_SPEC D.8): Sonnet placebo/fm/ceiling/blindfm k5, Opus placebo/fm k1 = 220 episodes, 4 concurrent, after stage 1b.
cd ~/Documents/harbor/v5/v5

export V5_S2R_ROUND=2 MCENV_URL=http://192.168.100.11:8768/call MCENV_RETRY_DIR=$PWD/runs/stage2r/retries
~/v5env/bin/python -m mcenv.run_claude runs/stage2r/plan_v2.jsonl runs/stage2r/episodes --conc 4 >> runs/stage2r/run.log 2>&1
