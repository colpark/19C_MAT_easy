"""vP.1 program-run plan (node A2): registers one token per program x world x k on the vP.1 state (admin_vp1, so the manipulated arms
are refused where they do not apply) and writes runner plan lines {token, prog, url, arm, model, k, scen, batch}. Worlds are the family's
bench worlds (folds.json). The arm is the family's fm arm (B1 v6-active-fm, H v7h-fm, T v7t-fm) unless --arm is given (VP1-3: fit-once).
Order: one smoke episode per program first (its first world at the first k, in sorted world order), then every other episode in a seeded
shuffle; ports round-robin over the plan order.
  MCENV_STATE=~/vp1_state python ops/make_plan.py --set G --progs R1,R2 --ks 2,3,4 --ports 8820,8821 --tag vp1-1 OUT.jsonl"""
import argparse, json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mcenv import admin_vp1 as AV  # noqa: E402
from mcenv import scenarios as SC  # noqa: E402

VP1 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAM = {'R': 'B1', 'H': 'H', 'T': 'T'}
FM_ARM = {'B1': 'v6-active-fm', 'H': 'v7h-fm', 'T': 'v7t-fm'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--set', required=True); ap.add_argument('--progs', required=True); ap.add_argument('--ks', required=True)
    ap.add_argument('--ports', required=True); ap.add_argument('--tag', required=True); ap.add_argument('--arm', default='')
    ap.add_argument('out')
    a = ap.parse_args()
    folds = json.load(open(os.path.join(VP1, 'folds.json')))['families']
    ks = [int(k) for k in a.ks.split(',')]; ports = a.ports.split(',')
    smoke, rest = [], []
    for prog in a.progs.split(','):
        fam = FAM[prog[0]]; arm = a.arm or FM_ARM[fam]
        model = f'sllm{a.set}-{prog}'
        items = [dict(world=w, arm=arm, k=k, model=model, batch=f'{a.tag}-{model}-{arm}-k{k}', prog=prog) for k in ks for w in folds[fam]['worlds']]
        smoke.append(items[0]); rest += items[1:]
    random.Random(f'vp1-order|{a.tag}|{a.set}|{a.progs}|{a.ks}|{a.arm}').shuffle(rest)
    items = smoke + rest
    if os.path.exists(a.out): raise SystemExit(f'{a.out} exists')
    toks = AV._register([{k: it[k] for k in ('world', 'arm', 'k', 'model', 'batch')} for it in items])
    with open(a.out, 'w') as f:
        for i, (it, t) in enumerate(zip(items, toks)):
            f.write(json.dumps(dict(token=t, prog=it['prog'], url=f'http://192.168.100.11:{ports[i % len(ports)]}/call', arm=it['arm'], model=it['model'],
                                    k=it['k'], scen=SC.WORLD_SCEN[it['world']], batch=it['batch'], smoke=i < len(smoke))) + '\n')
    print(len(items), 'episodes;', len(smoke), 'smoke first')


if __name__ == '__main__':
    main()
