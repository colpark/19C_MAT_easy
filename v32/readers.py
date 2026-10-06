#!/usr/bin/env python3
"""readers.py (v3.2 Stage 5C): feature-level readers for curves, stacked spectra and bars (user instruction 2: only the features the laws
and T1 need). Code only; validated on synthetic replicas per panel style before any real panel is read (rule 5).

Calibration: digitize.py's frame/tick/OCR machinery (find_axes, ticks_along, robust label fit, printed tick entries from the profile).
Series: declared per panel in the profile ('series': [{label, value, colour: [r, g, b] | 'order:<k>'}]); a series mask = pixels of the
declared hue whose luma/chroma fit a white blend of the colour with JPEG desaturation (see series_mask),
or, for stacked monochrome spectra, the k-th trace from the top in each column ('order:<k>').
Trace: per column, the runs of mask pixels; single-valued curves use the run nearest the trace continuation; loops keep all runs
(branch 'upper' / 'lower').
Features (value, u in data units; u = hypot(feature pixel uncertainty, calibration residual) converted with the local scale):
  y_at_x(x[, branch])       curve value at a given x (T1 cells, laws)          u_px = line half-width (+ slope x 1 px in x)
  x_at_extremum(max|min, window)                                               u_px = half the width of the region within 1 px of the extremum
  crossing('x=0' -> y, branch) / crossing('y=0' -> x, branch): loop or curve intercepts (Pr, Ec)
  plateau(x_from, x_to)     mean level of a flat segment (TGA residue, COF steady state)   u = hypot(line half-width, std of the level)
  peak_x(window)            spectrum peak position (top of the trace in a window, parabolic sub-pixel)   u_px = hypot(0.5, half-width at 1 px below the top / 4)
  bar_top(index)            bar value (top edge of the k-th bar of a colour, left to right)   u_px = 1
  y_at_extremum(max|min, window)  value at the extremum (peak stress, maximum wear depth)       u_px = 1
  x_end(side)               x of the last traced column (break strain)                         u_px = hypot(line half-width, 1)
Every reader returns None (not a guess) when the feature is not found; a miss is counted by the replica gate."""
import json, math, os, re, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
sys.path.insert(0, '/home/aid1/Documents/harbor/v32')
import digitize as D

def calibrate(rgb, pc):
    gray = rgb.mean(2); dark = gray < 110; ax = D.find_axes(gray)
    if not ax: return None
    if ax['x_left'] - ax['y_col'] > 10 and dark[ax['x_row'], ax['y_col']:ax['x_left']].mean() >= 0.8: ax['x_left'] = ax['y_col']
    x0, x1, yb, yt = ax['x_left'], ax['x_right'], ax['x_row'], ax['y_top']
    right = pc.get('y_side') == 'right'   # quantity on the right-hand axis (e.g. TGA mass over a DSC plot): ticks and labels of the right frame line
    xt = D.ticks_along(dark, yb, x0, x1, 'x'); yt_ = D.ticks_along(dark, x1 if right else ax['y_col'], yt, yb, 'y')
    bot = rgb[yb + 2:yb + 34, :]
    left = rgb[:, x1 + 2:x1 + 72] if right else rgb[:, max(ax['y_col'] - 62, 0):ax['y_col'] - 2]
    xl = [(t['cx'], numval(t['text'])) for t in D.ocr(bot) if numval(t['text']) is not None]
    yl = [(t['cy'], numval(t['text'])) for t in D.ocr(left) if numval(t['text']) is not None]
    out = {'frame': (x0, x1, yb, yt)}
    for key, majors, ticks, labels in (('x', [t for t, r in xt if r >= 6], xt, xl), ('y', [t for t, r in yt_ if r >= 6], yt_, yl)):
        if pc.get(f'{key}_ticks'):   # declared tick values (profile): matched to the contiguous run of detected majors that fits best
            vals = pc[f'{key}_ticks']; log = pc.get(f'{key}_log', False); maj = sorted(majors, reverse=(key == 'y')); n_ = len(vals)
            if len(maj) < n_: out[key] = None; continue
            fits = [D.fit(maj[i:i + n_], vals, log) for i in range(len(maj) - n_ + 1)]; a, b, r = min(fits, key=lambda f: f[2]); out[key] = (log, a, b, r)
        elif pc.get(f'{key}_none'): out[key] = 'none'   # e.g. intensity (a.u.): no calibration needed
        else:
            cal = D.robust(labels, majors, pc.get(f'{key}_log')); out[key] = cal[:4] if cal else None
        if isinstance(out[key], tuple) and out[key][3] > 1.5: out[key] = None   # residual > 1.5 px: calibration rejected (it would inflate u)
    return out

