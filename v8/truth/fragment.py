"""Cut one internal 50-residue repeat from a design model and cap it with ACE/NME.

The V8-X4 fragment reading (amendment C item 3): one internal repeat, never a
design's own N or C cap, because the caps sit at the rod ends and do not set the
registry. Caps are built by renaming the flanking repeats' terminal residues, so
the geometry stays the published one.

Usage: python fragment.py MODEL.pdb UNIT_SEQ OUT.pdb
"""
import sys

import gemmi


def longest_protein_chain(st):
    best = None
    for ch in st[0]:
        seq = gemmi.one_letter_code([r.name for r in ch])
        if seq.count("X") < len(seq) / 2 and (best is None or len(seq) > len(best[1])):
            best = (ch, seq)
    return best


def cut(model_path, unit_seq, out_path):
    st = gemmi.read_structure(model_path)
    st.setup_entities()
    st.remove_alternative_conformations()
    st.remove_hydrogens()
    ch, seq = longest_protein_chain(st)
    i = seq.find(unit_seq)
    if i < 0:
        raise SystemExit(f"unit not found in {model_path}")
    n = len(unit_seq)
    if i == 0 or i + n >= len(seq):
        raise SystemExit("unit sits at a terminus; an internal repeat is required")

    res = list(ch)
    # ACE from the preceding residue's C=O, NME from the following residue's N-CA.
    out = gemmi.Structure()
    out.spacegroup_hm = "P 1"
    mod = gemmi.Model("1")
    nch = gemmi.Chain("A")

    prev, nxt = res[i - 1], res[i + n]
    ace = gemmi.Residue()
    ace.name, ace.seqid = "ACE", gemmi.SeqId(1, " ")
    for src, dst in (("CA", "CH3"), ("C", "C"), ("O", "O")):
        a = prev.find_atom(src, "*")
        if a is None:
            raise SystemExit(f"{model_path}: preceding residue lacks {src}")
        b = gemmi.Atom()
        b.name, b.element, b.pos, b.occ, b.b_iso = dst, a.element, a.pos, 1.0, 0.0
        ace.add_atom(b)
    nch.add_residue(ace)

    for k, r in enumerate(res[i:i + n], start=2):
        nr = gemmi.Residue()
        nr.name, nr.seqid = r.name, gemmi.SeqId(k, " ")
        for a in r:
            if a.name in ("OXT",):
                continue
            nr.add_atom(a)
        nch.add_residue(nr)

    nme = gemmi.Residue()
    nme.name, nme.seqid = "NME", gemmi.SeqId(n + 2, " ")
    for src, dst in (("N", "N"), ("CA", "CH3")):
        a = nxt.find_atom(src, "*")
        if a is None:
            raise SystemExit(f"{model_path}: following residue lacks {src}")
        b = gemmi.Atom()
        b.name, b.element, b.pos, b.occ, b.b_iso = dst, a.element, a.pos, 1.0, 0.0
        nme.add_atom(b)
    nch.add_residue(nme)

    mod.add_chain(nch)
    out.add_model(mod)
    out.setup_entities()
    out.write_pdb(out_path)
    acidic = sum(1 for r in nch if r.name in ("ASP", "GLU"))
    print(f"{out_path}: {len(nch)} residues (ACE + {n} + NME), {acidic} acidic, "
          f"{sum(len(r) for r in nch)} heavy atoms, source {model_path.split('/')[-1]}")
    return out_path


if __name__ == "__main__":
    cut(sys.argv[1], sys.argv[2], sys.argv[3])
