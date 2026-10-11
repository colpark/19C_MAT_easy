#!/bin/bash
# sync the working tree (code, frozen inputs) to the sweep hosts; data/ only if missing there
cd "$(dirname "$0")/../.."
for h in aid1@130.199.95.15 aid1@192.168.100.11; do
  rsync -a --delete --exclude runs --exclude data --exclude '__pycache__' --exclude '.git' --exclude 'stage2s/tuning_runs/*.json' --exclude 'stage2s/tuning_runs/*.log' --exclude 'stage2s/tuning_runs/*.pid' ./ $h:~/v5sweep/ 2>/dev/null
  ssh -n $h 'test -f ~/v5sweep/data/stage2/2024-08-04-wbm-relaxed-atoms.extxyz.zip && echo wbm-ok || echo wbm-missing' 2>/dev/null | grep wbm
done
