#!/bin/bash
# usage: sweep.sh TAG SCENS PICK 'tune-json' ['tune-json' ...]   (from the v5 folder; PICK like 42:1 or -)
tag=$1; scens=$2; pick=$3; shift 3; i=0
for tj in "$@"; do
  i=$((i+1)); echo "$tag-$i pick=$pick $tj" >> stage2r/tuning_runs/$tag.index
  V5_S2R_PICK=$([ "$pick" = "-" ] && echo "" || echo "$pick") V5_2R_TUNE="$tj" ~/v5env/bin/python -m mcenv.tune2r stage2r/tuning_runs/$tag-$i.json $scens --procs ${PROCS:-19} > stage2r/tuning_runs/$tag-$i.log 2>&1
done
