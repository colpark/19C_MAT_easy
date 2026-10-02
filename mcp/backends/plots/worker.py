"""PanelBench MCP backend worker: family `plots`.

Tools (POST /<tool>, body {"image_b64": ..., "args": {...}, "seed": int}):
  read_text       RapidOCR (PP-OCRv4 det/rec ONNX, bundled in rapidocr-onnxruntime) -> tokens [{text, box, score}]
  read_scale_bar  EXSCLAIM! scale-bar Faster R-CNN + CRNN label reader (+ deterministic bar-length refinement;
                  deterministic fallback detector + OCR when EXSCLAIM finds nothing)
  chart_to_table  DePlot (google/deplot, Pix2Struct) -> linearized table + parsed table
  digitize_curve  LineFormer (Mask2Former Swin-T, mmdet 2.28.2 / mmcv-full 1.7.2) -> per-series pixel polylines;
                  method="color" selects the deterministic colour/darkness tracer fallback
All coordinates are image pixels, origin top-left, x right, y down.
"""
import base64, hashlib, io, json, logging, os, re, sys, threading, time, warnings

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
warnings.filterwarnings("ignore")

import numpy as np
import cv2
from PIL import Image
import torch
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

ROOT = os.path.dirname(os.path.abspath(__file__))
W = os.path.join(ROOT, "weights")
REPOS = os.path.join(ROOT, "repos")
PORT = int(os.environ.get("PLOTS_PORT", "8103"))
DEVICE = os.environ.get("PLOTS_DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
WORKER_VERSION = "plots-worker 0.1.0"

torch.use_deterministic_algorithms(True, warn_only=True)
torch.backends.cudnn.benchmark = False

PATHS = {
    "deplot": os.path.join(W, "deplot", "model.safetensors"),
    "deplot_font": os.path.join(W, "fonts", "Arial.TTF"),
    "exsclaim_scale_bar_det": os.path.join(W, "exsclaim", "scale_bar_detection_model.pt"),
    "exsclaim_scale_label_rec": os.path.join(W, "exsclaim", "scale_label_recognition_model.pt"),
    "lineformer": os.path.join(W, "lineformer", "models", "iter_3000.pth"),
}
REPO_COMMITS = {"exsclaim": "003400ee7486568cd229d3ff012613baa2fa6554",
                "LineFormer": "7952e27b4653dea025394618fbd655f41d82ab6b"}

LOG = logging.getLogger("plots")
_lock = threading.Lock()
_models = {}
_sha_cache = {}


def sha256_file(p):
    if p in _sha_cache:
        return _sha_cache[p]
    cache_f = os.path.join(W, "sha256.json")
    try:
        cache = json.load(open(cache_f))
    except Exception:
        cache = {}
    st = os.stat(p)
    key = f"{p}|{st.st_size}|{int(st.st_mtime)}"
    if key not in cache:
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 22), b""):
                h.update(chunk)
        cache[key] = h.hexdigest()
        try:
            json.dump(cache, open(cache_f, "w"), indent=1)
        except Exception:
            pass
    _sha_cache[p] = cache[key]
    return cache[key]


def pkg_version(name):
    try:
        from importlib.metadata import version
        return version(name)
    except Exception:
        return None


def seed_all(seed):
    import random
    random.seed(seed); np.random.seed(seed % (2 ** 32)); torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def decode_image(b64):
    raw = base64.b64decode(b64)
    im = Image.open(io.BytesIO(raw))
    im.load()
    return raw, im.convert("RGB")


def png_b64(arr_rgb):
    buf = io.BytesIO()
    Image.fromarray(arr_rgb).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


# ----------------------------------------------------------------------------------------------- OCR
def get_ocr():
    if "ocr" not in _models:
        from rapidocr_onnxruntime import RapidOCR
        _models["ocr"] = RapidOCR()
    return _models["ocr"]


def _ocr_raw(arr_rgb):
    res, _ = get_ocr()(arr_rgb[:, :, ::-1].copy())  # RapidOCR expects BGR ndarray
    out = []
    for quad, text, score in res or []:
        q = np.array(quad, dtype=float)
        out.append((q, text, float(score)))
    return out


def _iou_box(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0])); iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0


