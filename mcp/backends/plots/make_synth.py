"""Generate synthetic smoke-test images + ground truth for the plots family."""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.expanduser("~/mcp/plots/smoke/data")
os.makedirs(OUT, exist_ok=True)
gt = {}


def save(fig, ax, name, series, extra=None):
    fig.canvas.draw()
    path = f"{OUT}/{name}.png"
    fig.savefig(path, dpi=100)
    H = fig.get_size_inches()[1] * 100
    # ground-truth pixel polylines (y measured from top) for each series
    px = {}
    for lab, (x, y) in series.items():
        d = ax.transData.transform(np.c_[x, y])
        px[lab] = [[float(a), float(H - b)] for a, b in d]
    xl, yl = sorted(ax.get_xlim()), sorted(ax.get_ylim())
    xt = [t.get_text() for t, v in zip(ax.get_xticklabels(), ax.get_xticks()) if t.get_text() and xl[0] - 1e-9 <= v <= xl[1] + 1e-9]
    yt = [t.get_text() for t, v in zip(ax.get_yticklabels(), ax.get_yticks()) if t.get_text() and yl[0] * (1 - 1e-9) <= v <= yl[1] * (1 + 1e-9)]
    gt[name] = {"series": {k: {"x": list(map(float, v[0])), "y": list(map(float, v[1]))} for k, v in series.items()},
                "pixel_polylines": px, "xlabel": ax.get_xlabel(), "ylabel": ax.get_ylabel(),
                "title": ax.get_title(), "xticks": xt, "yticks": yt, **(extra or {})}
    plt.close(fig)


# 1. linear axes, single dark series
fig, ax = plt.subplots(figsize=(6.4, 4.8))
x = np.arange(0, 11, 1.0); y = 2.0 * x + 3.0
ax.plot(x, y, color="black", lw=2, label="sample A")
ax.set_xlabel("Temperature (K)"); ax.set_ylabel("Current (mA)"); ax.set_title("Linear plot")
ax.legend()
save(fig, ax, "linear", {"sample A": (x, y)})

# 2. log y axis
fig, ax = plt.subplots(figsize=(6.4, 4.8))
x = np.arange(1, 9, 1.0); y = 10.0 ** (x / 2.0)
ax.semilogy(x, y, color="tab:blue", lw=2, label="decay")
ax.set_xlabel("Time (s)"); ax.set_ylabel("Counts"); ax.set_title("Log plot")
save(fig, ax, "logy", {"decay": (x, y)}, {"yscale": "log"})

# 3. two coloured series
fig, ax = plt.subplots(figsize=(6.4, 4.8))
x = np.linspace(0, 10, 11); y1 = np.sin(x / 2) * 5 + 10; y2 = 0.5 * x + 2
ax.plot(x, y1, color="tab:red", lw=2, label="red series")
ax.plot(x, y2, color="tab:green", lw=2, label="green series")
ax.set_xlabel("Voltage (V)"); ax.set_ylabel("Signal (a.u.)"); ax.set_title("Two series")
ax.legend(loc="upper left")
save(fig, ax, "two_series", {"red series": (x, y1), "green series": (x, y2)})

# 4. bar chart (DePlot sweet spot)
fig, ax = plt.subplots(figsize=(6.4, 4.8))
cats = ["A", "B", "C", "D"]; vals = [12.0, 30.0, 21.0, 7.0]
ax.bar(cats, vals, color="tab:blue")
ax.set_ylabel("Yield (%)"); ax.set_title("Bar chart")
for i, v in enumerate(vals):
    ax.text(i, v + 0.5, f"{v:g}", ha="center")
fig.savefig(f"{OUT}/bar.png", dpi=100); plt.close(fig)
gt["bar"] = {"categories": cats, "values": vals}

# 5. synthetic SEM-like image with a 10 um scale bar
rng = np.random.default_rng(0)
W, H = 1024, 768
base = rng.normal(110, 25, (H, W))
yy, xx = np.mgrid[0:H, 0:W]
for _ in range(60):  # bright particles
    cx, cy, r = rng.uniform(0, W), rng.uniform(0, H - 120), rng.uniform(8, 40)
    base += 90 * np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r * r))
from scipy.ndimage import gaussian_filter
img = np.clip(gaussian_filter(base, 1.5), 0, 255).astype(np.uint8)
im = Image.fromarray(img).convert("RGB")
d = ImageDraw.Draw(im)
bar_px = 200  # 10 um = 200 px -> 20 px/um
x0, y0 = 780, 715
d.rectangle([x0, y0, x0 + bar_px - 1, y0 + 7], fill=(255, 255, 255))
font = None
for f in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
    if os.path.exists(f):
        font = ImageFont.truetype(f, 34); break
font = font or ImageFont.load_default()
d.text((x0 + bar_px / 2, y0 - 8), "10 µm", fill=(255, 255, 255), font=font, anchor="ms")
im.save(f"{OUT}/sem_10um.png")
gt["sem_10um"] = {"bar_length_px": bar_px, "label_value": 10, "label_unit": "um", "px_per_um": bar_px / 10}

# 6. second SEM with black bar on white strip, 500 nm
im2 = Image.fromarray(img[:, :800]).convert("RGB")
im2 = im2.crop((0, 0, 800, 620))
canvas = Image.new("RGB", (800, 700), (255, 255, 255)); canvas.paste(im2, (0, 0))
d = ImageDraw.Draw(canvas)
d.rectangle([40, 660, 40 + 150 - 1, 666], fill=(0, 0, 0))
d.text((40 + 75, 652), "500 nm", fill=(0, 0, 0), font=font.font_variant(size=26) if hasattr(font, "font_variant") else font, anchor="ms")
canvas.save(f"{OUT}/sem_500nm.png")
gt["sem_500nm"] = {"bar_length_px": 150, "label_value": 500, "label_unit": "nm", "px_per_nm": 150 / 500}

json.dump(gt, open(f"{OUT}/ground_truth.json", "w"), indent=1)
print("wrote", sorted(os.listdir(OUT)))
