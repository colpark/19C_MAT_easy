#!/bin/bash
# V5-3 second runner (concurrency raised to 6 total, David 2026-10-11): Haiku then Opus, 3 concurrent, alongside Sonnet blind/passive
cd /home/aid1/Documents/harbor/v5/v5
for p in p3_haiku_a p4_opus_a; do
  nice -n 10 ~/v5env/bin/python -m mcenv.run_claude runs/stage1/$p.jsonl runs/stage1/$p --conc 3
done
echo "STAGE1B DONE $(date -u +%FT%TZ)"
