#!/usr/bin/env python3
"""digitize.py: v3 digitizer (code only; no model reads values). Per panel:
 1. Frame: plot box from the long dark axis lines (find_axes of the tool-ceiling plot.py, frozen there).
 2. Ticks: major tick marks on the bottom and left axes (short dark runs perpendicular to the axis, inside the frame).
 3. Tick labels: Tesseract OCR of numbers below / left of the axes, matched to the nearest tick mark; or, if OCR fails on a panel,
    printed tick labels from digitize_config.json ("source": "printed tick label"), assigned to the detected tick marks in order and
    verified by the fit residual (<= 1 px). Calibration: linear or log10 least squares on (tick position, value); residual in px.
 4. Legend: OCR tokens 'x=<value>' (case-insensitive); legend box = their union plus the swatch area to their left. The swatch colour
    left of each token is classified -> colour class -> x. A panel whose legend does not give all five x with distinct colour classes is
    flagged (mapping 'unclean').
 5. Series: per colour class, pixels inside the plot box (outside the legend box) -> morphological opening (removes connecting lines,
    dashes and text strokes) -> connected blobs of marker size -> centroids -> data units. Reference/literature series have other colours
    and are ignored by construction.
 6. Reading uncertainty per point: u_px = sqrt((marker size / 2)^2 + calibration residual^2), converted to data units (multiplicative on
    log axes).
Outputs digitized/<panel>.json (points per x) and an overlay PNG in v3_host/overlays/."""
import json, os, re, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
sys.path.insert(0, '/home/aid1/Documents/harbor/ceiling_run/ceiling')
from plot import find_axes
import pytesseract

V3 = '/home/aid1/Documents/harbor/v32'
# v3.2: everything paper-specific comes from the paper profile (papers/<paper>/profile.json): crops dir, series values, colour classes
# (strict / relaxed masks as numpy expressions in r, g, b), swatch classification rules, legend-token regexes, per-panel printed tick
# labels and printed legend entries. configure(profile) sets the module state; nothing paper-specific is left in this file.
PROFILE = None; HOST = None; X_VALUES = []; CLASSES = []; PAPER_DIR = None

def configure(profile, paper_dir=None):
    global PROFILE, HOST, X_VALUES, CLASSES, PAPER_DIR
    PROFILE = profile; X_VALUES = [float(v) for v in profile['series_values']]; CLASSES = list(profile['colour_classes'])
    HOST = os.path.dirname(profile['crops_dir'].rstrip('/')); PAPER_DIR = paper_dir

def load_profile(paper):
    d = f'{V3}/papers/{paper}'; p = json.load(open(f'{d}/profile.json')); configure(p, d); return p

def _masks(rgb, kind):
    r, g, b = [rgb[..., i].astype(int) for i in range(3)]
    return {c: eval(spec[kind], {'__builtins__': {}}, {'r': r, 'g': g, 'b': b}) for c, spec in PROFILE['colour_classes'].items()}

def color_class(rgb):
    return _masks(rgb, 'strict')

def color_class_relaxed(rgb):
    """looser masks for the occluded-marker pass (series partly hidden under other markers)."""
    return _masks(rgb, 'relaxed')

def swatch_class_counts(sw):
    """legend swatch: per non-white pixel, spread < gray_spread and mean < gray_dark_mean -> gray_class; else the first matching
    profile rule (expressions in r, g, b, mx, mn)."""
    sr = PROFILE['swatch_rules']; rules = [(compile(e, '<rule>', 'eval'), c) for e, c in sr['rules']]
    a = sw.reshape(-1, 3).astype(float); a = a[a.min(1) < 210]
    cnt = {c: 0 for c in CLASSES}
    for r, g, b in a:
        mx, mn = max(r, g, b), min(r, g, b)
        if mx - mn < sr['gray_spread']:
            if (r + g + b) / 3 < sr['gray_dark_mean']: cnt[sr['gray_class']] += 1
            continue
        env = {'r': r, 'g': g, 'b': b, 'mx': mx, 'mn': mn}
        for code, c in rules:
            if eval(code, {'__builtins__': {}}, env): cnt[c] += 1; break
    return cnt

