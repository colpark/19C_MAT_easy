#!/bin/bash
# V5-1 tuning sweep 2: scenario 7 at low count rates; refined 3, 5, 8 (logged in TUNING.md)
cd ~/v5work
while pgrep -f sweep1.sh > /dev/null; do sleep 20; done
run(){ s=$1; shift; tag=$(echo "$@" | tr ' =' '_-'); nice -n 10 ~/v5env/bin/python -m mcenv.tune $s "$@" 2>/dev/null > scenarios/tuning_runs/s${s}_${tag}.json; echo "$(date -u +%T) done s$s $@"; }
for L in 300 1000; do for bg in 2 20; do for N in 3 6 10; do run 7 N=$N L=$L bg=$bg; done; done; done
run 3 N=50 L=60
run 5 N=30 L=30
run 8 N=100