def ocr_tokens(img, box=None, rotated=True, upscale=None, min_score=0.3):
    arr = np.asarray(img)
    ox, oy = 0, 0
    if box:
        x0, y0, x1, y1 = [int(round(v)) for v in box]
        x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(arr.shape[1], x1), min(arr.shape[0], y1)
        arr = arr[y0:y1, x0:x1]; ox, oy = x0, y0
    h, w = arr.shape[:2]
    if upscale is None:
        upscale = 2.0 if max(h, w) < 1200 else 1.0
    s = float(upscale)
    big = cv2.resize(arr, (int(w * s), int(h * s)), interpolation=cv2.INTER_CUBIC) if s != 1 else arr
    toks = []
    for q, text, sc in _ocr_raw(big):
        q = q / s
        toks.append({"text": text, "box": [round(float(q[:, 0].min()) + ox, 1), round(float(q[:, 1].min()) + oy, 1),
                                           round(float(q[:, 0].max()) + ox, 1), round(float(q[:, 1].max()) + oy, 1)],
                     "score": round(sc, 4), "rotation": 0})
    if rotated:
        # vertical text reading bottom-to-top (typical y-axis label): rotate image 90 deg clockwise
        rot = np.ascontiguousarray(np.rot90(big, k=-1))
        H = big.shape[0]
        for q, text, sc in _ocr_raw(rot):
            # rotated pixel (u,v) -> original big (x,y): x = v, y = H-1-u
            xs = q[:, 1]; ys = (H - 1) - q[:, 0]
            b = [xs.min() / s + ox, ys.min() / s + oy, xs.max() / s + ox, ys.max() / s + oy]
            if (b[3] - b[1]) < 1.5 * (b[2] - b[0]) or len(text.strip()) < 2:
                continue  # only keep genuinely vertical multi-char strings
            over = [t for t in toks if t["rotation"] == 0 and _iou_box(b, t["box"]) > 0.05]
            # upright-pass fragments of vertical text are tall & thin; replace them with the rotated read
            if any((t["box"][3] - t["box"][1]) < 1.2 * (t["box"][2] - t["box"][0]) for t in over):
                continue
            toks = [t for t in toks if not any(t is o for o in over)]
            toks.append({"text": text, "box": [round(float(v), 1) for v in b], "score": round(sc, 4), "rotation": 90})
    toks = [t for t in toks if t["score"] >= min_score]
    toks.sort(key=lambda t: (round(t["box"][1] / 10), t["box"][0]))
    return toks


# ------------------------------------------------------------------------------------------ scale bar
UNIT_TO_NM = {"a": 0.1, "å": 0.1, "nm": 1.0, "um": 1e3, "µm": 1e3, "μm": 1e3, "mm": 1e6, "cm": 1e7, "m": 1e9}
LABEL_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(nm|[uµμ]m|mm|cm|Å|A|m)\b", re.I)


def norm_unit(u):
    u = u.strip().replace("µ", "u").replace("μ", "u")
    ul = u.lower()
    if ul in ("a", "å"):
        return "A"
    return ul if ul in ("nm", "um", "mm", "cm", "m") else ul


def get_exsclaim():
    if "exs" not in _models:
        import torchvision
        from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
        sys.path.insert(0, os.path.join(REPOS, "exsclaim"))
        from exsclaim.figures.models.crnn import CRNN
        from exsclaim.figures.scale import ctc
        det = torchvision.models.detection.fasterrcnn_resnet50_fpn(weights=None, weights_backbone=None)
        det.roi_heads.box_predictor = FastRCNNPredictor(det.roi_heads.box_predictor.cls_score.in_features, 3)
        det.load_state_dict(torch.load(PATHS["exsclaim_scale_bar_det"], map_location="cpu"))
        det.to(DEVICE).eval()
        cfg = json.load(open(os.path.join(REPOS, "exsclaim/exsclaim/figures/config/scale_label_reader.json")))["theta"]
        rec = CRNN(configuration=cfg)
        rec.load_state_dict(torch.load(PATHS["exsclaim_scale_label_rec"], map_location="cpu"))
        rec.to(DEVICE).eval()
        _models["exs"] = (det, rec, ctc)
    return _models["exs"]


