#!/usr/bin/env python3
"""measure_crfeni.py (v4 Track D, M2): run grainsize.py (D3) on every CrFeNi TIFF. Pixel size from the FEI tag (PixelWidth), databar cropped
(ResolutionY). Binning b in {1, 2, 4}: the smallest that brings the measured noise into the validated range (<= 0.12); images whose
intercept falls outside the validated 25-200 px are flagged. The 1573 K condition has only a stitched JPG with a scale bar: measured for
the record, excluded from keys until the scale bar passes a pixel check plus a blind read (skill M2). Held-out check: the authors'
intercepts (file names, A level) are compared by rank and ratio only. Output trackD/grains_crfeni.json."""
import glob, json, os, re, sys
import numpy as np
from PIL import Image
from scipy import stats
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import grainsize as G
R = '/home/aid1/Documents/harbor/v4_host/trackD/crfeni'
def binned(a, b):
    if b == 1: return a
    h, w = a.shape[0] // b * b, a.shape[1] // b * b; return a[:h, :w].reshape(h // b, b, w // b, b).mean((1, 3))
def one(p):
    im = Image.open(p); t = im.tag_v2[34682]; ry = int(re.search(r'ResolutionY=(\d+)', t)[1]); pw = float(re.search(r'PixelWidth=([\d.e-]+)', t)[1]) * 1e6
    a = np.array(im).astype(float)[:ry]
    for b in (1, 2, 4):
        r = G.measure(binned(a, b))
        if r['noise'] <= 0.12: break
    r.update({'file': os.path.basename(p), 'bin': b, 'um_per_px': pw * b, 'I_um': r['I_px'] * pw * b, 'II_um': r['II_px'] * pw * b,
              'in_range': bool(25 <= r['I_px'] <= 200 and 25 <= r['II_px'] <= 200 and r['noise'] <= 0.12)}); return r
if __name__ == '__main__':
    from multiprocessing import Pool
    files = sorted(glob.glob(f'{R}/CrFeNi_*K_*min/*.tif'))
    with Pool(8) as P: rows = P.map(one, files)
    out = {'images': rows, 'conditions': {}}
    for r in rows: r['cond'] = re.match(r'CrFeNi_(.+?)_\d+\.tif', r['file'])[1]
    for c in sorted({r['cond'] for r in rows}):
        rr = [r for r in rows if r['cond'] == c]; I = np.array([r['I_um'] for r in rr]); II = np.array([r['II_um'] for r in rr])
        fs = glob.glob(f'{R}/CrFeNi_{c}/*'); cA = sorted({int(re.search(r'c=(\d+)', f)[1]) for f in fs if 'c=' in f}); dA = sorted({int(re.search(r'd=(\d+)', f)[1]) for f in fs if 'd=' in f})
        out['conditions'][c] = {'n': len(rr), 'I_um': float(I.mean()), 'I_se': float(I.std(ddof=1) / np.sqrt(len(I))) if len(I) > 1 else None, 'II_um': float(II.mean()),
                                'II_se': float(II.std(ddof=1) / np.sqrt(len(II))) if len(II) > 1 else None, 'all_in_range': all(r['in_range'] for r in rr), 'authors_c (A)': cA, 'authors_d (A)': dA}
    C = out['conditions']; ks = [c for c in C if C[c]['authors_c (A)']]
    for m in ('I_um', 'II_um'):
        x = [C[c][m] for c in ks]; y = [C[c]['authors_c (A)'][0] for c in ks]; rat = np.array(x) / np.array(y)
        out[f'heldout_{m}'] = {'spearman_vs_c': float(stats.spearmanr(x, y)[0]), 'ratio_to_c_mean': float(rat.mean()), 'ratio_cv': float(rat.std() / rat.mean())}
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'grains_crfeni.json'), 'w'), indent=1)
    for c, v in C.items(): print(c, v['n'], round(v['I_um'], 1), round(v['I_se'] or 0, 1), round(v['II_um'], 1), round(v['II_se'] or 0, 1), v['all_in_range'], v['authors_c (A)'], v['authors_d (A)'])
    print({k: v for k, v in out.items() if k.startswith('heldout')})
    print('bins', sorted({(r['cond'], r['bin']) for r in rows}), 'out_of_range', [r['file'] for r in rows if not r['in_range']])
