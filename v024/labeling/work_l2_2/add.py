import json,sys,os
p='/home/aid1/Documents/harbor/v024/labeling/labels_l2_2.json'
d=json.load(open(p)) if os.path.exists(p) else {}
new=json.loads(sys.stdin.read())
d.update(new)
json.dump(d,open(p,'w'),indent=1)
print(len(d))
