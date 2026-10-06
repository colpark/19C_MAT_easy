#!/usr/bin/env python3
"""synth_validate.py (v4 Track C, rule I7): validate measure.method_s and method_i on synthetic SEM-like micrographs with known particle
sizes before any real micrograph is measured for keys.
Synthetic image: 484 x 645, matrix = smooth noise + lamellar texture (martensite-like) + shot noise; particles = bright ellipses (aspect
1-1.6, random orientation) with lognormal diameters (median d0, sigma 0.35) at area fraction 6-12 %, edge brightening, Gaussian blur 0.8 px.
Scales: 0.0388 um/px (4910X) and 0.0971 um/px (1964X). Truth: number-mean ECD of particles >= DMIN_PX (the same cut as the methods).
Gates (frozen): per image |S - truth| / truth <= 0.20 on >= 90 % of images; I agrees with the size-weighted truth sum(D^2)/sum(D) within 0.30 on >= 90 %; ordering of two
conditions with true mean ratio >= 1.3 recovered by both methods in >= 95 % of pairs. Output: synth_validation.json."""
import json, sys, os
import numpy as np
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import measure as M

def synth(rng, d0_um, um_px, H=484, W=645):
    yy, xx = np.mgrid[0:H, 0:W]
    a = 70 + 15 * ndi.gaussian_filter(rng.normal(size=(H, W)), 30) * 8
    th = rng.uniform(0, np.pi); a += 12 * np.sin((xx * np.cos(th) + yy * np.sin(th)) / rng.uniform(2.5, 5)) * (ndi.gaussian_filter(rng.normal(size=(H, W)), 20) > 0)
    mask = np.zeros((H, W), bool); diam = []
    target = rng.uniform(0.06, 0.12) * H * W; area = 0; tries = 0
    while area < target and tries < 20000:
        tries += 1
        d = d0_um * np.exp(rng.normal(0, 0.35)) / um_px; asp = rng.uniform(1, 1.6); ang = rng.uniform(0, np.pi)
        ra, rb = d / 2 * np.sqrt(asp), d / 2 / np.sqrt(asp); cy, cx = rng.uniform(0, H), rng.uniform(0, W)
        R = int(ra) + 3; y0, y1, x0, x1 = int(max(cy - R, 0)), int(min(cy + R, H)), int(max(cx - R, 0)), int(min(cx + R, W))
        if y1 <= y0 or x1 <= x0: continue
        Y, X = np.mgrid[y0:y1, x0:x1]; u = (X - cx) * np.cos(ang) + (Y - cy) * np.sin(ang); v = -(X - cx) * np.sin(ang) + (Y - cy) * np.cos(ang)
        e = (u / ra) ** 2 + (v / rb) ** 2 <= 1
        if (mask[y0:y1, x0:x1] & ndi.binary_dilation(e, iterations=2)).any(): continue
        mask[y0:y1, x0:x1] |= e; area += e.sum()
        touches = y0 == 0 or x0 == 0 or y1 == H or x1 == W
        if not touches and 2 * np.sqrt(e.sum() / np.pi) >= M.DMIN_PX: diam.append(2 * np.sqrt(e.sum() / np.pi))
    diam = np.array(diam)
    edge = mask & ~ndi.binary_erosion(mask, iterations=1)
    img = a + 110 * mask + 40 * edge
    img = ndi.gaussian_filter(img, 0.8) + rng.normal(0, 8, (H, W))
    return np.clip(img, 0, 255).astype(np.uint8), float(np.mean(diam) * um_px), float((diam ** 2).sum() / diam.sum() * um_px)

if __name__ == '__main__':
    rng = np.random.default_rng(20261006); rows = []
    for um_px in (0.0388, 0.0971):
        for d0 in (0.15, 0.25, 0.4, 0.6, 0.9, 1.3):
            if d0 / um_px < 3 or d0 / um_px > 40: continue
            for k in range(6):
                img, truth, truth_w = synth(rng, d0, um_px); s = M.method_s(img, um_px); i = M.method_i(img, um_px)
                rows.append({'um_px': um_px, 'd0': d0, 'truth': truth, 'truth_w': truth_w, 'S': s['mean_um'], 'I': i['d_um']})
    okS = [abs(r['S'] - r['truth']) / r['truth'] <= 0.20 for r in rows if r['S']]; okI = [abs(r['I'] - r['truth_w']) / r['truth_w'] <= 0.30 for r in rows if r['I']]
    pairs = [(a, b) for a in rows for b in rows if a['um_px'] == b['um_px'] and b['truth'] / a['truth'] >= 1.3]
    ordS = np.mean([b['S'] > a['S'] for a, b in pairs]); ordI = np.mean([b['I'] > a['I'] for a, b in pairs])
    res = {'n_images': len(rows), 'S_within_20pct': float(np.mean(okS)), 'I_within_30pct': float(np.mean(okI)), 'order_S': float(ordS), 'order_I': float(ordI),
           'bias_S': float(np.median([(r['S'] - r['truth']) / r['truth'] for r in rows])), 'bias_I': float(np.median([(r['I'] - r['truth_w']) / r['truth_w'] for r in rows])),
           'gates': {'S': bool(np.mean(okS) >= 0.9), 'I': bool(np.mean(okI) >= 0.9), 'order': bool(ordS >= 0.95 and ordI >= 0.95)}, 'rows': rows}
    json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'synth_validation.json'), 'w'), indent=1)
    print({k: v for k, v in res.items() if k != 'rows'})
