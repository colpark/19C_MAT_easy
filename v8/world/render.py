"""Rod-scan rendering. One afmize top-view stamp per rod type (cached), placed in the scan frame, then in order:
tip dilation (instrument/dilation.py tip), line noise (+white noise), drift (smooth Gaussian displacement
field), plane flattening. Heights in nm, lengths in nm. Image array: row = y, col = x (y down); rod angles
are measured in this image frame.
"""
import os, sys, subprocess, shutil
import numpy as np
from scipy.ndimage import map_coordinates, gaussian_filter, grey_dilation, zoom

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "instrument"))
from dilation import tip_profile  # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sample as S  # noqa: E402
import cost as C  # noqa: E402

HOME = os.path.expanduser("~")
STAMPS = HOME + "/v8_data/stamps/"
RODS = HOME + "/v8_data/rods/"
STAMP_PX_NM = 0.3
TIP_ANGLE_DEG = 10.0     # afmize / dilation.py default cone half-angle
DRIFT_CORR_FOV = 3.0     # drift-field correlation length in units of the field of view
LINE_NOISE_REL = 1.5     # line-offset sigma relative to white sigma (CALIBRATION.md: measured 1.4-3.3 in Supp Data 1)


def stamp(hash_id, n_rep):
    """Cached afmize top-view height stamp (nm), long axis along x. Returns (array, cx, cy) centroid in px."""
    f = STAMPS + "%s_%drep.npz" % (hash_id, n_rep)
    if os.path.exists(f):
        z = np.load(f)
        return z["h"], float(z["cx"]), float(z["cy"])
    L, W = S.rod_dims(hash_id, n_rep)
    work = STAMPS + "work_%s_%d/" % (hash_id, n_rep)
    os.makedirs(work, exist_ok=True)
    rx, ry = L / 2 + 3.0, max(W, 4.0) / 2 + 4.0
    open(work + "t.toml", "w").write(
        'file.input = "%s%s_%drep.pdb"\nfile.output.basename = "t"\nfile.output.formats = ["tsv"]\n'
        'probe.size = {radius = "0.1angstrom", angle = 10.0}\n'
        'resolution.x = "%.1fangstrom"\nresolution.y = "%.1fangstrom"\nresolution.z = "0.1angstrom"\n'
        'range.x = ["%.2fnm", "%.2fnm"]\nrange.y = ["%.2fnm", "%.2fnm"]\nscale_bar.length = "5.0nm"\n'
        'stage.align = true\nstage.position = 0.0\nnoise = "0.0nm"\n'
        % (RODS, hash_id, n_rep, STAMP_PX_NM * 10, STAMP_PX_NM * 10, -rx, rx, -ry, ry))
    subprocess.run([os.environ["AFMIZE"], "t.toml"], cwd=work, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    h = np.loadtxt(work + "t.tsv") / 10.0   # Angstrom -> nm
    yy, xx = np.mgrid[:h.shape[0], :h.shape[1]]
    m = h.sum()
    cx, cy = (h * xx).sum() / m, (h * yy).sum() / m
    np.savez(f, h=h, cx=cx, cy=cy)
    shutil.rmtree(work, ignore_errors=True)
    return h, cx, cy


def drift_field(rng, shape, px_nm, amp_nm, corr_nm):
    """Smooth Gaussian random displacement field (dx, dy) in nm. Coarse N(0, amp^2) nodes spaced corr_nm,
    cubic-interpolated (no per-image renormalisation, so a long correlation length is mostly a shift)."""
    out = []
    n = int(np.ceil(max(shape) * px_nm / corr_nm)) + 4
    yy, xx = np.mgrid[:shape[0], :shape[1]].astype(float)
    for _ in range(2):
        g = rng.normal(0, amp_nm, (n, n))
        out.append(map_coordinates(g, [yy * px_nm / corr_nm + 1.5, xx * px_nm / corr_nm + 1.5], order=3, mode="nearest"))
    return out[0], out[1]


def warp(img, dx_nm, dy_nm, px_nm):
    yy, xx = np.mgrid[:img.shape[0], :img.shape[1]].astype(float)
    return map_coordinates(img, [yy + dy_nm / px_nm, xx + dx_nm / px_nm], order=1, mode="nearest")


def flatten_plane(img, iters=3):
    yy, xx = np.mgrid[:img.shape[0], :img.shape[1]].astype(float)
    A = np.c_[np.ones(img.size), xx.ravel() / img.shape[1], yy.ravel() / img.shape[0]]
    z = img.ravel()
    keep = np.ones(z.size, bool)
    for _ in range(iters):
        c = np.linalg.lstsq(A[keep], z[keep], rcond=None)[0]
        r = z - A @ c
        keep = r < np.percentile(r[keep], 70) + 0.0
    return (z - A @ c).reshape(img.shape)


def noise_image(rng, shape, sigma_nm):
    white = rng.normal(0, sigma_nm, shape)
    line = rng.normal(0, LINE_NOISE_REL * sigma_nm, (shape[0], 1))
    slope = rng.normal(0, 0.5 * LINE_NOISE_REL * sigma_nm, (shape[0], 1)) * np.linspace(-1, 1, shape[1])[None, :]
    return white + line + slope


def tip_halfwidth(radius, angle_deg, px, hmax):
    a = np.radians(angle_deg)
    r = np.arange(0, 4000 * px, px / 2)
    r_join = radius * np.cos(a)
    sphere = radius - np.sqrt(np.clip(radius**2 - r**2, 0, None))
    zj = radius - np.sqrt(radius**2 - r_join**2)
    cone = zj + (r - r_join) / np.tan(a)
    drop = np.where(r <= r_join, sphere, cone)
    i = np.searchsorted(drop, hmax * 1.05)
    return int(np.ceil(r[min(i, len(r) - 1)] / px)) + 1


def dilate_tip(h, radius_nm, px_nm, hmax):
    hw = tip_halfwidth(radius_nm, TIP_ANGLE_DEG, px_nm, hmax)
    return grey_dilation(h, structure=tip_profile(radius_nm, TIP_ANGLE_DEG, px_nm, half_width_px=hw), mode="nearest"), hw


def scan_rods(world, plan, scan_seed=0, ideal=False):
    """Render a rod scan. ideal=True skips tip/noise/drift/flatten (for debugging only)."""
    plan.validate()
    nz, tr = world["nuisance"], world["truth"]
    px = plan.fov_nm / plan.npx
    minutes = plan.minutes()
    rng = np.random.default_rng(S.seed_int("scan", *world["key"], scan_seed, repr(plan.asdict())))
    st, cx0, cy0 = stamp(tr["hash_id"], tr["n_rep"])
    amp = nz["drift_nm_min"] * plan.frame_minutes()
    pad = int(np.ceil(4 * amp / px)) + 2
    hmax = float(st.max())
    if not ideal:
        hw0 = tip_halfwidth(nz["tip_nm"], TIP_ANGLE_DEG, px, hmax)
    else:
        hw0 = 0
    pad += hw0
    n = plan.npx + 2 * pad
    # stamp prefilter to the pixel footprint
    sig = 0.5 * px / STAMP_PX_NM
    sf = gaussian_filter(st, sig) if sig > 0.4 else st
    pos, ang = S.to_scan_frame(world)
    x0 = plan.cx_nm - plan.fov_nm / 2 - pad * px
    y0 = plan.cy_nm - plan.fov_nm / 2 - pad * px
    img = np.zeros((n, n))
    reach = world["scene"]["length_nm"] / 2 + 3.0
    sel = np.where((np.abs(pos[:, 0] - (x0 + n * px / 2)) < n * px / 2 + reach) & (np.abs(pos[:, 1] - (y0 + n * px / 2)) < n * px / 2 + reach))[0]
    for i in sel:
        xc, yc, t = pos[i, 0], pos[i, 1], np.radians(ang[i])
        i0, i1 = int(max(0, np.floor((xc - reach - x0) / px))), int(min(n, np.ceil((xc + reach - x0) / px) + 1))
        j0, j1 = int(max(0, np.floor((yc - reach - y0) / px))), int(min(n, np.ceil((yc + reach - y0) / px) + 1))
        if i1 <= i0 or j1 <= j0:
            continue
        X = x0 + (np.arange(i0, i1) + 0.5) * px - xc
        Y = y0 + (np.arange(j0, j1) + 0.5) * px - yc
        XX, YY = np.meshgrid(X, Y)
        u = (XX * np.cos(t) + YY * np.sin(t)) / STAMP_PX_NM + cx0
        v = (-XX * np.sin(t) + YY * np.cos(t)) / STAMP_PX_NM + cy0
        patch = map_coordinates(sf, [v, u], order=1, cval=0.0)
        sl = (slice(j0, j1), slice(i0, i1))
        img[sl] = np.maximum(img[sl], patch)
    if ideal:
        return dict(img=img[pad:pad + plan.npx, pad:pad + plan.npx], px_nm=px, plan=plan, minutes=minutes)
    img, _ = dilate_tip(img, nz["tip_nm"], px, hmax)
    img = img + noise_image(rng, img.shape, nz["noise_nm"] * C.noise_scale(plan))
    dx, dy = drift_field(rng, img.shape, px, amp, DRIFT_CORR_FOV * plan.fov_nm)
    img = warp(img, dx, dy, px)
    img = img[pad:pad + plan.npx, pad:pad + plan.npx]
    img = flatten_plane(img)
    return dict(img=img, px_nm=px, plan=plan, minutes=minutes)
