#!/bin/bash
# V5-3 restart after V5-E9: Haiku (v2 plan with 5 replacement tokens) and Opus side by side, 3 + 3 concurrent (David: 6 total)
cd /home/aid1/Documents/harbor/v5/v5
nice -n 10 ~/v5env/bin/python -m mcenv.run_claude runs/stage1/p3_haiku_a_v2.jsonl runs/stage1/p3_haiku_a --conc 3 > runs/stage1/run_haiku.log 2>&1 &
nice -n 10 ~/v5env/bin/python -m mcenv.run_claude runs/stage1/p4_opus_a.jsonl runs/stage1/p4_opus_a --conc 3 > runs/stage1/run_opus.log 2>&1 &
wait
echo "STAGE1C DONE $(date -u +%FT%TZ)" >> runs/stage1/run.log
