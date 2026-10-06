#!/usr/bin/env python3
"""measure_all.py (v4 Track C, M2): both frozen methods (measure.py, freeze C1) on every micrograph whose scale check agrees and whose data
bar crops to the standard 484 rows. Writes v4/uhcs/cells_micrograph.jsonl: micrograph id, sample, anneal T/time/cooling, magnification,
detector, um/px, method S (n, mean ECD, median, area fraction), method I (chords, d_I). Level: M-derived by our procedure (definition 7
analogue); the primary_microconstituent label is carried as an I field (never a key)."""
import json, os, sqlite3, sys, warnings
import numpy as np
from PIL import Image
warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import measure as M
H = '/home/aid1/Documents/harbor/v4_host/uhcsdb'; SC = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scale_check.json')))
c = sqlite3.connect(f'{H}/nist940/microstructures.sqlite')
q = ('select m.micrograph_id, m.path, m.micron_bar, m.micron_bar_px, m.magnification, m.detector, m.primary_microconstituent, s.sample_id, s.label, '
     's.anneal_time, s.anneal_time_unit, s.anneal_temperature, s.cool_method from micrograph m left join sample s on m.sample_key = s.sample_id')
out = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cells_micrograph.jsonl'), 'w'); n = skipped = 0
for mid, path, mb, mbpx, mag, det, pmc, sid, lab, at, atu, aT, cool in c.execute(q):
    sc = SC.get(str(mid)) or {}
    f = f'{H}/data/micrographs/{sc.get("path") or path}'
    if not sc.get('agree') or not os.path.exists(f): skipped += 1; continue
    a = np.asarray(Image.open(f).convert('L')); im = M.crop_image(a)
    if im.shape[0] != 484: skipped += 1; continue
    um = mb / mbpx; s = M.method_s(im, um); i = M.method_i(im, um)
    t_h = None if at is None else at * {'M': 1 / 60, 'H': 1.0}.get(atu, float('nan'))
    out.write(json.dumps({'micrograph': mid, 'path': path, 'sample': sid, 'label': lab, 'T_C': aT, 't_h': t_h, 'cool': cool, 'mag': (mag or '').upper(), 'detector': det,
                          'um_per_px': um, 'S': s, 'I': i, 'microconstituent_I': pmc}) + '\n'); n += 1
print('measured', n, 'skipped', skipped)
