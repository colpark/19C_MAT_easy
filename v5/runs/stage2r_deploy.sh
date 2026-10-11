#!/bin/bash
# Frozen copy of the V5-10 code for the stage 2r environment server on node A2 (port 8768), replacement-round scenarios.
set -e
cd ~/Documents/harbor/v5/v5
ssh aid1@192.168.100.11 'mkdir -p ~/v5srv_2r/data/stage2 ~/v5_state_2r_runs && chmod 700 ~/v5_state_2r_runs'
rsync -a --delete --exclude __pycache__ mcenv scenarios stage2 stage2r aid1@192.168.100.11:v5srv_2r/
rsync -a data/stage2/2024-08-04-wbm-relaxed-atoms.extxyz.zip aid1@192.168.100.11:v5srv_2r/data/stage2/
ssh -n -f aid1@192.168.100.11 'cd ~/v5srv_2r && cat mcenv/*.py | sha256sum | cut -c1-16 > CODE_SHA && V5_S2R_ROUND=2 MCENV_STATE=~/v5_state_2r_runs MCENV_BIND=192.168.100.11 MCENV_PORT=8768 V5_FM_URL=http://192.168.100.11:8770/relax OPENBLAS_NUM_THREADS=1 setsid nohup ~/v5env/bin/python -m mcenv.server2r > ~/v5_state_2r_runs/server.log 2>&1 < /dev/null &'
