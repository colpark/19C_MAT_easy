"""Place a capped fragment on a muscovite slab in a given registry.

theta0 is defined by geometry alone (no FM, no truth energy): the fragment is laid
with its acidic face down, then rotated about the surface normal to maximise the
overlap between its carboxylate oxygens and the surface cation sublattice. The two
registries are theta0 and theta0 + 30 degrees; the three placements are in-plane
shifts along the surface lattice.

Usage as a module: place(frag_pdb, slab_pdb, registry, placement) -> positions.
"""
import numpy as np
import gemmi

GAP = 3.2  # Angstrom, closest heavy-atom approach of fragment to surface
CARBOX = {("ASP", "OD1"), ("ASP", "OD2"), ("GLU", "OE1"), ("GLU", "OE2")}


def load(path):
    st = gemmi.read_structure(path)
    st.remove_hydrogens()
    xyz, tags = [], []
    for ch in st[0]:
        for r in ch:
            for a in r:
                xyz.append([a.pos.x, a.pos.y, a.pos.z])
                tags.append((r.name, a.name))
    return np.array(xyz), tags


def surface_cations(slab_pdb):
    st = gemmi.read_structure(slab_pdb)
    pts = []
    for ch in st[0]:
        for r in ch:
            for a in r:
                if a.element.name in ("K", "Na"):
                    pts.append([a.pos.x, a.pos.y, a.pos.z])
    p = np.array(pts)
    top = p[:, 2] > p[:, 2].mean()
    return p[top]


def acid_face_frame(xyz, tags):
    """Rotate so the carboxylate array faces -z and the long axis lies along x."""
    cb = np.array([i for i, t in enumerate(tags) if t in CARBOX])
    if len(cb) < 4:
        raise SystemExit("too few carboxylate oxygens")
    c = xyz.mean(0)
    x = xyz - c
    # long axis from the heavy-atom inertia tensor
    _, _, vt = np.linalg.svd(x, full_matrices=False)
    long_ax, mid_ax = vt[0], vt[1]
    # the acidic face is the side the carboxylate centroid sits on
    face = x[cb].mean(0)
    n = face - np.dot(face, long_ax) * long_ax
    if np.linalg.norm(n) < 1e-6:
        n = mid_ax
    n /= np.linalg.norm(n)
    ex = long_ax / np.linalg.norm(long_ax)
    ez = -n                      # acid face points to -z
    ey = np.cross(ez, ex); ey /= np.linalg.norm(ey)
    ex = np.cross(ey, ez)
    return (x @ np.array([ex, ey, ez]).T), cb


def rotz(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])


def match_score(pts_xy, cat_xy, sigma=1.6):
    """Gaussian overlap of carboxylate oxygens with the nearest cation site."""
    d2 = ((pts_xy[:, None, :] - cat_xy[None, :, :]) ** 2).sum(-1)
    return float(np.exp(-d2.min(1) / (2 * sigma ** 2)).sum())


def scan_theta0(frag_pdb, slab_pdb, n=361):
    xyz, tags = load(frag_pdb)
    body, cb = acid_face_frame(xyz, tags)
    cat = surface_cations(slab_pdb)
    cxy = cat[:, :2] - cat[:, :2].mean(0)
    best, curve = None, []
    for k in range(n):
        a = 2 * np.pi * k / (n - 1)
        r = body @ rotz(a).T
        pxy = r[cb][:, :2] - r[cb][:, :2].mean(0)
        s = match_score(pxy, cxy)
        curve.append((np.degrees(a), s))
        if best is None or s > best[1]:
            best = (np.degrees(a), s)
    return best[0], np.array(curve), body, cb, cat


def place(frag_pdb, slab_pdb, registry, placement, theta0=None):
    """registry 0 -> theta0, 1 -> theta0+30. placement in 0,1,2 -> in-plane shift."""
    if theta0 is None:
        theta0, _, body, cb, cat = scan_theta0(frag_pdb, slab_pdb)
    else:
        xyz, tags = load(frag_pdb)
        body, cb = acid_face_frame(xyz, tags)
        cat = surface_cations(slab_pdb)
    ang = np.radians(theta0 + 30.0 * registry)
    r = body @ rotz(ang).T
    # drop onto the surface: lowest fragment atom GAP above the highest cation
    ztop = cat[:, 2].max()
    r[:, 2] += (ztop + GAP) - r[:, 2].min()
    # centre over the slab, then shift by placement (thirds of a surface lattice row)
    cxy = cat[:, :2].mean(0)
    r[:, :2] += cxy - r[:, :2].mean(0)
    shifts = np.array([[0.0, 0.0], [1.73, 0.0], [0.0, 3.01]])  # A, a/3 and b/3
    r[:, :2] += shifts[placement % 3]
    return r, theta0


if __name__ == "__main__":
    import sys
    t0, curve, body, cb, cat = scan_theta0(sys.argv[1], sys.argv[2])
    s = curve[:, 1]
    print(f"theta0 {t0:.1f} deg  score {s.max():.2f}  (mean {s.mean():.2f}, min {s.min():.2f})")
    for d in (30, 60, 90):
        k = int(round((t0 + d) % 360 / 360 * (len(s) - 1)))
        print(f"  +{d:3d} deg: score {s[k]:.2f}  ratio {s[k] / s.max():.3f}")
