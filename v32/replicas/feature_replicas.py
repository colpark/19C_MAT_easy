#!/usr/bin/env python3
"""feature_replicas.py (v3.2 Stage 5C): synthetic replicas per panel style with known feature values, and the A5 gate in feature units.
A style = (paper, kind) defined by a representative real panel: image size, frame (find_axes), series count and colours (k-means of the
panel's chromatic pixels; stacked monochrome spectra use trace order). Kinds and truth features:
  curve     smooth single-valued series (sigmoid/exponential/polynomial mixes)   -> y_at_x, x_at_extremum
  loop      P-E style hysteresis loops (tanh branches)                          -> crossing x=0 (upper branch), crossing y=0 (right branch)
  plateau   TGA style decay to a residue / COF settling to a level             -> plateau
  spectrum  stacked spectra: Lorentzian peaks on a baseline with offsets       -> peak_x
  bar       bars per series                                                    -> bar_top
Rendering: 2x supersampled lines (panel line width), DejaVu labels at real-panel scale, legend box in the real legend region, blur 0.5,
JPEG quality 90. Truth: exact feature values from the analytic functions (peak position = argmax of the rendered trace, sampled finely).
Gate per (style, feature type), pooled over 5 replicas: >= 95% of found features within 2u, |mean error/u| <= 0.5, >= 80% of visible
features found (the Phase 3 coverage criterion; 'all_visible_found' is reported too); a feature hidden under a later-drawn series (series-id render) may be returned as None ('flagged'); a read of a hidden one still counts.
usage: feature_replicas.py make|check   (styles in replicas/feature_styles.json)"""
import json, math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
V32 = '/home/aid1/Documents/harbor/v32'; HOSTP = '/home/aid1/Documents/harbor/v32_host/papers'; sys.path.insert(0, V32)
import digitize as D, readers as R
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
OUT = '/home/aid1/Documents/harbor/v32_host/feature_replicas'; TRUTH = f'{V32}/replicas/feature_truth'

def palette(rgb, frame, k):
    x0, x1, yb, yt = frame; px = rgb[yt + 4:yb - 3, x0 + 4:x1 - 3].reshape(-1, 3).astype(float)
    sat = px.max(1) - px.min(1); px = px[(sat > 60) & (px.max(1) > 60)]
    if len(px) < k * 20: return [[30, 30, 30]] * k
    rng = np.random.RandomState(0); C = px[rng.choice(len(px), k, replace=False)]
    for _ in range(25):
        lab = ((px[:, None, :] - C[None]) ** 2).sum(2).argmin(1)
        C = np.array([px[lab == i].mean(0) if (lab == i).any() else C[i] for i in range(k)])
    lab = ((px[:, None, :] - C[None]) ** 2).sum(2).argmin(1); sat = px.max(1) - px.min(1)
    C = [px[lab == i][sat[lab == i] >= np.percentile(sat[lab == i], 70)].mean(0) if (lab == i).sum() > 5 else C[i] for i in range(k)]   # line core, not edge blends
    C = sorted([list(c) for c in C], key=lambda c: (c[0] - c[2]))
    return [[int(v) for v in c] for c in C]

def nice_ticks(lo, hi, n=6):
    span = hi - lo; step = 10 ** math.floor(math.log10(span / n)); step *= min((1, 2, 2.5, 5, 10), key=lambda m: abs(span / (m * step) - n))
    s = math.ceil(lo / step) * step; return [round(s + i * step, 10) for i in range(int((hi - s) / step + 1e-9) + 1)]

