import json,sys,os
out='/home/aid1/Documents/harbor/v024/labeling/labels_l2_1.json'
d=json.load(open('/home/aid1/Documents/harbor/v024/labeling/l2_1.json'))
pan={x['id']:list(x['crops'].keys()) for x in d}
cur=json.load(open(out)) if os.path.exists(out) else {}
for line in open(sys.argv[1]):
    line=line.strip()
    if not line: continue
    i,l,n=line.split('|',2)
    assert l in('sound','weak','defective'); assert len(n.split())<15,n
    cur[i]={'label':l,'note':n,'panel_seen':pan[i]}
json.dump(cur,open(out,'w'),indent=1); print(len(cur))
