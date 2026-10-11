#!/bin/bash
# stage 2s run plans (V5_SPEC E.7), registered on the frozen server copy on node A2 (state ~/v5_state_2s_runs); prints runner lines only
ssh aid1@192.168.100.11 'cd ~/v5srv_2s && W=461,462,463,464,465,466,467,468,469,470 && export MCENV_STATE=~/v5_state_2s_runs V5_STAGE=2s &&
  ~/v5env/bin/python -m mcenv.admin newplan --arms placebo,fm,ceiling --model sonnet --ks 1,2,3,4,5 --batch v5-14-sonnet --worlds $W &&
  ~/v5env/bin/python -m mcenv.admin newplan --arms placebo,fm --model opus --ks 1 --batch v5-14-opus --worlds $W &&
  ~/v5env/bin/python -m mcenv.admin newplan --arms fm,placebo --model haiku --ks 1,2,3 --batch v5-14-haiku --worlds $W' > runs/stage2s/plan_all.jsonl
wc -l runs/stage2s/plan_all.jsonl
