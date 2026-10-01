"""Pilot comparison: MatMech panel store vs MinerU-built panel store, same 30 papers, same v0.21 paragraphs,
frozen item rules (driver_v021 logic, Nano Letters journal-wide). Counts only."""
import json,os,glob,collections,sys
V=os.path.abspath('..'); K=json.load(open(f'{V}/paper_keys.json')); P=json.load(open('pilot_keys.json'))
def store_stats(folder_of):
    c=collections.Counter()
    for k in P:
        m=json.load(open(folder_of(k)+'/panels/match.json'))
        for f in m['figures']:
            c['figures']+=1; c['tier_'+f['tier']]+=1
            for p in f['panels']:
                c['panels']+=1; c['panels_use']+=bool(p.get('use')); c['panels_crop_def']+=bool(p.get('crop') and p.get('definition'))
                if f['tier']=='A': c['tierA_panels']+=1
    return c
def items(nl5):
    os.chdir(f'{V}/work')
    g={'__name__':'pilot'}; exec(open('open.py').read().rsplit("\nif __name__ ==",1)[0], g)
    g['KEYS']={k:k for k in P}; g['NL5']=nl5
    fe=g['eligible']; g['eligible']=lambda paras,key: fe(paras,'Xu17' if K[key]['journal']=='Nano_Letters' else key)
    out={}
    for k in P:
        try: out[k]=g['build'](k)
        except Exception as e: out[k]=e
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    return out
mm=store_stats(lambda k: K[k]['matmech_folder'])
mi=store_stats(lambda k: f"store/{K[k]['journal']}/{k}")
Imm=items(f'{V}/nl5_v021'); Imi=items(os.path.abspath('nl5_mineru'))
lv=lambda I: collections.Counter(it['level'] for v in I.values() if isinstance(v,list) for it in v)
err=lambda I: sum(1 for v in I.values() if not isinstance(v,list))
rows=[('figures','figures'),('tier A figures','tier_A'),('tier B figures','tier_B'),('tier C figures','tier_C'),('accepted panels','panels'),('tier-A panels','tierA_panels'),('panels with crop and caption span','panels_crop_def'),('panels cited in text (use)','panels_use')]
print('| 30 pilot papers | MatMech store | MinerU store |\n|---|---|---|')
for name,k in rows: print(f'| {name} | {mm[k]} | {mi[k]} |')
a,b=lv(Imm),lv(Imi)
print(f"| items L1 / L2 / L3 | {a[1]} / {a[2]} / {a[3]} | {b[1]} / {b[2]} / {b[3]} |")
print(f"| items total | {sum(a.values())} | {sum(b.values())} |")
print(f"| papers with >= 1 item | {sum(1 for v in Imm.values() if isinstance(v,list) and v)} | {sum(1 for v in Imi.values() if isinstance(v,list) and v)} |")
print(f"| item-rule errors | {err(Imm)} | {err(Imi)} |")
sig=lambda it:(it['level'],it.get('question'),it.get('key'))
same=sum(len({sig(i) for i in Imm[k]}&{sig(i) for i in Imi[k]}) for k in P if isinstance(Imm[k],list) and isinstance(Imi[k],list))
print(f"| items identical in both (level, question, key) | {same} | {same} |")
print('\nper paper (journal, version, MatMech items -> MinerU items):')
import csv
ver={r['doi']:r['version'] for r in csv.DictReader(open('/home/aid1/Documents/oa_harvest/oa_manifest.csv'))}
for k in P:
    n=lambda I: len(I[k]) if isinstance(I[k],list) else 'ERR'
    print(f"  {k} {K[k]['journal'][:22]:22s} {ver.get(K[k]['doi'],'?')[:9]:9s} {n(Imm)} -> {n(Imi)}")
