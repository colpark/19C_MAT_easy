"""V7-X8: API-equivalent cost per batch (the total_cost_usd of each Claude Code result message; the runs use the subscription, so this is
not money spent) and episode counts, from the runner transcripts. Writes v7/USAGE.md.
  python v7/usage7.py"""
import glob, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
BATCHES = [('H', 'Sonnet noprior, fm (k 1-4; gates use k 1)', 'runs/H/v7_4/episodes'), ('H', 'Haiku noprior, fm', 'runs/H/haiku/episodes'),
           ('H', 'Sonnet fm-planner', 'runs/H/planner/episodes'), ('T', 'Sonnet noprior, fm', 'runs/T/v7_4/episodes'),
           ('T', 'Haiku noprior, fm', 'runs/T/haiku/episodes'), ('T', 'Sonnet fm-planner', 'runs/T/planner/episodes'),
           ('H', 'Sonnet fm-hint (V7-F4)', 'runs/F/hint/episodes_H'), ('T', 'Sonnet fm-hint (V7-F4)', 'runs/F/hint/episodes_T'),
           ('B1', 'Sonnet fm-hint (V7-F4)', 'runs/F/hint/episodes_B1'),
           ('T', 'fresh T Sonnet fm + fm-hint, first run on node A2:8784 (voided, V7-E5 and V7-E6; used, not analysed)', 'runs/G/fresh/episodes'),
           ('T', 'fresh T Sonnet fm + fm-hint, rerun on node A2:8781 (V7-G1)', 'runs/G/fresh/episodes_rerun')]
rows = []; tot = 0.0
for fam, name, d in BATCHES:
    p = os.path.join(HERE, d)
    if not os.path.isdir(p): continue
    cost, n, k1 = 0.0, 0, 0
    eps = {json.loads(l)['token'][:12]: json.loads(l) for l in open(os.path.join(p, 'episodes.jsonl'))} if os.path.exists(os.path.join(p, 'episodes.jsonl')) else {}
    for f in glob.glob(os.path.join(p, '*.jsonl')):
        if f.endswith('episodes.jsonl'): continue
        c = None
        for l in open(f, errors='replace'):
            try: m = json.loads(l)
            except ValueError: continue
            if m.get('type') == 'result': c = m.get('total_cost_usd')
        if c is not None: cost += c; n += 1
        e = eps.get(os.path.basename(f)[:12]); k1 += bool(e and e.get('k') == 1)
    rows.append((fam, name, n, k1, round(cost, 2))); tot += cost
for name, pat in (('S-llm authoring sessions, kept (V7-F3; sessions, not episodes)', 'F/sllm/logs/*/session_*.jsonl'),
                  ('S-llm authoring sessions discarded under V7-E3', 'F/sllm/discarded_V7-E3/**/session_*.jsonl'),
                  ('S-llm round G authoring sessions (V7-G2; sessions, not episodes)', 'F/sllm/logs_G/*/session_*.jsonl')):
    cost, n = 0.0, 0
    for f in glob.glob(os.path.join(HERE, pat), recursive=True):
        c = None
        for l in open(f, errors='replace'):
            try: m = json.loads(l)
            except ValueError: continue
            if m.get('type') == 'result': c = m.get('total_cost_usd')
        if c is not None: cost += c; n += 1
    rows.append(('R, H, T', name, n, '-', round(cost, 2))); tot += cost
L = ['# v7 subscription use (API-equivalent, V7-X8)', '',
     'Claude Code reports `total_cost_usd` per episode. These runs use the subscription, so the figure is an API-equivalent size, not money spent; spend is $0.',
     'Qwen3-8B runs on local vLLM and has no cost. Scripts (S-broad, S-neutron, S-plan, S-llm programs) and S-replay use no LLM.', '',
     '| family | batch | episodes with a result | of them at k = 1 | API-equivalent USD |', '|---|---|---|---|---|']
L += [f'| {f} | {n} | {e} | {k} | {c:.2f} |' for f, n, e, k, c in rows]
L += ['', f'**Total so far:** {tot:.2f} USD API-equivalent.']
open(os.path.join(HERE, 'USAGE.md'), 'w').write('\n'.join(L) + '\n'); print('\n'.join(L[-len(rows) - 2:]))
