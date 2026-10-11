#!/bin/bash
# Frozen copy of the V5-15 code for the stage 3 environment server on node A2 (port 8770; the FM service, if running, moves to 8771).
set -e
cd ~/Documents/harbor/v5/v5
ssh aid1@192.168.100.11 'mkdir -p ~/v5srv_3 ~/v5_state_3_runs && chmod 700 ~/v5_state_3_runs'
rsync -a --delete --exclude __pycache__ mcenv scenarios stage1b stage3 aid1@192.168.100.11:v5srv_3/
ssh -n -f aid1@192.168.100.11 'cd ~/v5srv_3 && cat mcenv/*.py | sha256sum | cut -c1-16 > CODE_SHA && MCENV_STATE=~/v5_state_3_runs MCENV_BIND=192.168.100.11 MCENV_PORT=8770 OPENBLAS_NUM_THREADS=1 setsid nohup ~/v5env/bin/python -m mcenv.server3 > ~/v5_state_3_runs/server.log 2>&1 < /dev/null & echo $! > ~/v5_state_3_runs/server.pid'
