"""print stage 1b tuning lines: python stage1b/tuning_runs/summ.py LOG [LOG ...]"""
import json, sys
for p in sys.argv[1:]:
    for l in open(p):
        pre = ''
        if not l.startswith('{'):
            if ' {' not in l: continue
            pre, l = l.split(' ', 1)
        try: r = json.loads(l)
        except ValueError: continue
        c = r['cheapest']
        pl = c and [(m['start'], m['n'], m['t'], m['optics'][:2], int(m['si_standard'])) if m['radiation'] == 'xray' else 'neutron' for m in c['plan']]
        print(pre, r['world'], 'Dm0', r['D_m0'], 'cheap', c and c['cost'], pl, 'best', r['best']['D'], 'c2e', r['best_c2e']['D'], 'ndec', r['n_decisive_singles'],
              'obv', r.get('obvious'), r['sec'])
