#!/bin/bash
# V7-F4 fm-hint: Sonnet fm arm with the expert advice appended to the task text (runner-side only), k 1, 4 concurrent
cd ~/Documents/harbor/v7/v7
R=runs/F/hint
MCENV_URL=http://192.168.100.11:8784/call MCENV_RETRY_DIR=$PWD/$R/retries ~/v5env/bin/python -m mcenv.run_claude $R/plan_H.jsonl $R/episodes_H --conc 4 >> $R/run.log 2>&1
echo "$(date -u +%FT%TZ) H done" >> $R/run.log
MCENV_URL=http://192.168.100.11:8784/call MCENV_RETRY_DIR=$PWD/$R/retries ~/v5env/bin/python -m mcenv.run_claude $R/plan_T.jsonl $R/episodes_T --conc 4 >> $R/run.log 2>&1
echo "$(date -u +%FT%TZ) T done" >> $R/run.log
MCENV_URL=http://192.168.100.11:8778/call MCENV_RETRY_DIR=$PWD/$R/retries ~/v5env/bin/python -m mcenv.run_claude $R/plan_B1.jsonl $R/episodes_B1 --conc 4 >> $R/run.log 2>&1
echo "$(date -u +%FT%TZ) B1 done" >> $R/run.log
