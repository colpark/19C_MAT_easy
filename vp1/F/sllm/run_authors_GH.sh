#!/bin/bash
# VP1-2: the 15 Haiku author sessions, one at a time, in round G's order (R, H, T for i = 1..5); author_vp1.py waits for a slot.
# Development episodes on node A2:8825 with the session's fresh k = 99 tokens (dev_tokens_GH.json). A session that stops on a usage limit
# or a login error exits 3; this script then stops (no further session starts) and is resumed by hand after the reset or a login.
cd ~/Documents/harbor/vp1/vp1/F/sllm
echo $$ > logs_GH.runner.pid
for i in 1 2 3 4 5; do for F in R H T; do
  [ -f programs_GH/$F$i.py ] && continue
  read T1 T2 < <(~/v5env/bin/python -c "import json; print(*json.load(open('dev_tokens_GH.json'))['$F$i'])")
  ~/v5env/bin/python author_vp1.py $F $i http://192.168.100.11:8825/call $T1 $T2 >> author_runs_GH.log 2>&1
  rc=$?; [ $rc -eq 3 ] && { echo "$(date -u +%FT%TZ) stopped at $F$i (limit or login)" >> author_runs_GH.log; exit 3; }
done; done
echo "$(date -u +%FT%TZ) authors done" >> author_runs_GH.log
