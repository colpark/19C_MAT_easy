# Stage 4b data audit (V5_SPEC J.1; V5-26)

Cached files (data/stage4, sha256 in data/stage4/data_stage4.sha256; data/stage2 WBM relaxed structures):

| quantity | file | WBM entries carrying it |
|---|---|---|
| PBE band gap | 2023-12-13-wbm-summary.csv.gz, column `bandgap_pbe` | 256,963 of 256,963 (36,944 with gap > 0; 21,680 with gap ≥ 1.0 eV; 220,019 with gap 0) |
| total magnetic moment | any cached file | 0 (the summary has no moment column; the computed structure entries have no `data` field) |
| site magnetic moments | 2022-10-19-wbm-computed-structure-entries.json.bz2 (site properties), 2024-08-04-wbm-relaxed-atoms.extxyz.zip (headers) | 0 of 256,963; 0 of the first 3,000 extxyz headers |

Property families (J.1): R, H and G run; M does not run; CHGNet is not fetched.

Gap model (approved fetch, 2026-10-12): MatGL 4.1.0 `MEGNet-BandGap-mfi-MP-2019.4.1` from the Hugging Face repo `materialyze/MEGNet-BandGap-mfi-MP-2019.4.1`, revision 21979da3d95d41e51ab920d149ae745f910efe11, in a separate venv on node A2 (~/v5gap; the MACE venv unchanged). Files copied to data/stage4b/gap_model/ (sha256 in data/stage4b/gap_model.sha256): model.pt 742071cb…, state.pt 2ab94270…, model.json 8022a635…. Check: Si 0.46 eV, NaCl 5.05 eV, Cu 0.01 eV at PBE fidelity (state 0).