def ocr(rgb, scale=3, psm=11, cfg=''):
    im = Image.fromarray(rgb).resize((rgb.shape[1] * scale, rgb.shape[0] * scale), Image.LANCZOS)
    d = pytesseract.image_to_data(im, config=f'--psm {psm} {cfg}', output_type=pytesseract.Output.DICT)
    out = []
    for i, t in enumerate(d['text']):
        t = t.strip()
        if not t or float(d['conf'][i]) < 0: continue
        x0, y0, w, h = [v / scale for v in (d['left'][i], d['top'][i], d['width'][i], d['height'][i])]
        out.append({'text': t, 'x0': x0, 'y0': y0, 'x1': x0 + w, 'y1': y0 + h, 'cx': x0 + w / 2, 'cy': y0 + h / 2, 'conf': float(d['conf'][i])})
    return out

NUMRE = re.compile(r'^[-−–]?\d+(?:\.\d+)?$')
def numval(s):
    s = s.replace('−', '-').replace('–', '-').strip('.,;:')
    return float(s) if NUMRE.match(s) else None

def ticks_along(dark, line, lo, hi, axis):
    """tick marks on an axis line, inward and outward: [(position, run length)]; major = run >= 6, minor = 2-5."""
    out = []
    for p in range(lo + 2, hi - 1):
        best = 0
        for inward in (-1, 1):
            run = 0
            for k in range(1, 16):
                q = line + inward * k
                if not (0 <= q < (dark.shape[0] if axis == 'x' else dark.shape[1])): break
                v = dark[q, p] if axis == 'x' else dark[p, q]
                if v: run += 1
                else: break
            best = max(best, run)
        if 2 <= best <= 14: out.append((p, best))
    groups = []
    for p, r in out:
        if groups and p - groups[-1][-1][0] <= 1: groups[-1].append((p, r))
        else: groups.append([(p, r)])
    return [(float(np.mean([a for a, _ in g])), max(r for _, r in g)) for g in groups]

def fit(pos, val, log):
    v = np.log10(val) if log else np.asarray(val, float)
    A = np.vstack([pos, np.ones(len(pos))]).T; (a, b), *_ = np.linalg.lstsq(A, v, rcond=None)
    pred_pos = (v - b) / a; resid = float(np.sqrt(np.mean((pred_pos - np.asarray(pos)) ** 2)))
    return a, b, resid

def robust(labels, majors, log_hint=None):
    """labels: [(pixel center, value)] from OCR. Snap to the nearest major tick within 4 px; RANSAC over pairs (inliers within 3 px);
    least squares on inliers. Returns (log, a, b, resid_px, n_inliers, used_pairs) or None."""
    pts = []
    for c, v in labels:
        if majors:
            t = min(majors, key=lambda t: abs(t - c))
            if abs(t - c) <= 4: c = t
        pts.append((c, v))
    best = None
    for log in ((False, True) if log_hint is None else (log_hint,)):
        P = [(c, v) for c, v in pts if (v > 0 or not log)]
        if len(P) < 3: continue
        vv = [np.log10(v) if log else v for _, v in P]
        for i in range(len(P)):
            for j in range(i + 1, len(P)):
                if P[i][0] == P[j][0] or vv[i] == vv[j]: continue
                a = (vv[j] - vv[i]) / (P[j][0] - P[i][0]); b = vv[i] - a * P[i][0]
                inl = [k for k in range(len(P)) if abs((vv[k] - b) / a - P[k][0]) <= 3]
                key = (len(inl), -0.5 if log else 0)
                if best is None or key > best[0]: best = (key, log, [P[k] for k in inl])
    if not best or len(best[2]) < 3: return None
    log, used = best[1], best[2]
    a, b, r = fit([c for c, _ in used], [v for _, v in used], log)
    return (log, a, b, r, len(used), used)

