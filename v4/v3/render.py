#!/usr/bin/env python3
"""render.py (A1): uniform-style re-render of a T2 target panel from its digitized points. Same image size, frame, tick positions,
tick labels and scale type as the crop (from the digitizer's calibration); all five series in one gray, one marker shape (circle,
the panel's median marker size), thin gray connecting lines; no legend. Letters A-E in a column right of the plot, each tied by a
leader line to a ringed anchor marker of its series (the series' rightmost marker >= 9 px from every marker of the other series).
Deterministic: no randomness here (letters come from the caller)."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'; FONTB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
TITLE = {'F4a': 'n_H (10^19 cm^-3)', 'F4b': 'μ_H (cm² V⁻¹ s⁻¹)', 'F5a': 'ρ (μΩ m)', 'F5b': 'S (μV K⁻¹)', 'F5c': 'PF (μW cm⁻¹ K⁻²)',
         'F5d': 'κ (W m⁻¹ K⁻¹)', 'F5e': 'κ_e (W m⁻¹ K⁻¹)', 'F5f': 'κ_L + κ_b (W m⁻¹ K⁻¹)', 'F6a': 'ZT'}
GRAY, LINE = (70, 70, 70), (160, 160, 160)

def inv(cal, v):
    t = math.log10(v) if cal['log'] else v
    return (t - cal['b']) / cal['a']

def _ticks(cal, lo_px, hi_px, pairs):
    lo_v, hi_v = sorted([(10 ** (cal['a'] * p + cal['b']) if cal['log'] else cal['a'] * p + cal['b']) for p in (lo_px, hi_px)])
    if cal['log']:
        maj = [10.0 ** e for e in range(math.floor(math.log10(lo_v)), math.ceil(math.log10(hi_v)) + 1) if lo_v <= 10.0 ** e <= hi_v]
        mnr = [m * 10.0 ** e for e in range(math.floor(math.log10(lo_v)) - 1, math.ceil(math.log10(hi_v)) + 1) for m in range(2, 10) if lo_v <= m * 10.0 ** e <= hi_v]
        return maj, mnr
    vals = sorted(v for _, v in pairs); step = min(b - a for a, b in zip(vals, vals[1:]))
    k0 = math.ceil((lo_v - 1e-9) / step); k1 = math.floor((hi_v + 1e-9) / step)
    return [round(k * step, 6) for k in range(k0, k1 + 1)], [round((k + 0.5) * step, 6) for k in range(k0 - 1, k1 + 1) if lo_v <= (k + 0.5) * step <= hi_v]

def target_image(panel, dig, size, letters_of):
    W, H = size; fr = dig['frame']; x0, x1, yb, yt = fr['x_left'], fr['x_right'], fr['y_bottom'], fr['y_top']
    xc, yc = dig['x_cal'], dig['y_cal']
    im = Image.new('RGB', (W, H), 'white'); d = ImageDraw.Draw(im); f = ImageFont.truetype(FONT, 17)
    d.rectangle([x0, yt, x1, yb], outline=(0, 0, 0), width=2)
    xmaj, xmin = _ticks(xc, x0, x1, xc['pairs']); ymaj, ymin = _ticks(yc, yb, yt, yc['pairs'])
    if panel == 'F4b': ymaj, ymin = [50, 100, 150, 200, 250], []
    for v in xmaj:
        p = inv(xc, v)
        if x0 + 2 < p < x1 - 2:
            for yy, s in ((yb, -1), (yt, 1)): d.line([(p, yy), (p, yy + s * 7)], fill=(0, 0, 0), width=2)
            t = '%g' % v; d.text((p - d.textlength(t, font=f) / 2, yb + 6), t, fill=(0, 0, 0), font=f)
    for v in xmin:
        p = inv(xc, v)
        if x0 + 2 < p < x1 - 2:
            for yy, s in ((yb, -1), (yt, 1)): d.line([(p, yy), (p, yy + s * 4)], fill=(0, 0, 0), width=1)
    for v in ymaj:
        p = inv(yc, v)
        if yt + 1 < p < yb - 1:
            for xx, s in ((x0, 1), (x1, -1)): d.line([(xx, p), (xx + s * 7, p)], fill=(0, 0, 0), width=2)
            if yc['log'] and panel == 'F5a':
                d.text((x0 - 36, p - 10), '10', fill=(0, 0, 0), font=f); d.text((x0 - 15, p - 16), str(int(round(math.log10(v)))), fill=(0, 0, 0), font=ImageFont.truetype(FONT, 11))
            else:
                t = '%g' % v; d.text((x0 - d.textlength(t, font=f) - 6, p - 10), t, fill=(0, 0, 0), font=f)
    for v in ymin:
        p = inv(yc, v)
        if yt + 1 < p < yb - 1:
            for xx, s in ((x0, 1), (x1, -1)): d.line([(xx, p), (xx + s * 4, p)], fill=(0, 0, 0), width=1)
    d.text(((x0 + x1) / 2 - 20, yb + 30), 'T (K)', fill=(0, 0, 0), font=ImageFont.truetype(FONT, 19))
    ttl = Image.new('RGBA', (260, 26), (255, 255, 255, 0)); ImageDraw.Draw(ttl).text((0, 0), TITLE[panel], fill=(0, 0, 0), font=ImageFont.truetype(FONT, 18))
    ttl = ttl.rotate(90, expand=True); im.paste(ttl, (max(2, x0 - 80), int((yt + yb) / 2 - 130)), ttl)
    sizes = [p['size_px'] for v in dig['series'].values() for p in v if not p.get('occluded')]; ms = float(np.median(sizes)) if sizes else 8.0
    pts = {float(k): sorted(v, key=lambda p: p['px']) for k, v in dig['series'].items()}
    for x in sorted(pts):
        for a, b in zip(pts[x], pts[x][1:]): d.line([(a['px'], a['py']), (b['px'], b['py'])], fill=LINE, width=1)
    for x in sorted(pts):
        for p in pts[x]: d.ellipse([p['px'] - ms / 2, p['py'] - ms / 2, p['px'] + ms / 2, p['py'] + ms / 2], fill=GRAY)
    allp = [(x, p) for x, v in pts.items() for p in v]; anchor = {}
    for x, v in pts.items():
        clear = [p for p in v if all(math.hypot(p['px'] - q['px'], p['py'] - q['py']) >= 9 for xx, q in allp if xx != x)]
        anchor[x] = max(clear or v, key=lambda p: p['px'])
    tx = x1 + 4 if W - x1 >= 17 else x1 - 17
    order = sorted(anchor, key=lambda x: anchor[x]['py']); ys = []
    for x in order: ys.append(max(anchor[x]['py'] - 8, (ys[-1] + 17) if ys else -1e9))
    over = ys[-1] + 16 - (yb - 2) if ys else 0
    if over > 0: ys = [y - over for y in ys]
    fb = ImageFont.truetype(FONTB, 14); placed = {}
    for x, ty in zip(order, ys):
        p = anchor[x]; d.line([(p['px'] + 6, p['py']), (tx - 1, ty + 7)], fill=(0, 0, 0), width=1)
        d.ellipse([p['px'] - 7, p['py'] - 7, p['px'] + 7, p['py'] + 7], outline=(0, 0, 0), width=2)
        d.rectangle([tx - 1, ty - 1, tx + 11, ty + 15], fill=(255, 255, 255), outline=(0, 0, 0))
        d.text((tx + 1, ty - 1), letters_of[x], fill=(0, 0, 0), font=fb); placed[letters_of[x]] = {'x': x, 'anchor_px': [p['px'], p['py']], 'label_xy': [tx, ty]}
    return im, placed
