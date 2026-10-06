#!/usr/bin/env python3
"""fm_reader_test.py (v4 Track C, option (c): UHCSDB for the FM reader test only; local models, no quote). Same protocol as the classical
reader (reader2_select.py): the 24 human-annotated particle images of NIST 11256/964 (I level: validation only), the same dev/test split,
the same quantity (number-mean ECD of particles >= 0.15 um, edge particles ignored, 26 px/um), the same acceptance (test: >= 90 % of images
within 20 % of the mask truth, and the 800 C condition medians in the truth order).
Readers (masks -> particle map = union of selected masks):
  SAM     segment_anything ViT-H automatic mask generator, default parameters (MatSAM's bundled copy of segment_anything).
  MatSAM  ViT-H with MatSAM's prompt generator and its published UHCS parameters (layers 0, scales 3, n_per_side_base 80, method 2,
          pred_iou 0.88, stability 0.90, box/crop NMS 0.7).
  SAM2    SAM 2.1 hiera-large automatic mask generator, default parameters.
Mask selection rule, chosen per reader on dev only from the same menu: area cap {250 px (MatSAM published), none} x brightness {none,
mask mean > image mean}. Classical reader 2 (dev-tuned) is re-scored on the same split for the comparison. Output fm_reader_test.json."""
import glob, json, os, re, sys, time
import numpy as np, tifffile, torch
from skimage import measure
F = '/home/aid1/Documents/harbor/v4_host/fm'; X = '/home/aid1/Documents/harbor/v4_host/uhcsdb/nist964/x/particles'
sys.path.insert(0, f'{F}/matsam'); sys.path.insert(0, f'{F}/matsam/utils')
import types; sys.modules['gala'] = types.ModuleType('gala'); sys.modules['gala.evaluate'] = types.ModuleType('gala.evaluate')   # gala is used only by MatSAM's evaluation metrics, not by the prompt generator
UM = 1 / 26.0; DMIN_UM = 0.15
SEL = json.load(open('/home/aid1/Documents/harbor/v4/uhcs/reader2_selection.json'))
split = {r['file']: r['split'] for r in SEL['rows']}; truth = {r['file']: r['truth'] for r in SEL['rows']}; cond = {r['file']: r['cond'] for r in SEL['rows']}
def ecd_mean(m):
    L = measure.label(m); H, W = m.shape; d = []
    for p in measure.regionprops(L):
        r0, c0, r1, c1 = p.bbox
        if r0 == 0 or c0 == 0 or r1 == H or c1 == W: continue
        e = p.equivalent_diameter_area * UM
        if e >= DMIN_UM: d.append(e)
    return float(np.mean(d)) if d else float('nan')
def select(masks, img, cap, bright):
    out = np.zeros(img.shape[:2], bool); mu = img.mean()
    for mk in masks:
        s = mk['segmentation']; a = int(s.sum())
        if a < 2 or (cap and a > cap): continue
        if bright and img[s].mean() <= mu: continue
        out |= s
    return out
def run_reader(name, gen):
    res = {}
    for f in sorted(glob.glob(f'{X}/images/*.tif')):
        a = tifffile.imread(f); a = a[..., 0] if a.ndim == 3 else a; rgb = np.stack([a] * 3, -1).astype(np.uint8)
        t0 = time.time(); masks = gen(rgb); res[os.path.basename(f)] = {'masks': masks, 'img': a, 'sec': time.time() - t0}
        print(name, os.path.basename(f), len(masks), 'masks', '%.1fs' % (time.time() - t0), flush=True)
    return res
def evaluate(name, res):
    menu = [(cap, br) for cap in (250, None) for br in (False, True)]; dev = [k for k in res if split[k] == 'dev']; best = None
    for cap, br in menu:
        e = [abs(np.log(ecd_mean(select(res[k]['masks'], res[k]['img'], cap, br)) / truth[k])) for k in dev]
        e = [x for x in e if np.isfinite(x)]; obj = float(np.median(e)) if e else 9.0
        if best is None or obj < best[0]: best = (obj, cap, br)
    _, cap, br = best; rows = []
    for k in res:
        v = ecd_mean(select(res[k]['masks'], res[k]['img'], cap, br)); rows.append({'file': k, 'split': split[k], 'cond': cond[k], 'truth': truth[k], 'reader': v})
    test = [r for r in rows if r['split'] == 'test']; ok = [np.isfinite(r['reader']) and abs(r['reader'] - r['truth']) / r['truth'] <= 0.20 for r in test]
    times = ['800C-3H-Q', '800C-8H-Q', '800C-24H-Q', '800C-85H-Q']; med = lambda key, c: float(np.nanmedian([r[key] for r in rows if r['cond'] == c]))
    ot = [times[i] for i in np.argsort([med('truth', c) for c in times])]; orr = [times[i] for i in np.argsort([med('reader', c) for c in times])]
    return {'reader': name, 'rule': {'area_cap_px': cap, 'bright_only': br}, 'dev_objective': best[0], 'test_within_20pct': float(np.mean(ok)), 'n_test': len(test),
            'order_truth': ot, 'order_reader': orr, 'accept': bool(np.mean(ok) >= 0.9 and ot == orr), 'mean_sec_per_image': float(np.mean([res[k]['sec'] for k in res])), 'rows': rows}
if __name__ == '__main__':
    dev = os.environ.get('FM_DEVICE', 'cpu'); torch.set_num_threads(16); out = {'device': dev, 'classical_reader2': {k: SEL[k] for k in ('best_params', 'test_within_20pct', 'order_truth', 'order_reader', 'accept')}}
    from segment_anything_ import sam_model_registry, SamAutomaticMaskGenerator
    from utils.prompt_generator import PromptGenerator
    sam = sam_model_registry['vit_h'](checkpoint=f'{F}/ckpt/sam_vit_h_4b8939.pth').to(dev)
    g_sam = SamAutomaticMaskGenerator(sam)
    out['SAM'] = evaluate('SAM', run_reader('SAM', g_sam.generate))
    def g_mat(rgb):
        pts = PromptGenerator(rgb, 0, 3, 80, 2).generate_prompt_points()
        return SamAutomaticMaskGenerator(model=sam, points_per_side=None, point_grids=pts, pred_iou_thresh=0.88, crop_n_layers=0, crop_n_points_downscale_factor=3,
                                         box_nms_thresh=0.7, crop_nms_thresh=0.7, stability_score_thresh=0.90, points_per_batch=256, min_mask_region_area=0).generate(rgb)
    out['MatSAM'] = evaluate('MatSAM', run_reader('MatSAM', g_mat))
    del sam; torch.cuda.empty_cache()
    from sam2.build_sam import build_sam2
    from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator
    s2 = build_sam2('configs/sam2.1/sam2.1_hiera_l.yaml', f'{F}/ckpt/sam2.1_hiera_large.pt', device=dev)
    out['SAM2'] = evaluate('SAM2', run_reader('SAM2', SAM2AutomaticMaskGenerator(s2).generate))
    json.dump(out, open('/home/aid1/Documents/harbor/v4/uhcs/fm_reader_test.json', 'w'), indent=1, default=float)
    for k in ('SAM', 'MatSAM', 'SAM2'): print(k, {kk: out[k][kk] for kk in ('rule', 'test_within_20pct', 'order_reader', 'accept', 'mean_sec_per_image')})
    print('classical', out['classical_reader2'])
