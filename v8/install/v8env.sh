# Source before every v8 job (amendment A, item 3): v8-only caches, BLAS caps.
export FAIRCHEM_CACHE_DIR=$HOME/v8_data/fairchem
export HF_HOME=$HOME/v8_data/hf
export HF_TOKEN_PATH=$HOME/.cache/huggingface/token   # read only; never copied
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4
export PYTHONDONTWRITEBYTECODE=1
export TMPDIR=$HOME/v8_data/tmp; mkdir -p "$TMPDIR"
for p in $HOME/v8_data/src/afmize/bin/afmize $HOME/v8_data/src/afmize_src/bin/afmize; do [ -x "$p" ] && export AFMIZE=$p; done
V8PY=$HOME/v8env/bin/python
