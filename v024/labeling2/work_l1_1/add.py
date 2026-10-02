import json,sys,os
p='/home/aid1/Documents/harbor/v024/labeling2/labels_l1_1.json'
d=json.load(open(p)) if os.path.exists(p) else {}
for e in json.loads(sys.argv[1]):
    d[e[0]]={"label":e[1],"note":e[2],"panel_seen":e[3]}
json.dump(d,open(p,'w'),indent=1);print(len(d))
