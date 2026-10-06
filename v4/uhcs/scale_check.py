#!/usr/bin/env python3
"""scale_check.py (v4 Track C, skill M2): verify the database scale (micron_bar / micron_bar_px) against the bar drawn in each micrograph's
data bar. Rule: in the bottom data bar (rows below the last image row, found as the first row from the bottom band whose mean brightness
changes abruptly), the longest horizontal run of bright pixels (> 180) is the bar; agreement when |run - micron_bar_px| <= 3 px.
Output: v4/uhcs/scale_check.json (per micrograph: detected px, db px, agree) and a summary line."""
import json, sqlite3, os, sys
import numpy as np
from PIL import Image
H = '/home/aid1/Documents/harbor/v4_host/uhcsdb'
c = sqlite3.connect(f'{H}/nist940/microstructures.sqlite')
rows = c.execute('select micrograph_id, path, micron_bar, micron_bar_units, micron_bar_px, magnification, detector, sample_key from micrograph').fetchall()
def longest_run(mask):
    best = (0, -1, -1)
    for r in range(mask.shape[0]):
        row = mask[r]; i = 0
        while i < len(row):
            if row[i]:
                j = i
                while j + 1 < len(row) and row[j + 1]: j += 1
                if j - i + 1 > best[0]: best = (j - i + 1, r, i)
                i = j + 1
            else: i += 1
    return best
out = {}; n = agree = 0
for mid, path, mb, mbu, mbpx, mag, det, sk in rows:
    f = f'{H}/data/micrographs/{path}'
    if not os.path.exists(f):
        alt = os.path.splitext(f)[0] + '.png'; f = alt if os.path.exists(alt) else None
    if not f: out[mid] = {'missing': True}; continue
    a = np.asarray(Image.open(f).convert('L')).astype(int); h = a.shape[0]
    band = a[int(h * 0.88):]   # data bar region (bottom 12 %)
    L, r, x0 = longest_run(band > 180)
    ok = mbpx is not None and abs(L - mbpx) <= 3
    out[mid] = {'path': os.path.basename(f), 'shape': a.shape, 'detected_px': L, 'db_px': mbpx, 'micron_bar': mb, 'units': mbu, 'agree': bool(ok),
                'um_per_px_db': (mb / mbpx) if mb and mbpx else None, 'sample': sk, 'magnification': mag, 'detector': det}
    n += 1; agree += ok
json.dump(out, open('/home/aid1/Documents/harbor/v4/uhcs/scale_check.json', 'w'), indent=0)
from collections import Counter
print(f'checked {n}, agree {agree} ({agree / n:.1%}); shapes', Counter(str(v.get('shape')) for v in out.values()).most_common(5))
dis = [(k, v['detected_px'], v['db_px'], v['magnification']) for k, v in out.items() if not v.get('missing') and not v['agree']]
print('disagree examples', dis[:15])
