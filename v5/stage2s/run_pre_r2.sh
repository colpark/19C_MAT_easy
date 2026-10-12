#!/bin/bash
# stage 2s ceiling precondition (V5_SPEC E.6): the ceiling planner on 46-50, k = 1..5, FM disabled (no FM call), own state; then grade
cd ~/v5run2s
export MCENV_STATE=$HOME/v5_state_2s_pre_r2 OPENBLAS_NUM_THREADS=1 V5_NO_FM=1 V5_GATE_BATCH=v5-13r-pre V5_S2S_ROUND=2 V5_PROCS=10
mkdir -p stage2s/validation/pre_r2
~/v5env/bin/python -m mcenv.planner2s stage2s/validation/pre_r2/tokens.txt first ceiling 1,2,3,4,5 46,47,48,49,50 > stage2s/validation/pre_r2/run.log 2>&1
~/v5env/bin/python -m mcenv.grade2s stage2s/validation/pre_r2/tokens.txt stage2s/validation/pre_r2/graded.jsonl 16 >> stage2s/validation/pre_r2/run.log 2>&1
echo done >> stage2s/validation/pre_r2/run.log
