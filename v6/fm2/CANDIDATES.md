# V6-14 candidates: sources, versions, weights

The candidate list is fixed by fm2/PREREG.md. Each model's training data was re-verified at its source, using the card or config shipped with the package or weights. No candidate lists Alexandria, OMat24, sAlex, MatPES or WBM-derived data.

## The three candidates

| model | package | training data, as stated at the source | weights (sha256) | venv on node A2 | device |
|---|---|---|---|---|---|
| CHGNet 0.3.0 (the package default) | chgnet 0.4.2 | the pretrained card `chgnet/pretrained/0.3.0/README.md`: "MPtrj dataset with 9-0.5-0.5 train-val-test splitting" | `chgnet_0.3.0_e29f68s314m37.pth.tar` d14ab7c0f093efe6… | ~/v6fm2/.venv | CUDA |
| SevenNet-0 11Jul2024 ('7net-0') | sevenn 0.13.0 | the shipped preset `sevenn/presets/sevennet-0.yaml`: `load_dataset_path: ["path_to_MPtrj_total.sevenn_data"]`; the checkpoint's config validates on the MP CHGNet (MPtrj) set | `checkpoint_sevennet_0.pth` 7052cb42b7b3be42… | ~/v6fm2/.venv | CUDA |
| M3GNet-MP-2021.2.8-PES | matgl 1.1.3 (DGL 2.1.0) | the model card `README.md`: "MP-2021.2.8: Materials Project structure relaxations as of 2021.2.8", 167,378 training structures | from the matgl GitHub tag v1.1.3 (`pretrained_models/M3GNet-MP-2021.2.8-PES/`): model.pt 62678f76fbc5d899…, state.pt a9aa723705bd1a24…, model.json 05e7db8676ceb37e… | ~/v6fm2/.venv_m3g | CPU |

## Versions

- **~/v6fm2/.venv:** Python 3.12.13 (uv), torch 2.12.0+cu130 (the MACE venv's build), chgnet 0.4.2, sevenn 0.13.0, matgl 4.1.0 (installed, unused), torch-geometric 2.8.1, ase 3.29.0, pymatgen 2026.10.16. Install log: ~/v6fm2/install.log.
- **~/v6fm2/.venv_m3g:** matgl 1.1.3, dgl 2.1.0, torch 2.2.1 (CPU), ase 3.23.0, numpy 1.26.4, scipy 1.13.1, pymatgen 2024.5.1. Install log: ~/v6fm2/install_m3g.log.

## Why M3GNet needs a second venv (V6-X22)

- matgl 4.1.0 no longer distributes M3GNet-MP-2021.2.8-PES. Its pretrained list holds only ANI-1x and MatPES variants, which the rule excludes.
- matgl 1.1.3 still loads the model, but it fetches from the repository's main branch, where the files were removed. The weights were therefore taken from the v1.1.3 release tag.
- matgl 1.1.3 needs DGL. DGL 2.1.0 pairs with torch 2.2.1, which has no aarch64 CUDA build, so this model runs on CPU.

## Protocol and ports

- **Protocol:** `mcenv/fm2_service.py`, identical to `mcenv/fm_service.py` (FIRE, FrechetCellFilter, FixSymmetry symprec 1e-3, fmax 0.02 eV/Å, at most 500 steps). The dev relaxations run in batch mode.
- **Ports in use on node A2 at the check:** 8765, 8766, 8768, 8770, 8773, 8776, 8777, 8778.
- **Ports for new services:** 8780 and up. 8771 is left alone (v5 stage 2s).
