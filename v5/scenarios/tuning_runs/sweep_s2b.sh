#!/bin/bash
# stage 2 tuning sweep B: S2-B (scenario 12) size/background (logged in stage2/TUNING2.md)
cd ~/v5work
while pgrep -f sweep_s2a.sh > /dev/null; do sleep 20; done
run(){ s=$1; shift; tag=$(echo "$@" | tr ' =' '_-'); nice -n 10 ~/v5env/bin/python -m mcenv.tune $s "$@" 2>/dev/null > scenarios/tuning_runs/s${s}_${tag}.json; echo "$(date -u +%T) done s$s $@"; }
run 12 N=40 L=150
run 12 N=40 L=60 bg=5
run 12 N=30 L=300 bg=5
run 12 N=60 L=300 bg=5
run 12 N=30 L=1000 bg=2
