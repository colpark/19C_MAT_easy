import json, sys
for p in sys.argv[1:]:
    for l in open(p):
        if not l.startswith('{'): continue
        r = json.loads(l); c = r['cheapest']
        pl = c and [(m['start'], m['n'], m['step'], m['t'], m['optics'][:2]) if m['radiation'] == 'xray' else 'neutron' for m in c['plan']]
        print(p.split('/')[-1], r['world'], 'Dm0', r['D_m0'], 'cheap', c and c['cost'], pl, 'best', r['best']['D'], 'def', r['best_default_range']['D'], 'neu', r['neutron'], r['checks'], r['sec'])