def make_series(kind, n, rng, xr):
    a, b = xr; S = []
    for i in range(n):
        if kind == 'curve':
            c1, c2, c3 = rng.uniform(0.2, 1.0), rng.uniform(-0.5, 0.5), rng.uniform(0.3, 0.7)
            S.append(lambda x, c1=c1, c2=c2, c3=c3, i=i: 0.6 * c1 * np.exp(-((x - (a + c3 * (b - a))) / (0.35 * (b - a))) ** 2) + 0.15 * c2 * (x - a) / (b - a) + 0.2 + 0.1 * i)
        elif kind == 'plateau':
            r0, k_, t0 = rng.uniform(0.25, 0.6), rng.uniform(8, 14), rng.uniform(0.3, 0.5)
            S.append(lambda x, r0=r0, k_=k_, t0=t0: r0 + (1 - r0) / (1 + np.exp(k_ * ((x - a) / (b - a) - t0))))
        elif kind == 'spectrum':
            c = rng.uniform(0.35, 0.65); w = rng.uniform(0.015, 0.04); c2 = c + rng.choice([-1, 1]) * rng.uniform(0.18, 0.28)
            S.append(lambda x, c=c, w=w, c2=c2, i=i: 0.15 * i + 0.02 + 0.10 / (1 + ((x - (a + c * (b - a))) / (w * (b - a))) ** 2) + 0.05 / (1 + ((x - (a + c2 * (b - a))) / (0.03 * (b - a))) ** 2))
        elif kind == 'bar':
            S.append(rng.uniform(0.2, 0.9))
        elif kind == 'dip':   # stacked transmittance spectra with two absorption dips
            c = rng.uniform(0.3, 0.7); w = rng.uniform(0.02, 0.05); c2 = c + rng.choice([-1, 1]) * rng.uniform(0.15, 0.25)
            S.append(lambda x, c=c, w=w, c2=c2, i=i: 0.18 * i + 0.14 - 0.10 / (1 + ((x - (a + c * (b - a))) / (w * (b - a))) ** 2) - 0.05 / (1 + ((x - (a + c2 * (b - a))) / (0.03 * (b - a))) ** 2))
        elif kind in ('noisy', 'wear'):   # deterministic noise on a fine grid, interpolated
            g = np.linspace(a, b, 600); nz = np.array([rng.gauss(0, 1) for _ in g]); nz = np.convolve(nz, np.ones(3) / 3, 'same')
            if kind == 'noisy':
                lev, tau = rng.uniform(0.25, 0.4), rng.uniform(0.04, 0.2); amp = rng.uniform(0.004, 0.012)
                S.append(lambda x, lev=lev, tau=tau, amp=amp, g=g, nz=nz: lev * (1 - np.exp(-(np.asarray(x) - a) / (tau * (b - a)))) + amp * np.interp(x, g, nz))
            else:
                c, hw, D_ = rng.uniform(0.45, 0.55), rng.uniform(0.25, 0.4), rng.uniform(0.2, 1.0); amp = rng.uniform(0.01, 0.03)
                S.append(lambda x, c=c, hw=hw, D_=D_, amp=amp, g=g, nz=nz: -D_ * np.clip(1 - ((np.asarray(x) - (a + c * (b - a))) / (hw * (b - a))) ** 2, 0, None) + 0.1 * i + amp * np.interp(x, g, nz))
        elif kind == 'stress_strain':   # flat toe, saturating rise, break at x_b (vertical drop drawn separately)
            xs_, xb = rng.uniform(0.0, 0.35), rng.uniform(0.5, 0.95); Sm, tau = rng.uniform(0.4, 1.0), rng.uniform(0.3, 1.5)
            S.append((xs_, xb, Sm, tau))
    return S

def stroke(g, pts, width, fill):
    """thick polyline as stamped discs every <= 0.5 supersampled px: symmetric about the given coordinates (PIL's own wide lines are
    centred differently for straight lines and polylines, which shifted curves against ticks by half an output pixel)."""
    r = width / 2.0
    for (xa, ya), (xb, yb_) in zip(pts, pts[1:] if len(pts) > 1 else pts):
        k = max(1, int(math.ceil(math.hypot(xb - xa, yb_ - ya) / 0.5)))
        for j in range(k + 1):
            x = xa + (xb - xa) * j / k; y = ya + (yb_ - ya) * j / k; g.ellipse([x - r + 0.5, y - r + 0.5, x + r - 0.5, y + r - 0.5], fill=fill)

