"""Measure detection fraction and angle error of the render+segment pipeline vs pixel size (feeds simulate.py)."""
import sys, json, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R, sample as S, cost as C, fit as F
pxs = [0.4, 0.8, 1.2, 1.6, 2.0, 2.5, 3.0, 3.5]
ws = [S.sample_world("A", "HRm-ea", 18, 500 + s) for s in range(8)]
out = []
for px in pxs:
    npx = 256
    fov = px * npx
    found = tot = 0
    errs = []
    for w in ws:
        p = C.Plan("rods", fov, npx, 1, 1)
        r = R.scan_rods(w, p)
        pos, ang = S.to_scan_frame(w)
        h = fov / 2
        ins = (abs(pos[:, 0]) < h) & (abs(pos[:, 1]) < h)
        tp, ta = pos[ins] + h, ang[ins]
        L = w["scene"]["length_nm"]
        seg = F.segment_rods(r["img"], r["px_nm"], L)
        # rods inside margin only
        inner = ins & (abs(pos[:, 0]) < h - L) & (abs(pos[:, 1]) < h - L)
        tot += inner.sum()
        for x, y, a in seg:
            d = np.hypot(tp[:, 0] - x, tp[:, 1] - y)
            k = d.argmin()
            if d[k] < 6 and inner[np.where(ins)[0][k]]:
                errs.append(((a - ta[k] + 90) % 180) - 90)
    errs = np.array(errs)
    # robust sigma
    sig = 1.4826 * np.median(np.abs(errs - np.median(errs))) if len(errs) else float("nan")
    out.append(dict(px_nm=px, det_per_true=float(len(errs) / max(tot, 1)), sigma_theta_deg=float(sig), rms=float(np.sqrt(np.mean(errs ** 2))) if len(errs) else None, n=len(errs)))
    print(out[-1], flush=True)
json.dump(out, open(os.path.dirname(os.path.abspath(__file__)) + "/sim_calib.json", "w"), indent=1)
