#!/usr/bin/env python3
"""make_replicas.py (A5): synthetic replicas of the 9 digitized panels in the crop's own style, with known truth.
Per panel and replica k = 0..4 (seed = hash(panel, k)):
 - canvas: crop size, white; frame, inward major/minor ticks on all four sides at the crop's calibrated positions; the same
   major tick labels (log decades as 10 + superscript where the crop prints them so, plain numbers otherwise); axis titles;
 - legend: five rows at the crop's legend row positions (line + marker + 'x=<value>' text, 'X=' for F4a);
 - series: the digitized points of each series times one random factor in [0.8, 1.2] per series (curve shape kept), drawn
   as thin connecting lines plus markers of the crop's shape, size and sampled colour, in the crop's legend order
   (x = 0 first, x = 0.04 last, so later series cover earlier ones);
 - no marker within 11 px + half a marker size of the crop's legend box (where the digitizer's 10 px legend pad would clip it) (the crops have none; the digitizer excludes that region);
 - marker overlap: the share of markers within one marker size of another series' marker must lie within 30% (relative,
   or 0.05 absolute) of the crop's share; up to 200 seeds are tried, the closest one is kept and logged;
 - blur 0.6 px and JPEG quality 90 (the crops' quantisation tables match quality ~90).
Truth per marker: data x, y, pixel centre and visible fraction (pixels of its own colour left after later series are drawn).
Writes v31_host/replicas/<panel>_r<k>/crops/<panel>.jpg and v31/replicas/truth/<panel>_r<k>.json."""
import sys as _pb_s, os as _pb_o
_pb_d = _pb_o.path.dirname(_pb_o.path.abspath(__file__))
while not _pb_o.path.exists(_pb_o.path.join(_pb_d, 'pbroot.py')) and _pb_o.path.dirname(_pb_d) != _pb_d: _pb_d = _pb_o.path.dirname(_pb_d)
_pb_s.path.insert(0, _pb_d)
from pbroot import ROOT, HOST
import hashlib, json, math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
V32 = f'{ROOT}'
PAPER = sys.argv[1] if len(sys.argv) > 1 else 'mo21'   # v3.2: per paper (papers/<paper>/, v32_host/papers/<paper>/)
V31 = f'{V32}/papers/{PAPER}'; HOST = f'{HOST}/papers/{PAPER}'
PANELS = ['F4a', 'F4b', 'F5a', 'F5b', 'F5c', 'F5d', 'F5e', 'F5f', 'F6a']
S = [0.0, 0.005, 0.01, 0.02, 0.04]
SHAPE = {0.0: 'tri_left', 0.005: 'square', 0.01: 'circle', 0.02: 'tri_up', 0.04: 'tri_down'}
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
font = lambda n: ImageFont.truetype(FONT, n)

def inv(cal, v):   # data -> pixel
    t = math.log10(v) if cal['log'] else v
    return (t - cal['b']) / cal['a']

def marker(d, shape, cx, cy, s, col):
    h = s / 2
    if shape == 'square': d.rectangle([cx - h, cy - h, cx + h, cy + h], fill=col)
    elif shape == 'circle': d.ellipse([cx - h, cy - h, cx + h, cy + h], fill=col)
    elif shape == 'tri_up': d.polygon([(cx, cy - h), (cx - h, cy + h), (cx + h, cy + h)], fill=col)
    elif shape == 'tri_down': d.polygon([(cx, cy + h), (cx - h, cy - h), (cx + h, cy - h)], fill=col)
    elif shape == 'tri_left': d.polygon([(cx - h, cy), (cx + h, cy - h), (cx + h, cy + h)], fill=col)

def overlap_share(series_px, size):
    allp = [(x, p) for x, pts in series_px.items() for p in pts]; n = hit = 0
    for x, p in allp:
        n += 1; hit += any(xx != x and math.hypot(p[0] - q[0], p[1] - q[1]) < size for xx, q in allp)
    return hit / max(n, 1)

def ticks(cal, lo_px, hi_px, majors_known):
    """major tick values covering the frame: log -> decades (+ 2..9 minors); linear -> the label step (+ half-step minors)."""
    lo_v, hi_v = sorted([(10 ** (cal['a'] * p + cal['b']) if cal['log'] else cal['a'] * p + cal['b']) for p in (lo_px, hi_px)])
    if cal['log']:
        maj = [10.0 ** e for e in range(math.floor(math.log10(lo_v)), math.ceil(math.log10(hi_v)) + 1) if lo_v <= 10.0 ** e <= hi_v]
        mnr = [m * 10.0 ** e for e in range(math.floor(math.log10(lo_v)) - 1, math.ceil(math.log10(hi_v)) + 1) for m in range(2, 10) if lo_v <= m * 10.0 ** e <= hi_v]
        return maj, mnr
    vals = sorted(v for _, v in majors_known); step = min(b - a for a, b in zip(vals, vals[1:]))
    k0 = math.ceil((lo_v - 1e-9) / step); k1 = math.floor((hi_v + 1e-9) / step)
    maj = [round(k * step, 6) for k in range(k0, k1 + 1)]
    mnr = [round((k + 0.5) * step, 6) for k in range(k0 - 1, k1 + 1) if lo_v <= (k + 0.5) * step <= hi_v]
    return maj, mnr

