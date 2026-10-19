#!/bin/bash
# V8-0: build ~/v8env (Python 3.12) for OpenMM, ParmEd, fairchem-core 2.x, ESMFold (transformers).
set -x
export UV_LINK_MODE=copy
uv venv --python 3.12 ~/v8env
source ~/v8env/bin/activate
uv pip install --index-url https://download.pytorch.org/whl/cu130 torch
uv pip install "fairchem-core>=2,<3"
uv pip install "openmm[cuda13]" || uv pip install "openmm[cuda12]" || uv pip install openmm
uv pip install parmed "transformers<5" accelerate scipy numpy ase pymatgen gemmi pdbfixer jsonschema
uv pip freeze > ~/v8env_freeze.txt
echo DONE
