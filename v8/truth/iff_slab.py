"""Build an OpenMM-ready muscovite (001) slab from the IFF v1.5 distribution model.

Reads the Materials Studio CAR file of the IFF mica model (atom types, charges,
coordinates, cell), tiles it in a and b, optionally exchanges the surface cation,
and writes a PDB plus a matching OpenMM ForceField XML.

The slab is held rigid in the truth protocol, so no bonded terms are emitted: a
fixed slab contributes no internal energy to the registry margin, which is a
difference between two placements of the same slab. Nonbonded parameters come
from charmm27_interface_v1_5.prm (IFF) with CHARMM combination rules, which match
OpenMM's Lorentz-Berthelot in sigma and epsilon.

Usage:
  python iff_slab.py CAR PRM OUT_PREFIX --na 2 --nb 3 [--cation NA]
"""
import argparse, hashlib, math, os, re

import numpy as np

KCAL = 4.184  # kJ per kcal
SIG = 2.0 ** (-1.0 / 6.0) * 2.0  # Rmin/2 -> sigma factor: sigma = 2*(Rmin/2)/2^(1/6)

# Element masses (amu) for the species the mica model uses, plus Na.
MASS = dict(H=1.008, O=15.9994, Al=26.981539, Si=28.086, K=39.102, Na=22.98977)


def read_car(path):
    """Return (cell, atoms) where atoms is a list of dicts with name, type, element, charge, xyz."""
    cell, atoms = None, []
    for line in open(path):
        if line.startswith("PBC "):
            f = line.split()
            cell = tuple(float(x) for x in f[1:7])
            continue
        f = line.split()
        # CAR atom line: name x y z resname resid type element charge
        if len(f) >= 9 and re.match(r"^[A-Za-z]{1,2}\d+$", f[0]):
            try:
                xyz = [float(f[1]), float(f[2]), float(f[3])]
                q = float(f[8])
            except ValueError:
                continue
            atoms.append(dict(name=f[0], type=f[6], element=f[7], charge=q, xyz=xyz))
    if cell is None:
        raise ValueError(f"no PBC line in {path}")
    return cell, atoms


def read_prm_nonbonded(path):
    """Parse the CHARMM-IFF NONBONDED block: type -> (epsilon kcal/mol, Rmin/2 Angstrom)."""
    out, inblock = {}, False
    for line in open(path):
        s = line.split("!")[0].rstrip()
        if not s:
            continue
        head = s.split()[0].upper()
        if head == "NONBONDED":
            inblock = True
            continue
        if inblock and head in ("BONDS", "ANGLES", "DIHEDRALS", "IMPROPER", "CMAP", "NBFIX", "HBOND", "END"):
            inblock = False
        if not inblock or line[0].isspace():
            continue
        f = s.split()
        if len(f) >= 4:
            try:
                out[f[0].lower()] = (float(f[2]), float(f[3]))
            except ValueError:
                pass
    return out


def cell_vectors(cell):
    a, b, c, al, be, ga = cell
    al, be, ga = (math.radians(x) for x in (al, be, ga))
    va = np.array([a, 0.0, 0.0])
    vb = np.array([b * math.cos(ga), b * math.sin(ga), 0.0])
    cx = c * math.cos(be)
    cy = c * (math.cos(al) - math.cos(be) * math.cos(ga)) / math.sin(ga)
    vc = np.array([cx, cy, math.sqrt(max(c * c - cx * cx - cy * cy, 1e-12))])
    return np.array([va, vb, vc])


def build(car, prm, na, nb, cation="K"):
    cell, atoms = read_car(car)
    nbd = read_prm_nonbonded(prm)
    V = cell_vectors(cell)
    out = []
    for ia in range(na):
        for ib in range(nb):
            shift = ia * V[0] + ib * V[1]
            for at in atoms:
                a = dict(at)
                a["xyz"] = list(np.array(at["xyz"]) + shift)
                out.append(a)
    # Surface cation exchange (amendment B item 2). The IFF single layer carries K+ on
    # both basal surfaces, so both are exchanged: a mixed-cation slab in 100 mM NaCl
    # would be neither K+ nor Na+ muscovite (logged in v8/OPEN_QUESTIONS.md).
    if cation.upper() == "NA":
        for a in out:
            if a["element"] == "K":
                a["element"], a["type"] = "Na", "na+"
    # Per-atom type key: IFF type plus charge (one IFF type carries several charges).
    for a in out:
        a["key"] = f"{a['type']}_{a['charge']:+.3f}".replace(".", "p").replace("+", "P").replace("-", "M")
    return cell, V, out, nbd


