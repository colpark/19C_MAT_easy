#!/bin/bash
# Ceiling precondition (V5_SPEC D.6) before V5-10: ceiling arm only, no FM call (V5_NO_FM=1), k = 1..5, all five scenarios.
cd ~/v5sweep
tag=${1:-pre1}; scens=${2:-41,42,43,44,45}
mkdir -p stage2r/validation/$tag; rm -rf ~/v5_state_2r_$tag
export MCENV_STATE=~/v5_state_2r_$tag V5_NO_FM=1 V5_GATE_BATCH=v5-10-$tag V5_PROCS=19 OPENBLAS_NUM_THREADS=1
~/v5env/bin/python -m mcenv.planner2r stage2r/validation/$tag/tokens.txt ceiling 1,2,3,4,5 $scens > stage2r/validation/$tag/planner.log 2>&1
~/v5env/bin/python -m mcenv.grade stage2r/validation/$tag/tokens.txt stage2r/validation/$tag/graded.jsonl > stage2r/validation/$tag/grade.log 2>&1
~/v5env/bin/python -m mcenv.gate_report2r stage2r/validation/$tag/graded.jsonl stage2r/validation/constraints_run.json stage2r/validation/$tag/tokens.txt.plans.json stage2r/validation/$tag/PRECONDITION.md "Stage 2r ceiling precondition ($tag)" > /dev/null 2>&1