def render(style, rng):
    W, H = style['size']; x0, x1, yb, yt = style['frame']; n = style['n']; kind = style['kind']; lw = style.get('lw', 2)
    xr = style['xrange']; cols = style['colours'] if kind not in ('spectrum', 'dip') or style.get('chromatic') else [[25, 25, 25]] * n
    sc = 2; im = Image.new('RGB', (W * sc, H * sc), 'white'); d = ImageDraw.Draw(im); idm = Image.new('L', (W * sc, H * sc), 0); di = ImageDraw.Draw(idm); solo = [Image.new('L', (W * sc, H * sc), 0) for _ in range(n)]; fs_ = int(round(15 * max(1.0, W / 600))); f = ImageFont.truetype(FONT, fs_ * sc)   # tick labels scale with the panel, as in the real crops
    truth = {'series': [], 'features': []}; xs = np.linspace(xr[0], xr[1], 1200)
    if kind in ('loop', 'butterfly'):
        if style.get('separated'): Ec = [xr[1] * (0.12 + 0.07 * k + rng.uniform(-0.01, 0.01)) for k in range(n)]; Ps = [rng.uniform(0.8, 0.9) for _ in range(n)]
        else: Ec = [rng.uniform(0.35, 0.6) * xr[1] for _ in range(n)]; Ps = [rng.uniform(0.6, 0.9) for _ in range(n)]
        yr = (-1.0, 1.0) if kind == 'loop' else (-0.1, 1.0)
    elif kind == 'bar': yr = (-0.5, 1.0) if style.get('negative') else (0.0, 1.0)
    elif kind == 'stress_strain':
        fs = make_series(kind, n, rng, xr); yr = (-0.05, 1.08)
        def ss_fn(prm, x):
            xs_, xb, Sm, tau = prm; xx = (np.asarray(x) - xr[0]) / (xr[1] - xr[0]); t = np.clip(xx - xs_, 0, None)
            return np.where(xx <= xb, Sm * (1 - np.exp(-t / tau)) / (1 - np.exp(-(xb - xs_) / tau)) * (xb - xs_ > 0), np.nan)
    else:
        fs = make_series(kind, n, rng, xr); vals = np.concatenate([fn(xs) for fn in fs]); pad = 0.05 * (vals.max() - vals.min()); yr = (float(vals.min()) - pad, float(vals.max()) + 1.6 * pad)
    TW = style.get('tick_w', 2) * sc; g_ = style.get('frame_grey', 0); TC = (g_, g_, g_)   # thin grey frames and ticks (resampled figures)
    S = lambda p: p * sc + (sc - 1) / 2   # output pixel centre p -> supersampled coordinate (LANCZOS 2x box: output j = sup 2j..2j+1)
    fx = lambda x: x0 + (x - xr[0]) / (xr[1] - xr[0]) * (x1 - x0); fy = lambda y: yb - (y - yr[0]) / (yr[1] - yr[0]) * (yb - yt)
    for t in nice_ticks(*xr):
        p = fx(t)
        if x0 < p < x1: stroke(d, [(S(p), S(yb)), (S(p), S(yb - 7))], TW, TC); s = '%g' % t; d.text(((p - 0.27 * fs_ * len(s)) * sc, (yb + 6) * sc), s, fill=(0, 0, 0), font=f)
    if not style.get('y_none'):
        for t in nice_ticks(*yr):
            p = fy(t)
            if not yt < p < yb: continue
            s = '%g' % t
            if style.get('y_side') == 'right':   # quantity on the right axis; the left axis carries another quantity (scaled 0..100)
                stroke(d, [(S(x1), S(p)), (S(x1 - 7), S(p))], TW, TC); d.text(((x1 + 6) * sc, (p - 0.6 * fs_) * sc), s, fill=(0, 0, 0), font=f)
                lv = '%g' % round((p - yt) / (yb - yt) * 100); stroke(d, [(S(x0), S(p)), (S(x0 + 7), S(p))], TW, TC); d.text(((x0 - 0.6 * fs_ * len(lv) - 6) * sc, (p - 0.6 * fs_) * sc), lv, fill=(0, 0, 0), font=f)
            else:
                stroke(d, [(S(x0), S(p)), (S(x0 + 7), S(p))], TW, TC); d.text(((x0 - 0.6 * fs_ * len(s) - 6) * sc, (p - 0.6 * fs_) * sc), s, fill=(0, 0, 0), font=f)
    def draw(i, pts, col):   # a series as a line, as markers (every marker_step px along the path), or both
        targets = ((d, col), (di, i + 1), (ImageDraw.Draw(solo[i]), 255))
        if not style.get('marker') or style.get('marker_line'):
            for g_, fill in targets: stroke(g_, pts, lw * sc, fill)
        if style.get('marker'):
            r = style['marker'] * sc; step = style.get('marker_step', 6) * sc; last = None
            for q in pts:
                if last is None or math.hypot(q[0] - last[0], q[1] - last[1]) >= step:
                    for g_, fill in targets: g_.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=fill)
                    last = q
    for i in range(n):
        col = tuple(cols[i % len(cols)])
        if kind == 'loop':
            up = lambda e, i=i: Ps[i] * np.tanh((e + Ec[i]) / (0.25 * xr[1])); lo = lambda e, i=i: Ps[i] * np.tanh((e - Ec[i]) / (0.25 * xr[1]))
            for br in (up, lo): draw(i, [(S(fx(e)), S(fy(br(e)))) for e in xs], col)
            truth['features'] += [{'type': 'crossing', 'series': str(i), 'args': {'line': 'x=0', 'branch': 'upper'}, 'value': float(up(0.0)), 'at': [[fx(0.0), fy(up(0.0))]]},
                                  {'type': 'crossing', 'series': str(i), 'args': {'line': 'y=0', 'branch': 'right'}, 'value': float(Ec[i]), 'at': [[fx(Ec[i]), fy(0.0)]]}]
            e1 = 0.5 * xr[1]; vu, vl = float(up(e1)), float(lo(e1))   # P at a given E on both branches (electrostriction fit input)
            truth['features'] += [{'type': 'y_at_x', 'series': str(i), 'args': {'x': e1, 'branch': 'upper'}, 'value': max(vu, vl), 'at': [[fx(e1), fy(max(vu, vl))]]},
                                  {'type': 'y_at_x', 'series': str(i), 'args': {'x': e1, 'branch': 'lower'}, 'value': min(vu, vl), 'at': [[fx(e1), fy(min(vu, vl))]]}]
        elif kind == 'butterfly':   # S = q P^2 on both branches; at E = +Ec/2 the branches are well apart
            q_ = rng.uniform(0.8, 1.1); w_ = 0.25 * xr[1]
            up = lambda e, i=i: q_ * (Ps[i] * np.tanh((e + Ec[i]) / w_)) ** 2; lo = lambda e, i=i: q_ * (Ps[i] * np.tanh((e - Ec[i]) / w_)) ** 2
            for br in (up, lo): draw(i, [(S(fx(e)), S(fy(br(e)))) for e in xs], col)
            e0 = 0.5 * Ec[i]; hi_, lo_ = max(up(e0), lo(e0)), min(up(e0), lo(e0))
            truth['features'] += [{'type': 'y_at_x', 'series': str(i), 'args': {'x': e0, 'branch': 'upper'}, 'value': float(hi_), 'at': [[fx(e0), fy(hi_)]]},
                                  {'type': 'y_at_x', 'series': str(i), 'args': {'x': e0, 'branch': 'lower'}, 'value': float(lo_), 'at': [[fx(e0), fy(lo_)]]}]
        elif kind == 'stress_strain':
            prm = fs[i]; xb = xr[0] + prm[1] * (xr[1] - xr[0]); xx = xs[xs <= xb]; yy = ss_fn(prm, xx)
            pts = [(S(fx(x)), S(fy(y))) for x, y in zip(xx, yy)] + [(S(fx(xb)), S(fy(0.0)))]; draw(i, pts, col)
            ytop = float(ss_fn(prm, xb - 1e-9))
            truth['features'] += [{'type': 'x_end', 'series': str(i), 'args': {}, 'value': float(xb), 'at': [[fx(xb), fy(ytop / 2)]]},
                                  {'type': 'y_at_extremum', 'series': str(i), 'args': {'kind': 'max', 'window': [xr[0], xr[1]]}, 'value': ytop, 'at': [[fx(xb) - 2, fy(ytop)]]}]
        elif kind == 'bar':
            v = make_series('bar', 1, rng, xr)[0]; bw = (x1 - x0) / (2.5 * n); cx_ = x0 + (i + 0.75) * (x1 - x0) / (n + 0.5)
            if style.get('negative') and i == n - 1: v = -rng.uniform(0.1, 0.4)   # one bar below the zero line
            ytop, ybot = (fy(v), fy(0.0)) if v >= 0 else (fy(0.0), fy(v))
            if style.get('gradient'):   # fill fades from the bar colour at the outer edge toward white at the zero line
                for yy in np.arange(ytop, ybot, 0.5):
                    f_ = (yy - ytop) / max(ybot - ytop, 1e-6) if v >= 0 else (ybot - yy) / max(ybot - ytop, 1e-6)
                    cc = tuple(int(c + (255 - c) * style['gradient'] * f_) for c in col); d.line([(S(cx_ - bw / 2), S(yy)), (S(cx_ + bw / 2), S(yy))], fill=cc, width=sc)
            else: d.rectangle([S(cx_ - bw / 2), S(ytop), S(cx_ + bw / 2), S(ybot)], fill=col)
            if style.get('errorbars'):   # central error bar with caps, and three replicate dots near the outer edge
                e = rng.uniform(0.03, 0.08) * (yr[1] - yr[0]); sg = 1 if v >= 0 else -1
                stroke(d, [(S(cx_), S(fy(v - e))), (S(cx_), S(fy(v + e)))], 1.5 * sc, (20, 20, 20))
                for vv in (v - e, v + e): stroke(d, [(S(cx_ - 0.2 * bw), S(fy(vv))), (S(cx_ + 0.2 * bw), S(fy(vv)))], 1.5 * sc, (20, 20, 20))
                for dx_, dv in ((-0.12, 0.6), (0.0, -0.5), (0.12, 0.1)):
                    px_, py_ = S(cx_ + dx_ * bw), S(fy(v + dv * e)); d.ellipse([px_ - 2.5 * sc, py_ - 2.5 * sc, px_ + 2.5 * sc, py_ + 2.5 * sc], outline=(30, 90, 160), width=sc)
            truth['features'].append({'type': 'bar_top', 'series': str(i), 'args': {'index': 0}, 'value': float(v)})
        else:
            fn = fs[i]; xd = xs[(xs >= xr[0] + 0.08 * (xr[1] - xr[0])) & (xs <= xr[0] + 0.95 * (xr[1] - xr[0]))] if kind == 'wear' else xs   # real wear profiles stay clear of the axes
            pts = [(S(fx(x)), S(fy(fn(x)))) for x in xd]; draw(i, pts, col)
            sv = str(i)
            if kind == 'curve':
                for q in (0.3, 0.7):
                    xv = xr[0] + q * (xr[1] - xr[0]); truth['features'].append({'type': 'y_at_x', 'series': sv, 'args': {'x': xv}, 'value': float(fn(xv)), 'at': [[fx(xv), fy(fn(xv))]]})
                win = (xr[0] + 0.1 * (xr[1] - xr[0]), xr[0] + 0.9 * (xr[1] - xr[0])); fine = np.linspace(*win, 20000)
                truth['features'].append({'type': 'x_at_extremum', 'series': sv, 'args': {'kind': 'max', 'window': list(win)}, 'value': float(fine[fn(fine).argmax()]), 'at': [[fx(fine[fn(fine).argmax()]), fy(fn(fine).max())]]})
                truth['features'].append({'type': 'y_at_extremum', 'series': sv, 'args': {'kind': 'max', 'window': list(win)}, 'value': float(fn(fine).max()), 'at': [[fx(fine[fn(fine).argmax()]), fy(fn(fine).max())]]})
            elif kind == 'noisy':   # plateau of a noisy trace: truth = mean of the drawn values in the window
                win = (xr[0] + 0.7 * (xr[1] - xr[0]), xr[0] + 0.95 * (xr[1] - xr[0])); sel = xs[(xs >= win[0]) & (xs <= win[1])]
                truth['features'].append({'type': 'plateau', 'series': sv, 'args': {'x_from': win[0], 'x_to': win[1]}, 'value': float(fn(sel).mean()), 'at': [[fx(x), fy(fn(x))] for x in sel[::20]]})
            elif kind == 'wear':   # maximum depth of a noisy profile: truth = minimum of the drawn values
                win = (xr[0] + 0.15 * (xr[1] - xr[0]), xr[0] + 0.85 * (xr[1] - xr[0])); sel = xs[(xs >= win[0]) & (xs <= win[1])]; j = int(fn(sel).argmin())
                truth['features'].append({'type': 'y_at_extremum', 'series': sv, 'args': {'kind': 'min', 'window': list(win)}, 'value': float(fn(sel)[j]), 'at': [[fx(sel[j]), fy(fn(sel)[j])]]})
            elif kind == 'dip':
                fine = np.linspace(xr[0], xr[1], 40000); y = fn(fine); j = int(y.argmin()); c = fine[j]
                win = (max(xr[0], c - 0.08 * (xr[1] - xr[0])), min(xr[1], c + 0.08 * (xr[1] - xr[0])))
                truth['features'].append({'type': 'peak_x', 'series': sv, 'args': {'window': list(win), 'kind': 'min'}, 'value': float(c), 'at': [[fx(c), fy(float(y[j]))]]})
            elif kind == 'plateau':
                for q in (0.3, 0.6):
                    xv = xr[0] + q * (xr[1] - xr[0]); truth['features'].append({'type': 'y_at_x', 'series': sv, 'args': {'x': xv}, 'value': float(fn(xv)), 'at': [[fx(xv), fy(fn(xv))]]})
                win = (xr[0] + 0.82 * (xr[1] - xr[0]), xr[0] + 0.97 * (xr[1] - xr[0])); fine = np.linspace(*win, 2000)
                truth['features'].append({'type': 'plateau', 'series': sv, 'args': {'x_from': win[0], 'x_to': win[1]}, 'value': float(fn(fine).mean()), 'at': [[fx(x), fy(fn(x))] for x in fine[::50]]})
            elif kind == 'spectrum':
                fine = np.linspace(xr[0], xr[1], 40000); y = fn(fine); j = int(y.argmax()); c = fine[j]
                win = (max(xr[0], c - 0.08 * (xr[1] - xr[0])), min(xr[1], c + 0.08 * (xr[1] - xr[0])))
                truth['features'].append({'type': 'peak_x', 'series': sv, 'args': {'window': list(win)}, 'value': float(c), 'at': [[fx(c), fy(float(y[j]))]]})
    # frame drawn last (spines on top of the data, as matplotlib/Origin do)
    fw = style.get('frame_w', 1.5) * sc   # frame lines centred on the frame coordinates (pixel-aligned after downsampling)
    o_ = rng.uniform(0.2, 0.8) if style.get('frame_split') else 0.0   # a 1-px line at a sub-pixel position: resampling splits it over two pixels
    for (p0, p1) in (((x0, yb), (x1, yb)), ((x0, yt), (x1, yt)), ((x0, yt), (x0, yb)), ((x1, yt), (x1, yb))):
        stroke(d, [(S(p0[0] + o_), S(p0[1] + o_)), (S(p1[0] + o_), S(p1[1] + o_))], fw, TC)
    ida = np.asarray(idm)   # visibility: >= 75% of the series' own line footprint within 1.5 px of the check point is on top (series-id render)
    for ft in truth['features']:
        if 'at' not in ft: ft['visible'] = True; continue
        sid = int(ft['series']) + 1; hit = []
        for xp, yp in ft.pop('at'):
            a, b = int(round(S(yp))), int(round(S(xp))); r_ = int(1.5 * sc) + int(lw * sc) // 2
            fp = np.asarray(solo[sid - 1])[max(a - r_, 0):a + r_ + 1, max(b - r_, 0):b + r_ + 1] > 0
            top = ida[max(a - r_, 0):a + r_ + 1, max(b - r_, 0):b + r_ + 1] == sid
            hit.append(bool(fp.any() and (top & fp).sum() >= 0.75 * fp.sum()))
        ft['visible'] = bool(np.mean(hit) >= 0.5)
    im = im.resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.5))
    series_decl = ([{'label': str(i), 'value': str(i), 'colour': (list(cols[i]) if kind not in ('spectrum', 'dip') or style.get('chromatic') else f'order:{n - 1 - i}')} for i in range(n)])
    pc = {'series': series_decl, 'y_none': bool(style.get('y_none'))}
    if style.get('y_side'): pc['y_side'] = style['y_side']
    if style.get('marker'): pc['merge_gap'] = int(math.ceil(style['marker']))   # declared with the series in the real profile
    if style.get('gradient'): pc['gradient_fill'] = True   # declared with the series in the profile (the fill is visible)
    if style.get('y_ticks_declared'): pc['y_ticks'] = [t for t in nice_ticks(*yr) if yt < fy(t) < yb]   # negative labels OCR-unreliable: declared
    if style.get('x_ticks_declared'): pc['x_ticks'] = [t for t in nice_ticks(*xr) if x0 < fx(t) < x1]   # x labels clipped in the real crop: values declared in the profile
    return im, truth, pc

