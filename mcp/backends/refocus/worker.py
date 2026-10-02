#!/usr/bin/env python3
"""PanelBench MCP backend worker: family `refocus` (BNL SEM refocus MAE-MoE).

Wraps github.com/mirajucr/naturecomm_refocus_release (commit 225aeca, NO LICENSE file:
internal evaluation only). The upstream code is imported from ~/mcp/refocus/repo at
runtime and is NOT copied here. Weights live in ~/mcp/refocus/weights on node 2.

Tools: POST /sem_refocus, POST /sem_embed. Port 8102.
"""
import base64
import hashlib
import io
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

ROOT = Path(os.environ.get("REFOCUS_ROOT", Path.home() / "mcp" / "refocus"))
sys.path.insert(0, str(ROOT / "repo"))

import numpy as np  # noqa: E402
import torch  # noqa: E402
from fastapi import FastAPI, HTTPException  # noqa: E402
from PIL import Image  # noqa: E402

PORT = 8102
FAMILY = "refocus"
TOOL_VERSION = "0.1.0"
REPO_COMMIT = "225aeca0366fb6d12f6280d9e4f3bbd35c44d5b1"
LICENSE = "none stated, internal only"
VIT_DIR = ROOT / "weights" / "vit-mae-large"
CKPT_DIR = ROOT / "weights" / "checkpoints"
CHECKPOINTS = {
    "zero_shot": "zero_shot_e4_public_review.ckpt",
    "edge10": "fine_tuned_edge10_e4_public_review.ckpt",
    "charb": "fine_tuned_charb_e4_public_review.ckpt",
}
TILE, OVERLAP, NUM_EXPERTS, TOP_K = 224, 8, 4, 1
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

torch.use_deterministic_algorithms(True, warn_only=True)
torch.backends.cudnn.benchmark = False

_SHA_CACHE = {}
_MODELS = {}


def sha256_file(path):
    path = Path(path)
    if not path.exists():
        return None
    key = (str(path), path.stat().st_mtime, path.stat().st_size)
    if key not in _SHA_CACHE:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 22), b""):
                h.update(chunk)
        _SHA_CACHE[key] = h.hexdigest()
    return _SHA_CACHE[key]


def ckpt_path(name):
    if name not in CHECKPOINTS:
        raise HTTPException(400, f"checkpoint must be one of {sorted(CHECKPOINTS)}")
    p = CKPT_DIR / CHECKPOINTS[name]
    if not p.exists():
        raise HTTPException(503, f"checkpoint file missing: {p} (Google Drive folder requires sign-in)")
    return p


def get_model(name):
    if name not in _MODELS:
        import refocus_inference as ri  # upstream code, imported not copied

        # torch>=2.6 defaults torch.load(weights_only=True); upstream calls torch.load without it.
        orig_load = torch.load

        def _load(*a, **k):
            k.setdefault("weights_only", False)
            return orig_load(*a, **k)

        torch.load = _load
        try:
            _MODELS[name] = ri.RefocusInferencer(
                str(ckpt_path(name)), str(VIT_DIR), DEVICE, num_experts=NUM_EXPERTS, top_k=TOP_K
            )
        finally:
            torch.load = orig_load
    return _MODELS[name]


def seed_all(seed):
    torch.manual_seed(seed)
    np.random.seed(seed % (2**32))


def decode_image(b64):
    raw = base64.b64decode(b64)
    return raw, Image.open(io.BytesIO(raw)).convert("RGB")


def png_b64(tensor, inf):
    img = (tensor * inf.std + inf.mean).clamp(0.0, 1.0)
    arr = (img.permute(1, 2, 0).cpu().numpy() * 255.0 + 0.5).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def n_windows(w, h):
    import math

    pw, ph = w + (-w) % TILE, h + (-h) % TILE
    s = TILE - OVERLAP
    return math.ceil((pw - OVERLAP) / s) * math.ceil((ph - OVERLAP) / s)


def provenance(tool, ckname, seed):
    return {
        "tool": tool,
        "tool_version": TOOL_VERSION,
        "backing_model": f"naturecomm_refocus_release@{REPO_COMMIT[:7]} MAE-MoE (vit-mae-large, {NUM_EXPERTS} experts, top-{TOP_K}) / {ckname}",
        "weights_sha256": {
            "checkpoint": sha256_file(CKPT_DIR / CHECKPOINTS[ckname]),
            "vit-mae-large/pytorch_model.bin": sha256_file(VIT_DIR / "pytorch_model.bin"),
        },
        "seed": seed,
        "device": DEVICE,
    }


