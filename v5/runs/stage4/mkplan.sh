#!/bin/bash
# stage 4 run plans (V5_SPEC I.14), registered on the frozen server copy on node A2 (state ~/v5_state_4_runs); prints runner lines only.
# Claude: 528 episodes. Seeds world x 100 + k (admin), shared by every arm and model.
W=601,602,603,604,605,606,607,608,609,610,611,612,613,614,615,616
ssh -n aid1@192.168.100.11 "cd ~/v5srv_4 && export MCENV_STATE=~/v5_state_4_runs V5_STAGE=4 &&
  ~/v5env/bin/python -m mcenv.admin newplan --arms active-noprior,active-fm --model sonnet --ks 1,2,3,4,5 --batch v5-25-sonnet-core --worlds $W &&
  ~/v5env/bin/python -m mcenv.admin newplan --arms blind-noprior,blind-fm --model sonnet --ks 1,2,3 --batch v5-25-sonnet-blind --worlds $W &&
  ~/v5env/bin/python -m mcenv.admin newplan --arms active-placebo,active-ceiling,active-dftpriced --model sonnet --ks 1,2,3 --batch v5-25-sonnet-extra --worlds $W &&
  ~/v5env/bin/python -m mcenv.admin newplan --arms active-noprior,active-fm --model haiku --ks 1,2,3 --batch v5-25-haiku --worlds $W &&
  ~/v5env/bin/python -m mcenv.admin newplan --arms active-noprior,active-fm --model opus --ks 1 --batch v5-25-opus --worlds $W" > runs/stage4/plan_all.jsonl
wc -l runs/stage4/plan_all.jsonl
