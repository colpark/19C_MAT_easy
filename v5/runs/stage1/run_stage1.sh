#!/bin/bash
# V5-3 stage 1 Claude episodes, host A, 3 concurrent, resumable (episodes.jsonl per batch)
cd /home/aid1/Documents/harbor/v5/v5
for p in p1_sonnet_ai p2_sonnet_bp p3_haiku_a p4_opus_a; do
  nice -n 10 ~/v5env/bin/python -m mcenv.run_claude runs/stage1/$p.jsonl runs/stage1/$p --conc 3
done
echo "STAGE1 DONE $(date -u +%FT%TZ)"