def log_request(tool, raw, args, dt):
    rec = {
        "time": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "tool": tool,
        "input_sha256": hashlib.sha256(raw).hexdigest() if raw else None,
        "args": args,
        "duration_s": round(dt, 3),
    }
    with open(ROOT / "requests.log", "a") as f:
        f.write(json.dumps(rec) + "\n")


def refocus_image(inf, image):
    return inf.run_full_image(image, tile_size=TILE, overlap=OVERLAP)


@torch.no_grad()
def embed_image(inf, image):
    """Mean-pooled encoder features (patch tokens, CLS excluded) over all sliding windows."""
    import refocus_inference as ri

    padded, _ = ri.pad_to_multiple(image, TILE)
    feats = []
    for _, _, patch in ri.tile_sliding(padded, TILE, OVERLAP):
        pv = inf.processor(patch, return_tensors="pt")["pixel_values"].to(inf.device)
        hs = inf.model.model.vit(pv, return_dict=True).last_hidden_state  # (1, 1+N, 1024)
        feats.append(hs[:, 1:, :].mean(dim=1))
    return torch.cat(feats, 0).mean(0).float().cpu().numpy()


app = FastAPI(title="refocus worker")


@app.get("/health")
def health():
    missing = [v for v in CHECKPOINTS.values() if not (CKPT_DIR / v).exists()]
    return {
        "ok": not missing and (VIT_DIR / "pytorch_model.bin").exists(),
        "family": FAMILY,
        "device": DEVICE,
        "missing_checkpoints": missing,
    }


@app.get("/version")
def version():
    import transformers

    return {
        "family": FAMILY,
        "tools": {"sem_refocus": TOOL_VERSION, "sem_embed": TOOL_VERSION},
        "license": {"sem_refocus": LICENSE, "sem_embed": LICENSE},
        "repo": {"url": "https://github.com/mirajucr/naturecomm_refocus_release", "commit": REPO_COMMIT},
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "checkpoint_files": CHECKPOINTS,
        "weights_sha256": {
            **{k: sha256_file(CKPT_DIR / v) for k, v in CHECKPOINTS.items()},
            "vit-mae-large/pytorch_model.bin": sha256_file(VIT_DIR / "pytorch_model.bin"),
        },
    }


@app.post("/sem_refocus")
def sem_refocus(req: dict):
    t0 = time.time()
    args = req.get("args") or {}
    seed = int(req.get("seed", 0))
    ck = args.get("checkpoint", "zero_shot")
    if "image_b64" not in req:
        raise HTTPException(400, "image_b64 required")
    raw, image = decode_image(req["image_b64"])
    inf = get_model(ck)
    seed_all(seed)
    out = refocus_image(inf, image)
    resp = {
        "values": {"restored": True, "checkpoint": ck, "windows": n_windows(*image.size)},
        "units": None,
        "confidence": None,
        "warnings": ["license: none stated, internal only"],
        "provenance": provenance("sem_refocus", ck, seed),
        "images": {"restored": png_b64(out, inf)},
    }
    log_request("sem_refocus", raw, args, time.time() - t0)
    return resp


@app.post("/sem_embed")
def sem_embed(req: dict):
    t0 = time.time()
    args = req.get("args") or {}
    seed = int(req.get("seed", 0))
    ck = args.get("checkpoint", "zero_shot")
    if "image_b64" not in req:
        raise HTTPException(400, "image_b64 required")
    raw, image = decode_image(req["image_b64"])
    inf = get_model(ck)
    seed_all(seed)
    vec = embed_image(inf, image)
    resp = {
        "values": {"embedding": [float(x) for x in vec], "dim": int(vec.shape[0]), "checkpoint": ck,
                   "pooling": "mean over patch tokens (CLS excluded) and over all 224px windows"},
        "units": None,
        "confidence": None,
        "warnings": ["license: none stated, internal only"],
        "provenance": provenance("sem_embed", ck, seed),
    }
    log_request("sem_embed", raw, args, time.time() - t0)
    return resp


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=PORT)
