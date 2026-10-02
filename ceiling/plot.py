"""Plot chain: axes, tick labels, axis calibration (linear or log), series extraction by color, bars, curve metrics.

Classical and deterministic. An optional learned digitizer (LineFormer) plugs in through CEILING_DIGITIZER=lineformer and
contributes extra series in pixel space, mapped through the same axis calibration.
"""
import os, re, itertools
import numpy as np
from scipy import ndimage as ndi
from scipy.signal import find_peaks
from PIL import Image
from common import ocr_tokens, NUMTOK, _clean_num, cand, unit_norm_or_none
from grade_v3 import unit_info


# ---------------------------------------------------------------- axes
def _longest_run(b):
    best = (0, 0, 0)
    start = None
    for i, v in enumerate(np.append(b, False)):
        if v and start is None:
            start = i
        elif not v and start is not None:
            if i - start > best[0]:
                best = (i - start, start, i)
            start = None
    return best


def find_axes(gray):
    h, w = gray.shape
    dark = gray < 110
    xa = None
    for y in range(h - 1, int(0.3 * h), -1):
        L, a, b = _longest_run(dark[y])
        if L >= 0.4 * w:
            xa = (y, a, b)
            break
    ya = None
    for x in range(0, int(0.7 * w)):
        L, a, b = _longest_run(dark[:, x])
        if L >= 0.4 * h:
            ya = (x, a, b)
            break
    if not xa or not ya:
        return None
    y_row, xl, xr = xa
    x_col, yt, yb = ya
    return dict(x_row=y_row, x_left=max(xl, x_col), x_right=xr, y_col=x_col, y_top=yt, y_bottom=min(yb, y_row))


# ---------------------------------------------------------------- calibration
def _fit(pos, val, log):
    v = np.log10(val) if log else val
    A = np.vstack([pos, np.ones_like(pos)]).T
    coef, *_ = np.linalg.lstsq(A, v, rcond=None)
    return coef


def calibrate(pos, val):
    """Robust 1D calibration pixel -> value. Returns (fn, info) or (None, None)."""
    pos, val = np.asarray(pos, float), np.asarray(val, float)
    if len(pos) < 2:
        return None, None
    best = None
    for log in (False, True):
        if log and (val <= 0).any():
            continue
        vv = np.log10(val) if log else val
        for i, j in itertools.combinations(range(len(pos)), 2):
            if pos[i] == pos[j] or vv[i] == vv[j]:
                continue
            a = (vv[j] - vv[i]) / (pos[j] - pos[i])
            b = vv[i] - a * pos[i]
            pred_pos = (vv - b) / a
            inl = np.abs(pred_pos - pos) < 4
            if inl.sum() < 2:
                continue
            key = (inl.sum(), -np.abs(pred_pos - pos)[inl].mean() - (0.5 if log else 0))
            if best is None or key > best[0]:
                best = (key, log, inl)
    if best is None:
        return None, None
    (_, _), log, inl = best
    a, b = _fit(pos[inl], val[inl], log)
    fn = (lambda p, a=a, b=b: 10 ** (a * np.asarray(p, float) + b)) if log else (lambda p, a=a, b=b: a * np.asarray(p, float) + b)
    return fn, dict(log=log, n_ticks=int(inl.sum()), n_labels=int(len(pos)))


def _numeric(toks):
    out = []
    for t in toks:
        s = t['text'].replace('−', '-').replace('–', '-')
        if NUMTOK.match(s) or re.match(r'^-?\d+(\.\d+)?$', s.strip('.,')):
            v = _clean_num(s)
            if v is not None:
                out.append(dict(t, value=v))
    return out


UNIT_RE = re.compile(r'[\(\[]\s*([^\)\]]{1,20})\s*[\)\]]')


def _unit_from_text(text):
    for m in UNIT_RE.finditer(text or ''):
        u = unit_norm_or_none(m.group(1))
        if u:
            return u
    for wd in re.split(r'[\s,/]+', text or ''):
        u = unit_norm_or_none(wd)
        if u and u not in ('m', 's', 'c', 'k', 'd', 'h'):
            return u
    if re.search(r'2\s*[θΘ0]|theta', text or '', re.I):
        return '°'
    return None


