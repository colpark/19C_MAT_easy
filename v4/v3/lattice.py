#!/usr/bin/env python3
"""lattice.py (v3.2 Stage 5C recovery, user instruction 1): HRTEM lattice spacings by FFT and SAED ring d-spacings by radial profile,
calibrated by the panel's scale bar. Starts from tool_ceiling tem.py (windowed, zero-padded FFT; radial profile about the beam spot).
Validated on synthetic lattice and ring images (replicas/tem_replicas.py) before any real panel is measured (rule 5).

Scale bar: the longest thin (<= 5 px) horizontal stroke that differs from the pixels just above and below it by >= 35 grey levels, in the
lower 45% of the panel, length 8-60% of the width (find_bar). Its label (value + unit, e.g. '5 nm', '5 1/nm') is read by OCR
(tool_ceiling scale.py) or, when OCR fails, declared in the profile ('bar_label'), with evidence and a blind Sol check.
px_per_unit = bar length / label value; u(bar) = 1 px.

hrtem(gray, region, ppu) -> dominant fringe spacing: high-pass (subtract a sigma-6 Gaussian), Hann window, periods 2.2-16 px, 4x zero padding, |FFT| peaks outside the DC disk; peaks on the JPEG
  8x8 block lattice (kx or ky = 0 and the other at a multiple of N/8 within 1.5 bins) are ignored; the peak with the highest ratio to its ring's median |F| (whitened spectrum; its
  Friedel mate is the same spacing) is refined by a 3x3 quadratic. d = N / r px; u_r = max(0.5 bin, radial HWHM / 4);
  u_d / d = hypot(u_r / r, 1 / bar_px). Returns None when the period is < 2.2 px (not resolvable) or the peak / ring-median ratio < 15.
saed(gray, n, ppi) -> n ring d-spacings, ascending radius: beam centre = centroid of the brightest blob (>= 90% of the smoothed maximum);
  radial mean profile in 0.5 px bins with text/arrow pixels (brighter than the ring intensity, thin, outside rings) not removed but
  averaged over the full circle; background = running minimum + smoothing; the n most prominent peaks beyond the beam-spot radius,
  refined by a parabola; d = 1 / (r / ppi); u_r = max(0.5 px, HWHM / 4); u_d / d = hypot(u_r / r, 1 / bar_px). Rings are assigned to the
  printed hkl labels by rank order of radius (never by closeness to the XRD prediction). Returns None if fewer than n peaks are found,
  and {'refused': ...} when the beam spot is elliptical (axis ratio > 1.08: anisotropically scaled figure)."""
import math, re, sys
import numpy as np
from scipy import ndimage as ndi
sys.path.insert(0, '/home/aid1/Documents/harbor/ceiling_run/ceiling')

