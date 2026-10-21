#!/bin/bash
# V7-F3: the 15 S-llm author sessions, one at a time (R, H, T x 5)
cd ~/Documents/harbor/v7/v7/F/sllm
R=($(cat dev_tokens_R.txt)); HT=($(cat dev_tokens_HT.txt))
for i in 1 2 3 4 5; do j=$(( (i-1)*2 ))
  ~/v5env/bin/python author.py R $i http://192.168.100.11:8778/call ${R[$j]} ${R[$((j+1))]} >> author_runs.log 2>&1
  ~/v5env/bin/python author.py H $i http://192.168.100.11:8780/call ${HT[$j]} ${HT[$((j+1))]} >> author_runs.log 2>&1
  ~/v5env/bin/python author.py T $i http://192.168.100.11:8781/call ${HT[$((j+10))]} ${HT[$((j+11))]} >> author_runs.log 2>&1
done
echo "$(date -u +%FT%TZ) authors done" >> author_runs.log
