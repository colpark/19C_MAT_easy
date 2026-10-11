#!/bin/bash
# Frozen copy of the V5-8 code for the stage 1b environment server on node A2 (V5_SPEC C.7). Run from host A after the V5-8 commit.
set -e
cd ~/Documents/harbor/v5/v5
rsync -a --delete --exclude __pycache__ mcenv scenarios stage1b aid1@192.168.100.11:v5srv_1b/
ssh aid1@192.168.100.11 'mkdir -p ~/v5_state_1b && chmod 700 ~/v5_state_1b && cd ~/v5srv_1b && cat mcenv/*.py | sha256sum | cut -c1-16 > CODE_SHA && \
  V5_STAGE=1b MCENV_STATE=~/v5_state_1b MCENV_BIND=192.168.100.11 MCENV_PORT=8766 OPENBLAS_NUM_THREADS=1 setsid nohup ~/v5env/bin/python -m mcenv.server > ~/v5_state_1b/server.log 2>&1 < /dev/null & sleep 3; cat ~/v5_state_1b/server.log; cat ~/v5srv_1b/CODE_SHA'
