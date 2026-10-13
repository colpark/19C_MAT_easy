"""V6-3 gold trace: the executor on both twins of the exemplar (scenario 101, worlds 1011 and 1012) on the v6 server (node A2:8776,
arm v6-gold, k = 1), graph_R.json with the kit's constants. Keys from the grader side (the scenario's DFT truth, D-gated, given here).
  python v6/graphexec/run_gold.py OUTDIR"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
import graphexec as G
import adapters_mcenv as AD

ROOT6 = os.path.join(HERE, '..')
KEYS = {1011: 'SUPPORTED', 1012: 'REFUTED'}


def env(batch='v6-3-gold'):
    return AD.Env('http://192.168.100.11:8776/call', 'aid1@192.168.100.11', '~/v6srv', '~/v6_state', 'V5_STAGE=6', batch=batch)


def task(e, world, k=1):
    return AD.make_task(e, world, 'v6-gold', k, 'R', key=KEYS.get(world if world in KEYS else (1011 if world in (1013, 1014, 1015) else 1012)))


if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True); e = env()
    g = G.Graph.load(os.path.join(ROOT6, 'spec', 'graph_R.json'))
    import jsonschema
    schema = json.load(open(os.path.join(ROOT6, 'spec', 'trace_schema.json')))
    for w, name in ((1011, 'gold_A.json'), (1012, 'gold_B.json')):
        log = G.Executor(g, AD.ADAPTERS, source='gold').run(task(e, w))
        jsonschema.validate(log, schema)
        json.dump(log, open(os.path.join(out, name), 'w'), indent=1)
        print(name, log['verdict'], 'key', log['key'], 'cost', log['cost_min'], [(s['node'], s['status'], s.get('accepted')) for s in log['steps']], flush=True)
    json.dump(e.tokens, open(os.path.join(out, 'gold_tokens.json'), 'w'), indent=1)
