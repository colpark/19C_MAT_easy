"""PanelBench MCP backend worker: family `vision` (node 2, port 8101).

Tools (POST /<tool>, body {"image_b64": ..., "args": {...}, "seed": int}):
  segment                 SAM 2.1 hiera_small (auto mask generator or point prompts)
  segment_microstructure  MatSAM recipe (USTB-AI3DVIP/matsam) on SAM v1 ViT-H weights
  grain_size_astm         Cellpose-SAM (cellpose v4, "cpsam" weights) + ASTM E112 planimetric / intercept
  grain_boundary_map      UNet++ + MicroNet encoder: UNAVAILABLE (no pretrained decoder published by NASA)
  classify_modality_embed MicroNet ResNet50 v1.1 encoder, 2048-d global-average-pooled feature
  find_atoms              AtomAI pretrained Segmentor (G_MD graphene default, or BFO)
GET /health, GET /version.
No network calls at request time; all weights are local under WEIGHTS.
"""
import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
HOME = os.path.expanduser("~/mcp/vision")
WEIGHTS = os.path.join(HOME, "weights")
os.environ.setdefault("CELLPOSE_LOCAL_MODELS_PATH", os.path.join(WEIGHTS, "cellpose"))

import base64
import hashlib
import io
import json
import math
import random
import threading
import time
from importlib.metadata import version as pkg_version

import cv2
import numpy as np
import torch
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image
from pydantic import BaseModel
from scipy.spatial import cKDTree
from skimage import measure, morphology

torch.use_deterministic_algorithms(True, warn_only=True)
torch.backends.cudnn.benchmark = False
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
WORKER_VERSION = "0.1.0"
LOG_PATH = os.path.join(HOME, "requests.log")

W = {
    "sam2": os.path.join(WEIGHTS, "sam2.1_hiera_small.pt"),
    "sam_vit_h": os.path.join(WEIGHTS, "sam_vit_h_4b8939.pth"),
    "cpsam": os.path.join(WEIGHTS, "cellpose", "cpsam"),
    "micronet_resnet50": os.path.join(WEIGHTS, "resnet50_pretrained_microscopynet_v1.1.pth.tar"),
    "atomai_G_MD": os.path.join(WEIGHTS, "G_MD.tar"),
    "atomai_BFO": os.path.join(WEIGHTS, "bfo.tar"),
}


def _load_sums():
    sums = {}
    p = os.path.join(WEIGHTS, "SHA256SUMS")
    if os.path.exists(p):
        for line in open(p):
            h, f = line.split()
            sums[os.path.basename(f)] = h
    return {k: sums.get(os.path.basename(v)) for k, v in W.items()}


SHA = _load_sums()
TOOLS = {
    "segment": ("sam2.1_hiera_small (facebookresearch/sam2)", ["sam2"]),
    "segment_microstructure": ("MatSAM recipe (USTB-AI3DVIP/matsam) + SAM ViT-H", ["sam_vit_h"]),
    "grain_size_astm": ("Cellpose-SAM cpsam (cellpose %s)" % pkg_version("cellpose"), ["cpsam"]),
    "grain_boundary_map": ("UNet++/MicroNet (unavailable: no pretrained decoder)", []),
    "classify_modality_embed": ("MicroNet resnet50 v1.1 (nasa/pretrained-microscopy-models)", ["micronet_resnet50"]),
    "find_atoms": ("AtomAI %s pretrained Segmentor" % pkg_version("atomai"), ["atomai_G_MD", "atomai_BFO"]),
}

_LOCK = threading.Lock()
_MODELS = {}


def seed_all(seed):
    random.seed(seed)
    np.random.seed(seed % (2**32))
    torch.manual_seed(seed)


def decode_image(b64):
    raw = base64.b64decode(b64)
    img = Image.open(io.BytesIO(raw))
    img.load()
    return raw, np.array(img.convert("RGB"))


def png_b64(arr):
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def palette(n, seed=0):
    rng = np.random.default_rng(seed)
    return rng.integers(40, 255, size=(max(n, 1), 3), dtype=np.uint8)


