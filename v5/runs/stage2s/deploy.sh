#!/bin/bash
# Frozen copy of the V5-13 code for the stage 2s environment server on node A2 (port 8769); FM service on node A2:8771.
set -e
cd ~/Documents/harbor/v5/v5
ssh aid1@192.168.100.11 'mkdir -p ~/v5srv_2s/data/stage2 ~/v5_state_2s_runs && chmod 700 ~/v5_state_2s_runs'
rsync -a --delete --exclude __pycache__ mcenv scenarios stage2 stage2r stage2s aid1@192.168.100.11:v5srv_2s/
rsync -a data/stage2/2024-08-04-wbm-relaxed-atoms.extxyz.zip aid1@192.168.100.11:v5srv_2s/data/stage2/
ssh -n -f aid1@192.168.100.11 'cd ~/v5srv_2s && cat mcenv/*.py | sha256sum | cut -c1-16 > CODE_SHA && MCENV_STATE=~/v5_state_2s_runs MCENV_BIND=192.168.100.11 MCENV_PORT=8769 V5_FM_URL=http://192.168.100.11:8771/relax OPENBLAS_NUM_THREADS=1 setsid nohup ~/v5env/bin/python -m mcenv.server2s > ~/v5_state_2s_runs/server.log 2>&1 < /dev/null & echo $! > ~/v5_state_2s_runs/server.pid'