def label_text(v, cal, superscript):
    if cal['log'] and superscript: return ('10', str(int(round(math.log10(v)))))
    s = ('%g' % v); return (s, None)

def render(panel, k, dig, colors, cfg, rng):
    W, H = Image.open(f'{HOST}/crops/{panel}.jpg').size
    fr = dig['frame']; x0, x1, yb, yt = fr['x_left'], fr['x_right'], fr['y_bottom'], fr['y_top']
    xc, yc = dig['x_cal'], dig['y_cal']
    sup = panel in ('F5a',)   # F5a prints 10^1, 10^2, 10^3; F4a prints 1 and 10; F4b plain numbers
    im = Image.new('RGB', (W, H), 'white'); d = ImageDraw.Draw(im)
    d.rectangle([x0, yt, x1, yb], outline=(0, 0, 0), width=2)
    xmaj, xmin = ticks(xc, x0, x1, xc['pairs']); ymaj, ymin = ticks(yc, yb, yt, yc['pairs'])
    if panel == 'F4b': ymaj = [50, 100, 150, 200, 250]; ymin = []
    f_lab = font(17)
    for v in xmaj:
        p = inv(xc, v)
        if not x0 + 2 < p < x1 - 2: continue
        for yy, s in ((yb, -1), (yt, 1)): d.line([(p, yy), (p, yy + s * 7)], fill=(0, 0, 0), width=2)
        t = '%g' % v; tw = d.textlength(t, font=f_lab); d.text((p - tw / 2, yb + 6), t, fill=(0, 0, 0), font=f_lab)
    for v in xmin:
        p = inv(xc, v)
        if x0 + 2 < p < x1 - 2:
            for yy, s in ((yb, -1), (yt, 1)): d.line([(p, yy), (p, yy + s * 4)], fill=(0, 0, 0), width=1)
    for v in ymaj:
        p = inv(yc, v)
        if not yt + 1 < p < yb - 1: continue
        for xx, s in ((x0, 1), (x1, -1)): d.line([(xx, p), (xx + s * 7, p)], fill=(0, 0, 0), width=2)
        main, ex = label_text(v, yc, sup); tw = d.textlength(main, font=f_lab)
        if ex: d.text((x0 - tw - 16, p - 10), main, fill=(0, 0, 0), font=f_lab); d.text((x0 - 15, p - 16), ex, fill=(0, 0, 0), font=font(11))
        else: d.text((x0 - tw - 6, p - 10), main, fill=(0, 0, 0), font=f_lab)
    for v in ymin:
        p = inv(yc, v)
        if yt + 1 < p < yb - 1:
            for xx, s in ((x0, 1), (x1, -1)): d.line([(xx, p), (xx + s * 4, p)], fill=(0, 0, 0), width=1)
    d.text(((x0 + x1) / 2 - 20, yb + 30), 'T (K)', fill=(0, 0, 0), font=font(19))
    ttl = Image.new('RGBA', (160, 26), (255, 255, 255, 0)); ImageDraw.Draw(ttl).text((0, 0), {'F4a': 'n_H', 'F4b': 'mu_H', 'F5a': 'rho', 'F5b': 'S', 'F5c': 'PF', 'F5d': 'kappa', 'F5e': 'kappa_e', 'F5f': 'kappa_L+b', 'F6a': 'ZT'}[panel], fill=(0, 0, 0), font=font(19))
    ttl = ttl.rotate(90, expand=True); im.paste(ttl, (max(2, x0 - 85), int((yt + yb) / 2 - 60)), ttl)
    # legend rows
    ent = dig['legend']['entries']; ranks = [S.index(float(kk)) for kk in ent]; cys = [v['cy'] for v in ent.values()]
    b_, a_ = np.polyfit(ranks, cys, 1) if len(ent) >= 2 else (22.0, cys[0] - 22 * ranks[0])
    pre = 'X=' if panel == 'F4a' else 'x='; size = {x: dig['_msize'][x] for x in S}
    # text start: entry right edge minus the label's width (the recorded x0 can include the swatch); swatch inside the frame
    lx = max(max(v['x1'] - d.textlength(pre + ('%g' % float(kk)), font=f_lab) for kk, v in ent.items()), x0 + 50)
    for r, x in enumerate(S):
        cy = a_ + b_ * r; col = colors[x]
        d.line([(lx - 42, cy), (lx - 6, cy)], fill=col, width=1); marker(d, SHAPE[x], lx - 24, cy, size[x], col)
        d.text((lx, cy - 10), pre + ('%g' % x), fill=(0, 0, 0), font=f_lab)
    # series
    fac = {x: rng.uniform(0.8, 1.2) for x in S}; truth = {}; pxs = {}
    for x in S:
        pts = sorted(dig['series'][str(x)], key=lambda p: p['x'])
        tp = []
        for p in pts:
            v = p['y'] * fac[x]
            if yc['log'] is False and v < 0 and p['y'] > 0: v = p['y']
            py = inv(yc, v); px = inv(xc, p['x'])
            if yt + 4 < py < yb - 4: tp.append({'T': p['x'], 'value': v, 'px': px, 'py': py})
        truth[x] = tp; pxs[x] = [(q['px'], q['py']) for q in tp]
    return im, d, truth, pxs, fac

