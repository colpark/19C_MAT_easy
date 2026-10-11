#!/bin/bash
# usage (on a sweep host, in ~/v5sweep): stage2s/tuning_runs/sweep.sh NAME SCENS [TUNE_JSON] [BUDGET_JSON] [WIDTHS_JSON] [extra args]
# runs mcenv.tune2s detached; PID in stage2s/tuning_runs/NAME.pid, output NAME.json, log NAME.log
cd ~/v5sweep
N=$1; S=$2; T=${3:-}; B=${4:-}; W=${5:-}; shift 5 2>/dev/null
V5_2S_TUNE="$T" V5_2S_BUDGET="$B" V5_2S_WIDTHS="$W" OPENBLAS_NUM_THREADS=1 setsid nohup ~/v5env/bin/python -m mcenv.tune2s stage2s/tuning_runs/$N.json $S "$@" > stage2s/tuning_runs/$N.log 2>&1 < /dev/null &
echo $! > stage2s/tuning_runs/$N.pid
