#!/usr/bin/env python3
"""validate_register.py (v4 Track B, rule I7): synthetic grain images (random blobs: thick grain + inclusions) imaged twice at different
pixel sizes (40 nm reference, 9.3 nm moving), the moving copy rotated by a known angle (-180..180) and shifted (up to 15 % of the field),
with independent noise and a different contrast mapping (power law), as between STXM OD and EDS counts. Gates (frozen with register.py):
angle error <= 1.5 deg and residual misplacement (image-space, best integer offset between warped moving and truth) <= 1 px on >= 90 % of 20 trials; accept flag true on >= 90 %; no accepted trial with an
angle error > 5 deg. Output validate_register.json."""
import json, os, sys
import numpy as np
from scipy import ndimage as ndi
from skimage.transform import rotate, rescale
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import register as G
rng = np.random.default_rng(5); rows = []
for t in range(20):
    N = 300; g0 = ndi.gaussian_filter(rng.normal(size=(N, N)), 25); base = g0 > np.percentile(g0, 70); base = ndi.binary_opening(base, iterations=5)   # ~30 % fill (generator fix: fixed threshold left empty images)
    incl = ndi.gaussian_filter(rng.normal(size=(N, N)), 6) > 0.6
    truth = base * 1.0 + incl * base * 0.8 + ndi.gaussian_filter(rng.normal(size=(N, N)), 3) * 0.05
    ang = float(rng.uniform(-180, 180)); sh = rng.uniform(-0.15, 0.15, 2) * 70
    ref = rescale(truth, 9.3 / 40.0, anti_aliasing=True) + rng.normal(0, 0.05, (70, 70))   # 70 px at 40 nm ~ 2.8 um
    mov = rotate(truth, -ang, preserve_range=True); mov = ndi.shift(mov, -sh * 40 / 9.3, order=1)
    mov = np.clip(mov, 0, None) ** 1.5 * 100 + rng.normal(0, 5, mov.shape)
    r = G.register(ref, 40.0, mov, 9.3)
    # the synthetic shift was applied after the rotation: the shift that maps mov onto ref (rotate by +ang, then shift) is the shift vector
    # expressed in the rotated frame (row, col with rows downward): R(+ang) applied to (-sh_moving) is not needed; compare against both
    # conventions' image-space check instead: residual = NCC-optimal placement error measured by warping the truth
    import register as _G
    warped = _G.apply(mov, 9.3, 40.0, ref.shape, r); tr = rescale(truth, 9.3 / 40.0, anti_aliasing=True)
    best = min(((np.mean((np.roll(np.roll(_G.prep(tr), dy, 0), dx, 1) - _G.prep(warped)) ** 2), dy, dx) for dy in range(-4, 5) for dx in range(-4, 5)))
    da = min(abs(r['angle'] - ang), 360 - abs(r['angle'] - ang)); ds = float(np.hypot(best[1], best[2]))
    rows_fill = float(base.mean())
    rows.append({'true_angle': ang, 'angle': r['angle'], 'angle_err': da, 'shift_err_px': ds, 'ncc': r['ncc'], 'margin': r['margin'], 'accept': r['accept'], 'grain_fill': rows_fill})
ok = [r['angle_err'] <= 1.5 and r['shift_err_px'] <= 1.0 for r in rows]
res = {'rows': rows, 'within': float(np.mean(ok)), 'accept_rate': float(np.mean([r['accept'] for r in rows])),
       'gates': {'accuracy': float(np.mean(ok)) >= 0.9, 'accept': float(np.mean([r['accept'] for r in rows])) >= 0.9,
                 'no_false_accept': not any(r['accept'] and r['angle_err'] > 5 for r in rows)}}
json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'validate_register.json'), 'w'), indent=1)
print(res['gates'], res['within'], res['accept_rate']); [print({k: round(v, 2) if isinstance(v, float) else v for k, v in r.items()}) for r in rows[:6]]
