"""Micrograph chain: segmentation -> size statistics in calibrated units, mean linear intercept, periodic spacings.

Backends (env CEILING_SEG, comma separated, all run and all contribute candidates):
  classical  Otsu threshold (both polarities) + distance-transform watershed (scikit-image). Always available.
  sam2       SAM 2 automatic mask generator (needs SAM2_CFG and SAM2_CKPT env vars).
  cellpose   Cellpose-SAM (cellpose>=4), non-commercial weights, research use.
Extra backends (MatSAM) plug in through register_backend().
"""
import os
import numpy as np
from scipy import ndimage as ndi
from skimage import filters, measure, segmentation, feature, morphology
from common import cand

BACKENDS = {}


def register_backend(name):
    def deco(fn):
        BACKENDS[name] = fn
        return fn
    return deco


def _clean(labels, min_px):
    out = np.zeros_like(labels)
    k = 1
    for r in measure.regionprops(labels):
        if r.area < min_px:
            continue
        minr, minc, maxr, maxc = r.bbox
        if minr == 0 or minc == 0 or maxr == labels.shape[0] or maxc == labels.shape[1]:
            continue  # border-touching objects bias sizes
        out[labels == r.label] = k
        k += 1
    return out


@register_backend('classical')
def seg_classical(gray, valid):
    g = filters.gaussian(gray / 255.0, sigma=2.0)
    t = filters.threshold_otsu(g[valid]) if valid.any() else 0.5
    results = []
    for name, fg in (('bright', g > t), ('dark', g < t)):
        fg = ndi.binary_fill_holes(fg & valid)
        fg = morphology.binary_opening(fg, morphology.disk(2))
        fg = morphology.remove_small_objects(fg, 16)
        if fg.mean() < 0.02 or fg.mean() > 0.9:
            continue
        dist = ndi.distance_transform_edt(fg)
        r95 = np.percentile(dist[fg], 95) if fg.any() else 4
        md = max(4, int(0.7 * r95))
        peaks = feature.peak_local_max(dist, min_distance=md, labels=measure.label(fg), exclude_border=False)
        markers = np.zeros_like(fg, dtype=int)
        for i, (r, c) in enumerate(peaks, 1):
            markers[r, c] = i
        lab = segmentation.watershed(-dist, markers, mask=fg)
        results.append((f'classical-{name}', lab))
    return results


@register_backend('sam2')
def seg_sam2(gray, valid):
    from sam2.build_sam import build_sam2
    from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator
    global _SAM2
    if '_SAM2' not in globals():
        model = build_sam2(os.environ['SAM2_CFG'], os.environ['SAM2_CKPT'], device=os.environ.get('SAM2_DEVICE', 'cuda'))
        _SAM2 = SAM2AutomaticMaskGenerator(model, points_per_side=32, pred_iou_thresh=0.8, stability_score_thresh=0.9)
    rgb = np.stack([gray] * 3, -1).astype(np.uint8)
    masks = _SAM2.generate(rgb)
    lab = np.zeros(gray.shape, dtype=int)
    for i, m in enumerate(sorted(masks, key=lambda m: -m['area']), 1):
        lab[m['segmentation'] & valid] = i
    return [('sam2', lab)]


@register_backend('cellpose')
def seg_cellpose(gray, valid):
    from cellpose import models
    global _CP
    if '_CP' not in globals():
        _CP = models.CellposeModel(gpu=os.environ.get('CELLPOSE_GPU', '1') == '1')
    masks = _CP.eval(gray.astype(np.float32))[0]
    masks[~valid] = 0
    return [('cellpose', masks.astype(int))]