def refine_bar(gray, box, pad=4):
    """Deterministic refinement: measure the horizontal extent of the solid bar inside a detected box.
    Returns (length_px, [x0,y0,x1,y1]) or None."""
    H, Wd = gray.shape
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    x0, y0, x1, y1 = max(0, x0 - pad), max(0, y0 - pad), min(Wd, x1 + pad), min(H, y1 + pad)
    crop = gray[y0:y1, x0:x1].astype(float)
    if crop.size == 0:
        return None
    best = None
    for polarity in ("bright", "dark"):
        m = crop > 200 if polarity == "bright" else crop < 55
        # longest run per row that does not touch the crop edges (a run spanning the whole crop is background)
        for r in range(m.shape[0]):
            row = m[r]
            if not row.any():
                continue
            d = np.diff(np.r_[0, row.astype(int), 0]); st = np.where(d == 1)[0]; en = np.where(d == -1)[0]
            ok = (st > 0) & (en < m.shape[1])
            if not ok.any():
                continue
            st, en = st[ok], en[ok]
            L = (en - st); k = int(L.argmax())
            if best is None or L[k] > best[0]:
                best = (int(L[k]), int(st[k]), int(en[k]), r, polarity)
    if best is None or best[0] < 5:
        return None
    L, s, e, r, pol = best
    m = crop > 200 if pol == "bright" else crop < 55
    rows = [rr for rr in range(m.shape[0]) if m[rr, s:e].mean() > 0.9]
    ry0, ry1 = (min(rows), max(rows)) if rows else (r, r)
    # bar length = median full-coverage run length over bar rows (robust to anti-aliased ends)
    lens = []
    for rr in range(ry0, ry1 + 1):
        row = m[rr]; d = np.diff(np.r_[0, row.astype(int), 0]); st = np.where(d == 1)[0]; en = np.where(d == -1)[0]
        if len(st):
            k = int((en - st).argmax()); lens.append(en[k] - st[k])
    length = float(np.median(lens)) if lens else float(L)
    return length, [x0 + s, y0 + ry0, x0 + e, y0 + ry1 + 1], pol


def fallback_scale_bar(img, warnings_):
    """Deterministic fallback: longest thin horizontal high-contrast bar in the bottom 45% + nearest number+unit (OCR)."""
    gray = np.asarray(img.convert("L")).astype(float)
    H, Wd = gray.shape
    best = None
    for pol in ("bright", "dark"):
        m = gray > 215 if pol == "bright" else gray < 40
        y_start = int(H * 0.55)
        for r in range(y_start, H):
            row = m[r]
            d = np.diff(np.r_[0, row.astype(int), 0]); st = np.where(d == 1)[0]; en = np.where(d == -1)[0]
            for s, e in zip(st, en):
                L = e - s
                if L < 0.03 * Wd or L > 0.9 * Wd:
                    continue
                # thickness: consecutive rows covering the same span
                t = 0
                while r + t < H and m[r + t, s:e].mean() > 0.9:
                    t += 1
                if 2 <= t <= max(30, int(0.05 * H)):
                    # contrast check: rows just above/below differ from bar
                    above = gray[max(0, r - 3), s:e].mean(); below = gray[min(H - 1, r + t + 2), s:e].mean()
                    bar = gray[r:r + t, s:e].mean()
                    contrast = min(abs(bar - above), abs(bar - below))
                    if contrast < 40:
                        continue
                    score = L * min(1.0, contrast / 100)
                    if best is None or score > best[0]:
                        best = (score, int(L), [int(s), int(r), int(e), int(r + t)], pol)
    if best is None:
        return None
    _, L, bbox, pol = best
    toks = ocr_tokens(img, rotated=False)
    cx, cy = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
    lab, bestd = None, 1e18
    for t in toks:
        mm = LABEL_RE.search(re.sub(r"(?<=\d)\s+(?=\d)", "", t["text"]))
        if not mm:
            continue
        tx, ty = (t["box"][0] + t["box"][2]) / 2, (t["box"][1] + t["box"][3]) / 2
        dd = (tx - cx) ** 2 + (ty - cy) ** 2
        if dd < bestd:
            bestd, lab = dd, (float(mm.group(1).replace(",", ".")), norm_unit(mm.group(2)), t)
    return {"bar_length_px": float(L), "bar_box": bbox, "polarity": pol, "label": lab}


