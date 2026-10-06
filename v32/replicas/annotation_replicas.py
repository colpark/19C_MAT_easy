#!/usr/bin/env python3
"""annotation_replicas.py (Stage 5C, rule 5): choose the OCR preprocessing of the annotation reader on synthetic replicas, never on the real
panels. Two replica styles, 20 images each, sized like the real annotation panels:
  hrtem  lattice-fringe texture (sinusoidal fringes + grain noise, dark mean) with a light or dark label 'd(hkl)=0.xyz nm' or '0.xyz nm'
         (10-16 px DejaVu, sometimes over a coloured marker line) and a scale bar '5 nm'
  ftir   white panel, dotted coloured curves, vertical (rotated 90 deg) coloured labels '5xx.xxx' / '4xx.xx' next to dips, row labels 'x=0.0k'
Variants: v0 = current (3x upscale, upright + rotated 90 both ways, psm 11); v1 = v0 plus 4x upscale of the grayscale, Otsu threshold,
both polarities; v2 = v1 plus per-channel max-contrast (min RGB channel) for coloured text.
Score: recall of printed decimal numbers (exact text) and false numbers (OCR decimals not printed). Chosen: highest recall with zero
false decimals that equal another printed value's neighbour... (any false decimal is reported). usage: annotation_replicas.py"""
import json, math, random, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import pytesseract
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
NUM = re.compile(r'(?<![\d.])(\d+\.\d+)(?![\d.])')

def hrtem(rng):
    W, H = 294, 222; yy, xx = np.mgrid[0:H, 0:W]; th = rng.uniform(0, math.pi); per = rng.uniform(3, 6)
    img = 90 + 40 * np.sin((xx * math.cos(th) + yy * math.sin(th)) * 2 * math.pi / per) + np.random.RandomState(rng.randint(0, 10**6)).normal(0, 25, (H, W))
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGB').filter(ImageFilter.GaussianBlur(0.7)); d = ImageDraw.Draw(im)
    v = '%.3f' % rng.uniform(0.1, 0.4); hkl = rng.choice(['(400)', '(222)', '(220)', '(111)', '(311)'])
    txt = rng.choice([f'd{hkl}={v}nm', f'{v} nm', f'd = {v} nm']); fs = rng.randint(10, 16); col = rng.choice([(255, 255, 255), (230, 230, 230), (40, 40, 40), (200, 40, 40)])
    x, y = rng.randint(5, W - 9 * len(txt) - 5), rng.randint(20, H - 50)
    if rng.random() < 0.5: d.line([(x - 20, y + 30), (x + 15, y - 5)], fill=(220, 50, 50), width=2)
    d.text((x, y), txt, fill=col, font=ImageFont.truetype(FONT, fs)); d.line([(15, H - 25), (75, H - 25)], fill=(255, 255, 255), width=3)
    d.text((20, H - 22), '5 nm', fill=(255, 255, 255), font=ImageFont.truetype(FONT, 14))
    return im, [v]

def ftir(rng):
    W, H = 645, 844; im = Image.new('RGB', (W, H), 'white'); d = ImageDraw.Draw(im); vals = []
    cols = [(30, 30, 140), (30, 140, 30), (120, 30, 140), (30, 30, 200), (200, 30, 30), (20, 20, 20)]
    for r in range(6):
        y0 = 40 + r * 130; col = cols[r]
        for x in range(60, 620, 4):
            dip = 60 * math.exp(-((x - 420) / 25) ** 2) + 50 * math.exp(-((x - 600) / 12) ** 2); d.ellipse([x - 1.5, y0 + 20 + dip - 1.5, x + 1.5, y0 + 20 + dip + 1.5], fill=col)
        for xc, lo, hi, nd in ((420, 584, 600, 3), (600, 422, 425, 3)):
            v = '%.*f' % (rng.choice([2, 3]), rng.uniform(lo, hi)); vals.append(v)
            t = Image.new('RGBA', (90, 18), (255, 255, 255, 0)); ImageDraw.Draw(t).text((0, 0), v, fill=col + (255,), font=ImageFont.truetype(FONT, rng.randint(10, 13)))
            t = t.rotate(90, expand=True); im.paste(t, (xc - 16, y0 + 5), t)
        d.text((65, y0 + 95), f'x=0.0{r}', fill=(0, 0, 0), font=ImageFont.truetype(FONT, 11))
    return im.filter(ImageFilter.GaussianBlur(0.4)), vals

def variants(im):
    big = im.resize((im.size[0] * 3, im.size[1] * 3)); out = {'v0': [big]}
    g = ImageOps.grayscale(im).resize((im.size[0] * 4, im.size[1] * 4), Image.LANCZOS); a = np.asarray(g)
    from skimage.filters import threshold_otsu
    t = threshold_otsu(a); b = Image.fromarray(((a > t) * 255).astype(np.uint8)); out['v1'] = out['v0'] + [b, ImageOps.invert(b)]
    mn = Image.fromarray(np.asarray(im).min(2)).resize((im.size[0] * 4, im.size[1] * 4), Image.LANCZOS); out['v2'] = out['v1'] + [mn, ImageOps.invert(mn)]
    return out

def ocr(imgs):
    txt = ''
    for img in imgs:
        for rot in (0, -90, 90):
            txt += '\n' + pytesseract.image_to_string(img.rotate(rot, expand=True) if rot else img, config='--psm 11')
    return {m.group(1) for m in NUM.finditer(txt.replace(',', '.'))}

if __name__ == '__main__':
    res = {}
    for style, fn in (('hrtem', hrtem), ('ftir', ftir)):
        for k in range(20 if style == 'hrtem' else 8):
            rng = random.Random(f'{style}|{k}'); im, vals = fn(rng); V = variants(im)
            for name, imgs in V.items():
                got = ocr(imgs); r = res.setdefault((style, name), {'printed': 0, 'found': 0, 'false': 0, 'false_examples': []})
                r['printed'] += len(vals); r['found'] += sum(v in got for v in vals); fl = [g for g in got if g not in vals and not re.fullmatch(r'0\.0\d', g)]
                r['false'] += len(fl); r['false_examples'] += fl[:3]
    out = []
    for (style, name), r in sorted(res.items()):
        print(f"{style:6} {name}: recall {r['found']}/{r['printed']} = {r['found'] / r['printed']:.0%}  false decimals {r['false']}  e.g. {r['false_examples'][:5]}")
        out.append(dict(r, style=style, variant=name, recall=r['found'] / r['printed']))
    json.dump(out, open('/home/aid1/Documents/harbor/v32/replicas/annotation_check.json', 'w'), indent=1)
