"""Fit statistic D and the classical image analysis feeding it.

Rod segmentation (classical ridge filter, scipy):
  Gaussian-derivative Hessian at scale SIGMA_RIDGE_NM (3.0 nm, floor 1 px); ridge strength = -lambda_min
  (largest-magnitude negative Hessian eigenvalue) times sigma^2; threshold = RIDGE_THR_FRAC (0.8) of the
  99th percentile of the strength; connected components (8-connectivity); keep components whose
  ridge-weighted PCA major axis is within [0.45, 1.6] x rod length, elongation (std ratio) >= 2.5, and
  that do not touch the border. Rod angle = major-axis angle of the ridge-weighted pixel cloud (image
  frame, degrees mod 180).
Lattice orientation: Hann-windowed zero-padded FFT; power-squared weighted sixth harmonic of the angle
over the annulus 0.8-1.25 f0 of the first-order reflections gives the row orientation mod 60 deg; its
standard error comes from the spread of the four quadrant estimates.
Statistic D = 2 [ max log L(true registry) - max( log L(other registry), log L(isotropic) ) ], nuisances
(kappa, isotropic fraction, and the lattice angle with a Gaussian penalty from its measured error)
profiled on grids. Without a lattice scan the lattice angle is free, so the two registries are
exactly degenerate and D = 0 (risk R6).
"""
import os, sys
import numpy as np
from scipy.ndimage import gaussian_filter, label, find_objects
from scipy.special import i0e

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lattice as LAT  # noqa: E402

SIGMA_RIDGE_NM = 3.0
RIDGE_THR_FRAC = 0.8
LEN_BOUNDS = (0.45, 1.6)
MIN_ELONG = 2.5


def ridge_strength(img, px_nm, sigma_nm=None):
    sigma_nm = SIGMA_RIDGE_NM if sigma_nm is None else sigma_nm
    s = max(1.0, sigma_nm / px_nm)
    Hxx = gaussian_filter(img, s, order=(0, 2))
    Hyy = gaussian_filter(img, s, order=(2, 0))
    Hxy = gaussian_filter(img, s, order=(1, 1))
    tr, det = Hxx + Hyy, Hxx * Hyy - Hxy ** 2
    disc = np.sqrt(np.maximum(tr ** 2 / 4 - det, 0))
    lmin = tr / 2 - disc
    return np.maximum(-lmin, 0) * s ** 2


def segment_rods(img, px_nm, rod_length_nm=19.5, return_all=False):
    """Returns array (n,3): x_nm, y_nm, angle_deg (mod 180) for accepted rods, in the image frame."""
    R = ridge_strength(img, px_nm)
    thr = RIDGE_THR_FRAC * np.percentile(R, 99)
    lab, n = label(R > thr, structure=np.ones((3, 3)))
    out = []
    H, W = img.shape
    for k, sl in enumerate(find_objects(lab), 1):
        if sl[0].start == 0 or sl[1].start == 0 or sl[0].stop == H or sl[1].stop == W:
            continue
        yy, xx = np.nonzero(lab[sl] == k)
        if len(yy) < 5:
            continue
        w = R[sl][yy, xx]
        x, y = (xx + sl[1].start) * px_nm, (yy + sl[0].start) * px_nm
        mx, my = np.average(x, weights=w), np.average(y, weights=w)
        C = np.cov(np.vstack([x - mx, y - my]), aweights=w)
        ev, evec = np.linalg.eigh(C)
        if ev[0] <= 0:
            continue
        major = 4 * np.sqrt(ev[1])           # ~ full length of a uniform bar
        if not (LEN_BOUNDS[0] * rod_length_nm <= major <= LEN_BOUNDS[1] * rod_length_nm):
            continue
        if np.sqrt(ev[1] / ev[0]) < MIN_ELONG:
            continue
        out.append((mx, my, np.degrees(np.arctan2(evec[1, 1], evec[0, 1])) % 180.0))
    return np.array(out).reshape(-1, 3)


def _rowflat(img):
    """Per-row linear detrend (line-noise removal, lattice scans only)."""
    x = np.arange(img.shape[1]) - (img.shape[1] - 1) / 2.0
    sl = (img * x[None, :]).sum(1, keepdims=True) / (x ** 2).sum()
    return img - img.mean(1, keepdims=True) - sl * x[None, :]


def _orient(img, px_nm):
    img = _rowflat(img)
    wnd = np.hanning(img.shape[0])[:, None] * np.hanning(img.shape[1])[None, :]
    x = (img - img.mean()) * wnd
    M = 4 * max(img.shape)
    F = np.fft.fftshift(np.fft.fft2(x, s=(M, M)))
    f = np.fft.fftshift(np.fft.fftfreq(M, d=px_nm))
    FX, FY = np.meshgrid(f, f)
    fr = np.hypot(FX, FY)
    f0 = 2.0 / (np.sqrt(3) * LAT.A_LAT_NM)
    if f0 > 0.9 * 0.5 / px_nm:
        return None
    m = (fr > 0.8 * f0) & (fr < 1.25 * f0)
    P = np.abs(F[m]) ** 2
    th = np.arctan2(FY[m], FX[m])
    z = np.sum(P ** 2 * np.exp(6j * th))
    phi = np.degrees(np.angle(z)) / 6.0
    return (phi - 30.0) % 60.0