def overlay_masks(rgb, masks, alpha=0.45, points=None):
    """masks: list of bool HxW arrays, drawn largest first."""
    out = rgb.astype(np.float32).copy()
    cols = palette(len(masks))
    order = np.argsort([-m.sum() for m in masks]) if masks else []
    for i in order:
        m = masks[i]
        out[m] = (1 - alpha) * out[m] + alpha * cols[i]
    out = out.astype(np.uint8)
    for i in order:
        cnts, _ = cv2.findContours(masks[i].astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        cv2.drawContours(out, cnts, -1, (255, 255, 255), 1)
    if points is not None:
        for x, y in points:
            cv2.circle(out, (int(round(x)), int(round(y))), 4, (255, 0, 0), -1)
    return out


def overlay_labels(rgb, labels, alpha=0.45):
    out = rgb.astype(np.float32).copy()
    n = int(labels.max())
    cols = palette(n + 1)
    fg = labels > 0
    out[fg] = (1 - alpha) * out[fg] + alpha * cols[labels[fg]]
    out = out.astype(np.uint8)
    edges = (cv2.dilate(labels.astype(np.float32), np.ones((3, 3))) != cv2.erode(labels.astype(np.float32), np.ones((3, 3))))
    out[edges] = (255, 255, 255)
    return out


# ---------------------------------------------------------------- model loaders
def get_sam2():
    if "sam2" not in _MODELS:
        from sam2.build_sam import build_sam2
        _MODELS["sam2"] = build_sam2("configs/sam2.1/sam2.1_hiera_s.yaml", W["sam2"], device=DEVICE)
    return _MODELS["sam2"]


def get_sam1():
    if "sam1" not in _MODELS:
        from segment_anything import sam_model_registry
        m = sam_model_registry["vit_h"](checkpoint=W["sam_vit_h"])
        _MODELS["sam1"] = m.to(DEVICE).eval()
    return _MODELS["sam1"]


def get_cellpose():
    if "cp" not in _MODELS:
        from cellpose import models
        _MODELS["cp"] = models.CellposeModel(gpu=DEVICE == "cuda", pretrained_model=W["cpsam"])
    return _MODELS["cp"]


def get_micronet():
    if "micronet" not in _MODELS:
        import torchvision
        m = torchvision.models.resnet50(weights=None)
        sd = torch.load(W["micronet_resnet50"], map_location="cpu", weights_only=False)
        if isinstance(sd, dict) and "state_dict" in sd:
            sd = sd["state_dict"]
        sd = {k.replace("module.", ""): v for k, v in sd.items()}
        missing, unexpected = m.load_state_dict(sd, strict=False)
        m.fc = torch.nn.Identity()
        _MODELS["micronet"] = m.to(DEVICE).eval()
        _MODELS["micronet_load"] = {"missing": list(missing), "unexpected": list(unexpected)}
    return _MODELS["micronet"]


def get_atomai(name):
    key = "atomai_" + name
    if key not in _MODELS:
        from atomai.models import load_model
        _MODELS[key] = load_model(W[key])
    return _MODELS[key]


# ---------------------------------------------------------------- tools
def tool_segment(rgb, args, seed):
    mode = args.get("mode", "auto")
    model = get_sam2()
    warnings = []
    pts = None
    if mode == "points":
        from sam2.sam2_image_predictor import SAM2ImagePredictor
        pts = args.get("points") or []
        if not pts:
            raise HTTPException(400, "mode=points requires args.points=[[x,y],...]")
        pred = SAM2ImagePredictor(model)
        with torch.inference_mode(), torch.autocast(DEVICE, dtype=torch.bfloat16, enabled=DEVICE == "cuda"):
            pred.set_image(rgb)
            masks = []
            scores = []
            for x, y in pts:  # one object per point prompt
                m, s, _ = pred.predict(point_coords=np.array([[x, y]], dtype=np.float32),
                                       point_labels=np.array([1]), multimask_output=True)
                j = int(np.argmax(s))
                masks.append(m[j] > 0)
                scores.append(float(s[j]))
    else:
        from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator
        gen = SAM2AutomaticMaskGenerator(model, points_per_side=int(args.get("points_per_side", 32)),
                                         pred_iou_thresh=float(args.get("pred_iou_thresh", 0.8)),
                                         stability_score_thresh=float(args.get("stability_score_thresh", 0.92)),
                                         min_mask_region_area=int(args.get("min_mask_region_area", 0)))
        with torch.inference_mode(), torch.autocast(DEVICE, dtype=torch.bfloat16, enabled=DEVICE == "cuda"):
            res = gen.generate(rgb)
        masks = [r["segmentation"].astype(bool) for r in res]
        scores = [float(r["predicted_iou"]) for r in res]
    areas = [int(m.sum()) for m in masks]
    if not masks:
        warnings.append("no masks produced")
    return {
        "values": {"mode": mode, "mask_count": len(masks), "mask_areas_px": areas,
                   "mask_scores": [round(s, 4) for s in scores]},
        "units": {"mask_areas_px": "px^2"},
        "confidence": float(np.mean(scores)) if scores else None,
        "warnings": warnings,
        "images": {"overlay": png_b64(overlay_masks(rgb, masks, points=pts))},
    }


def matsam_prompt_points(rgb, n_per_side_base=32, method_type=1):
    """Re-implementation of matsam utils/prompt_generator.PromptGenerator (layers=0).
    Deviation: centroid x is normalised by width and y by height (upstream divides x by shape[0], y by shape[1],
    identical only for square images)."""
    h, w = rgb.shape[:2]
    if method_type == 1:
        dst = cv2.Canny(rgb, 80, 130)
        canny = morphology.remove_small_objects(measure.label(dst), max_size=14, connectivity=2)
        canny = morphology.dilation(np.uint8(canny > 0) * 255, morphology.footprint_rectangle((5, 5)))
        contours, _ = cv2.findContours(canny, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_KCOS)
    else:
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, otsu = cv2.threshold(blurred, 50, 225, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(otsu, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_KCOS)
    cents = []
    for c in contours:
        M = cv2.moments(c)
        if M["m00"] != 0:
            cents.append([M["m10"] / M["m00"] / w, M["m01"] / M["m00"] / h])
    n = n_per_side_base
    off = 1 / (2 * n)
    side = np.linspace(off, 1 - off, n)
    grid = np.stack([np.tile(side[None, :], (n, 1)), np.tile(side[:, None], (1, n))], axis=-1).reshape(-1, 2)
    if cents:
        grid = np.concatenate([grid, np.array(cents)], 0)
    return grid, len(cents)


def tool_segment_microstructure(rgb, args, seed):
    from segment_anything import SamAutomaticMaskGenerator
    method_type = int(args.get("method_type", 1))
    grid, n_cent = matsam_prompt_points(rgb, int(args.get("n_per_side_base", 32)), method_type)
    gen = SamAutomaticMaskGenerator(model=get_sam1(), points_per_side=None, point_grids=[grid],
                                    pred_iou_thresh=float(args.get("pred_iou_thresh", 0.90)),
                                    crop_n_layers=0, crop_n_points_downscale_factor=3,
                                    box_nms_thresh=0.80, crop_nms_thresh=0.80, stability_score_thresh=0.92,
                                    points_per_batch=256, min_mask_region_area=0)
    with torch.inference_mode():
        res = gen.generate(rgb)
    masks = [r["segmentation"].astype(bool) for r in res]
    scores = [float(r["predicted_iou"]) for r in res]
    # MatSAM polycrystal post-processing -> boundary map (notebook "Segment result extraction" + postprocess)
    h, w = rgb.shape[:2]
    result = np.zeros((h, w), np.float64)
    area_threshold = float(args.get("area_threshold", 25000))
    for m in masks:
        tmp = np.uint8(m) * 255
        if tmp.sum() / 255 <= area_threshold:
            tmp = cv2.Laplacian(tmp, cv2.CV_8U)
            tmp = morphology.remove_small_objects(measure.label(tmp), max_size=49, connectivity=2)
            result += tmp
    b = np.uint8(result > 0)
    b = morphology.skeletonize(b, method="lee") > 0
    b = morphology.remove_small_objects(measure.label(b), max_size=199, connectivity=2) > 0
    b = morphology.dilation(b, morphology.footprint_rectangle((5, 5)))
    b = morphology.erosion(b, morphology.footprint_rectangle((3, 3)))
    b = morphology.remove_small_objects(measure.label(b), max_size=199, connectivity=2) > 0
    b = morphology.skeletonize(b, method="lee") > 0
    b = morphology.dilation(b, morphology.footprint_rectangle((2, 2)))
    regions = measure.label(~b, connectivity=1)
    ov = overlay_masks(rgb, masks)
    bnd = ov.copy()
    bnd[b] = (255, 0, 0)
    return {
        "values": {"mask_count": len(masks), "mask_areas_px": [int(m.sum()) for m in masks],
                   "mask_scores": [round(s, 4) for s in scores], "n_prompt_points": int(len(grid)),
                   "n_centroid_prompts": n_cent, "boundary_regions": int(regions.max())},
        "units": {"mask_areas_px": "px^2"},
        "confidence": float(np.mean(scores)) if scores else None,
        "warnings": [] if masks else ["no masks produced"],
        "images": {"overlay": png_b64(ov), "boundary_map": png_b64(bnd)},
    }


def intercept_stats(labels, n_lines=10):
    """Mean lineal intercept: total test-line length / number of grain-boundary crossings.
    Test lines: n_lines horizontal + n_lines vertical, evenly spaced. Background (0) gaps are collapsed."""
    h, w = labels.shape
    total_len, crossings = 0, 0
    for k in range(1, n_lines + 1):
        for line in (labels[int(k * h / (n_lines + 1)), :], labels[:, int(k * w / (n_lines + 1))]):
            seq = line[line > 0]
            total_len += len(line)
            if len(seq):
                crossings += int(np.count_nonzero(np.diff(seq) != 0))
    return (total_len / crossings) if crossings else None, crossings, total_len


def tool_grain_size_astm(rgb, args, seed):
    model = get_cellpose()
    kw = {}
    if args.get("diameter"):
        kw["diameter"] = float(args["diameter"])
    with torch.inference_mode():
        masks, flows, styles = model.eval(rgb, **kw)[:3]
    masks = masks.astype(np.int32)
    h, w = masks.shape
    ids = np.unique(masks)
    ids = ids[ids > 0]
    border = np.unique(np.concatenate([masks[0], masks[-1], masks[:, 0], masks[:, -1]]))
    border = set(int(b) for b in border if b > 0)
    n_in = sum(1 for i in ids if int(i) not in border)
    n_edge = len(ids) - n_in
    areas = np.bincount(masks.ravel())[1:]
    areas = areas[areas > 0]
    warnings = []
    n_equiv = n_in + 0.5 * n_edge  # Jeffries planimetric count
    NA_px = n_equiv / float(h * w) if n_equiv else None
    mean_area_px = (1.0 / NA_px) if NA_px else None
    L_px, crossings, _ = intercept_stats(masks)
    G = G_int = None
    px_per_um = args.get("px_per_um")
    if px_per_um:
        px_per_um = float(px_per_um)
        if NA_px:
            NA_mm2 = NA_px * (px_per_um ** 2) * 1e6  # grains per mm^2
            G = 3.321928 * math.log10(NA_mm2) - 2.954  # ASTM E112 planimetric
        if L_px:
            L_mm = L_px / px_per_um * 1e-3
            G_int = -6.643856 * math.log10(L_mm) - 3.288  # ASTM E112 intercept
    else:
        warnings.append("px_per_um not given: ASTM G cannot be computed (G=null); values are in px")
    if len(ids) < 50:
        warnings.append("fewer than 50 grains detected; ASTM E112 recommends >=50 grains for planimetric G")
    return {
        "values": {"grain_count": int(len(ids)), "grains_interior": int(n_in), "grains_edge": int(n_edge),
                   "mean_planimetric_grain_area_px": mean_area_px,
                   "mean_mask_area_px": float(areas.mean()) if len(areas) else None,
                   "mean_intercept_length_px": L_px, "intercept_crossings": crossings,
                   "astm_G_planimetric": G, "astm_G_intercept": G_int,
                   "px_per_um": px_per_um or None},
        "units": {"mean_planimetric_grain_area_px": "px^2", "mean_intercept_length_px": "px"},
        "confidence": None,
        "warnings": warnings,
        "images": {"overlay": png_b64(overlay_labels(rgb, masks))},
    }


def tool_grain_boundary_map(rgb, args, seed):
    return {
        "values": None, "units": {}, "confidence": None,
        "warnings": ["unavailable: nasa/pretrained-microscopy-models publishes MicroNet encoders only (no trained "
                     "UNet++ grain-boundary decoder); a decoder must be trained before this tool can work. "
                     "Use segment_microstructure (MatSAM boundary_map) or grain_size_astm instead."],
        "status": "unavailable",
    }


IMNET_MEAN = np.array([0.485, 0.456, 0.406], np.float32)
IMNET_STD = np.array([0.229, 0.224, 0.225], np.float32)


def tool_classify_modality_embed(rgb, args, seed):
    m = get_micronet()
    size = int(args.get("size", 224))
    x = cv2.resize(rgb, (size, size), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
    x = (x - IMNET_MEAN) / IMNET_STD
    t = torch.from_numpy(x.transpose(2, 0, 1)[None]).to(DEVICE)
    with torch.inference_mode():
        f = m(t)[0].float().cpu().numpy()
    return {
        "values": {"embedding": [round(float(v), 6) for v in f], "dim": int(f.shape[0]),
                   "encoder": "resnet50", "weights": "micronet v1.1", "input_size": size,
                   "preprocess": "RGB, resize (INTER_AREA) to size x size, ImageNet mean/std"},
        "units": {}, "confidence": None, "warnings": [],
    }


def estimate_spacing_px(gray):
    """Dominant nearest-neighbour period from the image autocorrelation (first off-centre peak)."""
    g = gray - gray.mean()
    f = np.fft.rfft2(g)
    ac = np.fft.irfft2(np.abs(f) ** 2, s=g.shape)
    ac = np.fft.fftshift(ac)
    cy, cx = np.array(ac.shape) // 2
    yy, xx = np.mgrid[0:ac.shape[0], 0:ac.shape[1]]
    r = np.hypot(yy - cy, xx - cx)
    lim = min(cy, cx) // 2
    # radial profile; the central peak ends at its first local minimum
    ri = r.astype(int)
    prof = np.bincount(ri.ravel(), ac.ravel()) / np.maximum(np.bincount(ri.ravel()), 1)
    r0 = None
    for k in range(1, lim):
        if prof[k] <= prof[k - 1] and prof[k] <= prof[k + 1]:
            r0 = k
            break
    if r0 is None:
        return None
    acm = ac.copy()
    acm[(r < r0) | (r > lim)] = -np.inf
    loc = (acm == cv2.dilate(acm.astype(np.float32), np.ones((5, 5)))) & np.isfinite(acm) & (acm > 0)
    if not loc.any():
        return None
    vals = acm[loc]
    keep = loc & (acm >= 0.5 * vals.max())
    return float(r[keep].min()) if keep.any() else None


ATOMAI_TARGET_SPACING_PX = float(os.environ.get("ATOMAI_TARGET", 32.0))  # sweep 16-32 px on synthetic lattices: 32 best (94-97% recall, a=6..30 px)


def tool_find_atoms(rgb, args, seed):
    name = args.get("model", "G_MD")
    if name not in ("G_MD", "BFO"):
        raise HTTPException(400, "args.model must be G_MD or BFO")
    model = get_atomai(name)
    warnings = []
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    gray = (gray - gray.min()) / (np.ptp(gray) + 1e-8)
    if args.get("invert"):
        gray = 1.0 - gray
    h, w = gray.shape
    rescale = args.get("rescale", "auto")
    spacing = None
    if rescale == "auto":
        spacing = estimate_spacing_px(gray)
        scale = float(np.clip(ATOMAI_TARGET_SPACING_PX / spacing, 0.25, 4.0)) if spacing else 1.0
        if not spacing:
            warnings.append("could not estimate lattice spacing; no rescale applied")
    elif rescale in (None, "none", False):
        scale = 1.0
    else:
        scale = float(rescale)
    if scale * h * scale * w > 4096 * 4096:
        scale = math.sqrt(4096 * 4096 / (h * w))
        warnings.append("rescale capped to keep the network input <= 4096^2 px")
    g = cv2.resize(gray, (max(8, round(w * scale)), max(8, round(h * scale))), interpolation=cv2.INTER_CUBIC) \
        if scale != 1.0 else gray
    hs, ws = g.shape
    # atomai nets downsample x8; pad to a multiple of 8
    H8, W8 = int(math.ceil(hs / 8) * 8), int(math.ceil(ws / 8) * 8)
    pad = np.pad(g, ((0, H8 - hs), (0, W8 - ws)), mode="reflect")
    nn_out, coords = model.predict(pad, thresh=float(args.get("thresh", 0.5)), verbose=False)
    c = coords[0]
    c = c[(c[:, 0] < hs) & (c[:, 1] < ws)]
    sx, sy = w / ws, h / hs
    pos = [[float(x) * sx, float(y) * sy] for y, x in c[:, :2]]  # atomai returns (row, col, class)
    cls = [int(v) for v in c[:, 2]] if c.shape[1] > 2 else []
    nn = None
    if len(pos) >= 2:
        P = np.array(pos)
        d, _ = cKDTree(P).query(P, k=2)
        d = d[:, 1]
        nn = {"mean": float(d.mean()), "median": float(np.median(d)), "std": float(d.std()),
              "min": float(d.min()), "max": float(d.max())}
    else:
        warnings.append("fewer than 2 atoms found")
    ppn = args.get("px_per_nm")
    nn_nm = {k: v / float(ppn) for k, v in nn.items()} if (nn and ppn) else None
    warnings.append("%s was trained on %s; results on other materials/scales are out of distribution"
                    % (name, "simulated graphene STEM" if name == "G_MD" else "experimental BFO STEM"))
    out = rgb.copy()
    for x, y in pos:
        cv2.circle(out, (int(round(x)), int(round(y))), 2, (255, 0, 0), -1)
    return {
        "values": {"atom_count": len(pos), "positions_px": [[round(x, 2), round(y, 2)] for x, y in pos],
                   "classes": cls, "nn_distance_px": nn, "nn_distance_nm": nn_nm, "model": name,
                   "estimated_spacing_px": spacing, "rescale_factor": scale},
        "units": {"positions_px": "px (x, y) in the original image", "nn_distance_px": "px", "nn_distance_nm": "nm"},
        "confidence": None, "warnings": warnings,
        "images": {"overlay": png_b64(out)},
    }


DISPATCH = {
    "segment": tool_segment,
    "segment_microstructure": tool_segment_microstructure,
    "grain_size_astm": tool_grain_size_astm,
    "grain_boundary_map": tool_grain_boundary_map,
    "classify_modality_embed": tool_classify_modality_embed,
    "find_atoms": tool_find_atoms,
}

# ---------------------------------------------------------------- http
app = FastAPI(title="panelbench-mcp-vision", version=WORKER_VERSION)


class Req(BaseModel):
    image_b64: str | None = None
    args: dict = {}
    seed: int = 0


@app.get("/health")
def health():
    return {"ok": True, "device": DEVICE, "cuda": torch.cuda.is_available(), "loaded": sorted(_MODELS)}


@app.get("/version")
def version():
    pk = {}
    for p in ["torch", "torchvision", "sam-2", "segment-anything", "cellpose", "atomai",
              "segmentation-models-pytorch", "pretrained-microscopy-models", "numpy", "opencv-python-headless"]:
        try:
            pk[p] = pkg_version(p)
        except Exception:
            pk[p] = None
    return {"worker": WORKER_VERSION, "packages": pk, "weights_sha256": SHA,
            "tools": {t: {"backing_model": b, "weights": {k: SHA.get(k) for k in ks}} for t, (b, ks) in TOOLS.items()}}


def run_tool(tool, req: Req):
    if tool not in DISPATCH:
        raise HTTPException(404, "unknown tool")
    if not req.image_b64:
        raise HTTPException(400, "image_b64 required")
    t0 = time.time()
    raw, rgb = decode_image(req.image_b64)
    in_sha = hashlib.sha256(raw).hexdigest()
    with _LOCK:
        seed_all(req.seed)
        out = DISPATCH[tool](rgb, req.args or {}, req.seed)
    backing, keys = TOOLS[tool]
    out.setdefault("images", {})
    out["provenance"] = {"tool": tool, "tool_version": WORKER_VERSION, "backing_model": backing,
                         "weights_sha256": {k: SHA.get(k) for k in keys}, "seed": req.seed, "device": DEVICE}
    dt = time.time() - t0
    out["provenance"]["duration_s"] = round(dt, 3)
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "tool": tool, "input_sha256": in_sha,
                            "args": req.args, "seed": req.seed, "duration_s": round(dt, 3)}) + "\n")
    return out


@app.post("/{tool}")
def post_tool(tool: str, req: Req):
    return JSONResponse(run_tool(tool, req))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8101)), workers=1)
