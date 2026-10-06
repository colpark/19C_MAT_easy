#!/usr/bin/env python3
"""tem_replicas.py (Stage 5C recovery): synthetic HRTEM lattice images and SAED ring patterns with known spacings, styled on the real
panels (size, scale-bar length/polarity/thickness, label text, colour tint), and the A5 gate in d-spacing units for lattice.py.
HRTEM: rendered 4x and LANCZOS-downsampled (fringes finer than the pixel grid vanish, as in a resampled figure), low-frequency contrast,
  one dominant fringe set over 50-90% of the frame (truth d) and optionally a weaker second set, Gaussian noise, blur, panel letter, an
  annotation with a marker, scale bar + label, JPEG q85. Visible = period >= 2.5 px.
SAED: dark field, beam spot with halo, six spinel rings d = a / sqrt(N), N = 8, 11, 16, 24, 27, 32 (diffuse ring + random spots),
  hkl labels with arrows, thin grey bar '5 1/nm', optional magenta tint, JPEG q85. Visible ring = full circle inside the frame.
Gate per style: >= 95% of reads within 2u, |mean error/u| <= 0.5, >= 80% of visible features read; a read of an invisible feature counts.
Calibration uses the declared bar label and bar half (profile path); OCR success of the label is reported separately.
usage: tem_replicas.py   -> replicas/tem_check.json"""
import json, math, random, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
V32 = '/home/aid1/Documents/harbor/v32'; sys.path.insert(0, V32)
import lattice as LT
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'; FONTB = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
STYLES = [
 {'id': 'hrtem_s039g', 'kind': 'hrtem', 'size': (294, 222), 'bar': (55, 80), 'label': '5 nm', 'pol': 'bright', 'thick': 2, 'd': (0.18, 0.55)},
 {'id': 'hrtem_s039h', 'kind': 'hrtem', 'size': (291, 220), 'bar': (45, 75), 'label': '10 nm', 'pol': 'bright', 'thick': 2, 'd': (0.3, 0.9)},
 {'id': 'hrtem_t042', 'kind': 'hrtem', 'size': (540, 417), 'bar': (50, 70), 'label': '5 nm', 'pol': 'dark', 'thick': 4, 'd': (0.12, 0.6), 'light': True},
 {'id': 'saed_s039j', 'kind': 'saed', 'size': (283, 221), 'bar': (50, 65), 'label': '5 1/nm', 'tint': None},
 {'id': 'saed_s039k', 'kind': 'saed', 'size': (279, 221), 'bar': (50, 65), 'label': '5 1/nm', 'tint': (1.0, 0.45, 1.0)},
 {'id': 'saed_stretched', 'kind': 'saed', 'size': (283, 221), 'bar': (50, 65), 'label': '5 1/nm', 'tint': None, 'stretch': (1.1, 1.3)},
 {'id': 'saed_wide_bar', 'kind': 'saed', 'size': (283, 221), 'bar': (65, 80), 'label': '5 1/nm', 'tint': None, 'a': (1.10, 1.20)},
]
N_REP = 12

def bar(d, W, H, sc, L, label, pol, thick, x0=None):
    col = (255, 255, 255) if pol == 'bright' else (0, 0, 0); x0 = x0 if x0 is not None else 0.07 * W; y = H - 0.07 * H
    d.rectangle([x0 * sc, (y - thick / 2) * sc, (x0 + L) * sc - 1, (y + thick / 2) * sc - 1], fill=col)
    d.text(((x0 + 0.2 * L) * sc, (y - 18) * sc), label, fill=col, font=ImageFont.truetype(FONTB, 13 * sc))

