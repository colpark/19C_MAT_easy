"""Scale bar detection on a micrograph crop: find a thin horizontal bar, then read the length label next to it.

Returns {px_per_unit, unit, recip, bar_px, label_value, bar_box, label_box, score} or None.
Classical image processing plus OCR (no learned weights), so the result is deterministic.
Steps: (1) bar candidates = horizontal line segments in very bright or very dark masks after a horizontal opening
(this removes end ticks and texture); (2) labels from the global OCR tokens; (3) if no label pairs with a bar, OCR a
binarized window around each bar (single text line); (4) pick the closest bar and label pair.
"""
import re
import numpy as np
from scipy import ndimage as ndi
from PIL import Image
from common import ocr_numbers_with_units, LEN_UNITS, RECIP_UNITS, norm_unit


def _bars(gray):
    h, w = gray.shape
    out = []
    k = max(9, int(0.02 * w))
    for pol, mask in (('bright', gray > 185), ('dark', gray < 60)):
        op = ndi.binary_opening(mask, structure=np.ones((1, k)))
        lab, n = ndi.label(op)
        if n == 0 or n > 5000:
            continue
        for sl in ndi.find_objects(lab):
            if sl is None:
                continue
            ys, xs = sl
            bh, bw = ys.stop - ys.start, xs.stop - xs.start
            if bw < max(15, 0.03 * w) or bw > 0.85 * w:
                continue
            if bh > max(3, 0.035 * h) or bw / max(bh, 1) < 6:
                continue
            if op[sl].mean() < 0.6:
                continue
            # a bar should stand out from its surroundings (not a long edge of a bright particle)
            y0, y1 = max(ys.start - 3, 0), min(ys.stop + 3, h)
            ring = np.concatenate([gray[y0:ys.start, xs].ravel(), gray[ys.stop:y1, xs].ravel()])
            contrast = abs(gray[sl].mean() - ring.mean()) if ring.size else 0
            if contrast < 40:
                continue
            out.append(dict(x0=xs.start, x1=xs.stop, y0=ys.start, y1=ys.stop, len=bw, pol=pol, contrast=float(contrast)))
    return out


def _labels_from_pairs(pairs):
    labels = []
    for p in pairs:
        u = norm_unit(p['unit'])
        m = re.match(r'^(1/nm|nm-1|nm|um|μm|µm|pm|mm|å|cm)', u)
        u = m.group(1) if m else u
        u = {'um': 'μm', 'µm': 'μm'}.get(u, u)
        if u in LEN_UNITS.values() or u in LEN_UNITS:
            labels.append(dict(value=p['value'], unit=LEN_UNITS.get(u, u), box=p['box'], recip=False))
        elif u in RECIP_UNITS:
            labels.append(dict(value=p['value'], unit=RECIP_UNITS[u], box=p['box'], recip=True))
    return labels


def _text_line(txt, max_glyph):
    """Keep one horizontal line of glyph-sized components: drop blobs cut by the window border, then keep the
    largest group of components that share a vertical center and a similar height (the label), plus dots inside it."""
    lab, n = ndi.label(txt)
    comps = []
    H, W = txt.shape
    for i, sl in enumerate(ndi.find_objects(lab), 1):
        if sl is None:
            continue
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        if y0 == 0 or y1 == H:
            continue
        gh, gw = y1 - y0, x1 - x0
        if gh > max_glyph or gw > 2 * max_glyph or (lab[sl] == i).sum() < 3:
            continue
        comps.append(dict(i=i, sl=sl, cy=(y0 + y1) / 2, h=gh, x0=x0, x1=x1, y0=y0, y1=y1))
    keep = np.zeros_like(txt)
    big = [c for c in comps if c['h'] >= 4]
    best = []
    for c in big:
        grp = [d for d in big if abs(d['cy'] - c['cy']) <= 0.35 * c['h'] and 0.5 <= d['h'] / c['h'] <= 2.0]
        if len(grp) > len(best):
            best = grp
    if len(best) < 2:
        return keep
    gy0, gy1 = min(d['y0'] for d in best), max(d['y1'] for d in best)
    gx0, gx1 = min(d['x0'] for d in best), max(d['x1'] for d in best)
    for c in comps:
        if c in best or (c['y0'] >= gy0 - 2 and c['y1'] <= gy1 + 2 and c['x0'] >= gx0 - 2 and c['x1'] <= gx1 + 2):
            keep[c['sl']] |= lab[c['sl']] == c['i']
    return keep


