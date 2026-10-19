"""World sampler (numpy only). A world is determined by (registry, rod unit hash id, repeat count, seed).

Frames: the SUBSTRATE (world) frame holds the lattice directions at 0, 60, 120 deg (registry A: rods
along them; registry B: rods offset by 30 deg). The hidden sample azimuth az rotates the whole scene into
the SCAN frame, so scan-frame rod angles alone carry no registry information (risk R6).
Angles are axial (mod 180 deg), in degrees. Lengths in nm.
"""
import os, json, hashlib
import numpy as np

HOME = os.path.expanduser("~")
DIMS = HOME + "/v8_data/rods/dims.json"
WORLD_SIDE_NM = 500.0 * np.sqrt(2.0) + 20.0      # any rotated 500 nm window is fully populated
MIN_GAP_NM = 2.0
REG_OFFSET_DEG = {"A": 0.0, "B": 30.0}
HASH_IDS = ["HRm-ea", "HRm-60", "HRm-ef", "HRm-5d", "HRm-f1"]
# nuisance ranges (instrument values are "uncalibrated", see CALIBRATION.md)
NUIS_RANGE = dict(
    coverage=(0.10, 0.30), tip_nm=(3.0, 10.0), drift_nm_min=(0.02, 0.2), noise_nm=(0.05, 0.30),
    kappa=(1.5, 10.0), f_iso=(0.0, 0.15), azimuth_deg=(0.0, 360.0))


def seed_int(*parts):
    h = hashlib.sha256("|".join(str(p) for p in parts).encode()).digest()
    return int.from_bytes(h[:8], "little")


def rod_dims(hash_id, n_rep):
    d = json.load(open(DIMS))["%s_%drep" % (hash_id, n_rep)]
    return d["length_nm"], d["width_nm"]


def _rect_overlap(c1, t1, c2, t2, hl, hw):
    """Separating-axis test for two equal rectangles (half-length hl, half-width hw, gap included)."""
    d = c2 - c1
    for t in (t1, t2):
        for ax in (np.array([np.cos(t), np.sin(t)]), np.array([-np.sin(t), np.cos(t)])):
            r = 0.0
            for tt in (t1, t2):
                e1, e2 = np.array([np.cos(tt), np.sin(tt)]), np.array([-np.sin(tt), np.cos(tt)])
                r += hl * abs(ax @ e1) + hw * abs(ax @ e2)
            if abs(d @ ax) > r:
                return False
    return True


def place_rods(rng, n_target, theta, L, W, gap=MIN_GAP_NM, side=WORLD_SIDE_NM, max_tries=100):
    """Random sequential addition: Poisson positions, rejected if a rod (plus gap) overlaps another."""
    hl, hw = L / 2 + gap / 2, W / 2 + gap / 2
    cell = L + gap
    ncell = int(np.ceil(side / cell))
    grid = {}
    pos, ang = [], []
    tries, k = 0, 0
    while k < n_target and tries < max_tries * n_target:
        tries += 1
        c = rng.uniform(-side / 2, side / 2, 2)
        t = np.radians(theta[k])
        ci = (int((c[0] + side / 2) / cell), int((c[1] + side / 2) / cell))
        ok = True
        for i in range(ci[0] - 1, ci[0] + 2):
            for j in range(ci[1] - 1, ci[1] + 2):
                for q in grid.get((i, j), ()):
                    if np.hypot(*(pos[q] - c)) < L + gap + 1e-9 and _rect_overlap(c, t, pos[q], np.radians(ang[q]), hl, hw):
                        ok = False
                        break
                if not ok:
                    break
            if not ok:
                break
        if ok:
            grid.setdefault(ci, []).append(len(pos))
            pos.append(c)
            ang.append(theta[k])
            k += 1
    return np.array(pos), np.array(ang)


def draw_angles(rng, n, mu0_deg, kappa, f_iso):
    """Axial von Mises mixture over three directions mu0+60j, plus isotropic fraction. Degrees in [0,180)."""
    j = rng.integers(0, 3, n)
    psi = rng.vonmises(0.0, kappa, n)                 # on the doubled angle
    th = mu0_deg + 60.0 * j + np.degrees(psi) / 2.0
    iso = rng.random(n) < f_iso
    th[iso] = rng.uniform(0, 180, iso.sum())
    return np.mod(th, 180.0)


def sample_world(registry, hash_id, n_rep, seed, place_rods_flag=True):
    """Returns dict: scene (world-frame centres/angles), nuisance (hidden), truth (registry)."""
    assert registry in REG_OFFSET_DEG and hash_id in HASH_IDS
    rng = np.random.default_rng(seed_int("world", registry, hash_id, n_rep, seed))
    nz = {}
    for k, (lo, hi) in NUIS_RANGE.items():
        nz[k] = float(np.exp(rng.uniform(np.log(lo), np.log(hi)))) if k == "kappa" else float(rng.uniform(lo, hi))
    L, W = rod_dims(hash_id, n_rep)
    n_target = int(round(nz["coverage"] * WORLD_SIDE_NM ** 2 / (L * W)))
    # draw angles in the WORLD frame (lattice at 0/60/120); rotating by az happens at scan time
    th = draw_angles(rng, n_target, REG_OFFSET_DEG[registry], nz["kappa"], nz["f_iso"])
    if place_rods_flag:
        pos, ang = place_rods(rng, n_target, th, L, W)
    else:   # nuisance-only world (lattice scans do not need rods); same nuisances as the full world
        pos, ang = np.zeros((0, 2)), np.zeros(0)
    nz["achieved_coverage"] = float(len(pos) * L * W / WORLD_SIDE_NM ** 2)
    return dict(
        scene=dict(centres_nm=pos, angles_deg=ang, length_nm=L, width_nm=W, side_nm=WORLD_SIDE_NM),
        nuisance=nz, truth=dict(registry=registry, hash_id=hash_id, n_rep=n_rep, seed=seed),
        key=(registry, hash_id, n_rep, seed))


def to_scan_frame(world):
    """Rod centres and angles in the scan frame (rotated by the hidden azimuth)."""
    az = np.radians(world["nuisance"]["azimuth_deg"])
    R = np.array([[np.cos(az), -np.sin(az)], [np.sin(az), np.cos(az)]])
    s = world["scene"]
    return s["centres_nm"] @ R.T, np.mod(s["angles_deg"] + world["nuisance"]["azimuth_deg"], 180.0)


if __name__ == "__main__":
    w = sample_world("A", "HRm-ea", 18, 1)
    print(len(w["scene"]["angles_deg"]), w["nuisance"])
