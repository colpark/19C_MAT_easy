# V8-0 install check (hosts A1 and B1)

Env `~/v8env` (uv, CPython 3.12.13 aarch64), built on host A by `make_env.sh`; freeze in `freeze_hostA.txt` (sha256 654f78c7b7500952). Host B has no egress to PyPI or download.pytorch.org (V8-E3), so the same env was copied from host A with rsync (no delete flag), and ESMFold weights were copied with it (run with HF_HUB_OFFLINE=1). BLAS caps OMP/OPENBLAS/MKL = 4 on every check.

| Item | Host A node 1 (spark-112b) | Host B node 1 (wcs-180522) |
|---|---|---|
| GPU | NVIDIA GB10 (sm_121) | NVIDIA GB10, driver 580.173.02 |
| torch | 2.13.0+cu130, CUDA available | same |
| OpenMM + CUDA | 8.6.1 (openmm-cuda-13 8.6.1), git b399af47; testInstallation: CUDA forces ok, all platforms within tolerance (Ref vs CUDA 6.75e-06) | same, CUDA ok, within tolerance |
| ParmEd | 4.3.1 | 4.3.1 |
| fairchem-core | 2.23.0 installed | 2.23.0 |
| uma-s-1p2 on GPU | **FAIL**: HF 403 GatedRepoError on `facebook/UMA/checkpoints/uma-s-1p2.pt`, logged-in account not on the authorized list; no cached checkpoint on host A, node A2 or host B | not attempted (no egress, no checkpoint) |
| ESMFold | transformers 4.57.6, `facebook/esmfold_v1` rev 75a3841e; 100 residues folded on GPU in 3.4 s, mean pLDDT 0.851, 100 CA | 2.5 s, mean pLDDT 0.851, 100 CA |
| afmize | ToruNiina/afmize 5b5e668b, Release build; Boost 1.77.0 from archives.boost.io, sha256 5347464a... equals afmize's expected hash (V8-E2); binary sha256 bf03d836aed28405; actin example rendered | built from the same source, binary 888922bcac78ac62 (build path differs); render `tip.tsv` sha256 9918ee6058ad907a, identical to host A |
| Gwyddion pygwy | **FAIL**: no sudo; Ubuntu noble ships gwyddion 2.64 whose pygwy is Python 2 only | same |

## Fallback for pygwy (prompt V8-0 step 3)
`v8/instrument/dilation.py`: Villarrubia dilation as `scipy.ndimage.grey_dilation` with afmize's tip (hemisphere R joined to a cone of half-angle alpha) as the structuring element. Check (`check_dilation.py`, `check/*.toml`): afmize renders the actin example at 5 Å px with a near-sharp probe (R 0.1 Å) and with its own R 20 Å, 10° tip, no noise. Over 3936 filament pixels (tip image max 92.7 Å), grey_dilation of the sharp image against afmize's tip image: RMS 2.86 Å, mean -2.04 Å, max 12.04 Å; without dilation, RMS 30.46 Å. Identical on both hosts. The residual -2 Å bias is consistent with sub-pixel atom peaks lost in the 5 Å sharp image; it will be re-checked at the instrument's pixel size in V8-2.

## Outcome
Every item passes except UMA weights. Per the prompt ("If access is missing, stop at V8-0 and ask David"), v8 stops here. No truth or world work has started.
