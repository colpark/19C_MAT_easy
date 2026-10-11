#!/bin/bash
# stage 2 tuning sweep C: S2-B (12) and S2-E (15) (logged in stage2/TUNING2.md)
cd ~/v5work
run(){ s=$1; shift; tag=$(echo "$@" | tr ' =' '_-'); nice -n 10 ~/v5env/bin/python -m mcenv.tune $s "$@" 2>/dev/null > scenarios/tuning_runs/s${s}_${tag}.json; echo "$(date -u +%T) done s$s $@"; }
run 12 N=30 L=60 bg=5
run 12 N=35 L=60 bg=5
run 15 N=800 bg=5
run 15 N=1000 bg=5
run 15 N=1000 bg=20
