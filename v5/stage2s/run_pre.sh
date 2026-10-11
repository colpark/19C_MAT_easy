#!/bin/bash
# stage 2s ceiling precondition (V5_SPEC E.6): the ceiling planner on 46-50, k = 1..5, FM disabled (no FM call), own state; then grade
cd ~/v5run2s
export MCENV_STATE=$HOME/v5_state_2s_pre OPENBLAS_NUM_THREADS=1 V5_NO_FM=1 V5_GATE_BATCH=v5-13-pre V5_PROCS=10
mkdir -p stage2s/validation/pre
~/v5env/bin/python -m mcenv.planner2s stage2s/validation/pre/tokens.txt first ceiling 1,2,3,4,5 46,47,48,49,50 > stage2s/validation/pre/run.log 2>&1
~/v5env/bin/python -m mcenv.grade2s stage2s/validation/pre/tokens.txt stage2s/validation/pre/graded.jsonl 16 >> stage2s/validation/pre/run.log 2>&1
echo done >> stage2s/validation/pre/run.log
