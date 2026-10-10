#!/bin/bash
# V5-1 tuning sweep 1 (logged in TUNING.md)
cd ~/v5work
run(){ s=$1; shift; tag=$(echo "$@" | tr ' =' '_-'); nice -n 10 ~/v5env/bin/python -m mcenv.tune $s "$@" 2>/dev/null > scenarios/tuning_runs/s${s}_${tag}.json; echo "$(date -u +%T) done s$s $@"; }
run 3 N=100 L=100
run 3 N=100 L=60
run 3 N=200 L=60
run 5 N=300 L=30
run 5 N=100 L=30
run 6 N=30
run 7 N=100 L=300
run 7 N=200 L=200
run 8 N=150
run 8 N=60
run 10 N=80
run 10 N=150
run 9
run 1
run 2
