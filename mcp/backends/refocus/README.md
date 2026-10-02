# refocus backend worker (node 2, port 8102)

Wraps https://github.com/mirajucr/naturecomm_refocus_release @ 225aeca (BNL SEM refocus MAE-MoE).
License: **none stated (no LICENSE file), internal evaluation only.** Do not commit or redistribute its code or weights;
only this wrapper lives in git. Upstream code is imported at runtime from `~/mcp/refocus/repo`.

Layout on node 2 (`~/mcp/refocus/`): `.venv` (uv, see freeze.txt), `repo/` (clone), `weights/vit-mae-large/`
(facebook/vit-mae-large), `weights/checkpoints/` (reviewer .ckpt files from the Google Drive folder in the upstream README:
`zero_shot_e4_public_review.ckpt`, `fine_tuned_edge10_e4_public_review.ckpt`, `fine_tuned_charb_e4_public_review.ckpt`).

Start: `~/mcp/refocus/start.sh` (runs `.venv/bin/python worker.py` with HF_HUB_OFFLINE=1, TRANSFORMERS_OFFLINE=1).

Endpoints: GET /health, GET /version, POST /sem_refocus, POST /sem_embed with
`{"image_b64": ..., "args": {"checkpoint": "zero_shot|edge10|charb"}, "seed": 0}`.
- sem_refocus: 224 px sliding window, overlap 8, 4 experts, top-1, Hann stitching (upstream). Returns `images.restored` (PNG).
- sem_embed: 1024-d mean of ViT-MAE-MoE encoder patch tokens over all windows.