def tool_read_scale_bar(img, args):
    warn = []
    import torchvision.transforms as T
    thr = float(args.get("score_threshold", 0.5))
    gray = np.asarray(img.convert("L"))
    bars, labels = [], []
    if args.get("method") == "fallback":  # force the deterministic path (testing / cross-check)
        o = {"boxes": torch.zeros(0, 4), "scores": torch.zeros(0), "labels": torch.zeros(0)}
    else:
        det, rec, ctc = get_exsclaim()
        with torch.no_grad():
            o = det([T.ToTensor()(img).to(DEVICE)])[0]
    tf = T.Compose([T.Resize((128, 512)), T.ToTensor(),
                    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
    for b, s, l in zip(o["boxes"].cpu().numpy(), o["scores"].cpu().numpy(), o["labels"].cpu().numpy()):
        if s < thr:
            continue
        b = [float(v) for v in b]
        if int(l) == 1:
            bars.append({"box": [round(v, 1) for v in b], "score": float(s)})
        elif int(l) == 2:
            crop = img.crop(tuple(int(round(v)) for v in b))
            with torch.no_grad():
                lp = rec(tf(crop).unsqueeze(0).to(DEVICE))
            mag, unit, conf = ctc.run_ctc(torch.exp(lp).squeeze(0).cpu(), "0123456789mMcCuUnN .A")
            ocr_txt = None
            # cross-check with RapidOCR on the label crop (helps with µ vs u etc.)
            tk = ocr_tokens(img, box=[b[0] - 12, b[1] - 12, b[2] + 12, b[3] + 12], rotated=False)
            if tk:
                ocr_txt = " ".join(t["text"] for t in sorted(tk, key=lambda t: t["box"][0]))
                ocr_txt = re.sub(r"(?<=\d)\s+(?=[\d.,])|(?<=[.,])\s+(?=\d)", "", ocr_txt)
            labels.append({"box": [round(v, 1) for v in b], "score": float(s), "crnn_value": float(mag),
                           "crnn_unit": unit.strip(), "crnn_confidence": float(conf), "ocr_text": ocr_txt})
    # suppress overlapping bar boxes (keep highest score)
    bars.sort(key=lambda d: -d["score"])
    keep = []
    for bb in bars:
        if all(_iou_box(bb["box"], k["box"]) < 0.3 for k in keep):
            keep.append(bb)
    bars = keep
    method = "exsclaim"
    result = None
    if bars:
        bar = bars[0]
        # pick label nearest to bar
        lab = None
        if labels:
            bc = np.array([(bar["box"][0] + bar["box"][2]) / 2, (bar["box"][1] + bar["box"][3]) / 2])
            lab = min(labels, key=lambda L_: np.sum((np.array([(L_["box"][0] + L_["box"][2]) / 2,
                                                              (L_["box"][1] + L_["box"][3]) / 2]) - bc) ** 2))
        ref = refine_bar(gray, bar["box"])
        box_len = bar["box"][2] - bar["box"][0]
        if ref and 0.7 * box_len <= ref[0] <= 1.15 * box_len:
            length, bbox, pol = ref
            length_src = "refined_pixel_run"
        else:
            length, bbox = box_len, bar["box"]
            length_src = "detector_box_width"
            warn.append("bar length taken from detector box width (refinement failed); expect a few % error")
        value, unit, lab_src = None, None, None
        if lab:
            if lab["crnn_value"] > 0:
                value, unit, lab_src = lab["crnn_value"], norm_unit(lab["crnn_unit"]), "exsclaim_crnn"
            m_ = LABEL_RE.search(lab["ocr_text"] or "")
            if m_:
                ov, ou = float(m_.group(1).replace(",", ".")), norm_unit(m_.group(2))
                if value is None:
                    value, unit, lab_src = ov, ou, "rapidocr"
                elif abs(ov - value) > 1e-9 or ou != unit:
                    warn.append(f"label disagreement: CRNN '{value} {unit}' vs OCR '{ov} {ou}'")
                    if lab["crnn_confidence"] < 0.5:
                        value, unit, lab_src = ov, ou, "rapidocr"
        result = {"bar_length_px": round(float(length), 2), "bar_length_source": length_src, "bar_box": bbox,
                  "bar_detector_score": round(bar["score"], 4), "label_box": lab["box"] if lab else None,
                  "label_value": value, "label_unit": unit, "label_source": lab_src,
                  "label_crnn_confidence": round(lab["crnn_confidence"], 4) if lab else None,
                  "label_ocr_text": lab["ocr_text"] if lab else None}
        if len(bars) > 1:
            warn.append(f"{len(bars)} scale-bar candidates detected; returned the highest-scoring one")
    if result is None or result["label_value"] is None:
        fb = fallback_scale_bar(img, warn)
        if fb and (result is None or fb["label"]):
            method = "fallback_deterministic" if result is None else "exsclaim+fallback_label"
            if result is None:
                result = {"bar_length_px": fb["bar_length_px"], "bar_length_source": "fallback_pixel_run",
                          "bar_box": fb["bar_box"], "bar_detector_score": None}
                warn.append("FALLBACK: EXSCLAIM detected no scale bar; used deterministic longest-bar detector")
            if fb["label"]:
                v, u, t = fb["label"]
                result.update({"label_value": v, "label_unit": u, "label_source": "rapidocr_fallback",
                               "label_box": t["box"], "label_ocr_text": t["text"]})
    if result is None:
        return {"values": None, "units": None, "confidence": 0.0, "warnings": warn + ["no scale bar found"],
                "method": method}
    v, u = result.get("label_value"), result.get("label_unit")
    if v and u in ("A", "nm", "um", "mm", "cm", "m"):
        nm = v * UNIT_TO_NM[u.lower() if u != "A" else "a"]
        result["label_length_nm"] = nm
        result["px_per_nm"] = result["bar_length_px"] / nm
        result["px_per_um"] = result["bar_length_px"] / (nm / 1e3)
        result["nm_per_px"] = nm / result["bar_length_px"]
    else:
        result.update({"px_per_nm": None, "px_per_um": None})
        warn.append("label not read; px_per_unit unavailable")
    conf = (result.get("bar_detector_score") or 0.5) * ((result.get("label_crnn_confidence") or 0.6) if v else 0.0)
    result["method"] = method
    result["all_candidates"] = {"bars": bars, "labels": labels}
    return {"values": result, "units": {"bar_length_px": "px", "px_per_nm": "px/nm", "px_per_um": "px/um",
                                        "nm_per_px": "nm/px", "label_length_nm": "nm"},
            "confidence": round(float(conf), 4), "warnings": warn, "method": method}


# ------------------------------------------------------------------------------------------- DePlot
DEPLOT_PROMPT = "Generate underlying data table of the figure below:"


def get_deplot():
    if "deplot" not in _models:
        import transformers.models.pix2struct.image_processing_pix2struct as A
        try:
            import transformers.models.pix2struct.image_processing_pil_pix2struct as B
        except Exception:
            B = None
        for mod in (A, B):
            if mod is not None and hasattr(mod, "render_text"):
                # transformers 5.x does not forward font_path; force the local font (no hub download at request time)
                mod.render_text = (lambda o: (lambda *a, **k: o(*a, **{**k, "font_path": PATHS["deplot_font"],
                                                                       "font_bytes": None})))(mod.render_text)
        from transformers import Pix2StructForConditionalGeneration, Pix2StructProcessor
        d = os.path.join(W, "deplot")
        proc = Pix2StructProcessor.from_pretrained(d)
        model = Pix2StructForConditionalGeneration.from_pretrained(d, use_safetensors=True).to(DEVICE).eval()
        _models["deplot"] = (proc, model)
    return _models["deplot"]


def _num(s):
    s2 = s.strip().replace(",", "").replace("%", "")
    try:
        return float(s2)
    except ValueError:
        return None


def parse_deplot(raw):
    lines = [l.strip() for l in re.split(r"<0x0A>|\n", raw) if l.strip()]
    title = None
    if lines and lines[0].upper().startswith("TITLE"):
        title = lines[0].split("|", 1)[1].strip() if "|" in lines[0] else ""
        lines = lines[1:]
    rows = [[c.strip() for c in l.split("|")] for l in lines]
    header = rows[0] if rows else []
    body = rows[1:]
    cols = {}
    for j, h in enumerate(header):
        key = h if h else f"col{j}"
        cols[key] = [(_num(r[j]) if j < len(r) else None) for r in body]
    return {"title": title, "header": header, "rows": body, "numeric_columns": cols}


def tool_chart_to_table(img, args):
    proc, model = get_deplot()
    inp = proc(images=img, text=args.get("prompt", DEPLOT_PROMPT), return_tensors="pt").to(DEVICE)
    with torch.no_grad():
        out = model.generate(**inp, max_new_tokens=int(args.get("max_new_tokens", 512)), do_sample=False, num_beams=1)
    raw = proc.decode(out[0], skip_special_tokens=True)
    parsed = parse_deplot(raw)
    warn = ["DePlot reads values from rendered ticks; it is unreliable on log axes and dense/overlapping series - "
            "cross-check with digitize_curve + axis calibration"]
    return {"values": {"raw_table": raw, "table": parsed}, "units": None, "confidence": None, "warnings": warn}


# ------------------------------------------------------------------------------------ curve digitizing
def get_lineformer():
    if "lf" not in _models:
        sys.path.insert(0, os.path.join(REPOS, "LineFormer"))
        import infer as lf_infer
        lf_infer.load_model(os.path.join(REPOS, "LineFormer", "lineformer_swin_t_config.py"), PATHS["lineformer"],
                            "cuda:0" if DEVICE == "cuda" else "cpu")
        _models["lf"] = lf_infer
    return _models["lf"]


def find_plot_area(arr):
    """Axes rectangle from long dark horizontal/vertical lines. Returns [x0,y0,x1,y1] or full image."""
    g = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    H, Wd = g.shape
    dark = g < 100
    rowf = dark.mean(1); colf = dark.mean(0)
    hr = np.where(rowf > 0.4)[0]; vc = np.where(colf > 0.4)[0]
    if len(hr) >= 1 and len(vc) >= 1:
        y0, y1 = (hr.min(), hr.max()) if hr.max() - hr.min() > 0.2 * H else (0, hr.max())
        x0, x1 = (vc.min(), vc.max()) if vc.max() - vc.min() > 0.2 * Wd else (vc.min(), Wd - 1)
        return [int(x0), int(y0), int(x1), int(y1)]
    return [0, 0, Wd - 1, H - 1]


def color_tracer(arr, box=None, max_series=8, min_pixels=150):
    H, Wd = arr.shape[:2]
    pa = box or find_plot_area(arr)
    x0, y0, x1, y1 = pa
    m = 4
    roi = np.zeros((H, Wd), bool); roi[y0 + m:y1 - m + 1, x0 + m:x1 - m + 1] = True
    # mask text (legends, annotations) found by OCR, extended left to cover legend handles
    for t in ocr_tokens(Image.fromarray(arr), rotated=False):
        bx = t["box"]; h = bx[3] - bx[1]
        roi[int(max(0, bx[1] - 2)):int(bx[3] + 3), int(max(0, bx[0] - 3.5 * h)):int(bx[2] + 3)] = False
    hsv = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV).astype(int)
    hue, sat, val = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    coloured = roi & (sat > 80) & (val > 60)
    darkpx = roi & (val < 90) & (sat <= 80)
    series = []
    # cluster coloured pixels by hue (OpenCV hue 0..179), deterministic histogram peak picking
    if coloured.sum() > 0:
        hist = np.bincount(hue[coloured].ravel(), minlength=180).astype(float)
        sm = np.convolve(np.r_[hist[-6:], hist, hist[:6]], np.ones(7) / 7, mode="same")[6:-6]
        peaks = [i for i in range(180) if sm[i] > 0 and sm[i] >= sm[(i - 1) % 180] and sm[i] > sm[(i + 1) % 180]]
        peaks = sorted(peaks, key=lambda i: -sm[i])
        chosen = []
        for p in peaks:
            if sm[p] * 7 < min_pixels:
                continue
            if all(min(abs(p - c), 180 - abs(p - c)) > 8 for c in chosen):
                chosen.append(p)
        for c in chosen[:max_series]:
            dh = np.minimum(np.abs(hue - c), 180 - np.abs(hue - c))
            series.append(("hue", c, coloured & (dh <= 7)))
    if darkpx.sum() >= min_pixels:
        series.append(("dark", None, darkpx))
    out = []
    for kind, c, mask in series:
        pts = []
        prev = None
        for x in range(x0, x1 + 1):
            ys = np.where(mask[:, x])[0]
            if len(ys) == 0:
                continue
            d = np.diff(np.r_[-10, ys]); starts = np.where(d > 1)[0]
            runs = np.split(ys, starts[1:]) if len(starts) > 1 else [ys]
            centers = [float(r.mean()) for r in runs]
            y = min(centers, key=lambda v: abs(v - prev)) if prev is not None else centers[0]
            prev = y
            pts.append([float(x), round(y, 2)])
        if len(pts) < 10:
            continue
        rgb = np.median(arr[mask], axis=0).astype(int).tolist()
        out.append({"points": pts, "color_rgb": rgb, "kind": kind, "n_pixels": int(mask.sum())})
    return out, pa


def subsample(pts, step):
    if step <= 1:
        return pts
    return pts[::step] + ([pts[-1]] if (len(pts) - 1) % step else [])


def tool_digitize_curve(img, args):
    arr = np.asarray(img)
    method = args.get("method", "lineformer")
    step = int(args.get("step", 1))
    warn = []
    series = []
    if method == "lineformer":
        try:
            lf = get_lineformer()
            ds, masks = lf.get_dataseries(arr[:, :, ::-1].copy(), to_clean=False,
                                          mask_kp_sample_interval=int(args.get("kp_interval", 10)), return_masks=True)
            for i, (line, mk) in enumerate(zip(ds, masks)):
                if not line:
                    continue
                pts = [[float(p["x"]), float(p["y"])] for p in line]
                mb = mk > 0
                rgb = np.median(arr[mb], axis=0).astype(int).tolist() if mb.any() else None
                series.append({"points": subsample(pts, step), "color_rgb": rgb, "n_mask_pixels": int(mb.sum())})
        except Exception as e:  # pragma: no cover
            warn.append(f"LineFormer failed ({type(e).__name__}: {e}); using colour tracer fallback")
            method = "color"
    if method == "color":
        ser, pa = color_tracer(arr, box=args.get("plot_box"))
        for s in ser:
            s["points"] = subsample(s["points"], step)
        series = ser
        warn.append("FALLBACK colour/darkness tracer (deterministic, not LineFormer); legend handles masked via OCR")
    else:
        pa = None
    warn.append("pixel polylines only; map to data with the orchestrator's axis calibration (y grows downward)")
    if args.get("return_overlay"):
        ov = arr.copy()
        pal = [(255, 0, 255), (0, 200, 255), (255, 128, 0), (0, 255, 0), (255, 0, 0), (0, 0, 255)]
        for i, s in enumerate(series):
            p = np.array(s["points"], dtype=np.int32).reshape(-1, 1, 2)
            cv2.polylines(ov, [p], False, pal[i % len(pal)], 2)
        images = {"overlay": png_b64(ov)}
    else:
        images = None
    return {"values": {"series": series, "n_series": len(series), "method": method, "plot_area_px": pa},
            "units": {"points": "px (x right, y down, origin top-left)"}, "confidence": None, "warnings": warn,
            "images": images, "method": method}


# ------------------------------------------------------------------------------------------ provenance
TOOLS = {
    "read_text": {"backing_model": "RapidOCR 1.4.4 (PaddleOCR PP-OCRv4 det/rec + mobile v2 cls, ONNX)",
                  "weights": []},
    "read_scale_bar": {"backing_model": f"EXSCLAIM! scale-bar FasterRCNN-R50-FPN + CRNN (commit {REPO_COMMITS['exsclaim'][:10]})",
                       "weights": ["exsclaim_scale_bar_det", "exsclaim_scale_label_rec"]},
    "chart_to_table": {"backing_model": "google/deplot (Pix2Struct)", "weights": ["deplot"]},
    "digitize_curve": {"backing_model": f"LineFormer Swin-T Mask2Former iter_3000 (commit {REPO_COMMITS['LineFormer'][:10]})",
                       "weights": ["lineformer"]},
}


def rapidocr_model_shas():
    import rapidocr_onnxruntime
    d = os.path.join(os.path.dirname(rapidocr_onnxruntime.__file__), "models")
    return {f: sha256_file(os.path.join(d, f)) for f in sorted(os.listdir(d)) if f.endswith(".onnx")}


def tool_weights_sha(tool):
    if tool == "read_text":
        return rapidocr_model_shas()
    return {k: sha256_file(PATHS[k]) for k in TOOLS[tool]["weights"]}


app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok", "family": "plots", "device": DEVICE, "cuda": torch.cuda.is_available(),
            "loaded": sorted(_models.keys())}


