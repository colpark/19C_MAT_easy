"""run_claude with a longer per-episode limit (planner arms, V6-E9): PLAN OUTDIR CONC TIMEOUT"""
import json, sys, os
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, '.')
from mcenv import run_claude as R
plan, out, conc, to = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
R.setup_root(); os.makedirs(out, exist_ok=True)
donep = os.path.join(out, 'episodes.jsonl')
done = {json.loads(l)['token'] for l in open(donep)} if os.path.exists(donep) else set()
eps = [json.loads(l) for l in open(plan) if l.strip() and json.loads(l)['token'] not in done]
print(len(eps), 'to run', flush=True)
with ThreadPoolExecutor(conc) as ex:
    for rec in ex.map(lambda e: R.run_one(e, out, timeout=to), eps):
        open(donep, 'a').write(json.dumps(rec) + '\n'); print(rec['token'][:8], rec['agent'], rec.get('answered'), rec['void'], rec.get('sec'), flush=True)