def _ocr_window(gray, x0, y0, x1, y1, pol, max_glyph, up=4):
    import pytesseract
    win = gray[y0:y1, x0:x1]
    if win.size == 0 or min(win.shape) < 6:
        return []
    big = np.asarray(Image.fromarray(win.astype(np.uint8)).resize((win.shape[1] * up, win.shape[0] * up), Image.BICUBIC)).astype(float)
    out = []
    thresholds = (150, 200, 120) if pol == 'bright' else (100, 60, 130)
    for thr in thresholds:
        txt = (big > thr) if pol == 'bright' else (big < thr)
        keep = _text_line(txt, max_glyph * up)
        if keep.sum() < 10 * up:
            continue
        img = Image.fromarray(np.pad(np.where(keep, 0, 255).astype(np.uint8), 20, constant_values=255))
        d = pytesseract.image_to_data(img, config='--psm 7', output_type=pytesseract.Output.DICT)
        toks = []
        for i, t in enumerate(d['text']):
            t = (t or '').strip()
            if not t:
                continue
            bx0, by0 = x0 + (d['left'][i] - 20) / up, y0 + (d['top'][i] - 20) / up
            bx1, by1 = bx0 + d['width'][i] / up, by0 + d['height'][i] / up
            toks.append(dict(text=t, x0=bx0, y0=by0, x1=bx1, y1=by1, cx=(bx0 + bx1) / 2, cy=(by0 + by1) / 2, conf=float(d['conf'][i])))
        labels = _labels_from_pairs(ocr_numbers_with_units(toks))
        if labels:
            conf = float(np.mean([t['conf'] for t in toks if t['conf'] >= 0] or [0]))
            for L in labels:
                L['conf'] = conf
            out += labels
            break
    return out


def _local_labels(gray, b):
    """Read the label in tight windows above, below and to the right of one bar (single text line each)."""
    h, w = gray.shape
    max_glyph = int(0.06 * h) + 4
    span = (max(b['x0'] - int(0.3 * b['len']) - 6, 0), min(b['x1'] + int(0.3 * b['len']) + 6, w))
    wins = []
    for lh in (int(0.035 * h) + 4, int(0.06 * h) + 6):
        wins += [(span[0], max(b['y0'] - lh, 0), span[1], max(b['y0'] - 1, 0)),
                 (span[0], min(b['y1'] + 1, h), span[1], min(b['y1'] + lh, h)),
                 (min(b['x1'] + 2, w), max(b['y0'] - lh // 2, 0), min(b['x1'] + b['len'] + 10, w), min(b['y1'] + lh // 2, h))]
    labels = []
    for (x0, y0, x1, y1) in wins:
        labels += _ocr_window(gray, x0, y0, x1, y1, b['pol'], max_glyph)
    labels.sort(key=lambda L: -L.get('conf', 0))
    return labels[:1]


def _pair(bars, labels):
    best = None
    for L in labels:
        if L['value'] <= 0:
            continue
        lb = L['box']
        for b in bars:
            dx = max(0, max(b['x0'] - lb['x1'], lb['x0'] - b['x1']))
            dy = max(0, max(b['y0'] - lb['y1'], lb['y0'] - b['y1']))
            dist = dx + dy
            if dist > 4 * (lb['y1'] - lb['y0'] + 6):
                continue
            score = dist + 0.01 * abs((b['x0'] + b['x1']) / 2 - lb['cx'])
            if best is None or score < best['score']:
                best = dict(score=score, bar=b, label=L)
    return best


def find_scale_bar(rgb, gray, toks):
    bars = _bars(gray)
    if not bars:
        return None
    best = _pair(bars, _labels_from_pairs(ocr_numbers_with_units(toks)))
    if best is None:
        h = gray.shape[0]
        for b in sorted(bars, key=lambda b: -(b['contrast'] + 100 * (b['y0'] > 0.75 * h) + 0.5 * b['len']))[:8]:
            labels = _local_labels(gray, b)
            cand = _pair([b], labels)
            if cand:
                best = cand
                break
    if best is None:
        return None
    b, L = best['bar'], best['label']
    return dict(px_per_unit=b['len'] / L['value'], unit=L['unit'], recip=L['recip'], bar_px=b['len'], label_value=L['value'],
                bar_box=[b['x0'], b['y0'], b['x1'], b['y1']], label_box=[L['box']['x0'], L['box']['y0'], L['box']['x1'], L['box']['y1']],
                score=best['score'])
