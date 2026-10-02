import json,sys,os
p='/home/aid1/Documents/harbor/v024/labeling/labels_l1_1.json'
d=json.load(open(p)) if os.path.exists(p) else {}
for line in sys.stdin:
    line=line.strip()
    if not line: continue
    i,l,ps,n=line.split('|',3)
    d[i]={"label":l,"note":n,"panel_seen":ps.split(',')}
json.dump(d,open(p,'w'),indent=1,ensure_ascii=False)
print(len(d))