def draw_series(im, truth, colors, sizes):
    d = ImageDraw.Draw(im); lab = np.zeros((im.size[1], im.size[0]), int) - 1; idx = 0; owners = []
    for x in S:
        tp = truth[x]; col = colors[x]; light = tuple(int(c + (255 - c) * 0.35) for c in col)
        for a, b in zip(tp, tp[1:]): d.line([(a['px'], a['py']), (b['px'], b['py'])], fill=light, width=1)
        for q in tp:
            m = Image.new('L', im.size, 0); marker(ImageDraw.Draw(m), SHAPE[x], q['px'], q['py'], sizes[x], 255)
            mm = np.asarray(m) > 127; lab[mm] = idx; owners.append((x, q, int(mm.sum()))); idx += 1
            marker(d, SHAPE[x], q['px'], q['py'], sizes[x], col)
    for i, (x, q, area) in enumerate(owners): q['visible'] = float((lab == i).sum() / max(area, 1))

if __name__ == '__main__':
    os.makedirs(f'{V31}/replicas/truth', exist_ok=True); summary = {}
    cfg = None
    for panel in PANELS:
        dig = json.load(open(f'{V31}/digitized/{panel}.json')); rgb = np.asarray(Image.open(f'{HOST}/crops/{panel}.jpg').convert('RGB')).astype(int)
        colors, sizes = {}, {}
        strict_all = [p['size_px'] for v in dig['series'].values() for p in v if not p.get('occluded')]
        for x in S:
            strict = [p for p in dig['series'][str(x)] if not p.get('occluded')]
            pts = strict or dig['series'][str(x)]
            cs = [rgb[int(round(p['py'])), int(round(p['px']))] for p in pts]
            colors[x] = tuple(int(c) for c in np.median(cs, axis=0))
            sizes[x] = float(np.median([p['size_px'] for p in strict])) if strict else float(np.median(strict_all))   # occluded sizes are doubled
        dig['_msize'] = sizes
        orig_px = {x: [(p['px'], p['py']) for p in dig['series'][str(x)]] for x in S}; msz = float(np.median(list(sizes.values())))
        target = overlap_share(orig_px, msz); summary[panel] = {'orig_overlap': target, 'colors': colors, 'sizes': sizes, 'replicas': []}
        for k in range(5):
            best = None
            for t in range(200):
                seed = int(hashlib.sha256(f'{panel}:{k}:{t}'.encode()).hexdigest()[:8], 16); rng = random.Random(seed)
                im, d, truth, pxs, fac = render(panel, k, dig, colors, cfg, rng)
                ov = overlap_share(pxs, msz); dist = abs(ov - target)
                lb = dig['legend']['box']   # no marker inside the legend box (+12 px): the crops have none there and the digitizer excludes it
                mg = 11 + msz / 2   # a marker of half-size h is clipped by the digitizer's 10 px legend pad when within 10 + h
                if lb and any(lb[0] - mg <= px <= lb[2] + mg and lb[1] - mg <= py <= lb[3] + mg for v in pxs.values() for px, py in v): dist += 10
                if best is None or dist < best[0]: best = (dist, seed, ov, fac)
                if dist <= max(0.3 * target, 0.05): break
            dist, seed, ov, fac = best; rng = random.Random(seed)
            im, d, truth, pxs, fac = render(panel, k, dig, colors, cfg, rng); draw_series(im, truth, colors, sizes)
            im = im.filter(ImageFilter.GaussianBlur(0.6))
            od = f'{HOST}/replicas/{panel}_r{k}/crops'; os.makedirs(od, exist_ok=True); im.save(f'{od}/{panel}.jpg', quality=90)
            json.dump({'panel': panel, 'k': k, 'seed': seed, 'factors': {str(x): f for x, f in fac.items()}, 'overlap': ov, 'orig_overlap': target,
                       'truth': {str(x): v for x, v in truth.items()}}, open(f'{V31}/replicas/truth/{panel}_r{k}.json', 'w'), indent=1)
            summary[panel]['replicas'].append({'k': k, 'seed': seed, 'overlap': ov})
        print(panel, 'orig overlap %.2f' % target, 'replicas', ['%.2f' % r['overlap'] for r in summary[panel]['replicas']])
    json.dump(summary, open(f'{V31}/replicas/make_summary.json', 'w'), indent=1, default=str)