def numval(t):
    """digitize.numval after one OCR confusion fix: a letter O/o where a digit stands (e.g. 'O.2') is read as 0. A label that still does
    not parse is dropped (never guessed)."""
    t2 = re.sub(r'(?<![A-Za-z])[Oo](?=[\d.,])|(?<=[\d.])[Oo]', '0', t.strip()); return D.numval(t2)

def to_data(cal, p):
    log, a, b, _ = cal; v = a * p + b; return 10 ** v if log else v
def to_px(cal, v):
    log, a, b, _ = cal; return ((math.log10(v) if log else v) - b) / a
def scale(cal, p):   # |d value / d px| at pixel p
    return abs(to_data(cal, p + 0.5) - to_data(cal, p - 0.5))

LUMA = np.array([0.299, 0.587, 0.114])
def _lch(rgb):
    """per pixel: luma L, chroma vector (p - mean(p)) and its length C."""
    p = np.asarray(rgb, float); L = p @ LUMA; ch = p - p.mean(-1, keepdims=True); return L, ch, np.linalg.norm(ch, axis=-1)

def series_mask(rgb, colour, others, inner):
    """mask of one declared series colour, robust to the two things a thin plotted line does to its colour:
      - antialiasing blends it with the white background: luma moves toward 255; the blend fraction a = (255 - L) / (255 - L_c)
        (JPEG keeps luma at full resolution, so a is read from luma);
      - JPEG 4:2:0 chroma subsampling desaturates it: chroma may fall to 0.5 x a x C_c (and up to 1.15 x).
    chromatic colour (C_c >= 20): hue angle of the chroma vector within tol of the declared hue, tol = 25 deg, or 0.45 x the hue
      separation to another declared chromatic colour of similar luma (|dL| < 30) when that is smaller;
    achromatic colour (black/gray): C <= 25.
    mask: 0.45 <= a <= 1.3; core: a >= 0.8. Only connected pieces holding a core pixel are kept."""
    L, ch, C = _lch(rgb); Lc, chc, Cc = _lch(np.array(colour, float)[None])
    Lc, chc, Cc = float(Lc[0]), chc[0], float(Cc[0]); a = (255.0 - L) / max(255.0 - Lc, 1.0)
    if Cc >= 20:
        cosang = (ch @ chc) / np.maximum(C * Cc, 1e-6); ang = np.degrees(np.arccos(np.clip(cosang, -1, 1))); tol = 25.0
        for o in others:
            Lo, cho, Co = _lch(np.array(o, float)[None])
            if float(Co[0]) >= 20 and abs(float(Lo[0]) - Lc) < 30:
                sep = float(np.degrees(np.arccos(np.clip(cho[0] @ chc / (float(Co[0]) * Cc), -1, 1)))); tol = min(tol, 0.45 * sep)
        ok = (ang <= tol) & (C >= 0.5 * np.clip(a, 0, 1) * Cc) & (C <= 1.15 * Cc + 10)
    else:
        tol = 25.0; ok = C <= 25
    m = ok & (a >= 0.45) & (a <= 1.3) & inner
    return core_filter(m, (a >= 0.8) & m), tol, (a >= 0.8) & m

def core_filter(m, core):
    lab, n = ndi.label(m, np.ones((3, 3))); keep = np.zeros(n + 1, bool); keep[np.unique(lab[core & m])] = True; keep[0] = False
    return keep[lab]

