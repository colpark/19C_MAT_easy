#!/bin/bash
# Qwen3-8B stage 4 (V5_SPEC I.14): host B, frozen V5-24 server copy at 127.0.0.1:8774 (state ~/v5_state_Q4), runner folder ~/v5runQ4,
# active-noprior and active-fm k = 1..3 (96 episodes), one runner at 8 concurrent (V5-E21). No delete flag on sync (new folders).
set -e
cd ~/Documents/harbor/v5/v5
ssh -n aid1@130.199.95.15 'test ! -e ~/v5srvB_4 && mkdir -p ~/v5srvB_4 ~/v5_state_Q4 ~/v5runQ4 && chmod 700 ~/v5_state_Q4'
rsync -a --exclude __pycache__ --exclude dev --exclude 'validation/scripted' mcenv scenarios stage1b stage4 aid1@130.199.95.15:v5srvB_4/
rsync -a --exclude __pycache__ mcenv .claude aid1@130.199.95.15:v5runQ4/
ssh -n -f aid1@130.199.95.15 'cd ~/v5srvB_4 && cat mcenv/*.py | sha256sum | cut -c1-16 > CODE_SHA && MCENV_STATE=~/v5_state_Q4 MCENV_BIND=127.0.0.1 MCENV_PORT=8774 OPENBLAS_NUM_THREADS=1 setsid nohup ~/v5env/bin/python -m mcenv.server4 > ~/v5_state_Q4/server.log 2>&1 < /dev/null & echo $! > ~/v5_state_Q4/server.pid'
sleep 10
ssh -n aid1@130.199.95.15 'cd ~/v5srvB_4 && MCENV_STATE=~/v5_state_Q4 V5_STAGE=4 ~/v5env/bin/python -m mcenv.admin newplan --arms active-noprior,active-fm --model qwen3-8b --ks 1,2,3 --batch v5-25-qwen --worlds 601,602,603,604,605,606,607,608,609,610,611,612,613,614,615,616 2>/dev/null' | grep token > baseline/stage4/plan_qwen4.jsonl
rsync -a baseline/stage4/plan_qwen4.jsonl aid1@130.199.95.15:v5runQ4/
ssh -n -f aid1@130.199.95.15 'cd ~/v5runQ4 && mkdir -p ep4 retries4 && MCENV_RETRY_LOG_DIR=$PWD/retries4 setsid nohup ~/v5env/bin/python -m mcenv.run_qwen plan_qwen4.jsonl ep4 --conc 8 --env http://127.0.0.1:8774/call > run4.log 2>&1 < /dev/null & echo $! > run4.pid'
