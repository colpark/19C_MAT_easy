"""How many steps does one peptide-on-Au relaxation actually need, and which optimiser is cheapest?

Projecting from a capped run is the v8 error that hard rule 4 forbids, so this measures the real
cost per evaluation before any production run is launched. Two optimisers on the identical
starting structure, high cap, convergence trajectory recorded.
"""
import json, os, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fm_run as F

cd = os.path.expanduser("~/v9_data/fm/conf")
pid, k, j = "P000", 1, 0
CAP = int(sys.argv[1]) if len(sys.argv) > 1 else 800

from ase import Atoms
from ase.constraints import FixAtoms
from ase.optimize import LBFGS, FIRE
from fairchem.core import FAIRChemCalculator, pretrained_mlip

pu = pretrained_mlip.get_predict_unit("uma-s-1p2", device="cuda")
calc = FAIRChemCalculator(pu, task_name="oc20")
S, fixed = F.slab()
cell = S.cell.array
ztop = S.positions[:, 2].max()
S.calc = calc
LBFGS(S, logfile=None).run(fmax=0.05, steps=200)
e_slab = float(S.get_potential_energy())
slab_pos = S.get_positions()

sym = list(np.load(os.path.join(cd, f"{pid}_sym.npy")))
base = F.lie_flat(np.load(os.path.join(cd, f"{pid}_c{k}.npy")))
row = F.placements(2)[j]
p = base @ F.rotz(row[2]).T
p[:, 0] += row[0] * cell[0, 0] - p[:, 0].mean()
p[:, 1] += row[1] * cell[1, 1] - p[:, 1].mean()
p[:, 2] += (ztop + F.GAP_A + row[3]) - p[:, 2].min()
allpos = np.vstack([slab_pos, p])
allsym = list(S.get_chemical_symbols()) + sym
m = np.zeros(len(allsym), bool); m[:len(S)] = fixed

out = {}
for name, Opt in (("LBFGS", LBFGS), ("FIRE", FIRE)):
    cx = Atoms(symbols=allsym, positions=allpos.copy(), cell=cell, pbc=True)
    cx.set_constraint(FixAtoms(mask=m))
    cx.set_tags(np.concatenate([np.where(fixed, 0, 1), np.full(len(sym), 2)]))
    cx.calc = calc
    traj, t0 = [], time.time()
    opt = Opt(cx, logfile=None)
    for conv in opt.irun(fmax=0.05, steps=CAP):
        n = opt.get_number_of_steps()
        if n % 50 == 0 or conv:
            fm = float(np.abs(cx.get_forces()[~m]).max())
            traj.append(dict(step=n, fmax=round(fm, 4),
                             e_ads=round(float(cx.get_potential_energy()) - e_slab, 4),
                             t=round(time.time() - t0, 1)))
            print(f"  {name} step {n:5d} fmax {fm:8.4f} t {time.time()-t0:7.1f}s", flush=True)
        if conv:
            break
    ns = opt.get_number_of_steps()
    out[name] = dict(steps=ns, converged=bool(np.abs(cx.get_forces()[~m]).max() <= 0.05),
                     final_fmax=round(float(np.abs(cx.get_forces()[~m]).max()), 4),
                     wall_s=round(time.time() - t0, 1),
                     s_per_step=round((time.time() - t0) / max(ns, 1), 4), traj=traj)
    print(f"{name}: {ns} steps, converged={out[name]['converged']}, "
          f"fmax {out[name]['final_fmax']}, {out[name]['wall_s']}s "
          f"({out[name]['s_per_step']}s/step)", flush=True)

out["n_atoms"] = len(allsym)
out["cap"] = CAP
json.dump(out, open(os.path.expanduser("~/v9_data/fm/probe/conv_probe.json"), "w"), indent=1)
