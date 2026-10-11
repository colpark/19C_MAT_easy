# v5 log (I10)

- 2026-10-10 `git worktree add -b v5/2026-10-10 ~/Documents/harbor/v5 5f94af618` (from ~/Documents/harbor/git/19C_MAT_easy).
- 2026-10-10 `python3 -m venv ~/v5env; pip install pymatgen mcp numpy scipy` -> pymatgen 2026.9.24, mcp 2.3.0, numpy 2.5.3, scipy 1.18.1, Python 3.12.3.
- 2026-10-10 partial-occupancy smoke test: XRDCalculator and NDCalculator both accept {Si:0.5, Ge:0.5} sites; L1_2 Ni3Al (100) 10.2 %, (110) 8.2 % of (111) fully ordered (X-ray, scaled).
- Claude Code 2.1.296. Spend $0.
- 2026-10-11 Qwen/Qwen3-8B (David approved): huggingface_hub snapshot_download on host B, revision b968826d9c46dd6066d109eabc6255188de91218, 16 GB, sha256 per file in validation/Qwen3-8B.sha256. vLLM 0.30.0 (torch 2.13.0+cu130) copied from host A ~/.venv-vllm.
- 2026-10-11 WBM relaxed structures (approved fetch, once): figshare article 22715158 file 48169600 `2024-08-04-wbm-relaxed-atoms.extxyz.zip`, 99,522,982 bytes, md5 4726643ac0dfbab69a4284454c891e68 (matches figshare computed_md5), sha256 7660992d648927e9aeac4eedf3b3c74622feea1160c946d9f0090d47e38e3daa, at data/stage2/ (not in git). figshare.com/ndownloader answers curl with an AWS WAF challenge (202, empty body); ndownloader.figshare.com from the API's download_url works. pip install matbench-discovery 1.3.1 into ~/v5env (additions only; frozen packages unchanged); importing matbench_discovery.data attempts a download (blocked, 0-byte file removed).
