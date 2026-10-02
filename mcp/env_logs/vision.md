# vision (node 2, ~/mcp/vision, port 8101) - 2026-10-01

STATUS: 5/6 tools work on GPU (NVIDIA GB10, CUDA). grain_boundary_map UNAVAILABLE (no pretrained decoder exists).
Worker tested over HTTP via start.sh (/health, /version, POST), then stopped. Not running.

## Env (~/mcp/vision/.venv, uv, py3.12.3) - freeze in env_logs/vision_freeze.txt (also ~/mcp/vision/freeze.txt)
- torch 2.14.0+cu130, torchvision 0.29.0+cu130 (download.pytorch.org/whl/cu130, same as ~/panels/.venv), numpy 2.5.3,
  opencv-python-headless 5.0.0.93, scikit-image 0.26.0, scipy 1.18.1, fastapi, uvicorn 0.54.0.
- sam-2 1.0 (editable, SAM2_BUILD_CUDA=0: no custom CUDA ext; only affects optional hole-filling post-proc),
  segment-anything 1.0 (editable), cellpose 4.2.1.1, atomai 0.8.1 (installed --no-deps; mendeleev pin <=0.6.1 ignored,
  latest mendeleev installed), pretrained-microscopy-models 0.1.0 (pins segmentation-models-pytorch 0.2.1, timm 0.4.12).
- venv size 6.0 GB.

## Repos (~/mcp/vision/repos)
| repo | commit | license file | license |
|---|---|---|---|
| https://github.com/facebookresearch/sam2 | 2b90b9f5ceec907a1c18123530e92e794ad901a4 | LICENSE, LICENSE_cctorch | Apache-2.0 (code + checkpoints, README "License") |
| https://github.com/facebookresearch/segment-anything | dca509fe793f601edb92606367a655c15ac00fdf | LICENSE | Apache-2.0 |
| https://github.com/USTB-AI3DVIP/matsam | cbea7edaada991d88d7dfee656bd7e3dac09863f (2024-03-08) | no LICENSE file | none stated, internal only |
| https://github.com/nasa/pretrained-microscopy-models | 9b7c4abc1321e81eca7a68d548e5371676fa74fa | LICENSE.txt, LICENSES_bunded.txt | MIT |
| https://github.com/pycroscopy/atomai | 93c88817a577686d6b8a84ab954872ca5cab7fcc | LICENSE | MIT |
| cellpose (PyPI 4.2.1.1; github.com/MouseLand/cellpose) | - | LICENSE (in dist-info) | BSD-3-Clause code; see weights |

## Weights (~/mcp/vision/weights, node 2 only; SHA256SUMS there)
| file | bytes | sha256 | source | license |
|---|---|---|---|---|
| sam2.1_hiera_small.pt | 184416285 | 6d1aa6f30de5c92224f8172114de081d104bbd23dd9dc5c58996f0cad5dc4d38 | dl.fbaipublicfiles.com/segment_anything_2/092824/ | Apache-2.0 |
| sam_vit_h_4b8939.pth | 2564550879 | a7bf3b02f3ebf1267aba913ff637d9a2d5c33d3173bb679e46d9f338c26f262e | dl.fbaipublicfiles.com/segment_anything/ | Apache-2.0 |
| cellpose/cpsam (USED) | 1233587898 | e1440429eb384f95afe32bcba6510f90d518eaedc917ede549bed6804004abe2 | huggingface.co/mouseland/cellpose-sam @ 7c61431b5fbb078f3296754bd15d9f51b320f837 | see below |
| cellpose/cpsam_v2 (unused; cellpose 4.2 default) | 1233586851 | 0f1cc3f7ecdd8a037a57c6c48d9d8921391be4cbce3fa9f13c3e3a2e1253c667 | same | see below |
| resnet50_pretrained_microscopynet_v1.1.pth.tar | 102546991 | 866d748420c99ccdd2ab988f2dcba12a5070b7c909d26bb3897a1ef65dca7402 | nasa-public-data.s3.amazonaws.com/microscopy_segmentation_models/ | MIT (repo README) |
| G_MD.tar | 11101422 | eda6cbb927a6561eb0ff45f62324c0aca0351a37e7660707902d073917861609 | atomai repo pretrained/ | MIT |
| bfo.tar | 7216226 | f362a7ca08311600b6be1a659d55054f78b6f42714dc3b471da63d9fe55f7fc3 | atomai repo pretrained/ | MIT |

Cellpose-SAM license text locations (conflicting, owner decision):
- HF model card mouseland/cellpose-sam README.md front-matter: `license: bsd-3-clause`.
- github.com/MouseLand/cellpose README.md line 37: "All Cellpose models are trained on data that is licensed under **CC-BY-NC**.
  The Cellpose annotated dataset is also CC-BY-NC." (README badge also shows "GPL v3", LICENSE file is BSD-3 HHMI.)
- Treat as research/non-commercial use.

## Tools
- segment: SAM 2.1 hiera_small (config configs/sam2.1/sam2.1_hiera_s.yaml), bf16 autocast. mode=auto: SAM2AutomaticMaskGenerator
  (points_per_side 32, pred_iou 0.8, stability 0.92; overridable). mode=points: one object per point (best of 3 multimask).