def styles():
    return json.load(open(f'{V32}/replicas/feature_styles.json'))

def make():
    os.makedirs(TRUTH, exist_ok=True); out = []
    for st in styles():
        src = f"/home/aid1/Documents/harbor/v32_host/fidelity/{st['paper']}/crops/{st['panel']}.jpg" if st['paper'] == 'S030' else f"{HOSTP}/{st['paper']}/crops/{st['panel']}.jpg"
        rgb = np.asarray(Image.open(src).convert('RGB'))
        if st.get('subplot'):   # style taken from one subplot of a grid figure (fractions of the crop)
            fa, fb, fc, fd = st['subplot']; H_, W_ = rgb.shape[:2]; rgb = rgb[int(fb * H_):int(fd * H_), int(fa * W_):int(fc * W_)]
        ax = D.find_axes(rgb.mean(2))
        h_, w_ = rgb.shape[:2]; st['size'] = [w_, h_]
        if st.get('frame_declared'): st['frame'] = st['frame_declared']   # geometry of a real panel whose thin frame find_axes misses
        elif ax: st['frame'] = [ax['x_left'], ax['x_right'], ax['x_row'], ax['y_top']]
        else: st['frame'] = [int(0.2 * w_), int(0.95 * w_), int(0.8 * h_), int(0.08 * h_)]; print(st['id'], 'no frame found on the real panel: default frame')
        if st.get('colours'): pass   # declared in the style file (e.g. a black loop)
        elif st['kind'] != 'spectrum' or st.get('chromatic'): st['colours'] = palette(rgb, st['frame'], st['n'])
        else: st['colours'] = [[25, 25, 25]]
        for k in range(5):
            rng = random.Random(f"{st['id']}|{k}"); im, truth, pc = render(st, rng)
            d = f"{OUT}/{st['id']}_r{k}"; os.makedirs(d, exist_ok=True); im.save(f'{d}/panel.jpg', quality=90)
            json.dump({'style': st, 'truth': truth, 'pc': pc}, open(f"{TRUTH}/{st['id']}_r{k}.json", 'w'), indent=1)
        out.append(st['id'])
    print('styles rendered:', out)