def minor_check(ticks, a, b):
    """log axis: predicted positions of minor values 2..9 per decade vs detected minor ticks; median |error| px (None if < 3 found)."""
    minors = [t for t, r in ticks if 2 <= r <= 5]
    if not minors: return None
    lo, hi = sorted([(min(t for t, _ in ticks) * a + b), (max(t for t, _ in ticks) * a + b)])
    errs = []
    for d in range(int(np.floor(lo)) - 1, int(np.ceil(hi)) + 1):
        for m in range(2, 10):
            p = (np.log10(m) + d - b) / a
            if min(t for t, _ in ticks) <= p <= max(t for t, _ in ticks): errs.append(min(abs(p - t) for t in minors))
    return float(np.median(errs)) if len(errs) >= 3 else None

SHAPE_CLASS_UNUSED = {'square': 'square', 'tri_up': 'tri_up', 'tri_down': 'tri_down', 'circle': 'compact', 'tri_left': 'compact', 'tri_right': 'compact', 'diamond': 'compact'}

def marker_shape(mask, cx, cy, r=7):
    """shape class of the marker blob at (cx, cy) on the raw colour mask (13x13 window): square (fill >= 0.82), tri_up (row width grows
    downward, slope >= +0.035 of the max width per row), tri_down (slope <= -0.025), else compact (circle and side-pointing triangles
    cannot be told apart at 6-8 px). None when the blob has < 6 px."""
    cy, cx = int(round(cy)), int(round(cx)); win = mask[max(cy - r, 0):cy + r + 1, max(cx - r, 0):cx + r + 1]
    lab, n = ndi.label(win)
    if not n: return None
    c = lab[min(r, lab.shape[0] - 1), min(r, lab.shape[1] - 1)] or (np.bincount(lab.ravel())[1:].argmax() + 1)
    m = lab == c; yy, xx = np.nonzero(m)
    if len(yy) < 6: return None
    f = len(yy) / ((np.ptp(yy) + 1) * (np.ptp(xx) + 1)); rw = [m[y].sum() for y in range(yy.min(), yy.max() + 1)]
    sv = np.polyfit(range(len(rw)), rw, 1)[0] / max(rw) if len(rw) > 1 else 0.0
    if f >= 0.82: return 'square'
    if sv >= 0.035: return 'tri_up'
    if sv <= -0.025: return 'tri_down'
    return 'compact'

