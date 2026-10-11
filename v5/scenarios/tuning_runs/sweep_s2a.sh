#!/bin/bash
# stage 2 tuning sweep A (logged in stage2/TUNING2.md)
cd ~/v5work
run(){ s=$1; shift; tag=$(echo "$@" | tr ' =' '_-'); nice -n 10 ~/v5env/bin/python -m mcenv.tune $s "$@" 2>/dev/null > scenarios/tuning_runs/s${s}_${tag}.json; echo "$(date -u +%T) done s$s $@"; }
run 11
run 12 N=50 L=60
run 12 N=20 L=60
run 13
run 13 N=600
run 14 N=30 L=30
run 14 N=10 L=30
run 15 N=100
run 15 N=50
