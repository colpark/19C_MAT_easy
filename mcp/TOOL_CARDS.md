# PanelBench MCP toolset v1: tool cards

Every image tool takes `panel` (a panel id such as `F3b`, resolved by the gateway to `/panels/<id>.jpg`, the task's own crop) and returns JSON
`{values, units, confidence, warnings, provenance, output_images?}`. Provenance always carries tool, tool_version, hub_version, gateway_version,
backing_model, weights_sha256, seed (0), cache (hit|miss), input_sha256 and duration. Image outputs are PNGs in `/workspace/tool_outputs/`.
No tool reads or returns paper text, captions, keys or item metadata. Weights live only on node 2 (never in git); hashes are sha256.
Status as of 2026-10-02 on host A's node 2 (spark-0b70). "internal only" = no licence stated or licence restricts redistribution.

| # | Tool | Family / where | Backing model / method | Version, commit | Weights sha256 | Licence | Status |
|---|---|---|---|---|---|---|---|
| 1 | classify_modality | vision + hub | MicroNet ResNet50 encoder (nasa/pretrained-microscopy-models) + logistic probe on 13 census classes | repo 9b7c4abc; probe trained 2026-10-02 (3,843 census crops, held-out top-1 0.484, top-3 0.748) | encoder 866d7484...7402; probe sha in hub provenance | MIT (encoder); probe ours | works (GPU) |
| 2 | read_scale_bar | plots | EXSCLAIM scale-bar detector + label reader, then a deterministic bar-length measurement; RapidOCR cross-check; deterministic fallback when nothing is found | MaterialEyes/exsclaim 003400ee | detector c7ae5154...b4; reader 31832d76...5c | LICENSE file GPL-3.0 (setup.py/PyPI 0.1.0 say MIT; no CC BY 4.0 text); weights: none stated -> internal only | works (GPU) |
| 3 | read_text | plots | RapidOCR 1.4.4 (PaddleOCR PP-OCRv4 det/rec/cls, ONNX), 2x upscale for small images, second pass rotated 90 deg | rapidocr-onnxruntime 1.4.4 | det d2a7720d...9da9; rec 48fc40f2...683b; cls e47acedf...215c | Apache-2.0 | works (CPU) |
| 4 | zoom_region | hub | PIL Lanczos crop + 2x/4x upsample | hub 1.0.0 | - | ours | works |
| 5 | segment | vision | SAM 2.1 hiera_small, auto or point prompts | facebookresearch/sam2 2b90b9f5 | sam2.1_hiera_small.pt 6d1aa6f3...4d38 | Apache-2.0 | works (GPU) |
| 6 | segment_microstructure | vision | MatSAM prompting recipe re-implemented on official segment-anything ViT-H (MatSAM repo imports a missing module; centroid normalisation bug fixed) | USTB-AI3DVIP/matsam cbea7eda (recipe); segment-anything dca509fe | sam_vit_h_4b8939.pth a7bf3b02...262e | MatSAM: no LICENSE file -> internal only; SAM Apache-2.0 | works (GPU, ~9 s/image) |
| 7 | grain_size_astm | vision + hub | Cellpose-SAM `cpsam` masks -> ASTM E112 planimetric G and mean intercept (G needs a scale bar, from read_scale_bar) | cellpose 4.2.1.1; HF mouseland/cellpose-sam 7c61431b | cpsam e1440429...abe2 | conflicting: HF card BSD-3, cellpose README "trained on CC-BY-NC data" -> research / non-commercial | works (GPU) |
| 8 | particle_stats | hub | statistics of SAM / MatSAM mask areas + read_scale_bar calibration | hub 1.0.0 | (from segment) | ours | works |
| 9 | grain_boundary_map | vision | UNet++ with MicroNet encoder: **no trained grain-boundary decoder is published** | nasa/pretrained-microscopy-models 9b7c4abc | - | MIT | **unavailable** (returns status unavailable) |
| 10 | sem_refocus | refocus | BNL refocus MAE-MoE (ViT-MAE-large backbone, 4 experts top-1, 224 px windows, overlap 8) | mirajucr/naturecomm_refocus_release 225aeca0; facebook/vit-mae-large 142cb8c | backbone 28a019bd...5a84; checkpoints not obtained | **none stated, internal only** | **unavailable**: checkpoints on a Google Drive folder that requires sign-in |
| 11 | sem_embed | refocus + hub | mean-pooled MAE-MoE encoder features, k nearest labelled census crops | as above | as above | **none stated, internal only** | **unavailable** (same blocker; census index not built) |
| 12 | color_regions | hub | k-means on RGB (scipy kmeans2, seeded), connected components, channel overlap fractions | hub 1.0.0 | - | ours | works |
| 13 | line_profile | hub | skimage profile_line + gradient edge detection | hub 1.0.0 | - | ours | works |
| 14 | sem_optics | myscope | sem_api /metadata (field of view = 127000/M um, pixel size, depth of field, ...) | sem_api 1.0.0 (myscopegit-main.zip 3bb7dd7b) | - | kit (no LICENSE file in the zip) -> internal | works |
| 15 | sem_simulate | myscope | sem_api /render, 24 bounded parameters, boundary errors returned unchanged | sem_api 1.0.0 | - | as above | works |
| 16 | find_atoms | vision | AtomAI pretrained segmenters G_MD (default) / BFO, plus our auto-rescale to ~32 px spacing (raw models found 0 atoms at 12 px) | atomai 0.8.1 (93c88817) | G_MD eda6cbb9...7861; bfo f362a7ca...7fc3 | MIT | works (GPU) |
| 17 | fft_dspacing | hub | numpy FFT (Hann), local maxima, Friedel pairs merged | hub 1.0.0 | - | ours | works |
| 18 | saed_rings | hub | radial profile peaks; spot mode (bright maxima grouped by radius) for spot patterns | hub 1.0.0 | - | ours | works |
| 19 | simulate_tem | science | abTEM HRTEM / HAADF / diffraction, own zone-axis supercell builder, 5 nm default thickness | abTEM 1.0.10 (cupy-cuda13x 14.2.0) | - | **GPL-3.0, internal use** | works (GPU) |
| 20 | axis_calibrate | hub | read_text tick OCR + least-squares linear / log10 fit; '10'+exponent runs read as powers of ten | hub 1.0.0 | (from read_text) | ours | works |
| 21 | digitize_curve | plots + hub | LineFormer line extraction (mmdet 2.28.2, mmcv-full 1.7.2 built from source) mapped through axis_calibrate; colour tracer fallback | TheJaeLal/LineFormer 7952e27b | iter_3000.pth ac03d7d5...eb0 | **no LICENSE file -> internal only** (colour fallback is ours) | works (GPU) |
| 22 | chart_to_table | plots | DePlot (google/deplot), local font file instead of a Hub download | transformers 5.18.0 | model.safetensors ab900556...711b; Arial.TTF 35c0f355... | Apache-2.0 (model); font proprietary, from an unlicensed HF repo | works (GPU); unreliable on log axes |
| 23 | curve_metrics | hub | numpy/scipy: yield_0p2_offset, uts, elongation, peaks, onset, arrhenius_slope, tauc_gap, value_at_x, x_at_value, slope_change | hub 1.0.0 | - | ours | works |
| 24 | xrd_phase_match | science | **fallback** peak-list matching against 43 library phases (Dara/BGMN is x86-64 only); ranked top-k and greedy combination | dara 1fd9bed2 (not used) | - | Dara MIT; fallback ours | works as fallback (labelled in every response) |
| 25 | xrd_simulate | science | pymatgen XRDCalculator; CIF, library phase or formula | pymatgen 2026.9.24 | - | MIT; library 43 COD CIFs (public domain / CC0) | works |
| 26 | peak_fit | science | lmfit gauss / lorentz / voigt, auto seeds | lmfit 1.3.4 | - | BSD-3 | works |
| 27 | xas_edge | science | xraylarch pre_edge: E0, edge step, white line | xraylarch 2026.2.2 | - | MIT | works |
| 28 | xas_predict | omnixas | OmniXAS XASBlock (FEFF Ti-Cu, VASP Ti/Cu) on M3GNet site features | AI-multimodal/OmniXAS 57a6282d; torch 2.1.0 CPU, dgl 2.2.1, matgl 0.8.5 | 10 XASBlock ckpts + M3GNet (hashes in env_logs/omnixas.md) | BSD-3 | works (CPU) |
| 29 | mlip_energy | science | MACE-MPA-0 medium (default), Orb v3 conservative (optional); energy / relax / eos / elastic | mace-torch 0.3.16; orb-models 0.7.0 | mace 75428afe...b638; orb bd1840d1...216a | MIT; Apache-2.0 | works (GPU) |
| 30 | phase_equilibria | science | pycalphad equilibrium with 3 open TDBs: nist_solder (public domain), mc_fe v2.059 and mc_fecocrnbti (MatCalc, ODbL) | pycalphad 0.11.2 | TDB sha256 in env_logs/science.md | MIT; TDBs as listed | works |

Full build logs, pins and weight hashes per family: `env_logs/<family>.md` and `env_logs/<family>_freeze.txt`.