def verify_legend(rgb, declared, entries, legend_box, rmasks, series_sizes, fx0=0):
    """v3.2: pixel check of the printed legend entries declared in the profile (they decide T2 keys). Per entry, in its legend row band
    (row from the OCR-read entries, or fitted from >= 2 read rows in legend order = series order; band = legend box width, +-6 px):
      (1) colour: >= 6 px of the declared colour class (relaxed mask, legend swatches are often washed out);
      (2) marker: a marker-sized blob of that colour sits in the row inside the plot frame (tallest filled blob: fill >= 0.45, short
          side >= 3 px; gray class also width >= 0.8 x height, which excludes lines, the frame and label glyphs), its height 0.5-2.0x the series' median marker size (the swatch line adds width only);
      (3) series cluster: the digitizer detected >= 3 markers of that colour in the plot (strict and occluded passes; v3.2: the check
          runs after series detection, so a half-hidden series counts what the digitizer itself recovers - replica evidence F5a r0);
      colours distinct across entries. Marker *shape* is not checked from pixels: at 6-8 px marker templates of different shapes overlap
      as much as same-shape templates (IoU table in LOG.md); the blind GPT-5.6-Sol legend read checks label, colour and marker.
    Returns (ok, details)."""
    det = {}
    if len({e['colour'] for e in declared}) != len(declared): return False, {'error': 'declared colours not distinct'}
    if len(entries) < 2: return False, {'error': f'only {len(entries)} legend rows located by OCR'}
    rk = [X_VALUES.index(float(k)) for k in entries]; cyv = [v['cy'] for v in entries.values()]; sl, ic = np.polyfit(rk, cyv, 1)
    lb = [int(round(v)) for v in legend_box]; ok = True
    for e in declared:
        xv = float(e['value']); c = e['colour']
        cy = int(round(entries[str(xv)]['cy'] if str(xv) in entries else ic + sl * X_VALUES.index(xv)))
        band = rmasks[c][max(cy - 6, 0):cy + 7, max(lb[0], 0):lb[2]]; c1 = int(band.sum()) >= 6
        # marker search inside the plot frame: candidates are filled blobs (fill >= 0.45 of the bounding box: a filled triangle covers
        # 0.5; short side >= 3 px), which excludes 1-2 px lines and the frame; for the gray class, which shares its colour with the
        # label text, also width >= 0.8 x height (markers are about square, digit glyphs narrow). The tallest candidate wins.
        lab, n = ndi.label(ndi.binary_opening(rmasks[c][max(cy - 6, 0):cy + 7, max(lb[0], fx0 + 3):lb[2]], structure=np.ones((2, 1)))); sw_size = None; cands = []   # 2x1 vertical opening drops a 1 px swatch line of the marker's colour (replica evidence)
        for i in range(1, n + 1):
            yy, xx = np.nonzero(lab == i); h_, w_ = np.ptp(yy) + 1, np.ptp(xx) + 1
            gray_ok = c != PROFILE['swatch_rules']['gray_class'] or w_ >= 0.8 * h_   # gray: markers ~square, digit glyphs narrow
            if min(h_, w_) >= 3 and len(yy) >= 0.45 * h_ * w_ and gray_ok: cands.append(float(h_))
        if cands: sw_size = max(cands)
        sizes = series_sizes.get(str(xv), [])
        med = float(np.median(sizes)) if sizes else None
        c2 = sw_size is not None and med is not None and 0.5 * med <= sw_size <= 2.0 * med   # replica evidence (F6a): opening trims a triangle apex; legends draw markers at other sizes
        c3 = len(sizes) >= 3
        det[str(xv)] = {'label': e['label'], 'colour': c, 'marker': e['marker'], 'swatch_colour_px': int(band.sum()), 'swatch_marker_px': sw_size,
                        'series_markers': len(sizes), 'series_marker_px': med, 'colour_ok': c1, 'marker_ok': c2, 'series_ok': c3}
        ok = ok and c1 and c2 and c3
    return ok, det

