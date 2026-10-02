import json,sys,os
p='/home/aid1/Documents/harbor/v024/labeling3/labels_l1_2.json'
d=json.load(open(p)) if os.path.exists(p) else {}
for line in sys.stdin:
    line=line.strip()
    if not line: continue
    i,l,n,ps=line.split('|')
    d[i]={"label":l,"note":n,"panel_seen":ps.split(',')}
json.dump(d,open(p,'w'),indent=1,ensure_ascii=False); print(len(d))
