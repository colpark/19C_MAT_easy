#!/bin/bash
# VP1-2 Qwen online fill, on host B from ~/vp1qwen: v7's frozen runner run_qwen7.py (mcenv.run_qwen with V6-X20's tools/list fix),
# unchanged, against the local vLLM server (served name Qwen3-8B) and node A2:8827 through host A's reverse tunnel (127.0.0.1:18827).
# The tunnel's tables must equal TABLES_FROZEN.json first, else nothing runs (exit 4).
#   bash ops/run_qwen_fill.sh PLAN.jsonl OUTDIR CONC
cd ~/vp1qwen
PLAN=$1; OUT=$2; CONC=${3:-4}
~/v5env/bin/python - <<'EOF' || { echo "table check FAILED; nothing runs"; exit 4; }
import json, urllib.request
fz = {k: v for k, v in json.load(open('TABLES_FROZEN.json')).items() if k not in ('pid', 'state', 'checks')}
r = json.loads(urllib.request.urlopen('http://127.0.0.1:18827/tables', timeout=60).read())
bad = [k for k in fz if r.get(k) != fz[k]] + [k for k, v in r['checks'].items() if not v]
print('tunnel 18827 -> pid', r['pid'], 'tables', 'equal' if not bad else bad); raise SystemExit(1 if bad else 0)
EOF
mkdir -p $OUT; echo $$ > $OUT/runner.pid
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 ~/v5env/bin/python run_qwen7.py $PLAN $OUT --conc $CONC --vllm http://127.0.0.1:8000/v1 --env http://127.0.0.1:18827/call --model Qwen3-8B
