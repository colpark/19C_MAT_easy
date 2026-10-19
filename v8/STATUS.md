# v8 status

**Stopped at V8-0 for David: UMA access missing.** The `facebook/UMA` checkpoints are gated, and the Hugging Face account logged in on host A is not on the authorized list (403 on `checkpoints/uma-s-1p2.pt`). No copy is cached on any reachable node.

Done: branch and folder, kits (both tests pass), PREREG pushed, reachability (host B node 2 unreachable, as in v6), install check on hosts A1 and B1 (`install/INSTALL_CHECK.md`), pygwy fallback.

To resume, one of the following:
1. Approve access for the account on https://huggingface.co/facebook/UMA, or log in on host A with an approved account (for example `! hf auth login`; the token is never written by this session).
2. Put `uma-s-1p2.pt` on host A and give its path.

Then: the UMA single point (`install/check_uma.py`), then V8-1.
