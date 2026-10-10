import json, sys, glob, os
def p(pl): return [ (q.get('radiation','x')[0], q.get('start'), round(q['start']+q['step']*(q['n']-1),2) if q.get('n') else None, q.get('step'), q.get('t'), (q.get('optics') or '')[:4], 'std' if q.get('si_standard') else '') for q in pl]
for f in sorted(glob.glob(sys.argv[1] if len(sys.argv)>1 else '*.json')):
    try: d=json.load(open(f))
    except Exception: continue
    print('==', os.path.basename(f), {k:v for k,v in d['tune'].items()})
    for w,v in d['worlds'].items():
        ch=v['cheapest']; b=v['best']; bx=v['best_xray']; bd=v['best_default_range']
        print(f"  w{w} Dm0={v['D_m0']:<8} cheapest={ch and (ch['cost'],ch['D'],p(ch['plan']))} best={b['D']}@{b['cost']} bestX={bx and bx['D']} best10-70={bd and bd['D']} neut={v['neutron']}")
