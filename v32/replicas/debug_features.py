#!/usr/bin/env python3
"""debug_features.py: per-replica reads vs truth (development aid for Stage 5C). usage: debug_features.py <replica-name-prefix> ..."""
import json, sys, glob, os, numpy as np
sys.path.insert(0, '/home/aid1/Documents/harbor/v32'); import readers as R
from PIL import Image
O = '/home/aid1/Documents/harbor/v32_host/feature_replicas'
for tf in sorted(glob.glob('/home/aid1/Documents/harbor/v32/replicas/feature_truth/*.json')):
    n = os.path.basename(tf)[:-5]
    if not any(n.startswith(a) for a in sys.argv[1:]): continue
    t = json.load(open(tf)); rgb = np.asarray(Image.open(f'{O}/{n}/panel.jpg').convert('RGB'))
    c = R.calibrate(rgb, t['pc']); print(n, 'frame', t['style']['frame'], 'cal', c and {k: (v if k == 'frame' or not isinstance(v, tuple) else ('%.4g %.4g r=%.2f' % (v[1], v[2], v[3]))) for k, v in c.items()})
    try: P = R.Panel(f'{O}/{n}/panel.jpg', t['pc'])
    except Exception as e: print('  ', e); continue
    for ft in t['truth']['features']:
        r = R.read(P, ft); print('   ', ft['type'], ft['series'], ft['args'], 'vis' if ft.get('visible', True) else 'HID', 'truth %.4g' % ft['value'], 'read', r and ('%.4g u=%.3g z=%.2f' % (r[0], r[1], (r[0] - ft['value']) / r[1])))
