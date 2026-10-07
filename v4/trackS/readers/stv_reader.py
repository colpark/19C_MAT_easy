#!/usr/bin/env python3
"""stv_reader.py (Track S pilot S2, Stinville 2022): reader for slip localization per crystallographic domain.
Definitions frozen (S4b) before the reader touched a real strain field or the .ang held-out comparison:
  domain        connected region of near-uniform colour in the IPF map registered to the DIC grid (IPF_DistordedDIC_X.tif); annealing
                twins are separate domains. segment_ipf(): median 3 px, boundary where the largest RGB difference to a 4-neighbour exceeds
                GRAD (8-bit levels), connected components of non-boundary pixels, boundary pixels assigned to the nearest domain, domains
                below MIN_AREA merged into their largest neighbour.
  localization  per domain, the fraction of its pixels with Exx > K x the field-mean Exx: DEFERRED. On synthetic dev seeds no K brings
                90 % of domains within +-(0.3 t + 0.01) of the clean-field value (best 0.85): slip bands are sub-resolution at 401 nm.
  domain mean   S2 observable used: mean Exx per domain (domains >= DOM_MIN px), on the DIC grid down-sampled by STRIDE (401 nm/px).
                Disclosure: field-mean Exx per step (0.68, 0.86, 1.12, 1.60 %) was printed before this fallback was chosen.
Domains from orientations (held-out route): ang_domains() groups .ang points whose neighbour misorientation (cubic symmetry) is below
MIS_DEG; it does not use colours.
No model is used. Data files are read only."""
import numpy as np
from scipy import ndimage as ndi
GRAD, MIN_AREA, K, STRIDE, MIS_DEG, SIG, DOM_MIN, ERODE = 18, 400, 2.5, 4, 5.0, 0.85, 2000, 3
def segment_ipf(rgb, grad=None, min_area=None, sig=None):
    """Gaussian SIG px per channel, Sobel gradient magnitude over the three channels, domains = connected pixels below GRAD,
    boundary pixels to the nearest domain, domains < MIN_AREA merged into their neighbour (tuned on synthetic dev seeds 1000-1007)."""
    grad = GRAD if grad is None else grad; min_area = MIN_AREA if min_area is None else min_area; sig = SIG if sig is None else sig
    a = ndi.gaussian_filter(rgb.astype(float), (sig, sig, 0))
    g = np.sqrt(sum(ndi.sobel(a[..., c], 0) ** 2 + ndi.sobel(a[..., c], 1) ** 2 for c in range(3)))
    lab, n = ndi.label(g < grad)
    idx = ndi.distance_transform_edt(lab == 0, return_distances=False, return_indices=True); lab = lab[tuple(idx)]
    for _ in range(3):
        sz = np.bincount(lab.ravel()); small = np.where((sz < min_area) & (sz > 0))[0]
        if not len(small): break
        keep = np.where(np.isin(lab, small), 0, lab); idx = ndi.distance_transform_edt(keep == 0, return_distances=False, return_indices=True); lab = keep[tuple(idx)]
    _, lab = np.unique(lab, return_inverse=True); return lab.reshape(rgb.shape[:2])
def domain_mean(f, lab, erode=None):
    """S2 observable (S4b-2): mean Exx over each domain's interior (domain eroded by ERODE px, so pixels mixed across a boundary by DIC
    smoothing are excluded; S4b used the whole domain and failed its fresh-seed gate, 4/10 maps). Returns (mean, interior pixel count)."""
    erode = ERODE if erode is None else erode
    inner = lab.copy()
    if erode:
        edge = np.zeros(lab.shape, bool); edge[:, 1:] |= lab[:, 1:] != lab[:, :-1]; edge[:, :-1] |= lab[:, 1:] != lab[:, :-1]; edge[1:] |= lab[1:] != lab[:-1]; edge[:-1] |= lab[1:] != lab[:-1]
        near = ndi.binary_dilation(edge, iterations=erode); inner = np.where(near, -1, lab)
    ok = inner >= 0; n = np.bincount(inner[ok], minlength=lab.max() + 1); s = np.bincount(inner[ok], weights=f[ok].astype(float), minlength=lab.max() + 1)
    return s / np.maximum(n, 1), n
def localization(exx, lab, k=None):
    k = K if k is None else k; thr = k * float(np.nanmean(exx)); hi = (exx > thr).astype(float)
    n = np.bincount(lab.ravel()); s = np.bincount(lab.ravel(), weights=hi.ravel()); return s / np.maximum(n, 1), n
