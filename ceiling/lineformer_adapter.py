"""lineformer_adapter.py: LineFormer for the ceiling run, via the LineFormer worker already serving on node 2 (port 8103, built for the
MCP toolset: TheJaeLal/LineFormer 7952e27b, checkpoint iter_3000.pth sha256 ac03d7d5..., mmdet 2.28.2 / mmcv-full 1.7.2).
extract_lines(rgb) -> [(name, xs_px, ys_px)] in full-image pixel coordinates. Deterministic (seed 0). No language model."""
import base64, io, json, os, urllib.request
import numpy as np
from PIL import Image
URL = os.environ.get('LINEFORMER_URL', 'http://127.0.0.1:8103/digitize_curve')

def extract_lines(rgb):
    b = io.BytesIO(); Image.fromarray(np.asarray(rgb, dtype=np.uint8)).save(b, 'PNG')
    payload = {'image_b64': base64.b64encode(b.getvalue()).decode(), 'args': {'method': 'lineformer'}, 'seed': 0}
    r = json.loads(urllib.request.urlopen(urllib.request.Request(URL, json.dumps(payload).encode(), {'Content-Type': 'application/json'}), timeout=300).read())
    out = []
    for i, s in enumerate((r.get('values') or {}).get('series') or []):
        pts = s.get('points') or s.get('points_px') or []
        if len(pts) < 2: continue
        xs = np.array([p[0] for p in pts], float); ys = np.array([p[1] for p in pts], float)
        o = np.argsort(xs); out.append((f's{i}', xs[o], ys[o]))
    return out