def graded_cleanup(masks, colours):
    """graded palettes (same hue, different lightness): the antialiased edge of a darker line has the luma/chroma of a lighter
    series of the same hue, and the core of a lighter line passes the darker series' (non-core) mask test. For same-hue pairs
    (hue within 25 deg, or both achromatic) with luma differing by > 15:
      lighter series: drop pixels within 1 px of the darker series' core (core and mask);
      darker series: drop the lighter series' cleaned core pixels.
    Then the core-component filter is applied again."""
    info = {}
    for k, c in colours.items():
        L, ch, C = _lch(np.array(c, float)[None]); info[k] = (float(L[0]), ch[0], float(C[0]))
    def same(k, o):
        (Lk, chk, Ck), (Lo, cho, Co) = info[k], info[o]
        return (Ck < 20 and Co < 20) or (Ck >= 20 and Co >= 20 and np.degrees(np.arccos(np.clip(chk @ cho / (Ck * Co), -1, 1))) <= 25)
    ring = {k: ndi.binary_dilation(core, np.ones((3, 3))) for k, (m, core) in masks.items()}
    cores = {}
    for k, (m, core) in masks.items():
        c = core.copy()
        for o in masks:
            if o != k and same(k, o) and info[o][0] < info[k][0] - 15: c &= ~ring[o]
        cores[k] = c
    out = {}
    for k, (m, core) in masks.items():
        m = m.copy()
        for o in masks:
            if o == k or not same(k, o): continue
            if info[o][0] < info[k][0] - 15: m &= ~ring[o]
            elif info[o][0] > info[k][0] + 15: m &= ~cores[o]
        out[k] = core_filter(m, cores[k] & m)
    return out

def runs(col):
    idx = np.nonzero(col)[0]
    if not len(idx): return []
    out, s = [], idx[0]
    for a, b in zip(idx, idx[1:]):
        if b != a + 1: out.append((s, a)); s = b
    out.append((s, idx[-1])); return [((a + b) / 2, b - a + 1) for a, b in out]