def axis_units(rgb, gray, ax, toks):
    h, w = gray.shape
    below = ' '.join(t['text'] for t in toks if t['cy'] > ax['x_row'] + 0.04 * h)
    xu = _unit_from_text(below)
    strip = rgb[:, : max(ax['y_col'] - 2, 1)]
    yu = None
    if strip.shape[1] > 8:
        rot = np.ascontiguousarray(np.rot90(strip, k=-1))
        ytoks = ocr_tokens(rot, scale=3, psm=11)
        yu = _unit_from_text(' '.join(t['text'] for t in ytoks))
    return xu, yu


# ---------------------------------------------------------------- series
def _series_masks(rgb, gray, box, toks):
    x0, x1, y0, y1 = box
    sub = rgb[y0:y1, x0:x1]
    g = gray[y0:y1, x0:x1]
    mx, mn = sub.max(axis=2), sub.min(axis=2)
    sat = (mx - mn) / np.maximum(mx, 1)
    excl = np.zeros(g.shape, bool)
    for t in toks:
        a, b = int(t['y0']) - y0 - 1, int(t['y1']) - y0 + 1
        c, d = int(t['x0']) - x0 - 1, int(t['x1']) - x0 + 1
        excl[max(a, 0):max(b, 0), max(c, 0):max(d, 0)] = True
    masks = []
    dark = (g < 90) & (sat < 0.25) & ~excl
    if dark.mean() > 0.0005:
        masks.append(('black', dark))
    col = (sat > 0.3) & (mx > 60) & ~excl
    if col.any():
        hsv_h = np.zeros(g.shape)
        r, gg, b = sub[..., 0], sub[..., 1], sub[..., 2]
        hsv_h = (np.degrees(np.arctan2(np.sqrt(3) * (gg - b), 2 * r - gg - b)) + 360) % 360
        bins = (hsv_h // 30).astype(int)
        for k in range(12):
            m = col & (bins == k)
            if m.mean() > 0.0005:
                masks.append((f'hue{k * 30}', m))
    return masks


def _curve(mask):
    xs, ys = [], []
    for c in range(mask.shape[1]):
        r = np.flatnonzero(mask[:, c])
        if len(r):
            xs.append(c)
            ys.append(np.median(r))
    return np.array(xs), np.array(ys)


def _bars(mask, base_row_local):
    out = []
    lab, n = ndi.label(mask)
    for sl in ndi.find_objects(lab):
        if sl is None:
            continue
        ys, xs = sl
        hgt, wid = ys.stop - ys.start, xs.stop - xs.start
        if wid < 4 or hgt < 4:
            continue
        if mask[sl].mean() < 0.85:
            continue
        if abs(ys.stop - base_row_local) > 6:
            continue
        out.append(((xs.start + xs.stop) / 2, ys.start))
    return out


# ---------------------------------------------------------------- metrics
def _curve_cands(X, Y, xu, yu, xt, yt, name, panel):
    out = []
    if len(X) < 5:
        return out
    order = np.argsort(X)
    X, Y = X[order], Y[order]
    rngY = np.ptp(Y) or 1.0
    i_max, i_min = int(np.argmax(Y)), int(np.argmin(Y))
    out += [cand(Y[i_max], yu, 'plot', f'{name}: max y', 1.0, panel), cand(X[i_max], xu, 'plot', f'{name}: x at max y', 0.9, panel),
            cand(Y[i_min], yu, 'plot', f'{name}: min y', 0.6, panel), cand(X[i_min], xu, 'plot', f'{name}: x at min y', 0.5, panel),
            cand(Y[0], yu, 'plot', f'{name}: first y', 0.4, panel), cand(Y[-1], yu, 'plot', f'{name}: last y', 0.5, panel),
            cand(np.median(Y[int(0.8 * len(Y)):]), yu, 'plot', f'{name}: plateau (last 20%)', 0.4, panel),
            cand(X[-1], xu, 'plot', f'{name}: last x (e.g. elongation)', 0.4, panel)]
    for sign, lab in ((1, 'peak'), (-1, 'dip')):
        pk, pr = find_peaks(sign * Y, prominence=0.05 * rngY)
        for i in np.argsort(-pr['prominences'])[:8]:
            p = pk[i]
            s = float(pr['prominences'][i] / rngY)
            out += [cand(X[p], xu, 'plot', f'{name}: {lab} position', 0.5 + s, panel),
                    cand(Y[p], yu, 'plot', f'{name}: {lab} height', 0.3 + s, panel)]
    for xv in xt:
        if X[0] <= xv <= X[-1]:
            out.append(cand(np.interp(xv, X, Y), yu, 'plot', f'{name}: y at x={xv:g}', 0.3, panel))
    for yv in yt:
        cross = np.flatnonzero(np.diff(np.sign(Y - yv)))
        if len(cross):
            i = cross[0]
            x_c = X[i] + (yv - Y[i]) * (X[i + 1] - X[i]) / ((Y[i + 1] - Y[i]) or 1e-9)
            out.append(cand(x_c, xu, 'plot', f'{name}: x where y={yv:g}', 0.3, panel))
    # 0.2% offset yield (x in % strain or unitless strain)
    n0 = max(3, int(0.15 * len(X)))
    if np.ptp(X[:n0]) > 0:
        k, b = np.polyfit(X[:n0], Y[:n0], 1)
        if k > 0:
            off = 0.2 if (xu == '%' or X[-1] > 1.5) else 0.002
            d = Y - (k * (X - off) + b)
            cr = np.flatnonzero((d[:-1] > 0) & (d[1:] <= 0))
            if len(cr):
                i = cr[0]
                out.append(cand(Y[i], yu, 'plot', f'{name}: 0.2% offset yield', 0.6, panel))
    # largest slope change
    if len(X) > 10:
        dy = np.gradient(Y, X)
        dd = np.abs(np.gradient(ndi.uniform_filter1d(dy, 5), X))
        i = int(np.argmax(dd[2:-2])) + 2
        out.append(cand(X[i], xu, 'plot', f'{name}: x at largest slope change', 0.4, panel))
    return out


def run(rgb, gray, panel, toks=None):
    toks = toks if toks is not None else ocr_tokens(rgb)
    ax = find_axes(gray)
    if not ax:
        return [], dict(status='no axes')
    h, w = gray.shape
    nums = _numeric(toks)
    xl = [t for t in nums if ax['x_row'] < t['cy'] < ax['x_row'] + 0.18 * h and ax['x_left'] - 15 <= t['cx'] <= ax['x_right'] + 15]
    yl = [t for t in nums if ax['y_col'] - 0.3 * w < t['cx'] < ax['y_col'] and ax['y_top'] - 15 <= t['cy'] <= ax['y_bottom'] + 15]
    fx, ix = calibrate([t['cx'] for t in xl], [t['value'] for t in xl])
    fy, iy = calibrate([t['cy'] for t in yl], [t['value'] for t in yl])
    info = dict(status='ok', axes=ax, x_cal=ix, y_cal=iy)
    if fx is None and fy is None:
        info['status'] = 'no calibration'
        return [], info
    xu, yu = axis_units(rgb, gray, ax, toks)
    info.update(x_unit=xu, y_unit=yu)
    box = (ax['y_col'] + 3, ax['x_right'], ax['y_top'], ax['x_row'] - 2)
    if box[1] - box[0] < 20 or box[3] - box[2] < 20:
        info['status'] = 'plot box too small'
        return [], info
    xt = sorted({t['value'] for t in xl})
    yt = sorted({t['value'] for t in yl})
    out = []
    for name, m in _series_masks(rgb, gray, box, toks):
        px, py = _curve(m)
        if len(px) < 5:
            continue
        X = fx(px + box[0]) if fx else None
        Y = fy(py + box[2]) if fy else None
        if X is not None and Y is not None:
            out += _curve_cands(np.asarray(X), np.asarray(Y), xu, yu, xt, yt, name, panel)
        for bx, top in _bars(m, m.shape[0]):
            if fy is not None:
                out.append(cand(float(fy(top + box[2])), yu, 'plot', f'{name}: bar height', 0.8, panel))
    if os.environ.get('CEILING_DIGITIZER') == 'lineformer':
        try:
            from lineformer_adapter import extract_lines  # provided on the nodes, returns [(name, xs_px, ys_px)]
            for name, xs, ys in extract_lines(rgb):
                if fx is not None and fy is not None:
                    out += _curve_cands(np.asarray(fx(xs)), np.asarray(fy(ys)), xu, yu, xt, yt, f'lineformer-{name}', panel)
        except Exception as e:
            out.append(dict(error=f'lineformer: {type(e).__name__}: {e}'[:300], chain='plot', panel=panel))
    return out, info
