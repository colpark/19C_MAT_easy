#!/bin/bash
# stage 2 replacement round tuning (V5_S2_PICK=S2-B:1,S2-C:1,S2-D:1,S2-E:1), logged in stage2/TUNING2.md
cd ~/v5srv2
export V5_S2_PICK="S2-B:1,S2-C:1,S2-D:1,S2-E:1"
run(){ s=$1; shift; tag=$(echo "$@" | tr ' =' '_-'); nice -n 10 ~/v5env/bin/python -m mcenv.tune $s "$@" 2>/dev/null > validation2r/tune_s${s}_${tag}.json; echo "$(date -u +%T) done s$s $@"; }
run 12 N=10 L=60 bg=5
run 12 N=5 L=60 bg=5
run 12 N=10 L=30 bg=5
run 13 N=600
run 13 N=450
run 15 N=450
run 15 N=500