@app.get("/version")
def version():
    return {"worker": WORKER_VERSION, "device": DEVICE, "python": sys.version.split()[0],
            "packages": {p: pkg_version(p) for p in ["torch", "torchvision", "transformers", "rapidocr-onnxruntime",
                                                      "onnxruntime", "mmcv-full", "mmdet", "opencv-python-headless",
                                                      "numpy", "fastapi", "uvicorn"]},
            "repos": REPO_COMMITS,
            "weights_sha256": {t: tool_weights_sha(t) for t in TOOLS},
            "tools": {t: v["backing_model"] for t, v in TOOLS.items()}}


HANDLERS = {
    "read_text": lambda img, a: {"values": {"tokens": ocr_tokens(img, box=a.get("box"), rotated=a.get("rotated", True),
                                                                  upscale=a.get("upscale"),
                                                                  min_score=float(a.get("min_score", 0.3)))},
                                 "units": {"box": "px [x0,y0,x1,y1]"}, "confidence": None,
                                 "warnings": ["rotation=90 tokens come from a second pass on the image rotated 90 deg",
                                              "superscripts are flattened (10^4 is read as '104'); check log-axis ticks"]},
    "read_scale_bar": tool_read_scale_bar,
    "chart_to_table": tool_chart_to_table,
    "digitize_curve": tool_digitize_curve,
}


