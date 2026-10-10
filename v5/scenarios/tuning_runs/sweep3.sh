#!/bin/bash
# V5-1 tuning sweep 3: scenario 7 narrow window; scenario 9 lower count rate (logged in TUNING.md)
cd ~/v5work
run(){ s=$1; shift; tag=$(echo "$@" | tr ' =' '_-'); nice -n 10 ~/v5env/bin/python -m mcenv.tune $s "$@" 2>/dev/null > scenarios/tuning_runs/s${s}_${tag}.json; echo "$(date -u +%T) done s$s $@"; }
for N in 4 5; do for bg in 0.5 1 2; do run 7 N=$N L=1000 bg=$bg; done; done
run 9 N=600
run 9 N=400