def check():
    import glob
    res = {}
    for tf in sorted(glob.glob(f'{TRUTH}/*.json')):
        t = json.load(open(tf)); st = t['style']; img = f"{OUT}/{os.path.basename(tf)[:-5]}/panel.jpg"
        pc = dict(t['pc']); pc['y_none'] = t['pc'].get('y_none')
        try: P = R.Panel(img, pc)
        except R.Refused as e:   # refusal by design: no read, no key
            for ft in t['truth']['features']: res.setdefault((st['id'], ft['type']), []).append(('refused', None))
            continue
        except Exception as e:
            for ft in t['truth']['features']: res.setdefault((st['id'], ft['type']), []).append(('calibration failed', None))
            continue
        for ft in t['truth']['features']:
            if P.series.get(str(ft['series']), {}).get('unreadable'): ft['visible'] = False   # declared-colour rule: never read, never keyed
            try: r = R.read(P, ft)
            except Exception as e: r = None
            res.setdefault((st['id'], ft['type']), []).append((('miss' if ft.get('visible', True) else 'flagged (occluded)'), None) if r is None else ('ok', (r[0] - ft['value']) / r[1] if r[1] > 0 else float('inf')))
    out = []
    print(f"{'style':22} {'feature':14} {'n':>3} {'found':>5} {'flag':>4} {'cov':>5} {'<=2u':>6} {'bias(u)':>8} gate")
    for (sid, ft), v in sorted(res.items()):
        e = [x for s, x in v if s == 'ok']; found = len(e); w = sum(abs(x) <= 2 for x in e) / max(found, 1); b = float(np.mean(e)) if e else float('nan')
        nflag = sum(s == 'flagged (occluded)' for s, _ in v); vis = len(v) - nflag
        cov = found / max(vis, 1); ok = cov >= 0.8 and found > 0 and w >= 0.95 and abs(b) <= 0.5   # coverage criterion as the Phase 3 gate (>= 80%)
        if v and all(s_ == 'refused' for s_, _ in v): ok = None   # the style is refused as a whole
        out.append({'style': sid, 'feature': ft, 'n': len(v), 'found': found, 'flagged_occluded': nflag, 'coverage_visible': cov, 'all_visible_found': found == vis, 'within_2u': float(w), 'bias_u': b, 'pass': bool(ok), 'fail_kinds': sorted({s for s, _ in v if s != 'ok'})})
        print(f'{sid:22} {ft:14} {len(v):3d} {found:5d} {nflag:4d} {cov:5.0%} {w:6.0%} {b:8.2f} {"REFUSED" if ok is None else ("PASS" if ok else "FAIL")}')
    json.dump(out, open(f'{V32}/replicas/feature_check.json', 'w'), indent=1)

if __name__ == '__main__':
    {'make': make, 'check': check}[sys.argv[1]]()
