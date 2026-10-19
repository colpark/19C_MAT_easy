"""V8-1 / amendment C item 1: verify the repeat-unit count and rod shapes from the design PDBs.

Builder-only (reads published design names). Sequence-only and geometry-only: no FM call,
no truth run. Usage: python supply.py ROSETTA_MODELS_DIR OUT.json
"""
import glob, json, os, sys
from collections import Counter

import gemmi
import numpy as np

P = 50  # repeat length


def protein_chains(path):
    st = gemmi.read_structure(path)
    out = []
    for ch in st[0]:
        seq = gemmi.one_letter_code([r.name for r in ch])
        if seq.count("X") < len(seq) / 2:
            ca = np.array([r["CA"][0].pos.tolist() for r in ch if r.find_atom("CA", "*")])
            out.append((ch.name, seq, ca))
    return out


def cyc_mismatch(a, b):
    """Fewest mismatches between two 50-mers over all cyclic shifts of b."""
    return min(sum(x != y for x, y in zip(a, b[k:] + b[:k])) for k in range(len(b)))


def internal_units(seq):
    """Distinct 50-mers tiling the sequence at the period, phase chosen to match the most blocks."""
    best = None
    for ph in range(P):
        blocks = [seq[i:i + P] for i in range(ph, len(seq) - P + 1, P)]
        c = Counter(blocks)
        score = c.most_common(1)[0][1] if c else 0
        if best is None or score > best[0]:
            best = (score, ph, blocks)
    _, ph, blocks = best
    inner = blocks[1:-1] if len(blocks) > 2 else blocks  # drop blocks that overlap caps
    return ph, blocks, inner


def rod_dims(ca):
    """Length and width (nm) of the CA cloud along its principal axes (full extent)."""
    x = ca - ca.mean(0)
    _, _, vt = np.linalg.svd(x, full_matrices=False)
    proj = x @ vt.T
    ext = proj.max(0) - proj.min(0)
    return float(ext[0]) / 10, float(ext[1]) / 10


if __name__ == "__main__":
    d = sys.argv[1]
    files = sorted(glob.glob(os.path.join(d, "*.pdb")) + glob.glob(os.path.join(d, "variants_and_non_assembling_designs", "*.pdb")))
    rows, all_inner = {}, Counter()
    for f in files:
        name = os.path.basename(f)[:-4]
        chains = protein_chains(f)
        ch, seq, ca = max(chains, key=lambda c: len(c[1]))  # longest protein chain = one rod
        ph, blocks, inner = internal_units(seq)
        all_inner.update(set(inner))
        L, W = rod_dims(ca)
        rows[name] = dict(chain=ch, length_res=len(seq), n_protein_chains=len(chains), phase=ph,
                          n_blocks=len(blocks), inner_units=sorted(set(inner)),
                          rod_length_nm=round(L, 1), rod_width_nm=round(W, 1), aspect=round(L / W, 2))
    U0 = all_inner.most_common(1)[0][0]
    print("U0 =", U0, " designs carrying it exactly:", all_inner[U0])
    for name, r in rows.items():
        mm = [cyc_mismatch(U0, u) for u in r["inner_units"]]
        r["mismatch_to_U0"] = mm
        r["shares_U0_within2"] = bool(mm) and max(mm) <= 2
        print(f"{name:32s} units {len(r['inner_units'])} mm {mm}  rod {r['rod_length_nm']:5.1f} x {r['rod_width_nm']:4.1f} nm  aspect {r['aspect']:4.1f}")
    n0 = sum(r["shares_U0_within2"] for r in rows.values())
    print(f"\n{n0} of {len(rows)} designs share U0 within 2 mismatches (all inner units)")
    json.dump(dict(U0=U0, designs=rows), open(sys.argv[2], "w"), indent=1)
