import json,sys,os
p='/home/aid1/Documents/harbor/v024/labeling3/labels_l3_1.json'
d=json.load(open(p)) if os.path.exists(p) else {}
iid,lab,note,ps=sys.argv[1:5]
d[iid]={"label":lab,"note":note,"panel_seen":ps.split(',')}
json.dump(d,open(p,'w'),indent=1)
print(len(d))