- segment_microstructure: MatSAM is a prompting recipe on SAM v1 (no own weights). Re-implemented from
  notebooks/matsam_example.ipynb + utils/prompt_generator.py: Canny(80,130) -> remove small (<15 px) -> dilate 5 ->
  contour centroids + 32x32 grid as point_grids; SamAutomaticMaskGenerator(ViT-H default in the repo, pred_iou 0.90,
  stability 0.92, box/crop NMS 0.80, 256 pts/batch); polycrystal post-processing (Laplacian edges of masks <=25000 px,
  skeletonize/dilate/erode) -> images.boundary_map and boundary_regions count. Deviations: upstream normalises centroid x by
  image height and y by width (bug for non-square images) -> fixed to x/width, y/height; skimage 0.26 API
  (max_size=N-1 for old min_size=N); upstream utils/segment_anything_ (missing from repo) replaced by official segment-anything.
- grain_size_astm: Cellpose-SAM (cpsam) masks. grain_count, Jeffries planimetric N = interior + 0.5*edge,
  mean_planimetric_grain_area_px = image_area/N, mean_mask_area_px, mean lineal intercept (10 horizontal + 10 vertical lines,
  total length / boundary crossings). ASTM E112: G = 3.321928 log10(N_A per mm^2) - 2.954 (planimetric) and
  G = -6.643856 log10(L_mm) - 3.288 (intercept), only when args.px_per_um given, else null + warning. Optional args.diameter.
- grain_boundary_map: UNAVAILABLE. nasa/pretrained-microscopy-models (and HF jstuckner/*) publish MicroNet ENCODERS only; the
  UNet++ examples train their own decoders on Super/EBC precipitate/oxide data, no grain-boundary model is published.
  Endpoint returns values=null, status "unavailable" with a warning.
- classify_modality_embed: torchvision resnet50 with MicroNet v1.1 weights (strict load: 0 missing, 0 unexpected), fc=Identity,
  2048-d global-avg-pooled feature. Preprocess: RGB, resize to 224x224 INTER_AREA, ImageNet mean/std (pmm uses imagenet
  preprocessing). args.size overrides 224.
- find_atoms: AtomAI 0.8.1 load_model(G_MD.tar) (default; graphene, simulated) or args.model=BFO. Both are scale sensitive
  (raw G_MD found 0 atoms at 12 px spacing). Added auto-rescale: lattice spacing from autocorrelation, image rescaled so
  spacing ~32 px (env ATOMAI_TARGET; sweep of 16/20/24/32 px on synthetic lattices, 32 best), clamp 0.25-4x, coords mapped back.
  args.rescale="auto"|"none"|float, thresh, invert, px_per_nm (adds nn_distance_nm).

## Smoke (GPU, synthetic images; cold = first call incl. model load, warm = second call)
| tool | input / truth | result | cold / warm |
|---|---|---|---|
| segment auto | 512^2, 5 discs | 8 masks (5 discs + background + 2 sub/dup) | 6.4 s / 4.1 s |
| segment points | discs r=60, r=80 (true 11310, 20106 px) | 11262, 20059 px | 0.18 s / 0.13 s |
| segment_microstructure | 768^2 Voronoi, 80 grains | 122 masks, 1073 prompts (49 centroid), 71 boundary regions | 15.4 s / 9.0 s |
| grain_size_astm | same, true mean area 7373 px | 78 grains (48 interior, 30 edge); mean mask area 7168 px; Jeffries 9362 px; intercept 80.8 px; px_per_um=2 -> G 5.78 (planimetric) / 5.97 (intercept) | 4.2 s / 2.4 s |
| grain_boundary_map | - | unavailable (by design) | 0.02 s |
| classify_modality_embed | grains | dim 2048, bitwise deterministic over repeat calls | 0.39 s / 0.02 s |
| find_atoms G_MD | 256^2 triangular lattice a=12 px, 538 atoms | 504 atoms, NN median 11.89 px (std 0.05) | 1.1 s / 0.16 s |
| find_atoms BFO | same | 506 atoms, NN median 11.91 px | 0.20 s / 0.10 s |
Spacing sweep (384^2, a=6/9/12/20/30 px, target 32): G_MD recall 98/97/96/93/90%, BFO 99/96/98/93/96%; NN median within 2% of truth.
Full output: backends/vision/smoke_output.txt.

## Owner decisions
1. Cellpose-SAM weights licence: HF card says BSD-3, cellpose README says models trained on CC-BY-NC data. Research use only?
2. MatSAM has no LICENSE: internal use only; recipe re-implemented (no MatSAM code vendored).
3. grain_boundary_map: train a UNet++/MicroNet decoder on a grain-boundary dataset (none bundled), or drop the tool
   (segment_microstructure boundary_map covers the use case).
4. find_atoms auto-rescale is our addition (not upstream AtomAI); keep or require px_per_nm-based scaling.
5. ViT-H for MatSAM (repo default) costs ~9 s/image warm; could switch to ViT-B for speed.
