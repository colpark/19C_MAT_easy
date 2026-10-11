#!/bin/bash
# Stage 2r gate (V5_SPEC D.7), after the V5-10 freeze: placebo and FM arms, k = 1..5, all five scenarios (ceiling from the precondition run).
cd ~/v5sweep
tag=${1:-gate1}; arms=${2:-placebo,fm}; scens=${3:-41,42,43,44,45}
mkdir -p stage2r/validation/$tag; rm -rf ~/v5_state_2r_$tag
export MCENV_STATE=~/v5_state_2r_$tag V5_GATE_BATCH=v5-10-$tag V5_PROCS=16 OPENBLAS_NUM_THREADS=1 V5_FM_URL=http://192.168.100.11:8770/relax
~/v5env/bin/python -m mcenv.planner2r stage2r/validation/$tag/tokens.txt $arms 1,2,3,4,5 $scens > stage2r/validation/$tag/planner.log 2>&1
~/v5env/bin/python -m mcenv.grade stage2r/validation/$tag/tokens.txt stage2r/validation/$tag/graded.jsonl > stage2r/validation/$tag/grade.log 2>&1
