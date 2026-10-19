"""V9-5 step 1: three conformers per dev peptide, from ESMFold plus two logged perturbations.

Peptides are addressed by index into the FM subset, never printed as sequences (V9-X1).
Every structure passes the amendment-F validity check before it is written (hard rule 3):
any heavy-atom pair below 1.0 A is refused and reported.

Conformer 0 = ESMFold output.
Conformer 1, 2 = Cartesian Gaussian noise, sigma 0.15 A, seeds logged below, followed by a
short UMA relaxation of the isolated peptide (omol head, 15 steps) to restore sane local
geometry. The noise is applied to all atoms; the relaxation is what makes the result a
conformer rather than a rattled copy.

Usage: python make_conformers.py SPLIT_JSON OUTDIR [--limit N]
"""
import argparse, json, os, time

import numpy as np

NOISE_SIGMA = 0.15
NOISE_SEEDS = [910_001, 910_002]      # logged; conformer 1 and 2
RELAX_STEPS = 15
LIMIT_A = 1.0                          # validity check


def validity(pos, sym):
    """min heavy-atom pair distance and count below LIMIT_A."""
    from scipy.spatial import cKDTree
    heavy = np.array([i for i, s in enumerate(sym) if s != "H"])
    p = pos[heavy]
    t = cKDTree(p)
    bad = t.query_pairs(LIMIT_A)
    d, _ = t.query(p, k=2)
    return float(d[:, 1].min()), len(bad)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("split"); ap.add_argument("outdir"); ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    sp = json.load(open(os.path.expanduser(a.split)))
    subset = [(i, s, "top") for i, s in enumerate(sp["fm_subset"]["top"])] + \
             [(60 + i, s, "bottom") for i, s in enumerate(sp["fm_subset"]["bottom"])]
    if a.limit:
        subset = subset[:a.limit // 2] + subset[60:60 + a.limit // 2]

    import torch
    from transformers import AutoTokenizer, EsmForProteinFolding
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained("facebook/esmfold_v1")
    model = EsmForProteinFolding.from_pretrained("facebook/esmfold_v1", low_cpu_mem_usage=True)
    model = model.cuda().eval()
    model.trunk.set_chunk_size(64)
    print(f"esmfold loaded in {time.time()-t0:.1f}s", flush=True)

    from fairchem.core import FAIRChemCalculator, pretrained_mlip
    from ase import Atoms
    from ase.optimize import LBFGS
    pu = pretrained_mlip.get_predict_unit("uma-s-1p2", device="cuda")
    calc_mol = FAIRChemCalculator(pu, task_name="omol")

    manifest, plddts, refused = [], [], []
    t_fold = t_pert = 0.0
    for idx, seq, cls in subset:
        pid = f"P{idx:03d}"
        t = time.time()
        with torch.no_grad():
            out = model.infer([seq])
        pdb = model.output_to_pdb(out)[0]
        plddt = float(out["plddt"][0, :, 1].mean())
        t_fold += time.time() - t
        plddts.append(plddt)

        # parse the ESMFold PDB by code; no sequence is emitted
        sym, pos = [], []
        for line in pdb.splitlines():
            if line.startswith(("ATOM", "HETATM")):
                e = line[76:78].strip() or line[12:16].strip()[0]
                sym.append(e)
                pos.append([float(line[30:38]), float(line[38:46]), float(line[46:54])])
        pos = np.array(pos)
        entry = dict(pid=pid, cls=cls, n_atoms=len(sym), plddt=plddt, conformers=[])

        for k in range(3):
            p = pos.copy()
            if k:
                t = time.time()
                rng = np.random.default_rng(NOISE_SEEDS[k - 1])
                p = p + rng.normal(0, NOISE_SIGMA, p.shape)
                at = Atoms(symbols=sym, positions=p)
                at.info["charge"], at.info["spin"] = 0, 1
                at.calc = calc_mol
                LBFGS(at, logfile=None).run(fmax=0.05, steps=RELAX_STEPS)
                p = at.get_positions()
                t_pert += time.time() - t
            mn, nbad = validity(p, sym)
            rec = dict(k=k, min_heavy_pair_A=round(mn, 4), n_pairs_below_1A=nbad, ok=nbad == 0)
            if nbad:
                refused.append((pid, k, mn, nbad))
            else:
                np.save(os.path.join(a.outdir, f"{pid}_c{k}.npy"), p)
            entry["conformers"].append(rec)
        if not any(c["ok"] for c in entry["conformers"]):
            print(f"  {pid}: ALL CONFORMERS REFUSED", flush=True)
        manifest.append(entry)
        np.save(os.path.join(a.outdir, f"{pid}_sym.npy"), np.array(sym))
        if len(manifest) % 10 == 0:
            print(f"  {len(manifest)}/{len(subset)} peptides, fold {t_fold:.0f}s pert {t_pert:.0f}s",
                  flush=True)

    summ = dict(n_peptides=len(manifest), noise_sigma=NOISE_SIGMA, noise_seeds=NOISE_SEEDS,
                relax_steps=RELAX_STEPS, validity_limit_A=LIMIT_A,
                plddt_mean=float(np.mean(plddts)), plddt_min=float(np.min(plddts)),
                plddt_max=float(np.max(plddts)),
                n_conformers_written=sum(c["ok"] for e in manifest for c in e["conformers"]),
                n_refused=len(refused), refused=refused,
                t_fold_s=round(t_fold, 1), t_perturb_s=round(t_pert, 1),
                peptides=manifest)
    json.dump(summ, open(os.path.join(a.outdir, "conformers.json"), "w"), indent=1)
    print(f"\npeptides {summ['n_peptides']} | conformers written {summ['n_conformers_written']}"
          f" | refused {summ['n_refused']}")
    print(f"pLDDT mean {summ['plddt_mean']:.3f} min {summ['plddt_min']:.3f} max {summ['plddt_max']:.3f}")
    print(f"fold {t_fold:.0f}s total ({t_fold/len(manifest):.2f}s per peptide), perturb+relax {t_pert:.0f}s")


if __name__ == "__main__":
    main()