def hrtem(st, rng):
    W, H = st['size']; sc = 4; L = rng.uniform(*st['bar']); ppu = L / float(st['label'].split()[0])
    dv = rng.uniform(*st['d']); per = dv * ppu; th = rng.uniform(0, math.pi)
    yy, xx = np.mgrid[0:H * sc, 0:W * sc] / sc
    rs = np.random.RandomState(rng.randint(0, 10 ** 6))
    low = ndi_smooth(rs.normal(0, 1, (H // 8 + 2, W // 8 + 2)), (H * sc, W * sc))
    mask = (low > np.quantile(low, rng.uniform(0.1, 0.5))).astype(float)
    f1 = np.cos(2 * math.pi * (xx * math.cos(th) + yy * math.sin(th)) / per)
    img = (150 if st.get('light') else 110) + 35 * low + rng.uniform(8, 25) * f1 * mask   # fringe amplitude as in the real crops
    if rng.random() < 0.5:
        d2 = dv * rng.uniform(1.25, 1.6); th2 = th + rng.uniform(0.5, 1.2)
        img += rng.uniform(4, 10) * np.cos(2 * math.pi * (xx * math.cos(th2) + yy * math.sin(th2)) / (d2 * ppu)) * (1 - mask)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGB'); d = ImageDraw.Draw(im)
    pol = st['pol']; bar(d, W, H, sc, L, st['label'], pol, st['thick'], x0=(0.83 * W - L) if st.get('light') else None)
    d.text((8 * sc, 4 * sc), '(g)', fill=(80, 80, 80), font=ImageFont.truetype(FONTB, 16 * sc))
    ax, ay = rng.uniform(0.3, 0.6) * W, rng.uniform(0.4, 0.6) * H
    d.line([(ax - 12) * sc, (ay - 8) * sc, (ax + 12) * sc, (ay + 8) * sc], fill=(200, 60, 60), width=2 * sc)
    d.text(((ax + 18) * sc, ay * sc), 'd=%.3fnm' % dv, fill=(255, 255, 255), font=ImageFont.truetype(FONTB, 9 * sc))
    im = im.resize((W, H), Image.LANCZOS)
    im = Image.fromarray(np.clip(np.asarray(im).astype(float) + rs.normal(0, 10, (H, W, 1)), 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.4))
    return im, {'d': dv, 'period_px': per, 'visible': per >= 2.5, 'bar_px': L, 'label': st['label']}

def ndi_smooth(a, shape):
    from scipy import ndimage as ndi
    z = ndi.zoom(a, (shape[0] / a.shape[0], shape[1] / a.shape[1]), order=3)[:shape[0], :shape[1]]; return (z - z.mean()) / (z.std() + 1e-9)

def saed(st, rng):
    W, H = st['size']; sc = 2; L = rng.uniform(*st['bar']); ppi = L / 5.0; a = rng.uniform(*st.get('a', (0.82, 0.86)))   # 'a' range keeps rings inside the frame for long bars
    Ns = [8, 11, 16, 24, 27, 32]; ds = [a / math.sqrt(n) for n in Ns]; cx, cy = rng.uniform(0.45, 0.55) * W, rng.uniform(0.40, 0.46) * H   # as in the real F4j/F4k: rings well inside the frame
    yy, xx = np.mgrid[0:H * sc, 0:W * sc] / sc; r = np.hypot(yy - cy, xx - cx); rs = np.random.RandomState(rng.randint(0, 10 ** 6))
    img = 8 + 240 * np.exp(-(r / 6) ** 2) + 60 / (1 + (r / 10) ** 2)
    ang = np.arctan2(yy - cy, xx - cx)
    for k, dk in enumerate(ds):
        rk = ppi / dk; amp = rng.uniform(25, 60) * (1 - 0.08 * k)
        img += amp * 0.5 * np.exp(-((r - rk) / 0.9) ** 2)
        for _ in range(int(rng.uniform(15, 35))):
            t = rng.uniform(-math.pi, math.pi); sx, sy = cx + rk * math.cos(t), cy + rk * math.sin(t)
            img += amp * 1.5 * np.exp(-(((xx - sx) ** 2 + (yy - sy) ** 2) / 1.0))
    img += rs.normal(0, 4, img.shape)
    g = np.clip(img, 0, 255); tint = st.get('tint') or (1, 1, 1)
    im = Image.fromarray(np.stack([np.clip(g * t, 0, 255) for t in tint], -1).astype(np.uint8)); d = ImageDraw.Draw(im)
    lc = tuple(int(200 * t) for t in tint); f = ImageFont.truetype(FONTB, 9 * sc)
    for k, (dk, lab) in enumerate(zip(ds, ['(220)', '(311)', '(400)', '(422)', '(511)', '(440)'])):
        t = -math.pi / 2 - 0.5 + 0.35 * k if k < 3 else math.pi / 2 + 0.6 - 0.35 * (k - 3); rk = ppi / dk
        tx, ty = cx + (rk + 18) * math.cos(t), min(cy + (rk + 18) * math.sin(t), 0.8 * H)   # labels stay clear of the scale bar, as in the real panels
        d.line([tx * sc, ty * sc, (cx + (rk + 3) * math.cos(t)) * sc, (cy + (rk + 3) * math.sin(t)) * sc], fill=lc, width=sc)
        d.text(((tx - 14) * sc, (ty - (12 if ty < cy else -2)) * sc), lab, fill=lc, font=f)
    x0 = 0.07 * W; y = H - 0.08 * H; d.rectangle([x0 * sc, (y - 0.5) * sc, (x0 + L) * sc - 1, (y + 0.5) * sc - 1], fill=lc)
    d.text(((x0 + 2) * sc, (y - 17) * sc), '5 1/nm', fill=lc, font=ImageFont.truetype(FONTB, 12 * sc))
    d.text((6 * sc, 4 * sc), '(j)', fill=(90, 90, 90), font=ImageFont.truetype(FONTB, 16 * sc))
    im = im.resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.4))
    rmax = min(cx, cy, W - cx, 0.92 * H - cy)
    if st.get('stretch'):   # figure scaled anisotropically after the bar was drawn: must be refused
        f = rng.uniform(*st['stretch']); big = im.resize((int(W * f), H), Image.LANCZOS); x0 = (big.size[0] - W) // 2; im = big.crop((x0, 0, x0 + W, H))
        return im, {'d': ds, 'visible': [False] * 6, 'bar_px': L, 'label': '5 1/nm', 'n': 6, 'expect_refusal': True}
    return im, {'d': ds, 'visible': [ppi / dk < 0.97 * rmax for dk in ds], 'bar_px': L, 'label': '5 1/nm', 'n': 6}

if __name__ == '__main__':
    import io
    res, ocr_ok, out = {}, {}, []
    for st in STYLES:
        for k in range(N_REP):
            rng = random.Random(f"{st['id']}|{k}"); im, t = (hrtem if st['kind'] == 'hrtem' else saed)(st, rng)
            buf = io.BytesIO(); im.save(buf, 'JPEG', quality=85); im = Image.open(io.BytesIO(buf.getvalue())).convert('RGB')
            rgb = np.asarray(im); gray = rgb.mean(2); cal = LT.calibrate(rgb, gray, declared=t['label'], where='right' if st.get('light') else 'left')
            ocr_ok.setdefault(st['id'], []).append(bool(cal and cal.get('ocr_agrees')))
            R = res.setdefault(st['id'], {'err': [], 'miss': 0, 'flag': 0, 'n': 0, 'bar_err_px': []})
            if cal: R['bar_err_px'].append(cal['bar_px'] - t['bar_px'])
            if st['kind'] == 'hrtem':
                R['n'] += 1; m = LT.hrtem(gray, cal['px_per_unit'], region=(0, 0, gray.shape[1], int(0.85 * gray.shape[0])), bar_px=cal['bar_px']) if cal else None
                if m is None: R['flag' if not t['visible'] else 'miss'] += 1
                else: R['err'].append((m['d'] - t['d']) / m['u'])
            else:
                rings = LT.saed(gray, 6 if t.get('expect_refusal') else sum(t['visible']), cal['px_per_unit'],   # n = printed hkl labels = rings shown
                                bar_px=cal['bar_px'], exclude=[cal['bar_box']]) if cal else None
                R['refused'] = R.get('refused', 0) + isinstance(rings, dict); R['expect_refusal'] = bool(t.get('expect_refusal'))
                if isinstance(rings, dict): rings = None
                vis = [dk for dk, v in zip(t['d'], t['visible']) if v]; R['n'] += 6; R['flag'] += 6 - len(vis)
                if rings is None: R['miss'] += len(vis)
                else:
                    for dk, m in zip(sorted(vis, reverse=True), rings): R['err'].append((m['d'] - dk) / m['u'])   # rank order: largest d = smallest radius
    print(f"{'style':14} {'n':>3} {'read':>4} {'flag':>4} {'cov':>5} {'<=2u':>5} {'bias':>6} {'bar err px (mean, max)':>22} {'OCR label':>9} refused gate")
    for sid, R in res.items():
        e = np.array(R['err']); vis = R['n'] - R['flag']; cov = len(e) / max(vis, 1); w = float((np.abs(e) <= 2).mean()) if len(e) else 0; b = float(e.mean()) if len(e) else float('nan')
        ok = cov >= 0.8 and w >= 0.95 and abs(b) <= 0.5
        if R.get('expect_refusal'): ok = R.get('refused', 0) == N_REP and len(e) == 0   # stretched: every replica refused, no read
        be = np.array(R['bar_err_px'] or [np.nan])
        print(f"{sid:14} {R['n']:3d} {len(e):4d} {R['flag']:4d} {cov:5.0%} {w:5.0%} {b:6.2f} {be.mean():10.2f} {np.abs(be).max():10.2f} {sum(ocr_ok[sid])}/{N_REP:<6} {R.get('refused', 0):5d}  {'PASS' if ok else 'FAIL'}")
        out.append({'style': sid, 'n': R['n'], 'read': len(e), 'flagged_invisible': R['flag'], 'coverage': cov, 'within_2u': w, 'bias_u': b, 'pass': bool(ok),
                    'bar_err_px_mean': float(np.nanmean(be)), 'refused': R.get('refused', 0), 'ocr_label_ok': sum(ocr_ok[sid]), 'errors_u': [round(float(x), 2) for x in e]})
    json.dump(out, open(f'{V32}/replicas/tem_check.json', 'w'), indent=1)
