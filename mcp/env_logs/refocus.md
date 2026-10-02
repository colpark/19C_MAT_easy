# refocus (node 2, ~/mcp/refocus, port 8102) - 2026-10-01

STATUS: BLOCKED on reviewer checkpoints (Google Drive folder requires Google sign-in). Stack verified on GPU.

## Repo
- https://github.com/mirajucr/naturecomm_refocus_release @ 225aeca0366fb6d12f6280d9e4f3bbd35c44d5b1
- LICENSE: no LICENSE file (GitHub license: null). Internal evaluation only; code/weights not copied to ~/Documents/harbor/mcp.
- Clone at node2 ~/mcp/refocus/repo

## Checkpoints (NOT downloaded)
- Source: https://drive.google.com/drive/folders/1V3yzRBqvQicnYk-yjKXr_Cy3moQ9ydqT
- gdown: "Failed to retrieve folder contents ... (status code 401)"; plain curl from node 2 and host A redirects to
  accounts.google.com/v3/signin. Folder is not shared "Anyone with the link".
- Needed: either the authors make the folder public, or the owner downloads the 3 files in a signed-in browser and copies them to
  node2 ~/mcp/refocus/weights/checkpoints/ with these names:
  - zero_shot -> zero_shot_e4_public_review.ckpt
  - edge10    -> fine_tuned_edge10_e4_public_review.ckpt
  - charb     -> fine_tuned_charb_e4_public_review.ckpt

## Backbone
- facebook/vit-mae-large @ 142cb8c25e1b1bc1769997a919aa1b5a2345a6b8, license apache-2.0
- ~/mcp/refocus/weights/vit-mae-large/pytorch_model.bin 1318371301 B sha256 28a019bd1842a7bdea1cfa9bb390047ad3fab82032cea2045873ca0399ca5a84
- config.json sha256 bc665638c9b2a8de59396d66b3ffe4a26df0240c903ebe6e19cfeb67e5506416; preprocessor_config.json a250969c94afba52d785a0e08dd36e13aeda97c4dd2b7fd0d24b457288536cea
- tf_model.h5 deleted (unused). HF_HOME=~/mcp/refocus/hf_cache.

## Env (~/mcp/refocus/.venv, uv, py3.12) - freeze in env_logs/refocus_freeze.txt
- torch 2.14.0+cu130, torchvision 0.29.1+cu130 (download.pytorch.org/whl/cu130), transformers 4.37.2, numpy 2.2.5, Pillow 11.1.0,
  scikit-image 0.25.0, timm 1.0.15, safetensors 0.5.2, huggingface-hub 0.28.1, fastapi, uvicorn, gdown.
- Not installed: lpips, pyiqa, opencv (only needed for upstream's optional LPIPS/NIQE).
- transformers 4.37.2 works with torch 2.14 on GPU, no API errors.

## Smoke (GPU, NVIDIA GB10) - base MAE weights + freshly initialised MoE wrapper, NO refocus checkpoint (architecture check only)
- model build 4.4 s; Zn-based_24HP_under_00.tif (1020x688) sliding window 224/8 -> output 3x688x1020 in 3.56 s; encoder tokens (1,197,1024).
- Worker: /health and /version OK; POST /sem_refocus returns 503 "checkpoint file missing" as designed. Worker stopped after test.

## Note for when checkpoints arrive
- torch>=2.6 defaults torch.load(weights_only=True); upstream calls torch.load without it. worker.py sets weights_only=False
  (trusts the author checkpoints). Running upstream refocus_inference.py directly may need the same shim.
- Validation still TODO: PSNR/SSIM on the 3 sample pairs per checkpoint (upstream --gt_dir --pair_mode index computes both).
- sem_embed = mean of encoder patch tokens (CLS excluded) over all windows, dim 1024.

## Files
- node2: ~/mcp/refocus/{worker.py,start.sh,freeze.txt,requests.log,repo/,weights/}
- host A: ~/Documents/harbor/mcp/backends/refocus/{worker.py,README.md}
