"""Tile rod PDBs by repeating the rigid screw transform between internal 50-residue repeats.

Geometry only, no new sequence. Rods are written with the long axis along +x,
centred at the origin, under ~/v8_data/rods/<hashid>_<n>rep.pdb.
"""
import os, sys, json
import numpy as np

HOME = os.path.expanduser("~")
_RAW = HOME + "/v8_data/src/raw_designs/"
_DD = [d for d in sorted(os.listdir(_RAW)) if os.path.isdir(_RAW + d + "/rosetta_models")][0]  # source dir found by listing (anonymity)
RM = _RAW + _DD + "/rosetta_models/"


def _src(suffix):
    return RM + [f for f in sorted(os.listdir(RM)) if f.endswith(suffix) and "NC" not in f and "checker" not in f][0]
RODS = HOME + "/v8_data/rods/"
HASH = {"U0": "HRm-ea", "C1": "HRm-60", "C2": "HRm-ef", "C3": "HRm-5d", "C4": "HRm-f1"}
REP = 50


def read_chain(path, chain):
    """Return list of residues; each residue = list of (name, element, xyz)."""
    res, key = [], None
    for ln in open(path):
        if not ln.startswith("ATOM") or ln[21] != chain:
            continue
        k = ln[22:27]
        if k != key:
            res.append((ln[17:20], []))
            key = k
        res[-1][1].append((ln[12:16], ln[76:78].strip() or ln[13], np.array([float(ln[30:38]), float(ln[38:46]), float(ln[46:54])])))
    return res


def ca_xyz(res):
    return np.array([[a[2] for a in r[1] if a[0].strip() == "CA"][0] for r in res])


def kabsch(P, Q):
    """Rigid R,t minimising |R P + t - Q|; returns R, t, rmsd."""
    pc, qc = P.mean(0), Q.mean(0)
    H = (P - pc).T @ (Q - qc)
    U, S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1, 1, d]) @ U.T
    t = qc - R @ pc
    return R, t, float(np.sqrt(np.mean(np.sum((P @ R.T + t - Q) ** 2, 1))))


def best_screw(ca):
    """Offset s whose repeat s..s+49 maps onto the next with least RMSD (averaged over available pairs)."""
    n = len(ca)
    best = None
    for s in range(REP):
        ks = [k for k in range(0, n, REP) if s + k + 2 * REP <= n]
        if not ks:
            continue
        rm = [kabsch(ca[s + k:s + k + REP], ca[s + k + REP:s + k + 2 * REP])[2] for k in ks]
        m = float(np.mean(rm))
        if best is None or m < best[0]:
            best = (m, s)
    return best


def screw_info(R, t):
    ang = np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1)))
    w, v = np.linalg.eig(R)
    ax = np.real(v[:, np.argmin(np.abs(w - 1))])
    return ang, float(abs(t @ ax))


def tile(src, chain, n, min_len_chain=True):
    res = read_chain(src, chain)
    ca = ca_xyz(res)
    rms, s = best_screw(ca)
    base = res[s:s + REP]
    R, t, r1 = kabsch(ca[s:s + REP], ca[s + REP:s + 2 * REP])
    atoms = []
    for k in range(n):
        for rr, (name, ats) in enumerate(base):
            for (an, el, x) in ats:
                atoms.append((k * REP + rr + 1, name, an, el, x))
        # advance
        base = [(nm, [(an, el, R @ x + t) for (an, el, x) in ats]) for nm, ats in base]
    meta = dict(offset=s, repeat_rmsd=rms, screw_rot_deg=screw_info(R, t)[0], screw_rise_A=screw_info(R, t)[1])
    return atoms, meta


def orient(xyz):
    c = xyz.mean(0)
    u, s, vt = np.linalg.svd(xyz - c, full_matrices=False)
    return (xyz - c) @ vt.T  # x = long axis


def dims(xyz):
    o = orient(xyz)
    L = np.ptp(o[:, 0])
    # width: extent along the 2nd and 3rd axes; take the larger (footprint seen from top is 2nd after orient of PCA)
    w2, w3 = np.ptp(o[:, 1]), np.ptp(o[:, 2])
    return float(L), float(w2), float(w3)


def write(atoms, path):
    xyz = np.array([a[4] for a in atoms])
    o = orient(xyz)
    with open(path, "w") as f:
        for i, (a, o_) in enumerate(zip(atoms, o), 1):
            rn, nm, an, el, _ = a
            f.write("ATOM  %5d %-4s %3s A%4d    %8.3f%8.3f%8.3f  1.00  0.00          %2s\n" % (i % 100000, an, nm, rn % 10000, o_[0], o_[1], o_[2], el))
        f.write("END\n")
    return dims(xyz)


def rod_path(design, n):
    return RODS + "%s_%drep.pdb" % (HASH[design], n)


def build_all(ns=(14, 18)):
    out = {}
    for d in HASH:
        if d == "U0":
            src, ch = _src("18.pdb"), "B"
        else:
            src, ch = _src("4H_honeycomb.pdb"), "B"
        for n in ns:
            atoms, meta = tile(src, ch, n)
            L, w2, w3 = write(atoms, rod_path(d, n))
            meta.update(length_nm=L / 10, width_nm=max(w2, w3) / 10, width_min_nm=min(w2, w3) / 10, aspect=L / max(w2, w3), natoms=len(atoms))
            out["%s_%drep" % (HASH[d], n)] = meta
    # reference: untiled published source dims
    for nm, src in [("U0_source_chainB", _src("18.pdb")), ("C_source_4H_chainB", _src("4H_honeycomb.pdb"))]:
        xyz = np.array([a[2] for r in read_chain(src, "B") for a in r[1]])
        L, w2, w3 = dims(xyz)
        out[nm] = dict(length_nm=L / 10, width_nm=max(w2, w3) / 10, aspect=L / max(w2, w3))
    json.dump(out, open(RODS + "dims.json", "w"), indent=1)
    return out


if __name__ == "__main__":
    for k, v in build_all().items():
        print(k, {a: (round(b, 3) if isinstance(b, float) else b) for a, b in v.items()})