def run(panel, cfg):
    rgb = np.asarray(Image.open(f'{HOST}/crops/{panel}.jpg').convert('RGB')); gray = rgb.mean(2)
    LT = PROFILE['legend_token']
    H, W = gray.shape; dark = gray < 110
    ax = find_axes(gray)
    if not ax: return {'panel': panel, 'status': 'no axes'}
    # find_axes takes the longest dark run on the x-axis row; a short JPEG gap can cut it. If the row between the y-axis
    # column and that run is >= 80% dark, the plot box starts at the y-axis.
    if ax['x_left'] - ax['y_col'] > 10 and dark[ax['x_row'], ax['y_col']:ax['x_left']].mean() >= 0.8: ax['x_left'] = ax['y_col']
    x0, x1, yb, yt = ax['x_left'], ax['x_right'], ax['x_row'], ax['y_top']
    xt = ticks_along(dark, yb, x0, x1, 'x'); yt_ = ticks_along(dark, ax['y_col'], yt, yb, 'y')
    xmaj = [t for t, r in xt if r >= 6]; ymaj = [t for t, r in yt_ if r >= 6]
    toks = ocr(rgb)
    bot = rgb[yb + 2:yb + 34, :]; left = rgb[:, max(ax['y_col'] - 62, 0):ax['y_col'] - 2]; xoff = max(ax['y_col'] - 62, 0)
    tb = ocr(bot); tl = ocr(left)
    pc = cfg.get(panel, {}) if cfg is not None else PROFILE['panels'].get(panel, {})
    res = {'panel': panel, 'frame': {'x_left': x0, 'x_right': x1, 'y_bottom': yb, 'y_top': yt}, 'n_xticks': len(xt), 'n_yticks': len(yt_)}
    def axis_cal(name, majors, ticks, labels, key):
        if f'{key}_ticks' in pc:   # printed tick labels for the major ticks, in order (bottom-up / left-right); verified below
            vals = pc[f'{key}_ticks']; log = pc.get(f'{key}_log', False)
            maj = sorted(majors, reverse=(key == 'y'))[:len(vals)]
            if len(maj) < len(vals): return None, 'printed tick label: fewer major ticks than labels'
            a, b, r = fit(maj, vals, log); mc = minor_check(ticks, a, b) if log else None
            return (log, a, b, r, len(vals), list(zip(maj, vals))), f'printed tick label (fit residual {r:.2f} px; minor-tick check {mc if mc is None else round(mc, 2)} px)'
        cal = robust(labels, majors, pc.get(f'{key}_log'))
        if cal and cal[0]:
            mc = minor_check(ticks, cal[1], cal[2]); return cal, f'ocr (log; minor-tick check {mc if mc is None else round(mc, 2)} px)'
        return cal, 'ocr'
    xl = [(t['cx'], numval(t['text'])) for t in tb if numval(t['text']) is not None]
    yl = [(t['cy'], numval(t['text'])) for t in tl if numval(t['text']) is not None]
    xcal, res['x_source'] = axis_cal('x', xmaj, xt, xl, 'x')
    ycal, res['y_source'] = axis_cal('y', ymaj, yt_, yl, 'y')
    xt = [t for t, _ in xt]; yt_ = [t for t, _ in yt_]
    res['x_cal'] = xcal and {'log': xcal[0], 'a': xcal[1], 'b': xcal[2], 'resid_px': xcal[3], 'n': xcal[4]}
    res['y_cal'] = ycal and {'log': ycal[0], 'a': ycal[1], 'b': ycal[2], 'resid_px': ycal[3], 'n': ycal[4]}
    if not (xcal and ycal):
        res['status'] = 'calibration failed'; res['x_labels_ocr'] = xl; res['y_labels_ocr'] = yl; return res
    res['x_cal']['pairs'] = [list(p) for p in xcal[5]]; res['y_cal']['pairs'] = [list(p) for p in ycal[5]]
    fx = lambda p: 10 ** (xcal[1] * p + xcal[2]) if xcal[0] else xcal[1] * p + xcal[2]
    fy = lambda p: 10 ** (ycal[1] * p + ycal[2]) if ycal[0] else ycal[1] * p + ycal[2]
    # legend: OCR of the plot interior (4x, whitelist), tokens on one row joined, then 'x=<value>'
    sub = rgb[yt + 2:yb - 1, x0 + 2:x1 - 1]
    lt = ocr(sub, scale=4, psm=11, cfg=f"-c tessedit_char_whitelist={LT['whitelist']}")
    for t in lt:
        for k in ('x0', 'x1', 'cx'): t[k] += x0 + 2
        for k in ('y0', 'y1', 'cy'): t[k] += yt + 2
    lt.sort(key=lambda t: (round(t['cy'] / 6), t['x0'])); rows = []
    for t in lt:
        if rows and abs(rows[-1][-1]['cy'] - t['cy']) <= 5 and t['x0'] - rows[-1][-1]['x1'] <= 14: rows[-1].append(t)
        else: rows.append([t])
    leg = []
    for r in rows:
        txt = ''.join(t['text'] for t in r).replace(',', '.')
        m = re.search(LT['pass2_regex'], txt)   # v3.1: '=' required after the x (replica F5b r4: '.4=X0' was read as x=0)
        if m:
            # a marker glyph OCR'd as a leading character ('4x=0'): start the entry at the 'x', pro rata on the token width
            pre = m.start() / max(len(txt), 1); xs = r[0]['x0'] + pre * (r[-1]['x1'] - r[0]['x0'])
            leg.append({'text': txt, 'x0': xs, 'x1': r[-1]['x1'], 'y0': min(t['y0'] for t in r), 'y1': max(t['y1'] for t in r),
                        'cy': float(np.mean([t['cy'] for t in r])), 'value': m.group(1)})
    for t in toks:   # union with the first-pass tokens (full charset)
        m = re.match(LT['pass1_regex'], t['text'].replace(' ', ''))
        if m and x0 < t['cx'] < x1 and yt < t['cy'] < yb:
            leg.append({'text': t['text'], 'x0': t['x0'], 'x1': t['x1'], 'y0': t['y0'], 'y1': t['y1'], 'cy': t['cy'], 'value': m.group(1).replace(',', '.')})
    mapping, legend_box = {}, None
    ent = {}
    for t in leg:   # merge duplicate entries of the same value (two OCR passes)
        try: xv = float(t['value'])
        except ValueError: continue
        if xv in X_VALUES: ent.setdefault(xv, []).append(t)
    if ent:
        left = int(min(t['x0'] for ts in ent.values() for t in ts)) - 45
        counts = {}
        for xv, ts in ent.items():
            cy = int(round(np.median([t['cy'] for t in ts]))); xr = int(min(t['x0'] for t in ts)) + 10
            sw = rgb[max(cy - 6, 0):cy + 7, max(left, 0):xr]
            counts[xv] = swatch_class_counts(sw)
        used = set()   # one-to-one: strongest chromatic signal first; black for an entry with no chromatic signal
        for xv in sorted(counts, key=lambda v: -max(n for c, n in counts[v].items() if c != 'black')):
            ch = {c: n for c, n in counts[xv].items() if c != 'black' and n >= 6 and c not in used}
            if ch: c = max(ch, key=ch.get); mapping[xv] = c; used.add(c)
        for xv in counts:
            if xv not in mapping and 'black' not in used and counts[xv]['black'] >= 6: mapping[xv] = 'black'; used.add('black')
        res['legend_counts'] = {str(k): v for k, v in counts.items()}
    for t in leg:
        b = (t['x0'] - 45, t['y0'] - 4, t['x1'] + 4, t['y1'] + 4)
        legend_box = b if legend_box is None else (min(legend_box[0], b[0]), min(legend_box[1], b[1]), max(legend_box[2], b[2]), max(legend_box[3], b[3]))
    res['legend_tokens'] = [t['text'] for t in leg]
    clean = len(mapping) == len(X_VALUES) and len(set(mapping.values())) == len(X_VALUES)
    res['legend'] = {'mapping': {str(k): v for k, v in mapping.items()}, 'box': legend_box, 'clean': clean}
    res['legend']['mapping_source'] = 'own legend'
    res['legend']['entries'] = {str(xv): {'cy': float(np.median([t['cy'] for t in ts])), 'x0': float(min(t['x0'] for t in ts)), 'x1': float(max(t['x1'] for t in ts)),
                                          'y0': float(min(t['y0'] for t in ts)), 'y1': float(max(t['y1'] for t in ts))} for xv, ts in ent.items()}
    declared = pc.get('legend')
    if declared:   # v3.2: printed legend entries from the profile decide the mapping; pixel check after series detection
        mapping = {float(e['value']): e['colour'] for e in declared}; res['legend']['mapping_source'] = 'printed legend entries (profile)'
    elif not clean and CONVENTION:
        # v3.1 (replica evidence, A5): only a strong own reading can conflict. Strong = the assigned colour has >= 12 px and >= 2x
        # the next chromatic colour (black is not a competitor: the label text is black). A weak reading is logged and ignored.
        def strong(k, v):
            cnt = (res.get('legend_counts') or {}).get(str(k), {}); own = cnt.get(v, 0)
            other = max([n for c, n in cnt.items() if c not in (v, 'black')] + [0])
            return own >= 12 and own >= 2 * other
        conflict = [k for k, v in mapping.items() if CONVENTION.get(k) != v and strong(k, v)]
        res['legend']['weak_conflicts_ignored'] = [str(k) for k, v in mapping.items() if CONVENTION.get(k) != v and not strong(k, v)]
        res['legend']['own_partial'] = {str(k): v for k, v in mapping.items()}
        if not conflict:
            mapping = dict(CONVENTION); res['legend']['mapping_source'] = f'series-wide colour convention (from clean legends {CONVENTION_FROM}); own legend read {len(res["legend"]["own_partial"])} entries, none conflicting'
        else:
            res['legend']['mapping_source'] = f'unresolved: own legend conflicts with the convention for {conflict}'; mapping = {}
    # series
    masks = color_class(rgb); inner = np.zeros_like(dark); inner[yt + 3:yb - 2, x0 + 3:x1 - 2] = True
    # v3.1 (replica evidence, A5: the F6a x = 0 legend glyph was taken as a data point because OCR missed that row): the legend
    # exclusion spans all five rows, fitted from the rows read (legend order x = 0 ... 0.04 top-down), as the T2 mask does
    ent_rows = res['legend'].get('entries') or {}
    if legend_box and len(ent_rows) >= 2:
        rk = [X_VALUES.index(float(k)) for k in ent_rows]; cy_ = [v['cy'] for v in ent_rows.values()]
        sl, ic = np.polyfit(rk, cy_, 1); rows5 = [ic + sl * r for r in range(len(X_VALUES))]
        legend_box = (legend_box[0], min(legend_box[1], min(rows5) - abs(sl) / 2), legend_box[2], max(legend_box[3], max(rows5) + abs(sl) / 2))
        res['legend']['box'] = legend_box
    if legend_box:
        lb = [int(round(v)) for v in legend_box]; inner[max(lb[1] - 10, 0):lb[3] + 10, max(lb[0] - 10, 0):lb[2] + 10] = False   # 10 px pad
    series = {}
    def blobs(m, amin, minside, occl):
        lab, n = ndi.label(m); out = []
        for i in range(1, n + 1):
            yy, xx = np.nonzero(lab == i); area = len(yy)
            if not (amin <= area <= 160): continue
            hgt, wid = np.ptp(yy) + 1, np.ptp(xx) + 1
            if max(hgt, wid) > 16 or min(hgt, wid) < minside: continue
            # occluded pass only: compact blobs (aspect <= 1.6, fill >= 0.45) away from the frame, so dashes and ticks drop out
            if occl and (max(hgt, wid) > 1.6 * min(hgt, wid) or area < 0.45 * hgt * wid or xx.min() < x0 + 8 or xx.max() > x1 - 8
                         or yy.min() < yt + 8 or yy.max() > yb - 8): continue
            out.append({'px': float(xx.mean()), 'py': float(yy.mean()), 'size_px': float(max(hgt, wid)), 'occluded': occl})
        return out
    for xv, c in mapping.items():
        series[str(xv)] = blobs(ndi.binary_opening(masks[c] & inner, structure=np.ones((3, 3))), 12, 4, False)
    # occluded-marker pass, every series: extra detections from the relaxed mask (no opening, area >= 8, min side >= 3), kept
    # only where the strict pass has no marker within 6 px in x. The fragment centroid can sit off the marker centre, so such a point takes the
    # panel's median marker size as its size and twice the half-size as position uncertainty. Kept only >= 6 px from existing points.
    nmax = max([len(v) for v in series.values()] or [0]); sizes = [p['size_px'] for v in series.values() for p in v]
    msize = float(np.median(sizes)) if sizes else 8.0; rmasks = color_class_relaxed(rgb); res['occluded_pass'] = {}
    for xv, c in mapping.items():
        pts = series[str(xv)]
        extra = [p for p in blobs(rmasks[c] & inner, 8, 3, True) if all(abs(p['px'] - q['px']) > 6 for q in pts)]
        # reject: on another series' strict marker (within 5 px), or > 12 px off this series' local trend (median py of its
        # strict points within +-40 px in x; needs >= 2 such points)
        others = [q for k, v in series.items() if k != str(xv) for q in v]
        def keep(p):
            if any(np.hypot(p['px'] - q['px'], p['py'] - q['py']) < 5 for q in others): return False
            loc = [q['py'] for q in pts if abs(q['px'] - p['px']) <= 40]
            return len(loc) < 2 or abs(p['py'] - float(np.median(loc))) <= 12
        extra = [p for p in extra if keep(p)]
        for p in extra: p['size_px'] = 2 * msize
        res['occluded_pass'][str(xv)] = {'before': len(pts), 'added': len(extra)}
        series[str(xv)] = pts + extra
    if declared:
        okL, detL = verify_legend(rgb, declared, res['legend']['entries'], legend_box, color_class_relaxed(rgb),
                                  {k: [p['size_px'] / (2 if p.get('occluded') else 1) for p in v] for k, v in series.items()}, x0)
        res['legend']['declared_check'] = {'ok': okL, 'entries': detL}
        if not okL:
            res['legend']['mapping_source'] += ', pixel check FAILED: panel dropped'; res['legend']['mapping'] = {}
            res['status'] = 'legend check failed'; res['series'] = {}; return res
        res['legend']['mapping_source'] += ', pixel check passed'
    for xv in list(series):
        pts = series[xv]
        pts.sort(key=lambda p: p['px'])
        for p in pts:
            p['x'] = float(fx(p['px'])); p['y'] = float(fy(p['py']))
            upx = float(np.hypot(p['size_px'] / 2, ycal[3]))
            if ycal[0]: p['u'] = float(p['y'] * (10 ** (abs(ycal[1]) * upx) - 1))
            else: p['u'] = float(abs(ycal[1]) * upx)
    res['series'] = series; res['status'] = 'ok'
    ov = Image.fromarray(rgb.copy()); d = ImageDraw.Draw(ov)
    for xv, pts in series.items():
        for p in pts: d.ellipse([p['px'] - 5, p['py'] - 5, p['px'] + 5, p['py'] + 5], outline=(0, 200, 255) if p.get('occluded') else (255, 140, 0), width=2)
    if legend_box: d.rectangle(legend_box, outline=(0, 200, 200))
    for t in xt: d.line([t, yb, t, yb + 6], fill=(0, 200, 200))
    for t in yt_: d.line([ax['y_col'] - 6, t, ax['y_col'], t], fill=(0, 200, 200))
    od = PROFILE.get('overlays_dir') if HOST == os.path.dirname(PROFILE['crops_dir'].rstrip('/')) else f'{HOST}/overlays'
    os.makedirs(od, exist_ok=True); ov.save(f'{od}/{panel}_overlay.png')
    return res