# ---------------- held-out route: domains from orientations
def _quat(phi1, Phi, phi2):
    c, s = np.cos, np.sin
    return np.stack([c(Phi / 2) * c((phi1 + phi2) / 2), s(Phi / 2) * c((phi1 - phi2) / 2), s(Phi / 2) * s((phi1 - phi2) / 2), c(Phi / 2) * s((phi1 + phi2) / 2)], -1)
def _cubic_ops():
    import itertools
    ops = []
    for p in itertools.permutations(range(3)):
        for sg in itertools.product((1, -1), repeat=3):
            M = np.zeros((3, 3)); M[range(3), p] = sg
            if np.linalg.det(M) > 0: ops.append(M)
    q = []
    for M in ops:   # rotation matrix -> quaternion
        w = np.sqrt(max(0, 1 + np.trace(M))) / 2
        if w > 1e-6: q.append([w, (M[2, 1] - M[1, 2]) / (4 * w), (M[0, 2] - M[2, 0]) / (4 * w), (M[1, 0] - M[0, 1]) / (4 * w)])
        else:
            x = np.sqrt(max(0, 1 + M[0, 0] - M[1, 1] - M[2, 2])) / 2; y = np.sqrt(max(0, 1 - M[0, 0] + M[1, 1] - M[2, 2])) / 2; z = np.sqrt(max(0, 1 - M[0, 0] - M[1, 1] + M[2, 2])) / 2
            x, y, z = x * np.sign(M[2, 1] - M[1, 2] or 1), y * np.sign(M[0, 2] - M[2, 0] or (M[0, 1] + M[1, 0]) or 1), z * np.sign(M[1, 0] - M[0, 1] or (M[0, 2] + M[2, 0]) or 1)
            q.append([0.0, x, y, z])
    return np.array(q)
SYM = None
def _mis(q1, q2):
    global SYM
    if SYM is None: SYM = _cubic_ops()
    w1, v1 = q1[..., 0], q1[..., 1:]; w2, v2 = q2[..., 0], q2[..., 1:]   # d = conj(q1) * q2
    dw = w1 * w2 + (v1 * v2).sum(-1); dv = w1[..., None] * v2 - w2[..., None] * v1 - np.cross(v1, v2)
    best = np.zeros(dw.shape)
    for s in SYM:   # |w| of d * s, maximised over the 24 cubic operators
        best = np.maximum(best, np.abs(dw * s[0] - (dv * s[1:]).sum(-1)))
    return np.degrees(2 * np.arccos(np.clip(best, 0, 1)))
def ang_domains(eul, mis_deg=None, min_area=None):
    """eul: (H, W, 3) radians. Returns domain labels (H, W) from neighbour misorientation < mis_deg (no colour information)."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    mis_deg = MIS_DEG if mis_deg is None else mis_deg; H, W, _ = eul.shape; q = _quat(eul[..., 0], eul[..., 1], eul[..., 2]); idx = np.arange(H * W).reshape(H, W)
    e1 = _mis(q[:, :-1], q[:, 1:]) < mis_deg; e2 = _mis(q[:-1], q[1:]) < mis_deg
    r = np.concatenate([idx[:, :-1][e1], idx[:-1][e2]]); c = np.concatenate([idx[:, 1:][e1], idx[1:][e2]])
    _, lab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(H * W, H * W)), directed=False); lab = lab.reshape(H, W)
    if min_area:
        sz = np.bincount(lab.ravel()); keep = np.where(sz[lab] >= min_area, lab, -1); return keep
    return lab
def match(truth, pred, min_area, iou=0.8):
    """fraction of truth domains (area >= min_area) whose best-overlap predicted domain has IoU >= iou."""
    t = truth.ravel(); p = pred.ravel(); ok = t >= 0
    nt = np.bincount(t[ok]); np_ = np.bincount(p[ok])
    pair = t[ok].astype(np.int64) * (p.max() + 1) + p[ok]; u, cnt = np.unique(pair, return_counts=True); ti, pi = u // (p.max() + 1), u % (p.max() + 1)
    best = {}
    for a, b, c in zip(ti, pi, cnt):
        j = c / (nt[a] + np_[b] - c)
        if j > best.get(a, 0): best[a] = j
    big = [a for a in range(len(nt)) if nt[a] >= min_area]
    return float(np.mean([best.get(a, 0) >= iou for a in big])) if big else float('nan'), len(big)
