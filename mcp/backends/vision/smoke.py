import base64, io, json, sys, time, os
sys.path.insert(0, os.path.expanduser("~/mcp/vision"))
import numpy as np, cv2
from PIL import Image
import worker
from worker import Req, run_tool

rng = np.random.default_rng(0)
def b64(a):
    buf = io.BytesIO(); Image.fromarray(a).save(buf, format="PNG"); return base64.b64encode(buf.getvalue()).decode()

# 1. circles
circ = np.full((512, 512, 3), 30, np.uint8)
for (x, y, r, c) in [(120,120,60,200),(380,140,80,150),(250,380,90,230),(420,420,40,120),(100,400,50,180)]:
    cv2.circle(circ, (x, y), r, (c, c, c), -1)
# 2. grains: Voronoi with dark boundaries, 80 seeds, random grey levels
H = W = 768; n = 80
seeds = rng.uniform(0, W, size=(n, 2))
yy, xx = np.mgrid[0:H, 0:W]
d = np.stack([(xx - sx)**2 + (yy - sy)**2 for sx, sy in seeds])
lab = d.argmin(0)
grey = rng.integers(110, 220, size=n)
g = grey[lab].astype(np.uint8)
edge = (cv2.dilate(lab.astype(np.float32), np.ones((3,3))) != cv2.erode(lab.astype(np.float32), np.ones((3,3))))
g[edge] = 25
g = cv2.GaussianBlur(g, (3,3), 0)
grains = np.dstack([g]*3)
true_mean_area = H*W/n
# 3. atom lattice: hexagonal-ish (graphene-like) gaussian blobs, spacing ~ 12 px
A = 256; a = 12.0
img = np.zeros((A, A), np.float32); pts = []
for i in range(-2, 40):
    for j in range(-2, 40):
        x = i*a + (j % 2)*a/2; y = j*a*np.sqrt(3)/2
        if 0 <= x < A and 0 <= y < A: pts.append((x, y))
for x, y in pts:
    img += np.exp(-((xx[:A,:A]-x)**2 + (yy[:A,:A]-y)**2)/(2*1.8**2))
img = img/img.max() + rng.normal(0, 0.05, img.shape)
atoms = np.dstack([np.uint8(np.clip(img, 0, 1)*255)]*3)
print("truth: circles=5, grains=%d mean_area=%.0f px, atoms=%d nn=%.1f px" % (n, true_mean_area, len(pts), a))

def call(tool, im, args={}, show=lambda v: v):
    t = time.time(); out = run_tool(tool, Req(image_b64=b64(im), args=args, seed=0)); t1 = time.time() - t
    t = time.time(); run_tool(tool, Req(image_b64=b64(im), args=args, seed=0)); t2 = time.time() - t
    print(f"== {tool} {args} cold={t1:.2f}s warm={t2:.2f}s device={out['provenance']['device']}")
    print("   ", json.dumps(show(out.get("values")))[:600], "warnings:", out["warnings"])
    for k, v in (out.get("images") or {}).items():
        open(os.path.expanduser(f"~/mcp/vision/smoke_{tool}_{k}.png"), "wb").write(base64.b64decode(v))
    return out

short = lambda v: {k: (vv[:8] if isinstance(vv, list) else vv) for k, vv in v.items()} if v else v
call("segment", circ, {"mode": "auto"}, short)
call("segment", circ, {"mode": "points", "points": [[120,120],[380,140]]}, short)
call("segment_microstructure", grains, {}, short)
call("grain_size_astm", grains, {}, short)
call("grain_size_astm", grains, {"px_per_um": 2.0}, short)
call("grain_boundary_map", grains, {})
o = call("classify_modality_embed", grains, {}, lambda v: {"dim": v["dim"], "head": v["embedding"][:5]})
o2 = run_tool("classify_modality_embed", Req(image_b64=b64(grains), args={}, seed=0))
print("    embed deterministic:", o["values"]["embedding"] == o2["values"]["embedding"], "load:", worker._MODELS.get("micronet_load"))
call("find_atoms", atoms, {"px_per_nm": 12/0.142}, short)
call("find_atoms", atoms, {"model": "BFO"}, short)
