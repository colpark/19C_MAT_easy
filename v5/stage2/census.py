"""Stage 2 census of the WBM relaxed structures (cached file only; no FM call). One row per material:
id, reduced formula, elements, nsites, space group (moyopy, symprec 1e-3 and 0.1), volume and energy per atom.
  python stage2/census.py data/stage2/2024-08-04-wbm-relaxed-atoms.extxyz.zip stage2/wbm_census.jsonl"""
import io, json, os, sys, zipfile
for _v in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS'): os.environ.setdefault(_v, '1')
from multiprocessing import Pool
import numpy as np


def parse(txt):
    lines = txt.strip().splitlines(); n = int(lines[0]); hdr = lines[1]
    import re, shlex
    lat = np.array([float(x) for x in re.search(r'Lattice="([^"]+)"', hdr).group(1).split()]).reshape(3, 3)
    mid = re.search(r'material_id=(\S+)', hdr).group(1); e = float(re.search(r'energy=(\S+)', hdr).group(1))
    sp, pos = [], []
    for l in lines[2:2 + n]:
        t = l.split(); sp.append(t[0]); pos.append([float(v) for v in t[1:4]])
    return mid, lat, sp, np.array(pos), e


def row(item):
    name, txt = item
    try:
        import moyopy
        from pymatgen.core import Composition
        mid, lat, sp, pos, e = parse(txt)
        frac = np.linalg.solve(lat.T, pos.T).T % 1.0
        els = sorted(set(sp)); num = [els.index(s) for s in sp]
        cell = moyopy.Cell(lat.tolist(), frac.tolist(), num)
        sg = {}
        for tol in (1e-3, 0.1):
            try: sg[str(tol)] = moyopy.MoyoDataset(cell, symprec=tol).number
            except Exception: sg[str(tol)] = None
        comp = Composition(''.join(sp))
        return dict(id=mid, formula=comp.reduced_formula, elements=els, nsites=len(sp), sg_tight=sg['0.001'], sg_loose=sg['0.1'],
                    vol_per_atom=round(abs(np.linalg.det(lat)) / len(sp), 4), e_per_atom=round(e / len(sp), 5))
    except Exception as ex:
        return dict(id=name, error=f'{type(ex).__name__}: {ex}')


def items(zp):
    with zipfile.ZipFile(zp) as z:
        for n in z.namelist(): yield n, z.read(n).decode()


if __name__ == '__main__':
    zp, out = sys.argv[1], sys.argv[2]
    with Pool(int(os.environ.get('V5_PROCS', '12'))) as p, open(out, 'w') as f:
        for i, r in enumerate(p.imap(row, items(zp), chunksize=500)):
            f.write(json.dumps(r) + '\n')
            if i % 50000 == 0: print(i, flush=True)
