#!/usr/bin/env python3
"""validate_stv.py (S4b, rule I7): fresh synthetic seeds 3000-3009 (dev seeds 1000-1007; seeds 2000-2009 validated S4b, which failed the domain-mean gate, validate_stv_S4b_failed.json). Gates frozen with the reader:
  segmentation  >= 90 % of truth domains (>= MIN_AREA) matched at IoU >= 0.8, in >= 9 of 10 maps;
  domain mean   >= 90 % of domains (>= DOM_MIN) within +-10 % of the clean-field domain mean, in >= 9 of 10 maps (on the reader's
                own segmentation, matched to truth by best overlap);
  localization  reported only (deferred).
Output validate_stv.json."""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import stv_reader as R, synth_stv as S
from multiprocessing import Pool
def one(seed):
    rng = np.random.default_rng(seed); lab, dom, col, ang = S.grains(rng); img = S.ipf_map(rng, dom, col); pred = R.segment_ipf(img)
    seg, nseg = R.match(dom, pred, R.MIN_AREA, 0.8)
    m = rng.uniform(0.006, 0.016); f, band = S.exx_field(rng, dom, ang, m); c = S.exx_field.clean
    pm, pn = R.domain_mean(f, pred); tm, tn = R.domain_mean(c, dom)
    ok = []
    for d in np.where(pn >= R.DOM_MIN)[0]:
        t = np.bincount(dom[pred == d]).argmax(); ok.append(abs(pm[d] - tm[t]) <= 0.10 * abs(tm[t]))
    L, n = R.localization(f, dom); T, _ = R.localization(c, dom); big = n >= R.DOM_MIN
    return {'seed': seed, 'seg_matched': seg, 'n_domains': nseg, 'mean_within10': float(np.mean(ok)), 'n_mean': len(ok), 'loc_within': float(np.mean(np.abs(L[big] - T[big]) <= 0.3 * T[big] + 0.01))}
if __name__ == '__main__':
    with Pool(10) as P: rows = P.map(one, range(int(os.environ.get('STV_SEED0', '3000')), int(os.environ.get('STV_SEED0', '3000')) + 10))
    res = {'rows': rows, 'seg_maps_pass': sum(r['seg_matched'] >= 0.9 for r in rows), 'mean_maps_pass': sum(r['mean_within10'] >= 0.9 for r in rows)}
    res['gates'] = {'segmentation': res['seg_maps_pass'] >= 9, 'domain_mean': res['mean_maps_pass'] >= 9, 'localization': 'deferred'}
    json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'validate_stv.json'), 'w'), indent=1); print(json.dumps({k: v for k, v in res.items() if k != 'rows'}))
    for r in rows: print(r)
