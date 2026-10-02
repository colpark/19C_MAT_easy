import json,sys,os
p='/home/aid1/Documents/harbor/v024/labeling3/labels_l1_1.json'
d=json.load(open(p)) if os.path.exists(p) else {}
for line in sys.stdin:
    line=line.strip()
    if not line: continue
    i,l,panels,note=line.split('|',3)
    d[i]={"label":l,"note":note,"panel_seen":panels.split(',')}
json.dump(d,open(p,'w'),indent=1,ensure_ascii=False)
print(len(d))