CONVENTION, CONVENTION_FROM = None, []
if __name__ == '__main__':
    # usage: digitize.py <paper> <panel> ...   (profile papers/<paper>/profile.json; output papers/<paper>/digitized/)
    paper, panels = sys.argv[1], sys.argv[2:]
    load_profile(paper); out_dir = f'{PAPER_DIR}/digitized'; os.makedirs(out_dir, exist_ok=True)
    # pass 1: own legends; the colour convention = the mapping shared by every panel whose own legend is clean (must agree)
    first = {p: run(p, None) for p in panels}
    clean = {p: r['legend']['mapping'] for p, r in first.items() if (r.get('legend') or {}).get('clean')}
    if clean and len({json.dumps(m, sort_keys=True) for m in clean.values()}) == 1:
        CONVENTION = {float(k): v for k, v in next(iter(clean.values())).items()}; CONVENTION_FROM = sorted(clean)
    elif clean: print('clean legends disagree:', clean)
    for p in panels:
        r = first[p] if p in clean or not CONVENTION else run(p, None); json.dump(r, open(f'{out_dir}/{p}.json', 'w'), indent=1)
        s = {k: len(v) for k, v in (r.get('series') or {}).items()}
        print(p, r['status'], '| x', r.get('x_source'), r.get('x_cal') and (('log' if r['x_cal']['log'] else 'lin'), round(r['x_cal']['resid_px'], 2), r['x_cal']['n']),
              '| y', r.get('y_source'), r.get('y_cal') and (('log' if r['y_cal']['log'] else 'lin'), round(r['y_cal']['resid_px'], 2), r['y_cal']['n']),
              '| legend clean', (r.get('legend') or {}).get('clean'), (r.get('legend') or {}).get('mapping_source', '')[:40], (r.get('legend') or {}).get('mapping'), '| points', s)