class Panel:
    def __init__(self, path, pc):
        self.rgb = np.asarray(Image.open(path).convert('RGB')); self.pc = pc
        if pc.get('crop'):   # one subplot of a stacked figure: [x0, y0, x1, y1] in crop pixels (profile input, logged)
            a, b, c, d = pc['crop']; self.rgb = self.rgb[b:d, a:c]
        self.cal = calibrate(self.rgb, pc)
        if not self.cal or not self.cal.get('x') or self.cal['y'] is None: raise ValueError('calibration failed')
        x0, x1, yb, yt = self.cal['frame']; self.inner = np.zeros(self.rgb.shape[:2], bool); self.inner[yt + 3:yb - 2, x0 + 3:x1 - 2] = True
        # tick stubs: inward ticks are short dark strokes inside the frame that a black/gray series mask would take; blank a band of the
        # tick length + 2 px at every tick found on the bottom/left axes, mirrored on the top/right frame lines
        dark = self.rgb.mean(2) < 110
        for t, r in D.ticks_along(dark, yb, x0, x1, 'x'):
            c = int(round(t)); self.inner[max(yb - r - 2, 0):yb + 1, c - 2:c + 3] = False; self.inner[yt:yt + r + 3, c - 2:c + 3] = False
        for t, r in D.ticks_along(dark, x0, yt, yb, 'y'):
            c = int(round(t)); self.inner[c - 2:c + 3, x0:x0 + r + 3] = False; self.inner[c - 2:c + 3, max(x1 - r - 2, 0):x1 + 1] = False
        for box in pc.get('exclude_boxes', []):   # legend or inset regions declared in the profile
            a, b, c, d = box; self.inner[b:d, a:c] = False
        self._traces = {}; self.series = {}; cols = [s['colour'] for s in pc.get('series', []) if isinstance(s.get('colour'), list)]
        raw, colours = {}, {}
        for s in pc.get('series', []):
            if isinstance(s.get('colour'), list):
                m, tol, core = series_mask(self.rgb, s['colour'], [c for c in cols if c != s['colour']], self.inner)
                raw[str(s['value'])] = (m, core); colours[str(s['value'])] = s['colour']; self.series[str(s['value'])] = {'tol': tol}
            else: self.series[str(s['value'])] = {'order': int(str(s['colour']).split(':')[1])}
        for k, m in graded_cleanup(raw, colours).items(): self.series[k]['mask'] = m

    def _col_runs(self, sv, col):
        s = self.series[sv]; col = int(round(col))
        if 'mask' in s:
            r = runs(s['mask'][:, col]); g = self.pc.get('merge_gap', 0)
            if g and len(r) > 1:   # marker series: markers stacked along a steep segment form one run (gap <= merge_gap px)
                ext = [(c - w / 2, c + w / 2) for c, w in r]; out = [list(ext[0])]
                for a, b in ext[1:]:
                    if a - out[-1][1] <= g: out[-1][1] = b
                    else: out.append([a, b])
                r = [((a + b) / 2, b - a) for a, b in out]
            return r
        allm = (self.rgb.mean(2) < 160) & self.inner; r = runs(allm[:, col]); k = s['order']
        return [r[k]] if len(r) > k else []

    def trace(self, sv, branch='only'):
        """{column: (row, run width)} for one series by continuity tracking. 'upper'/'lower' (loop branches): seed = the column nearest
        the centre with exactly two runs, its top/bottom run. 'only' (single-valued curve): seed column (the column with the most common single-run width, near
        the middle), choosing in each next column the run nearest the linear prediction (slope fitted on the last 8 chosen columns); a run
        further than max(4 px, 3 x line width + |slope| x gap) + 0.3 x (gap - 1) + run half-width from the prediction is not taken (gap: the series is hidden or absent there)."""
        key = (sv, branch)
        if key in self._traces: return self._traces[key]
        x0, x1, yb, yt = self.cal['frame']; R_ = {c: self._col_runs(sv, c) for c in range(x0 + 1, x1)}
        mid = (x0 + x1) / 2
        if branch in ('upper', 'lower'):   # loop branch: seed at the column nearest the centre with exactly two runs, then track
            pairs = [c for c, r in R_.items() if len(r) == 2]
            if not pairs: self._traces[key] = {}; return {}
            wmed = float(np.median([t[1] for c in pairs for t in R_[c]])); seed = min(pairs, key=lambda c: abs(c - mid))
            out = {seed: (min(R_[seed]) if branch == 'upper' else max(R_[seed]))}
        else:
            singles = [c for c, r in R_.items() if len(r) == 1]
            if not singles: self._traces[key] = {}; return {}
            wmed = float(np.median([R_[c][0][1] for c in singles]))
            seed = min(singles, key=lambda c: (abs(R_[c][0][1] - wmed) > 1.5, abs(c - mid))); out = {seed: R_[seed][0]}
        for step in (1, -1):
            hist = [seed]; c = seed + step
            while x0 < c < x1:
                if R_.get(c):
                    h = hist[-8:]
                    slope = float(np.polyfit(h, [out[q][0] for q in h], 1)[0]) if len(h) >= 3 and h[-1] != h[0] else 0.0
                    last = hist[-1]; pred = out[last][0] + slope * (c - last); gap = abs(c - last)
                    best = min(R_[c], key=lambda t: abs(t[0] - pred))
                    if abs(best[0] - pred) <= max(4.0, 3 * wmed + abs(slope) * gap) + 0.3 * (gap - 1) + best[1] / 2: out[c] = best; hist.append(c)
                c += step
        self._traces[key] = out; return out

    def y_at_x(self, sv, x, branch='only'):
        cx = self.cal['x']; px = int(round(to_px(cx, x)))
        def at(tr):   # (row, width, gap term) of a trace at column px; a short occlusion (<= 6 columns) is interpolated across
            if px in tr: return tr[px][0], tr[px][1], 0.0
            lft = [c for c in range(px - 1, px - 6, -1) if c in tr]; rgt = [c for c in range(px + 1, px + 6) if c in tr]
            if not lft or not rgt or rgt[0] - lft[0] > 6: return None
            c0, c1 = lft[0], rgt[0]; f = (px - c0) / (c1 - c0); r0, r1 = tr[c0][0], tr[c1][0]
            return r0 + f * (r1 - r0), max(tr[c0][1], tr[c1][1]), abs(r1 - r0) / 2
        if branch in ('upper', 'lower'):
            # two-valued curve (loop, butterfly): both branches are tracked; 'upper'/'lower' = the top/bottom of the two at this x
            # (tracked branches may swap where they cross, e.g. a butterfly at E = 0); the same run on both -> ambiguous, None
            rr = self._col_runs(sv, px)
            if len(rr) == 2: a_, b_ = (rr[0][0], rr[0][1], 0.0), (rr[1][0], rr[1][1], 0.0)   # exactly two runs here: the two branches
            else:   # more (contamination, stacked runs) or fewer: fall back on the tracked branches
                a_, b_ = at(self.trace(sv, 'upper')), at(self.trace(sv, 'lower'))
            if a_ is None or b_ is None or abs(a_[0] - b_[0]) <= 0.5 * max(a_[1], b_[1]): return None
            row, w, gap_u = (min if branch == 'upper' else max)((a_, b_), key=lambda t: t[0])
        else:
            r_ = at(self.trace(sv, branch))
            if r_ is None: return None
            row, w, gap_u = r_
        tr = self.trace(sv, branch)
        cy = self.cal['y']; v = to_data(cy, row)
        sl = [abs(tr[px + dc][0] - row) / 2 for dc in (-2, 2) if px + dc in tr]   # slope term: rows 2 columns either side
        upx = math.hypot(w / 2, cy[3], (max(sl) if sl else 0), gap_u)
        return v, scale(cy, row) * upx

    def x_at_extremum(self, sv, kind, window):
        cx, cy = self.cal['x'], self.cal['y']; a, b = sorted(to_px(cx, w) for w in window); tr = self.trace(sv)
        best = [(c, tr[c][0] - (tr[c][1] - 1) / 2 * (1 if kind == 'max' else -1)) for c in range(int(math.ceil(a)), int(b) + 1) if c in tr]
        if len(best) < 3: return None
        rows = np.array([t[1] for t in best]); ext = rows.min() if kind == 'max' else rows.max()
        near = [c for c, rw in best if abs(rw - ext) <= 1.0]; cpos = float(np.mean(near)); halfw = (max(near) - min(near)) / 2
        return to_data(cx, cpos), scale(cx, cpos) * math.hypot(halfw, 0.5, cx[3])

    def y_at_extremum(self, sv, kind, window):
        """value at the extremum of a single-valued curve (peak stress, maximum wear depth): extreme run centre of the trace in the window,
        u = hypot(1 px, line half-width / 2, calibration residual)."""
        cx, cy = self.cal['x'], self.cal['y']; a, b = sorted(to_px(cx, w) for w in window); tr = self.trace(sv)
        cs = [c for c in range(int(math.ceil(a)), int(b) + 1) if c in tr]
        if len(cs) < 3: return None
        wmed = float(np.median([tr[q][1] for q in tr])); sg = 1 if kind == 'max' else -1
        # outer edge of each run moved back by half the median line width: equals the centre for ordinary columns, and gives the tip
        # (not the middle) of a vertical segment such as the drop at a stress-strain break
        edge = {q: tr[q][0] - sg * (tr[q][1] - wmed) / 2 for q in cs}
        c = (min if kind == 'max' else max)(cs, key=lambda q: edge[q]); row = edge[c]
        # local roughness of a noisy trace (rows minus a 9-column running median, within 10 columns): the extreme of a noisy line is
        # not defined better than that
        near = [q for q in range(c - 10, c + 11) if q in tr]
        rough = float(np.std([tr[q][0] - np.median([tr[k][0] for k in range(q - 4, q + 5) if k in tr]) for q in near])) if len(near) >= 5 else 0.0
        return to_data(cy, row), scale(cy, row) * math.hypot(1.0, wmed / 4, rough, cy[3])

    def x_end(self, sv, side='right'):
        """x of the last (or first) traced column of a curve (break strain of a stress-strain curve): u = hypot(line half-width, 1 px)."""
        cx = self.cal['x']; tr = self.trace(sv)
        if len(tr) < 5: return None
        c = max(tr) if side == 'right' else min(tr); hw = float(np.median([tr[q][1] for q in tr])) / 2
        c = c - (hw - 0.5) if side == 'right' else c + (hw - 0.5)   # the last column is the outer edge of the line, not its centre
        return to_data(cx, c), scale(cx, c) * math.hypot(hw, 1.0, cx[3])

    def crossing(self, sv, line, branch='upper'):
        cx, cy = self.cal['x'], self.cal['y']
        if line == 'x=0':   # value of y where the curve crosses x = 0
            return self.y_at_x(sv, 0.0, branch)
        # line == 'y=0': x where the branch crosses y = 0 (branch 'left' / 'right' for loops)
        r0 = to_px(cy, 0.0); x0, x1, yb, yt = self.cal['frame']; hits = []
        for c in range(x0 + 4, x1 - 3):
            rr = self._col_runs(sv, c)
            if any(abs(t[0] - r0) <= max(1.0, t[1] / 2) for t in rr): hits.append(c)
        if not hits: return None
        groups = [[hits[0]]]
        for h in hits[1:]:
            if h - groups[-1][-1] <= 6: groups[-1].append(h)   # neighbouring loops occlude parts of a steep crossing
            else: groups.append([h])
        if branch in ('left', 'right') and len(groups) != 2: return None   # a loop crosses y = 0 exactly twice; otherwise ambiguous
        g = groups[0] if branch == 'left' else groups[-1]; cpos = float(np.mean(g))
        return to_data(cx, cpos), scale(cx, cpos) * math.hypot((max(g) - min(g)) / 2 + 0.5, cx[3])

    def plateau(self, sv, x_from, x_to):
        cx, cy = self.cal['x'], self.cal['y']; a, b = sorted((to_px(cx, x_from), to_px(cx, x_to))); tr = self.trace(sv); rows, ws = [], []
        for c in range(int(math.ceil(a)), int(b) + 1):
            if c in tr: rows.append(tr[c][0]); ws.append(tr[c][1])
        if len(rows) < 3: return None
        row = float(np.mean(rows)); v = to_data(cy, row)
        return v, scale(cy, row) * math.hypot(float(np.mean(ws)) / 2, float(np.std(rows)), cy[3])

    def peak_x(self, sv, window, kind='max'):
        """kind 'max': top of the trace (spectra, XRD); 'min': bottom (transmittance dips), handled by mirroring rows."""
        cx = self.cal['x']; a, b = sorted(to_px(cx, w) for w in window); tops = []; sg = 1 if kind == 'max' else -1
        for c in range(int(a), int(b) + 1):
            r = self._col_runs(sv, c)
            if r: tops.append((c, min(sg * (t[0] - sg * t[1] / 2) for t in r)))
        if len(tops) < 5: return None
        cs = np.array([t[0] for t in tops], float); rs = np.array([t[1] for t in tops], float); i = int(rs.argmin())
        if i in (0, len(rs) - 1): return None   # top on the window edge: no peak inside
        lo, hi = max(i - 3, 0), min(i + 4, len(rs)); p = np.polyfit(cs[lo:hi], rs[lo:hi], 2)
        c0 = -p[1] / (2 * p[0]) if p[0] > 0 else cs[i]
        if not cs[lo] <= c0 <= cs[hi - 1]: c0 = cs[i]
        flat = cs[rs <= rs[i] + 1.0]; halfw = (flat.max() - flat.min()) / 2
        return to_data(cx, c0), scale(cx, c0) * math.hypot(0.5, halfw / 4, cx[3])

    def bar_top(self, sv, index):
        s = self.series[sv]; m = s['mask']; colsum = m.sum(0); bars = []; inbar = False
        for c, n in enumerate(colsum):
            if n >= 3 and not inbar: start = c; inbar = True
            elif n < 3 and inbar: bars.append((start, c - 1)); inbar = False
        bars = [b for b in bars if b[1] - b[0] >= 3]
        if index >= len(bars): return None
        a, b = bars[index]; tops = [np.nonzero(m[:, c])[0].min() for c in range(a + 1, b) if m[:, c].any()]
        row = float(np.median(tops)); cy = self.cal['y']
        return to_data(cy, row), scale(cy, row) * math.hypot(1.0, cy[3])

FEATURES = ('y_at_x', 'x_at_extremum', 'y_at_extremum', 'x_end', 'crossing', 'plateau', 'peak_x', 'bar_top')
def read(panel, feat):
    """feat: {'type', 'series', 'args': {...}} -> (value, u) or None."""
    f = getattr(panel, feat['type']); return f(str(feat['series']), **feat.get('args', {}))
