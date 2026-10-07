#!/usr/bin/env python3
"""desk_registration_r90.py (Track S round 3, D0 condition 1): BSE-to-EDX registration residual for refodat90, as frozen in
DESK_refodat_rule.md (D0). No reader, no landmarks of ours.
Authors' global transform: their QGIS georeferencer points (Full-alginment/*.points, enabled points only). We fit an affine source->map
transform per raster (QGIS 'Linear'/'Polynomial 1' family) and report how well it reproduces the residuals the authors list.
  BSE source = the deposited stitched montage files/BSE_High-Res.tif (84.3099 nm/px) as 'Layer-Tile Set (2) (stitched).tif'.
  EDX source = full_phase_map.png, an exact 3x nearest upscale of the index map EDX full_phase_map.tif (702 x 1022, 288.722 nm/px);
  index labels from the authors' notebook (NI-evaluation+EDX-segmentation.ipynb, group_names).
Procedure (D0): EDX pixel centres -> map -> BSE pixel; BSE area-averaged to the EDX pixel by a box filter of 288.722/84.3099 px and
sampled bilinearly; pseudo-BSE = D0 Z-bar per class (by label name); >= 20 windows of 64 x 64 EDX px on a regular grid with >= 2 classes
each >= 5 %; local offset by phase correlation (upsample 20) on zero-mean, unit-variance windows; residual = |offset| in um.
Writes v4_host/trackS/refodat90/desk/registration.json and registration_map.png (residual vectors)."""
import json, os, re
import numpy as np
import tifffile
from PIL import Image
from scipy import ndimage as ndi
from skimage.registration import phase_cross_correlation
Image.MAX_IMAGE_PIXELS = None
H = '/home/aid1/Documents/harbor/v4_host/trackS/refodat90'; X = f'{H}/extracted'; OUT = f'{H}/desk'; os.makedirs(OUT, exist_ok=True)
EDX_NM, BSE_NM = 288.722, 84.3099
ZBAR = {'pores': 0.00, 'AFm/AFt': 10.77, 'alite/belite': 15.06, 'matrix': 13.11, 'CH': 14.30, 'C-A-S-H': 13.05, 'C3A/C4AF': 15.49,
        'Mg-C-A-S-H': 11.99, 'Slag': 13.17, 'quartz': 10.80, 'C-S-H': 13.11}   # D0 table (by label)
NAMES = {0: 'AFm/AFt', 1: 'C-A-S-H', 2: 'C-S-H', 3: 'C3A/C4AF', 4: 'CH', 5: 'Mg-C-A-S-H', 6: 'Slag', 7: 'alite/belite', 8: 'matrix', 9: 'pores', 10: 'quartz'}

def gcps(path):
    rows = []
    for l in open(path, encoding='utf-8'):
        if l.startswith('#') or l.startswith('mapX'): continue
        p = l.strip().split(',')
        if len(p) >= 5 and p[4].strip() == '1': rows.append([float(v) for v in p[:4]] + [float(v) for v in p[5:8]])
    return np.array(rows)

def affine(src, dst):
    A = np.c_[src, np.ones(len(src))]; M, *_ = np.linalg.lstsq(A, dst, rcond=None); return M   # dst = [x y 1] @ M

