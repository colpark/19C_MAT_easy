# omnixas build log (node 2 spark-0b70)
Started 2026-10-01T23:17:19-05:00

## Result: xas_predict WORKS (CPU)

Node 2 folder: ~/mcp/omnixas (src/ = clone, .venv/, weights/, worker.py, start.sh, validate.py, freeze.txt, requests.log, home/)
Port 8105. Built in ~25 min; no conda / source build needed.

### Environment (uv venv, Python 3.11.15, CPU)
- torch==2.1.0 (CPU aarch64 wheel from download.pytorch.org/whl/cpu)
- dgl==2.2.1 (official aarch64 cp311 wheel, https://data.dgl.ai/wheels/torch-2.1/repo.html)
- matgl==0.8.5, numpy==1.26.4, pymatgen==2024.11.13, torchdata==0.7.0, fastapi, uvicorn. Full pins: omnixas_freeze.txt.
- omnixas package itself is NOT installed (its pyproject pins python==3.11 and pulls jupyter/optuna/tensorboard); worker.py
  reimplements the 30-line inference path from omnixas/utils/lightshow.py + featurizer/m3gnet_featurizer.py.

### Repo
- https://github.com/AI-multimodal/OmniXAS commit 57a6282d3c6717586a1a562614c64a5d18d3ba6f, LICENSE (BSD-3-Clause, BNL/BSA 2022)
- .ckpt files are Git LFS pointers in the clone; fetched from https://media.githubusercontent.com/media/AI-multimodal/OmniXAS/<commit>/<path>;
  every sha256 matches the LFS pointer oid.

### Weights (~/mcp/omnixas/weights/, license BSD-3 OmniXAS/BNL unless noted)
| file | size | sha256 |
|---|---|---|
| xasblock/v1.1.1/Ti_FEFF.ckpt | 7705808 | 146ff8400c8592174eadc455eab7f9e880efea591b4664d335d72e392ef51a42 |
| xasblock/v1.1.1/V_FEFF.ckpt | 7705872 | c32f0e89a0370c48310b17bb57e737495d544bdc8d7632196536f6ed3e06d05c |
| xasblock/v1.1.1/Cr_FEFF.ckpt | 7705808 | 10bff3b14aad9cfcfa9bc9c5505805e8d57e3e07facfab482620c64a29108f4d |
| xasblock/v1.1.1/Mn_FEFF.ckpt | 7705808 | df104d5955bf2ebe0e4a2780d494fbd4ece32c1cc01d8eb9f20e0524f79d7767 |
| xasblock/v1.1.1/Fe_FEFF.ckpt | 7705808 | ccb19257719441ed47464fb08357bd2cd23ae35afd15acc9e6506bdf5a0e534b |
| xasblock/v1.1.1/Co_FEFF.ckpt | 7705872 | 2ec6a08d3754f713c1da630ff0fd475b9d433d93a1c57bb7a75b6ceae108effe |
| xasblock/v1.1.1/Ni_FEFF.ckpt | 7705808 | 255380c09029e32e9b22d34746b55f924e1caf16392a36ea7d2d88a879ca900f |
| xasblock/v1.1.1/Cu_FEFF.ckpt | 7705808 | 9203e7bde220fbb257e6ad2e36e7d3e44d2e95e9a042b55453a00ad945206b46 |
| xasblock/v1.1.1/Ti_VASP.ckpt | 7705808 | a5f38e35a8adec24e7738d6e621b42e5e045f2fbde8eb270a779f06ea2164649 |
| xasblock/v1.1.1/Cu_VASP.ckpt | 7705808 | 921833415f071fe86e0604cabce5b449c5fc6bb27af040775f02792c0bff5a01 |
| tutorial/last.ckpt (not used by worker) | 8430349 | (tutorial-trained Cu model, 600/600/400) |
| M3GNet-MP-2021.2.8-PES/state.pt (BSD-3, Materials Virtual Lab; vendored in OmniXAS repo) | 1193097 | b0bbb07e93642d0b632fb98f7af9d6905d366b94844e3141e81440cf518e3120 |
| M3GNet-MP-2021.2.8-PES/model.pt | 3743 | 69a89500488070be28d5c5f7eff8d45a382278c23993c4dd80029c59904e58e6 |
| M3GNet-MP-2021.2.8-PES/model.json | 7051 | 2c89cafe162bfd9e02471589da07690eefd168cc32ce8c0820709496afdfac7f |

All v1.1.1 checkpoints are 64 -> 500 -> 500 -> 550 -> 141 (tunedUniversalXAS), verified from state_dict shapes.

### Validation (tutorial_omnixas/CU_FEFF.npz, Cu_FEFF.ckpt, CPU) -- validate.py
- Energy grid 8983.173 + 0.25*k (k=0..140) == stored `energies` exactly.
- Our M3GNet features from the tutorial POSCARs vs stored npz features: median rel. max diff 4.4e-7, worst 2.3e-6 (416 test sites).
- MSE on the 416-site Cu FEFF test split (spectra x1000, the training scale): 0.003962 (full POSCAR->M3GNet->XASBlock pipeline;
  identical with stored features). Raw units: 3.96e-9. Mean-spectrum baseline: 0.014746 (pipeline ~3.7x lower).
  All 4172 sites (train+val+test, stored features): 0.000875.
- Repo example (lightshow.py main): mp-1005792 (Sm2CuAs3O) Cu site 8 via CIF through run_xas_predict: MSE 0.002187 (x1000) vs stored
  spectrum (that site is in train/val). Repeat call bit-identical.
- Timing (CPU, 8 threads): 416 test sites (featurize + predict) 22.7 s; single HTTP request 0.08-0.18 s once loaded.
- Refusals: Zn/FEFF and Fe/VASP return HTTP 400 with explicit supported-element list; absent absorber -> 400.

### Notes / owner decisions
- matgl 0.8.5 mkdirs ~/.cache/matgl on import and dgl wrote ~/.dgl/config.json on first import; both created by this build were removed
  (they were new and empty/trivial). start.sh now sets HOME=~/mcp/omnixas/home and DGLBACKEND=pytorch so nothing is written outside the folder.
- VASP models: energy window uses same e_start as FEFF per OmniXAS config (VASP spectra were aligned to it); VASP training
  features were for the excited site (index 0) of the supercell; worker featurizes the given cell and warns.
- Output units: OmniXAS training units (FEFF mu / a0^2), not edge-step normalized. No uncertainty (confidence=null).
- GPU not attempted (torch 2.1.0 CUDA wheels for aarch64/GB10 sm_121 not viable; model is tiny, CPU is fast).