def write_pdb(path, cell, atoms):
    with open(path, "w") as fh:
        a, b, c, al, be, ga = cell
        fh.write(f"CRYST1{a:9.3f}{b:9.3f}{c:9.3f}{al:7.2f}{be:7.2f}{ga:7.2f} P 1           1\n")
        for i, at in enumerate(atoms, 1):
            x, y, z = at["xyz"]
            nm = at["pdbname"]
            fh.write(f"HETATM{i:5d} {nm:<4s} SLB A   1    {x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00          {at['element']:>2s}\n")
        fh.write("END\n")


def write_xml(path, atoms, nbd):
    """One residue template SLB; one XML type per (IFF type, charge) pair."""
    keys = {}
    for a in atoms:
        keys.setdefault(a["key"], a)
    lines = ['<ForceField>', ' <AtomTypes>']
    for k, a in keys.items():
        lines.append(f'  <Type name="SLB-{k}" class="{k}" element="{a["element"]}" mass="{MASS[a["element"]]}"/>')
    lines.append(' </AtomTypes>')
    lines.append(' <Residues>\n  <Residue name="SLB">')
    for a in atoms:
        lines.append(f'   <Atom name="{a["pdbname"]}" type="SLB-{a["key"]}" charge="{a["charge"]}"/>')
    lines.append('  </Residue>\n </Residues>')
    # charmm36.xml takes LJ from <LennardJonesForce> (it supports NBFIX), so every type
    # needs an entry there as well as a charge in <NonbondedForce>.
    missing = []
    nb_lines, lj_lines = [], []
    for k, a in keys.items():
        t = a["type"].lower()
        if t not in nbd:
            missing.append(t)
            continue
        eps, rmin2 = nbd[t]
        sigma_nm = SIG * rmin2 / 10.0
        eps_kj = abs(eps) * KCAL
        nb_lines.append(f'  <Atom type="SLB-{k}" charge="{a["charge"]}" sigma="{sigma_nm:.6f}" epsilon="{eps_kj:.6f}"/>')
        lj_lines.append(f'  <Atom type="SLB-{k}" sigma="{sigma_nm:.6f}" epsilon="{eps_kj:.6f}"/>')
    lines.append(' <NonbondedForce coulomb14scale="1.0" lj14scale="1.0" useDispersionCorrection="False">')
    lines += nb_lines
    lines.append(' </NonbondedForce>')
    lines.append(' <LennardJonesForce lj14scale="1.0" useDispersionCorrection="False">')
    lines += lj_lines
    lines.append(' </LennardJonesForce>\n</ForceField>')
    if missing:
        raise SystemExit(f"no IFF nonbonded parameters for types: {sorted(set(missing))}")
    open(path, "w").write("\n".join(lines) + "\n")
    return keys


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("car"); p.add_argument("prm"); p.add_argument("prefix")
    p.add_argument("--na", type=int, default=2); p.add_argument("--nb", type=int, default=3)
    p.add_argument("--cation", default="K")
    ar = p.parse_args()
    cell, V, atoms, nbd = build(ar.car, ar.prm, ar.na, ar.nb, ar.cation)
    # unique 4-char PDB atom names
    for i, a in enumerate(atoms):
        a["pdbname"] = f"{a['element'][0]}{i:03X}"[:4]
    sup = (cell[0] * ar.na, cell[1] * ar.nb, cell[2], cell[3], cell[4], cell[5])
    write_pdb(ar.prefix + ".pdb", sup, atoms)
    keys = write_xml(ar.prefix + ".xml", atoms, nbd)
    q = sum(a["charge"] for a in atoms)
    zs = np.array([a["xyz"][2] for a in atoms])
    cat = [a for a in atoms if a["element"] in ("K", "Na")]
    print(f"{ar.prefix}: {len(atoms)} atoms, {len(keys)} types, net charge {q:+.4f}")
    print(f"  supercell {sup[0]:.3f} x {sup[1]:.3f} x {sup[2]:.3f} A, beta {sup[4]:.3f}")
    print(f"  z range {zs.min():.3f} to {zs.max():.3f} A")
    print(f"  surface cations: " + ", ".join(f"{e} {sum(1 for a in cat if a['element'] == e)}" for e in sorted({a['element'] for a in cat})))
    print(f"  pdb sha256 {hashlib.sha256(open(ar.prefix + '.pdb', 'rb').read()).hexdigest()[:16]}")
    print(f"  xml sha256 {hashlib.sha256(open(ar.prefix + '.xml', 'rb').read()).hexdigest()[:16]}")
