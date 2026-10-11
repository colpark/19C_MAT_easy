#!/bin/bash
# stage 3 run plans (V5_SPEC F.8), registered on the frozen server copy on node A2 (state ~/v5_state_3_runs); prints runner lines only
ssh aid1@192.168.100.11 'cd ~/v5srv_3 && export MCENV_STATE=~/v5_state_3_runs V5_STAGE=3 &&
  ~/v5env/bin/python -m mcenv.admin newplan --arms active,validity --model sonnet --ks 1,2,3,4,5 --batch v5-16-sonnet-fault --worlds 531,532,533,534,535,536,537,538,539,540,541,542,543,544,545,546,547,548,549,550,551,552,553,554,555,556,557,558 &&
  ~/v5env/bin/python -m mcenv.admin newplan --arms active --model sonnet --ks 1,2,3,4,5 --batch v5-16-sonnet-clean --worlds 501,502,503,504,505,506,507,508,509,510,511,512,513,514,515,516,517,518,519,520,521,522,523,524,525,526,527,528 &&
  ~/v5env/bin/python -m mcenv.admin newplan --arms active --model haiku --ks 1,2,3 --batch v5-16-haiku --worlds 531,532,533,534,535,536,537,538,539,540,541,542,543,544,545,546,547,548,549,550,551,552,553,554,555,556,557,558 &&
  ~/v5env/bin/python -m mcenv.admin newplan --arms active --model opus --ks 1 --batch v5-16-opus --worlds 531,532,533,534,535,536,537,538,539,540,541,542,543,544,545,546,547,548,549,550,551,552,553,554,555,556,557,558' > runs/stage3/plan_all.jsonl
wc -l runs/stage3/plan_all.jsonl
