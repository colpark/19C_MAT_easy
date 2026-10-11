#!/bin/bash
# usage: sweep.sh TAG SCEN WORLDS 'override-json' ['override-json' ...]   (run from the v5 folder on the sweep host)
tag=$1; scen=$2; worlds=$3; shift 3; i=0
for ov in "$@"; do
  i=$((i+1)); echo "$tag-$i $ov" >> stage1b/tuning_runs/$tag.index
  V5_1B_OVERRIDE="$ov" ~/v5env/bin/python -m mcenv.tune1b stage1b/tuning_runs/$tag-$i.json $scen --worlds $worlds --procs ${PROCS:-19} > stage1b/tuning_runs/$tag-$i.log 2>&1
done
