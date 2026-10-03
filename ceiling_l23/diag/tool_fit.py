"""tool_fit.py: how well do the tools fit real paper panels? No keys used. For every stored crop (v0.23 + v0.24 images arm), the cached
default output of each tool, judged against the panel type assigned by the classification agents (micrograph / spectrum / trace / generated)."""
import json, glob, collections, urllib.request
H='/home/aid1/Documents/harbor'
idx=json.load(open(f'{H}/mcp/crop_index.json'))
T={}
for ver,pat in (('v023',f'{H}/v022/paneltypes/types_*.json'),('v024',f'{H}/v024/paneltypes/types_*.json')):
    for f in glob.glob(pat):
        for k,v in json.load(open(f)).items(): T[f'{ver}:{k}']=v['type']
def ptype(h):
    for u in idx[h]['uses']:
        t=T.get(f"{u['paper']}:{u['panel']}")
        if t: return t
    return None
def hub(tool,h):
    r=urllib.request.Request('http://192.168.100.11:8099/call',json.dumps({'tool':tool,'image_ref':h,'args':{},'seed':0}).encode(),{'Content-Type':'application/json'})
    return json.loads(urllib.request.urlopen(r,timeout=600).read())
MAP={'SEM micrograph':'micrograph','TEM micrograph':'micrograph','optical micrograph':'micrograph','AFM/STM image':'micrograph','EBSD map':'micrograph',
     'element map':'micrograph','photograph':'micrograph','electron diffraction':'micrograph','XRD pattern':'spectrum','spectrum':'spectrum',
     'xy curve':'trace/generated','schematic':'generated','simulation render':'generated'}
rows=[]
for h in idx:
    t=ptype(h)
    if not t: continue
    o={tool:hub(tool,h) for tool in ('classify_modality','read_scale_bar','axis_calibrate','digitize_curve','chart_to_table','particle_stats','fft_dspacing','read_text')}
    top=(o['classify_modality'].get('values') or {}).get('top3') or [{}]
    pred=MAP.get(top[0].get('label'),'?')
    ok_mod = pred==t or (pred=='trace/generated' and t in ('trace','generated'))
    ac=o['axis_calibrate'].get('values') or {}
    dig=(o['digitize_curve'].get('values') or {}).get('series') or []
    sb=o['read_scale_bar'].get('values') or {}
    ct=json.dumps(o['chart_to_table'].get('values') or {})
    toks=(o['read_text'].get('values') or {}).get('tokens') or []
    ps=o['particle_stats'].get('values') or {}
    fft=(o['fft_dspacing'].get('values') or {}).get('peaks') or []
    rows.append(dict(type=t,mod_ok=ok_mod,mod_pred=pred,scale=bool(sb.get('px_per_um')),x_cal=bool(ac.get('x')),y_cal=bool(ac.get('y')),
        y_log=(ac.get('y') or {}).get('scale')=='log', dig_series=len(dig), dig_cal=any('x' in s for s in dig),
        ct_garbled=ct.count('0.000')>3 or 'TITLE' in ct and len(ct)<120, ocr_tokens=len(toks),
        ps_count=ps.get('count'), fft_nm=any('d_nm' in p for p in fft), fft_peaks=len(fft)))
json.dump(rows,open('tool_fit_rows.json','w'))
out=['| panel type | n | modality probe agrees | scale bar read | x and y axes calibrated | digitized series in data units | chart_to_table garbled | segmentation ran (any count) | FFT d-spacing in nm | median OCR tokens |','|---|---|---|---|---|---|---|---|---|---|']
for t in ('micrograph','spectrum','trace','generated'):
    X=[r for r in rows if r['type']==t]; n=len(X); p=lambda k: f"{sum(bool(r[k]) for r in X)} ({100*sum(bool(r[k]) for r in X)//n}%)"
    both=sum(r['x_cal'] and r['y_cal'] for r in X)
    out.append(f"| {t} | {n} | {p('mod_ok')} | {p('scale')} | {both} ({100*both//n}%) | {p('dig_cal')} | {p('ct_garbled')} | {p('ps_count')} | {p('fft_nm')} | {sorted(r['ocr_tokens'] for r in X)[n//2]} |")
print('\n'.join(out)); open('tool_fit.md','w').write('\n'.join(out)+'\n')
print(collections.Counter((r['type'],r['mod_pred']) for r in rows).most_common(16))
