"""The validity check every structure must pass before a force-field run (amendment F item 3).

Reports the minimum heavy-atom pair distance and the count of pairs below 1.0 A, and
refuses the structure if any pair is below 1.0 A. This is the check that would have caught
the tiled rods (V8-E14) before they reached a force field.

Usage: python validity.py FILE [FILE ...]      exit 1 if any structure is refused
"""
import sys

import gemmi
import numpy as np
from scipy.spatial import cKDTree

LIMIT = 1.0  # Angstrom


def check(path):
    st = gemmi.read_structure(path)
    st.remove_hydrogens()
    st.remove_alternative_conformations()
    xyz, lab = [], []
    for model in st:
        for ch in model:
            for r in ch:
                for a in r:
                    xyz.append([a.pos.x, a.pos.y, a.pos.z])
                    lab.append(f"{r.name}{r.seqid.num}:{a.name}")
        break
    p = np.array(xyz)
    tree = cKDTree(p)
    bad = sorted(tree.query_pairs(LIMIT))
    d, j = tree.query(p, k=2)
    near = d[:, 1]
    worst = [(float(np.linalg.norm(p[i] - p[k])), lab[i], lab[k]) for i, k in bad[:5]]
    return dict(path=path, n_atoms=len(p), min_pair_A=float(near.min()),
                n_pairs_below_limit=len(bad), ok=len(bad) == 0, worst=worst)


if __name__ == "__main__":
    bad_any = False
    for f in sys.argv[1:]:
        r = check(f)
        flag = "OK" if r["ok"] else "REFUSED"
        print(f"{flag:8s} {r['path'].split('/')[-1]:30s} {r['n_atoms']:7d} atoms  "
              f"min pair {r['min_pair_A']:.3f} A  pairs < {LIMIT} A: {r['n_pairs_below_limit']}")
        for d, a, b in r["worst"]:
            print(f"         {d:.3f} A  {a} <-> {b}")
        bad_any |= not r["ok"]
    sys.exit(1 if bad_any else 0)