def _cmean60(a):
    z = np.exp(1j * np.radians(np.asarray(a)) * 6)
    return (np.degrees(np.angle(z.mean())) / 6) % 60


def _dev60(a, ref):
    return (np.asarray(a) - ref + 30) % 60 - 30


DRIFT_PRIOR_NM_MIN = 0.1     # prior mean drift rate used for the drift term of the lattice error bar


def fit_lattice(img, px_nm, plan=None):
    """Row orientation (deg, mod 60, image frame) and its standard error; None if unresolvable."""
    a = _orient(img, px_nm)
    if a is None:
        return None
    hy, hx = img.shape[0] // 2, img.shape[1] // 2
    q = [_orient(img[i:i + hy, j:j + hx], px_nm) for i in (0, hy) for j in (0, hx)]
    if any(v is None for v in q):
        sig = 5.0
    else:
        sig = max(0.05, float(np.sqrt(np.mean(_dev60(q, _cmean60(q)) ** 2)) / 2.0 * 1.3))
    if plan is not None:    # add the drift-induced shear allowance (prior rate, DRIFT_CORR_FOV x fov correlation)
        import render as RR
        sd = np.degrees(0.7 * DRIFT_PRIOR_NM_MIN * plan.frame_minutes() / (RR.DRIFT_CORR_FOV * plan.fov_nm))
        sig = float(np.hypot(sig, sd))
    return dict(angle_deg=float(a), sigma_deg=float(sig))


# ---- likelihoods -------------------------------------------------------------------------------------
KAPPAS = np.exp(np.linspace(np.log(0.05), np.log(60), 40))
FISOS = np.linspace(0, 0.5, 11)
LOGIPI = -np.log(np.pi)


def _ll_grid(theta_deg, mu0_deg):
    """log-likelihood for all (kappa, f_iso) grid points, mixture centres mu0+60j."""
    t = np.radians(theta_deg)[None, :, None]
    mus = np.radians(mu0_deg + 60.0 * np.arange(3))[None, None, :]
    k = KAPPAS[:, None, None]
    # vM on doubled angle: exp(k cos 2(t-mu)) / (pi I0(k)); use scaled i0e for stability
    lg = k * (np.cos(2 * (t - mus)) - 1) - np.log(np.pi * i0e(k))
    m = lg.max(2, keepdims=True)
    lmix = (m[..., 0] + np.log(np.exp(lg - m).mean(2)))   # (nk, n)
    f = FISOS[None, :, None]
    ll = np.log((1 - f) * np.exp(lmix)[:, None, :] + f / np.pi + 1e-300).sum(2)   # (nk, nf)
    return ll


def loglik_registry(theta_deg, offset_deg, lat_angle=None, lat_sigma=None, ngrid=41):
    """Profiled log-likelihood (nats) of registry with offset (0 or 30) relative to the lattice rows."""
    th = np.asarray(theta_deg, float)
    if lat_angle is None:
        grid = np.arange(0, 60, 0.5)
        pen = np.zeros_like(grid)
    else:
        s = max(lat_sigma, 0.05)
        d = np.linspace(-4 * s, 4 * s, ngrid)
        grid = lat_angle + d
        pen = -0.5 * (d / s) ** 2
    best = -np.inf
    for a, p in zip(grid, pen):
        best = max(best, _ll_grid(th, a + offset_deg).max() + p)
    return float(best)


def loglik_iso(theta_deg):
    return float(-len(theta_deg) * np.log(np.pi))


def fit_D(theta_deg, true_registry, lattice=None):
    """lattice: dict(angle_deg, sigma_deg) from fit_lattice, or None. Returns dict with D and parts."""
    off = {"A": 0.0, "B": 30.0}
    th = np.asarray(theta_deg, float)
    if len(th) < 3:
        return dict(D=0.0, n=len(th), ll={})
    la, ls = (None, None) if lattice is None else (lattice["angle_deg"], lattice["sigma_deg"])
    ll = {r: loglik_registry(th, off[r], la, ls) for r in ("A", "B")}
    ll["iso"] = loglik_iso(th)
    other = "B" if true_registry == "A" else "A"
    D = 2.0 * (ll[true_registry] - max(ll[other], ll["iso"]))
    return dict(D=float(D), n=len(th), ll=ll)


def fit_D_blind(theta_deg, lattice=None):
    """D for the better-supported registry (no truth): 2 [ max(llA, llB) - max(other, iso) ] signed toward A-B."""
    th = np.asarray(theta_deg, float)
    la, ls = (None, None) if lattice is None else (lattice["angle_deg"], lattice["sigma_deg"])
    llA, llB = loglik_registry(th, 0.0, la, ls), loglik_registry(th, 30.0, la, ls)
    return dict(llA=llA, llB=llB, llI=loglik_iso(th), D_AB=2 * (llA - llB), n=len(th))
