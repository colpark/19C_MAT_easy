"""V8-0: compare grey_dilation of afmize's near-sharp image with afmize's own 2 nm tip image."""
import sys, numpy as np
sys.path.insert(0, ".")
from dilation import dilate
sharp, tip = np.loadtxt("check/sharp.tsv"), np.loadtxt("check/tip.tsv")
ours = dilate(sharp, radius=20.0, angle_deg=10.0, px=5.0)
mask = tip > 1.0  # on the filament
for name, img in [("no dilation", sharp), ("grey_dilation", ours)]:
    d = img - tip
    print(f"{name:14s} RMS {np.sqrt((d[mask]**2).mean()):6.2f} A  mean {d[mask].mean():6.2f} A  max|d| {np.abs(d).max():6.2f} A  (tip image max {tip.max():.1f} A, {mask.sum()} px)")
