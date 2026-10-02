#!/bin/bash
# PanelBench v0.22: MinerU 2.7.6 (pipeline backend, GPU) on the harvested OA PDFs, in chunks of CHUNK PDFs.
# usage: run_mineru_v021.sh <papers_hostX.json>   env: VENV (mineru venv), PDFROOT (oa_harvest folder)
# Resumable: a paper is done when mineru_out/<safe>/auto/<safe>_content_list.json exists.
set -u
cd "$(dirname "$0")"
LIST=$1; CHUNK=${CHUNK:-40}; source "$VENV/bin/activate"
mkdir -p mineru_out chunks logs
while true; do
  todo=$(python3 -c "
import json,os,sys
L=json.load(open('$LIST')); n=0
for p in L:
    if not os.path.exists(f\"mineru_out/{p['safe']}/auto/{p['safe']}_content_list.json\") and not os.path.exists(f\"logs/failed_{p['safe']}\"):
        print(p['pdf']); n+=1
        if n>=$CHUNK: break")
  [ -z "$todo" ] && { echo "$(date -Is) all done"; break; }
  d=chunks/$(date +%s); mkdir -p $d
  for f in $todo; do ln -sf "$PDFROOT/$f" "$d/$(basename $f)"; done
  [ -f "$(dirname $0)/../monitor/PAUSE" ] && { echo "$(date -Is) monitor PAUSE, waiting"; while [ -f "$(dirname $0)/../monitor/PAUSE" ]; do sleep 30; done; }
  s=$(date +%s); mineru -p $d -o mineru_out -b pipeline >> logs/mineru_$(basename $d).log 2>&1; rc=$?
  n=$(ls $d | wc -l); ok=0
  for f in $d/*.pdf; do b=$(basename $f .pdf); if [ -f "mineru_out/$b/auto/${b}_content_list.json" ]; then ok=$((ok+1)); else touch "logs/failed_$b"; fi; done
  echo "$(date -Is) chunk $(basename $d): $n pdfs, $ok ok, exit $rc, $(( $(date +%s)-s ))s"
  rm -rf $d
done