def _stats(lab, upp, unit, panel, chain_name, min_px):
    lab = _clean(lab, min_px)
    regs = measure.regionprops(lab)
    if len(regs) < 3:
        return []
    d = np.array([r.equivalent_diameter_area for r in regs]) * upp
    maj = np.array([r.axis_major_length for r in regs]) * upp
    mnr = np.array([r.axis_minor_length for r in regs]) * upp
    area_frac = 100.0 * (lab > 0).mean()
    s = 1.0 + np.log10(len(regs))
    out = [cand(np.mean(d), unit, 'micro', f'{chain_name}: mean equivalent diameter (n={len(regs)})', s, panel),
           cand(np.median(d), unit, 'micro', f'{chain_name}: median equivalent diameter', s, panel),
           cand(np.percentile(d, 10), unit, 'micro', f'{chain_name}: D10', 0.3, panel),
           cand(np.percentile(d, 90), unit, 'micro', f'{chain_name}: D90', 0.3, panel),
           cand(np.max(d), unit, 'micro', f'{chain_name}: max diameter', 0.2, panel),
           cand(np.min(d), unit, 'micro', f'{chain_name}: min diameter', 0.1, panel),
           cand(np.mean(maj), unit, 'micro', f'{chain_name}: mean major axis', 0.5, panel),
           cand(np.mean(mnr), unit, 'micro', f'{chain_name}: mean minor axis (width)', 0.5, panel),
           cand(area_frac, '%', 'micro', f'{chain_name}: area fraction', 0.5, panel)]
    return out


def _intercept(gray, valid, upp, unit, panel):
    """Mean linear intercept from Canny edges along horizontal and vertical test lines (ASTM E112 style)."""
    edges = feature.canny(gray / 255.0, sigma=2.0) & valid
    lengths = []
    for arr in (edges, edges.T):
        for line in arr[::max(1, arr.shape[0] // 20)]:
            xs = np.flatnonzero(line)
            if len(xs) >= 2:
                gaps = np.diff(xs)
                gaps = gaps[gaps > 2]
                lengths.extend(gaps.tolist())
    if len(lengths) < 10:
        return []
    L = np.array(lengths) * upp
    return [cand(np.mean(L), unit, 'micro', 'mean linear intercept (edges)', 0.8, panel),
            cand(np.median(L), unit, 'micro', 'median linear intercept (edges)', 0.5, panel)]


def _periodicity(gray, valid, upp, unit, panel):
    """Dominant spacing along rows and columns from the autocorrelation (lamellae, layers, fringes)."""
    out = []
    g = gray - gray[valid].mean() if valid.any() else gray - gray.mean()
    g = np.where(valid, g, 0)
    for axis, name in ((1, 'horizontal'), (0, 'vertical')):
        prof = g.mean(axis=1 - axis)
        if len(prof) < 16:
            continue
        ac = np.correlate(prof, prof, 'full')[len(prof) - 1:]
        ac = ac / (ac[0] + 1e-9)
        pk = feature.peak_local_max(ac, min_distance=3, num_peaks=3, exclude_border=False).ravel()
        pk = [p for p in sorted(pk) if p > 2]
        if pk and ac[pk[0]] > 0.2:
            out.append(cand(pk[0] * upp, unit, 'micro', f'{name} periodic spacing (autocorrelation)', 0.4, panel))
    return out


def run(gray, valid, scale, panel):
    """scale: dict from find_scale_bar (px_per_unit, unit) or None -> no calibrated candidates."""
    if not scale or scale.get('recip'):
        return []
    upp, unit = 1.0 / scale['px_per_unit'], scale['unit']
    min_px = max(12, int(gray.size * 2e-5))
    out = []
    names = [b.strip() for b in os.environ.get('CEILING_SEG', 'classical').split(',') if b.strip()]
    for name in names:
        try:
            for chain_name, lab in BACKENDS[name](gray, valid):
                out += _stats(lab, upp, unit, panel, chain_name, min_px)
        except Exception as e:  # a missing backend must not stop the run
            out.append(dict(error=f'{name}: {type(e).__name__}: {e}'[:300], chain='micro', panel=panel))
    out += _intercept(gray, valid, upp, unit, panel)
    out += _periodicity(gray, valid, upp, unit, panel)
    return out
