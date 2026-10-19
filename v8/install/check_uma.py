"""V8-0 install check: fairchem-core 2.x, uma-s-1p2 on GPU, single point on a water box."""
import hashlib, time, numpy as np, torch, fairchem.core
from ase import Atoms
from ase.build import molecule
from fairchem.core import pretrained_mlip, FAIRChemCalculator
from huggingface_hub import hf_hub_download

ckpt = hf_hub_download("facebook/UMA", "checkpoints/uma-s-1p2.pt")
print("fairchem-core", fairchem.core.__version__, "ckpt sha256", hashlib.sha256(open(ckpt, "rb").read()).hexdigest()[:16])
rng = np.random.default_rng(0)
box, n = 9.86, 32  # ~1 g/cm3 for 32 waters
w = molecule("H2O"); pos, sym = [], []
grid = [(i, j, k) for i in range(4) for j in range(4) for k in range(2)]
for g in grid:
    c = (np.array(g) + 0.5) * np.array([box / 4, box / 4, box / 2])
    pos += list(w.positions + c); sym += w.get_chemical_symbols()
atoms = Atoms(sym, positions=pos, cell=[box] * 3, pbc=True)
pu = pretrained_mlip.get_predict_unit("uma-s-1p2", device="cuda")
for task in ["omol", "omat"]:
    a = atoms.copy()
    if task == "omol":
        a.pbc = False; a.info.update(charge=0, spin=1)
    a.calc = FAIRChemCalculator(pu, task_name=task)
    t = time.time(); e = a.get_potential_energy(); f = a.get_forces()
    print(f"task {task}: E {e:.4f} eV, |F|max {np.abs(f).max():.3f} eV/A, {time.time()-t:.2f} s, natoms {len(a)}")
print("UMA OK")
