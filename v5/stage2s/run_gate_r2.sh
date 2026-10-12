#!/bin/bash
# stage 2s gate and scripted agents (V5_SPEC E.5, E.6), on node A2 (FM service at 8771): FM-first, placebo-first, survey-first, prior-only,
# always-abstain on 46-50, k = 1..5, own state; then grade
cd ~/v5run2s
export V5_S2S_ROUND=2
export MCENV_STATE=$HOME/v5_state_2s_gate_r2 OPENBLAS_NUM_THREADS=1 V5_FM_URL=http://192.168.100.11:8771/relax V5_PROCS=8
export V5_2S_CONSTRAINTS=stage2s/validation/constraints_r2.json
O=stage2s/validation/gate_r2; mkdir -p $O
for spec in "first fm" "first placebo" "survey placebo" "prior fm" "abstain placebo"; do set -- $spec
  V5_GATE_BATCH=v5-13r-gate-$1-$2 ~/v5env/bin/python -m mcenv.planner2s $O/tokens_$1_$2.txt $1 $2 1,2,3,4,5 46,47,48,49,50 >> $O/run.log 2>&1
done
cat $O/tokens_*.txt > $O/tokens.txt
~/v5env/bin/python -m mcenv.grade2s $O/tokens.txt $O/graded.jsonl 12 >> $O/run.log 2>&1
echo done >> $O/run.log
