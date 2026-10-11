import sys, json
for l in open(sys.argv[1]):
    if not l.startswith('{'): print(l[:300].rstrip()); continue
    r = json.loads(l); cd = r['c_dec']; cp = r.get('c_pla'); cl = r.get('c_loc')
    print(r['scen'], 'N', r['tune']['N'], 'B', r['budget'], 'c_dec', cd and (cd['cost'], cd.get('D_pl_per_world'), cd.get('D_key_per_world'), [(m['start'], m['n'], m['step'], round(m['t'], 2), m['optics'][:3], m['si_standard']) for m in cd['plan']]),
          '| c_loc', cl and cl['cost'], '| dflt', r['default_survey'], '| locdec', r.get('c_loc_dec') and r['c_loc_dec']['cost'],
          '| c_pla', cp and (cp['cost'], cp['D_key_true']), r['checks'], r['sec'], 's')
