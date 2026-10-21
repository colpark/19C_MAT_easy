#!/bin/bash
# V7-G2: the 15 corrected-input S-llm author sessions, one at a time (R, H, T x 5); slot gate in author.py (V7-X17)
cd ~/Documents/harbor/v7/v7/F/sllm
export SLLM_ROUND=G
R=($(cat dev_tokens_G_R.txt)); HT=($(cat dev_tokens_G_HT.txt))
for i in 1 2 3 4 5; do j=$(( (i-1)*2 ))
  ~/v5env/bin/python author.py R $i http://192.168.100.11:8778/call ${R[$j]} ${R[$((j+1))]} >> author_runs_G.log 2>&1
  ~/v5env/bin/python author.py H $i http://192.168.100.11:8780/call ${HT[$j]} ${HT[$((j+1))]} >> author_runs_G.log 2>&1
  ~/v5env/bin/python author.py T $i http://192.168.100.11:8781/call ${HT[$((j+10))]} ${HT[$((j+11))]} >> author_runs_G.log 2>&1
done
echo "$(date -u +%FT%TZ) authors done" >> author_runs_G.log