def main():
    gb = gcps(f'{X}/Full-alginment/Layer-Tile Set (2) (stitched).tif.points'); ge = gcps(f'{X}/Full-alginment/full_phase_map.png.points')
    Mb = affine(gb[:, 2:4], gb[:, 0:2]); Me = affine(ge[:, 2:4], ge[:, 0:2])
    # how well an affine reproduces the authors' listed residuals (source px): forward map, then inverse to source
    def resid(g, M):
        pred = np.c_[g[:, 2:4], np.ones(len(g))] @ M; Minv = affine(g[:, 0:2], g[:, 2:4]); back = np.c_[g[:, 0:2], np.ones(len(g))] @ Minv
        return float(np.sqrt(np.mean(np.sum((back - g[:, 2:4]) ** 2, 1)))), float(np.sqrt(np.mean(g[:, 6] ** 2)))
    rb, rb_auth = resid(gb, Mb); re_, re_auth = resid(ge, Me)
    edx = tifffile.imread(f'{X}/NI-EDX_phase_evaluation/EDX/full_phase_map.tif').astype(int); h, w = edx.shape
    # EDX index pixel (r, c) centre -> png source coords (x = 3c + 1.5, y = -(3r + 1.5)) -> map -> BSE source (x, -y)
    rr, cc = np.mgrid[0:h, 0:w]; src_e = np.c_[(3 * cc + 1.5).ravel(), (-(3 * rr + 1.5)).ravel()]
    mp = np.c_[src_e, np.ones(len(src_e))] @ Me
    Mb_inv = affine(gb[:, 0:2], gb[:, 2:4]); sb = np.c_[mp, np.ones(len(mp))] @ Mb_inv
    bx, by = sb[:, 0].reshape(h, w), (-sb[:, 1]).reshape(h, w)   # BSE column, row (pixels)
    x0, x1 = int(max(bx.min() - 200, 0)), int(bx.max() + 200); y0, y1 = int(max(by.min() - 200, 0)), int(by.max() + 200)
    bse_full = tifffile.memmap(f'{H}/files/BSE_High-Res.tif') if True else None
    crop = np.asarray(bse_full[y0:y1, x0:x1], dtype=np.float32)
    if crop.ndim == 3: crop = crop[..., :3].mean(2)
    k = EDX_NM / BSE_NM; box = ndi.uniform_filter(crop, size=int(round(k)))
    bse_on_edx = ndi.map_coordinates(box, [by - y0, bx - x0], order=1, mode='constant', cval=np.nan)
    zmap = np.vectorize(lambda i: ZBAR[NAMES[i]])(edx).astype(np.float32)
    # windows
    W = 64; res = []
    for r0 in range(0, h - W + 1, W // 2):
        for c0 in range(0, w - W + 1, W // 2):
            e = edx[r0:r0 + W, c0:c0 + W]; b = bse_on_edx[r0:r0 + W, c0:c0 + W]; z = zmap[r0:r0 + W, c0:c0 + W]
            if np.isnan(b).any(): continue
            fr = np.bincount(e.ravel(), minlength=11) / e.size
            if (fr >= 0.05).sum() < 2: continue
            nz = lambda a: (a - a.mean()) / (a.std() + 1e-9)
            sh, err, _ = phase_cross_correlation(nz(z), nz(b), upsample_factor=20, normalization=None)
            cc_ = float(np.corrcoef(nz(z).ravel(), nz(ndi.shift(b, sh, order=1, mode='nearest')).ravel())[0, 1])
            res.append({'r0': r0, 'c0': c0, 'dy_px': float(sh[0]), 'dx_px': float(sh[1]), 'resid_um': float(np.hypot(*sh) * EDX_NM / 1000), 'corr_after': cc_,
                        'corr_before': float(np.corrcoef(nz(z).ravel(), nz(b).ravel())[0, 1])})
    R = np.array([x['resid_um'] for x in res]) if res else np.array([np.nan])
    off = np.array([[x['dy_px'], x['dx_px']] for x in res]) if res else np.zeros((1, 2)); med = np.median(off, 0)
    R2 = np.hypot(*(off - med).T) * EDX_NM / 1000
    out = {'gcp_affine_rms_src_px': {'bse': rb, 'edx_png': re_}, 'authors_listed_rms_src_px': {'bse': rb_auth, 'edx_png': re_auth},
           'bse_crop_px': [x0, x1, y0, y1], 'windows_grid': 'W 64, step 32 (overlapping)', 'n_windows': len(res),
           'median_um': float(np.median(R)), 'p95_um': float(np.percentile(R, 95)), 'median_offset_px': med.tolist(),
           'after_removing_median_offset': {'median_um': float(np.median(R2)), 'p95_um': float(np.percentile(R2, 95))},
           'corr_before_median': float(np.median([x['corr_before'] for x in res])) if res else None,
           'corr_after_median': float(np.median([x['corr_after'] for x in res])) if res else None, 'windows': res}
    out['D0_registration'] = bool(len(res) >= 20 and out['median_um'] <= 1.0 and out['p95_um'] <= 2.0)
    json.dump(out, open(f'{OUT}/registration.json', 'w'), indent=1)
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 6.5), dpi=120); ax.imshow(zmap, cmap='gray')
    for x in res: ax.arrow(x['c0'] + W / 2, x['r0'] + W / 2, x['dx_px'] * 5, x['dy_px'] * 5, color='red', head_width=4)
    ax.set_title(f"BSE-EDX local offsets (x5), median {out['median_um']:.2f} um, p95 {out['p95_um']:.2f} um, n {len(res)}"); fig.tight_layout(); fig.savefig(f'{OUT}/registration_map.png'); plt.close(fig)
    print(json.dumps({k: v for k, v in out.items() if k != 'windows'}, indent=1))

if __name__ == '__main__':
    main()
