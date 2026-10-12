#!/bin/bash
# Frozen copy of the V5-24 code for the stage 4 environment server on node A2 (port 8773; state ~/v5_state_4_runs). No delete flag
# (V5-E19): the target folder is new.
set -e
cd ~/Documents/harbor/v5/v5
ssh -n aid1@192.168.100.11 'test ! -e ~/v5srv_4 && mkdir -p ~/v5srv_4 ~/v5_state_4_runs && chmod 700 ~/v5_state_4_runs'
rsync -a --exclude __pycache__ --exclude dev --exclude 'validation/scripted' mcenv scenarios stage1b stage4 aid1@192.168.100.11:v5srv_4/
ssh -n -f aid1@192.168.100.11 'cd ~/v5srv_4 && cat mcenv/*.py | sha256sum | cut -c1-16 > CODE_SHA && MCENV_STATE=~/v5_state_4_runs MCENV_BIND=192.168.100.11 MCENV_PORT=8773 OPENBLAS_NUM_THREADS=1 setsid nohup ~/v5env/bin/python -m mcenv.server4 > ~/v5_state_4_runs/server.log 2>&1 < /dev/null & echo $! > ~/v5_state_4_runs/server.pid'