def _log(rec):
    with open(os.path.join(ROOT, "requests.log"), "a") as f:
        f.write(json.dumps(rec) + "\n")


def make_endpoint(name):
    async def ep(request: Request):
        t0 = time.time()
        body = await request.json()
        args = body.get("args") or {}
        seed = int(body.get("seed", 0))
        in_sha = None
        try:
            raw, img = decode_image(body["image_b64"])
            in_sha = hashlib.sha256(raw).hexdigest()
            with _lock:
                seed_all(seed)
                res = HANDLERS[name](img, args)
            method = res.pop("method", None)
            out = {"values": res.get("values"), "units": res.get("units"), "confidence": res.get("confidence"),
                   "warnings": res.get("warnings", []),
                   "provenance": {"tool": name, "tool_version": WORKER_VERSION,
                                  "backing_model": ("deterministic colour/darkness tracer (fallback, no model) + RapidOCR text masking"
                                                    if method == "color" else TOOLS[name]["backing_model"] + (f" [method={method}]" if method else "")),
                                  "weights_sha256": tool_weights_sha(name), "seed": seed,
                                  "device": "cpu" if (name == "read_text" or method == "color") else DEVICE}}
            if res.get("images"):
                out["images"] = res["images"]
            status = 200
        except Exception as e:
            out = {"values": None, "units": None, "confidence": None,
                   "warnings": [f"error: {type(e).__name__}: {e}"],
                   "provenance": {"tool": name, "tool_version": WORKER_VERSION, "seed": seed, "device": DEVICE}}
            status = 500
        _log({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "tool": name, "input_sha256": in_sha, "args": args,
              "seed": seed, "status": status, "duration_s": round(time.time() - t0, 3)})
        return JSONResponse(out, status_code=status)
    return ep


for _name in HANDLERS:
    app.add_api_route(f"/{_name}", make_endpoint(_name), methods=["POST"])


if __name__ == "__main__":
    import uvicorn
    if os.environ.get("PLOTS_PRELOAD", "0") == "1":
        get_ocr(); get_exsclaim(); get_deplot(); get_lineformer()
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
