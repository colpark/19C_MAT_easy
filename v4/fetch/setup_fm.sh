#!/bin/bash
# v4 Track C FM reader test environment (local models, no quote): torch (cu130, aarch64) + opencv + SAM 2; checkpoints SAM ViT-H (MatSAM default) and SAM 2.1 hiera-large.
set -u; F=/home/aid1/Documents/harbor/v4_host/fm; cd $F
~/.local/bin/uv venv -q .venv-fm --python 3.12 && \
~/.local/bin/uv pip install -q --python .venv-fm/bin/python torch torchvision --extra-index-url https://download.pytorch.org/whl/cu130 --index-strategy unsafe-best-match && \
~/.local/bin/uv pip install -q --python .venv-fm/bin/python opencv-python-headless scikit-image scipy numpy tifffile natsort matplotlib pillow hydra-core iopath && \
~/.local/bin/uv pip install -q --python .venv-fm/bin/python "git+https://github.com/facebookresearch/sam2.git" ; echo "venv rc=$?"
mkdir -p ckpt && curl -sL -m 3600 -o ckpt/sam_vit_h_4b8939.pth https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth; echo "vit_h $(stat -c %s ckpt/sam_vit_h_4b8939.pth)"
curl -sL -m 3600 -o ckpt/sam2.1_hiera_large.pt https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_large.pt; echo "sam2.1_l $(stat -c %s ckpt/sam2.1_hiera_large.pt)"
sha256sum ckpt/* > ckpt/sha256.txt; .venv-fm/bin/python -c "import torch, sam2, cv2; print('torch', torch.__version__, 'cuda', torch.cuda.is_available())"; echo DONE