def find_bar(gray, where=None):
    """where: 'left' | 'right' (profile hint: the half of the panel holding the bar)."""
    h, w = gray.shape; g = gray.astype(float); best = None
    up = np.roll(g, 3, 0); dn = np.roll(g, -3, 0)
    for pol in (1, -1):
        diff = np.minimum(pol * (g - up), pol * (g - dn))        # brighter (pol 1) / darker (pol -1) than 3 px above and below
        m = diff >= 35; m[:int(0.55 * h)] = False; m[:3] = m[-3:] = False
        if where == 'left': m[:, w // 2:] = False
        elif where == 'right': m[:, :w // 2] = False
        m = ndi.binary_opening(m, np.ones((1, max(7, int(0.03 * w)))))
        lab, n = ndi.label(m)
        for i, sl in enumerate(ndi.find_objects(lab), 1):
            ys, xs = sl; bh, bw = ys.stop - ys.start, xs.stop - xs.start
            if bh > 5 or not (0.08 * w <= bw <= 0.6 * w): continue
            cols = (lab[sl] == i).any(0)
            # sub-pixel ends: half-contrast crossing along the bar's centre row
            rows = g[max(ys.start - 1, 0):ys.stop + 1]; row = rows.max(0) if pol > 0 else rows.min(0)   # column profile over the bar's rows
            inside = np.median(row[xs.start:xs.stop]); outside = np.median(np.r_[row[max(xs.start - 12, 0):xs.start], row[xs.stop:xs.stop + 12]] if xs.start > 0 else row[xs.stop:xs.stop + 12])
            a, b = xs.start, xs.stop - 1
            # ends: steepest step of the bar-row profile within 4 px of each component end (sub-pixel by a parabola on the gradient);
            # robust when the background next to an end is as bright as the bar (a fringe along the bar row)
            gr = np.gradient(row) * (1 if pol > 0 else -1)
            def edge(lo, hi, sign):
                lo, hi = max(lo, 1), min(hi, w - 2); seg = sign * gr[lo:hi + 1]
                if len(seg) < 3: return None
                k = int(seg.argmax()) + lo; y0_, y1_, y2_ = sign * gr[k - 1], sign * gr[k], sign * gr[k + 1]; den = y0_ - 2 * y1_ + y2_
                return k + (0.5 * (y0_ - y2_) / den if den else 0.0)
            below = (pol * (g - dn))[max(ys.start - 1, 0):ys.stop + 1].max(0)   # labels sit above the bar: extend while it still contrasts with 3 px below
            inside = float(np.median(row[xs.start:xs.stop]))    # a bar is flat at its own (near-saturated) level; a fringe crest is not
            while a > 0 and below[a - 1] >= 15 and (row[a - 1] - inside) * pol > -25: a -= 1
            while b < w - 1 and below[b + 1] >= 15 and (row[b + 1] - inside) * pol > -25: b += 1
            e1, e2 = edge(a - 4, a + 4, 1), edge(b - 4, b + 4, -1)
            if e1 is None or e2 is None: continue
            L_ = e2 - e1; bw = L_
            if not (0.08 * w <= bw <= 0.6 * w): continue
            score = bw * (1 + float(np.median(diff[sl][lab[sl] == i])) / 100)
            if best is None or score > best['score']:
                best = {'len': float(L_), 'box': [int(xs.start), int(ys.start), int(xs.stop), int(ys.stop)], 'pol': 'bright' if pol > 0 else 'dark', 'score': float(score)}
    return best

def parse_label(s):
    m = re.match(r'\s*([0-9.]+)\s*(1/nm|nm-1|nm\^-1|nm⁻¹|nm|μm|um|Å|A)\s*$', s)
    if not m: return None
    u = m.group(2); recip = u in ('1/nm', 'nm-1', 'nm^-1', 'nm⁻¹')
    return {'value': float(m.group(1)), 'unit': '1/nm' if recip else ('nm' if u == 'nm' else u), 'recip': recip}

def calibrate(rgb, gray, declared=None, where=None):
    """-> {px_per_unit, unit, recip, bar_px, source} or None. OCR first (tool_ceiling scale.find_scale_bar), declared label otherwise;
    the bar length is always this module's find_bar measurement."""
    bar = find_bar(gray, where)
    if not bar: return None
    lab = None; ocr_lab = None
    try:
        import common, scale as SC
        s = SC.find_scale_bar(rgb, gray.astype(float), common.ocr_tokens(rgb))
        if s and abs(s['bar_px'] - bar['len']) <= 3: ocr_lab = {'value': s['label_value'], 'unit': s['unit'], 'recip': s['recip'], 'source': 'ocr'}
    except Exception: pass
    # a declared label (profile, Sol-checked) wins; OCR is used only without one (OCR misreads '5 nm' on replicas)
    lab = dict(parse_label(declared) or {}, source='declared') if declared else ocr_lab
    if not lab or 'value' not in lab: return None
    return {'px_per_unit': bar['len'] / lab['value'], 'unit': lab['unit'], 'recip': lab['recip'], 'bar_px': bar['len'], 'bar_box': bar['box'], 'source': lab['source'],
            'ocr_agrees': (ocr_lab is not None and abs(ocr_lab['value'] - lab['value']) < 1e-9) if declared else None}

def hrtem(gray, ppu, region=None, bar_px=None):
    g = gray.astype(float)
    if region: x0, y0, x1, y1 = region; g = g[y0:y1, x0:x1]
    side = min(g.shape); cy, cx = g.shape[0] // 2, g.shape[1] // 2; sub = g[cy - side // 2:cy - side // 2 + side, cx - side // 2:cx - side // 2 + side]
    if side < 32: return None
    sub = sub - ndi.gaussian_filter(sub, 6)                 # high-pass: thickness/defocus contrast (periods >~ 25 px) is not a lattice fringe
    sub = (sub - sub.mean()) * np.outer(np.hanning(side), np.hanning(side))
    N = 1 << int(math.ceil(math.log2(4 * side))); F = np.abs(np.fft.fftshift(np.fft.fft2(sub, s=(N, N)))); c = N // 2
    yy, xx = np.indices(F.shape); r = np.hypot(yy - c, xx - c); ky, kx = yy - c, xx - c
    F[r < 4 * N / side] = 0; F[ky < 0] = 0; F[(ky == 0) & (kx < 0)] = 0           # DC disk; one half-plane (Friedel mates)
    bs = N / 8 * side / side
    jpg = np.zeros_like(F, bool)
    for kk in range(1, 8):   # JPEG block lattice: period 8/k px -> frequency k*N/8
        f0 = kk * N / 8
        jpg |= (np.abs(kx) <= 1.5 * N / side) & (np.abs(np.abs(ky) - f0) <= 1.5 * N / side)
        jpg |= (np.abs(ky) <= 1.5 * N / side) & (np.abs(np.abs(kx) - f0) <= 1.5 * N / side)
    F[jpg] = 0
    F[(r > N / 2.2) | (r < N / 16)] = 0                         # method range: fringe periods 2.2-16 px
    # whitening: divide by the radial median (a fringe is a narrow peak above its own ring; broad backgrounds are flat after this)
    ri = r.astype(int); pos = F > 0; med = np.zeros(ri.max() + 1)
    for v in np.unique(ri[pos]): med[v] = np.median(F[pos & (ri == v)])
    Wf = np.where(pos, F / np.maximum(med[ri], 1e-12), 0)
    Wf[(r > N / 2.2 - 2) | (r < N / 16 + 2)] = 0                # a maximum on the window boundary is not a peak
    j = int(Wf.argmax()); py, px = divmod(j, N)
    if F[py, px] <= 0: return None
    bg = float(med[ri[py, px]])
    if Wf[py, px] < 15: return None                             # peak / ring median (replicas: fringes 35-90, spurious 5-12)
    # 3x3 quadratic refinement
    def q(a, b, cc): den = a - 2 * b + cc; return 0.5 * (a - cc) / den if den else 0.0
    dy = q(F[py - 1, px], F[py, px], F[py + 1, px]) if 0 < py < N - 1 else 0; dx = q(F[py, px - 1], F[py, px], F[py, px + 1]) if 0 < px < N - 1 else 0
    ry, rx = py + dy - c, px + dx - c; rr = math.hypot(ry, rx); per = N / rr
    if per < 2.2: return None
    # radial HWHM along the peak direction
    uy, ux = ry / rr, rx / rr; prof = []
    for t in np.arange(-30, 30.5, 0.5):
        yy_, xx_ = c + (rr + t) * uy, c + (rr + t) * ux; prof.append((t, float(ndi.map_coordinates(F, [[yy_], [xx_]], order=1)[0])))
    pk = max(v for _, v in prof); above = [t for t, v in prof if v >= pk / 2]; hw = (max(above) - min(above)) / 2 if above else 1.0
    ur = max(0.5, hw / 4); rel = math.hypot(ur / rr, (1.0 / bar_px) if bar_px else 0.0)
    d = per / ppu; return {'d': d, 'u': d * rel, 'period_px': per, 'snr': F[py, px] / bg}

def saed(gray, n, ppi, bar_px=None, exclude=None):
    g = gray.astype(float)
    if exclude:
        for a, b, cc, dd in exclude: g[b:dd, a:cc] = np.nan
    gs = ndi.gaussian_filter(np.nan_to_num(g), 2); mx = gs.max(); lab, k = ndi.label(gs >= 0.9 * mx)
    i = int(np.argmax(ndi.sum(gs, lab, range(1, k + 1)))) + 1; cy, cx = ndi.center_of_mass(gs * (lab == i))
    spot = math.sqrt((lab == i).sum() / math.pi)
    # validity: an elliptical beam spot means the figure was scaled anisotropically (or the pattern is distorted); a horizontal scale bar
    # then does not calibrate a radial average -> refuse (axis ratio of the >= 50%-of-max spot region beyond 1.08)
    ys_, xs_ = np.nonzero((gs >= 0.5 * mx) & ndi.binary_dilation(lab == i, iterations=int(3 * spot + 3)))
    ev = np.sort(np.linalg.eigvalsh(np.cov(np.vstack([xs_, ys_])))); ratio = math.sqrt(ev[1] / max(ev[0], 1e-9))
    if ratio > 1.08: return {'refused': f'beam spot axis ratio {ratio:.3f} > 1.08 (anisotropic scaling)', 'axis_ratio': ratio}   # replicas: round <= 1.056, stretched 1.1x >= 1.12
    yy, xx = np.indices(g.shape); r = np.hypot(yy - cy, xx - cx); ok = ~np.isnan(g)
    rb = (r[ok] * 2).astype(int); prof = np.bincount(rb, g[ok]) / np.maximum(np.bincount(rb), 1); rr = (np.arange(len(prof)) + 0.5) / 2   # bin centres
    rmax = min(cy, cx, g.shape[0] - cy, g.shape[1] - cx) * 0.98   # full circles only
    # halo: start where the smoothed profile has decayed to 5% of its height (at the spot edge) above the outer floor
    sm = ndi.uniform_filter1d(prof, 9); inside = rr < rmax; floor = float(np.percentile(sm[inside & (rr > 0.5 * rmax)], 20))
    e0 = int(np.searchsorted(rr, spot)); h0 = sm[e0] - floor; halo_end = next((rr[i] for i in range(e0, len(sm)) if sm[i] - floor < 0.05 * h0), rmax)
    keep = (rr > max(2.5 * spot + 3, halo_end)) & (rr < rmax)
    if keep.sum() < 20: return None
    base = ndi.uniform_filter1d(ndi.minimum_filter1d(prof, 21), 21); sig = prof - base; sig[~keep] = 0
    from scipy.signal import find_peaks
    pk, pr = find_peaks(sig, prominence=0, distance=4)
    if len(pk) < n: return None
    # a ring has signal around the circle: >= 8 of 16 angular sectors show the peak above the local baseline (labels, arrows are local)
    th = np.arctan2(yy - cy, xx - cx); sec = ((th + np.pi) / (2 * np.pi) * 16).astype(int) % 16; good = []
    for p_ in pk:
        rad = rr[p_]; ann = ok & (np.abs(r - rad) <= 0.75); out_ = ok & (np.abs(r - rad) > 2) & (np.abs(r - rad) <= 4); hits = 0
        for q in range(16):
            a1, a2 = g[ann & (sec == q)], g[out_ & (sec == q)]
            if len(a1) and len(a2) and a1.mean() > a2.mean(): hits += 1
        if hits >= 8: good.append(p_)
    pk = np.array(good, int); pr = {'prominences': np.array([sig[p_] for p_ in pk])}
    if len(pk) < n: return None
    top = sorted(pk[np.argsort(pr['prominences'])[::-1][:n]])
    out = []
    for p in top:
        a_, b_, c_ = sig[p - 1], sig[p], sig[p + 1]; den = a_ - 2 * b_ + c_; dp = 0.5 * (a_ - c_) / den if den else 0.0
        rad = rr[p] + dp / 2; half = sig[p] / 2; lo = p
        while lo > 0 and sig[lo] > half: lo -= 1
        hi = p
        while hi < len(sig) - 1 and sig[hi] > half: hi += 1
        hw = (hi - lo) / 4; ur = max(0.5, hw / 4); qv = rad / ppi; d = 1.0 / qv
        out.append({'d': d, 'u': d * math.hypot(ur / rad, (1.0 / bar_px) if bar_px else 0.0), 'r_px': rad})
    return out
