# plots build log (node 2 spark-0b70)
Built 2026-10-02 (node clock) / 2026-10-01 23:17-23:50 host-A time. Total time was about 35 min.

## Result: all 4 tools WORK on GPU (CUDA, NVIDIA GB10). No fallback was needed for the primary path.

Node 2 folder: `~/mcp/plots` contains `.venv/`, `repos/` (exsclaim, LineFormer), `build/mmcv-1.7.2` (an editable install that must stay in place),
`weights/`, `worker.py`, `start.sh`, `freeze.txt`, `requests.log`, and `smoke/` (synthetic data, client, report). The port is 8103. The worker is NOT left running.
Code copy: `~/Documents/harbor/mcp/backends/plots/` (worker.py, start.sh, README.md, make_synth.py, smoke_client.py).

### Environment (uv venv, Python 3.12.13)
- The torch wheels match ~/panels/.venv: torch==2.14.0+cu130 and torchvision==0.29.0+cu130 from download.pytorch.org/whl/cu130.
- transformers==5.18.0, rapidocr-onnxruntime==1.4.4, onnxruntime==1.30.0 (CPU EP), opencv-python-headless==5.0.0.93, numpy==2.5.3,
  fastapi==0.142.2, uvicorn==0.54.0.
- mmcv-full==1.7.2 is built from source (github.com/open-mmlab/mmcv tag v1.7.2, Apache-2.0) with CUDA ops for sm_121. Two patches were needed:
  `setup.py` `-std=c++14/17` was changed to `-std=c++20` (torch 2.14 headers require C++20), and setuptools was pinned to 75.8.0 because `pkg_resources` was removed in newer versions.
  The build took about 3 min with ninja (MAX_JOBS=16).
- mmdet==2.28.2 is the copy vendored in the LineFormer repo (Apache-2.0, OpenMMLab), installed editable with `--no-deps`. Other packages: bresenham 0.2.1, pycocotools.
- Full pins: `plots_freeze.txt` (107 lines).

### Repos
| repo | URL | commit | LICENSE file | license |
|---|---|---|---|---|
| EXSCLAIM! | https://github.com/MaterialEyes/exsclaim | 003400ee7486568cd229d3ff012613baa2fa6554 (master, 2022-03-26) | `LICENSE` | **GPL-3.0** (full GNU GPL v3 text) |
| LineFormer | https://github.com/TheJaeLal/LineFormer | 7952e27b4653dea025394618fbd655f41d82ab6b (2025-11-26) | **no LICENSE file** | none stated (README has no license either) |
| mmdetection (vendored in LineFormer) | (inside LineFormer/mmdetection) | same | `LICENSE` | Apache-2.0 |
| mmcv | https://github.com/open-mmlab/mmcv | tag v1.7.2 tarball | `LICENSE` | Apache-2.0 |

**EXSCLAIM license detail (the prompt asked whether it is CC BY 4.0 or GPL-3.0).** No CC BY 4.0 text appears anywhere in the repo (grep of md/txt/py/cff).
- The repo's `LICENSE` file is GNU GPL v3.
- `setup.py` sets the classifier `License :: OSI Approved :: MIT License`.
- On PyPI, `exsclaim` 0.1.0 has an empty license field and the classifier "MIT License". The latest release, 2.5.2, has license None and no license classifier. 2.5.2 is built from a different repo, github.com/MaterialEyes/exsclaim2.0.

So the sources conflict. The LICENSE file (GPL-3.0) is the controlling text. CC BY 4.0 may refer to the EXSCLAIM paper or dataset, not the code.
The worker imports only EXSCLAIM's CRNN class and CTC/LM decoder modules (GPL-3.0 code) at runtime, from the clone. Nothing is vendored into this git repo.

### Weights (`~/mcp/plots/weights/`, all on node 2 only)
| file | size (bytes) | sha256 | source | license |
|---|---|---|---|---|
| deplot/model.safetensors (used) | 1129177976 | ab90055611f42fee327d9ecf3c9cdac63e847bd19a0ac8ea86b0e8134fe0711b | hf google/deplot | Apache-2.0 (model card) |
| deplot/pytorch_model.bin (not used) | 1129238081 | d32fa3870d2d89d4e9a7d18bea0a797046eca929035243aa8dcaa8b4bc029c5b | hf google/deplot | Apache-2.0 |
| fonts/Arial.TTF (DePlot header rendering) | 275572 | 35c0f3559d8db569e36c31095b8a60d441643d95f59139de40e23fada819b833 | hf ybelkada/fonts @7f29c3755a0d | **none stated; Arial is a proprietary Monotype font** |
| exsclaim/scale_bar_detection_model.pt | 165749326 | c7ae5154a9acd476a7d61087395c92fc789f79ecd201a172bd407ae8de9237b4 | Google Drive id 1B4_rMbP3a1XguHHX4EnJ6tSlyCCRIiy4 (hard-coded in exsclaim/figure.py) | not stated (repo GPL-3.0) |
| exsclaim/scale_label_recognition_model.pt | 24382780 | 31832d760811d616440aaab89c1ad432292a48a8941423f0f697c80333a95a5c | Google Drive id 1oGjPG698LdSGvv3FhrLYh_1FhcmYYKpu | not stated (repo GPL-3.0) |
| lineformer/models/iter_3000.pth | 569731833 | ac03d7d52a11ce253350bf4bc73416e42ac68021c00bcce14d47fcc28ec65eb0 | Google Drive folder 1K_zLZwgoUIAJtfjwfCU5Nv33k17R0O5T (README link), file id 1cIWM7lTisd1GajDR98IymDssvvLAKH1n | **not stated** |
| RapidOCR models (inside the rapidocr-onnxruntime 1.4.4 wheel): ch_PP-OCRv4_det_infer.onnx | (in .venv) | d2a7720d45a54257208b1e13e36a8479894cb74155a5efe29462512d42f49da9 | PyPI rapidocr-onnxruntime 1.4.4 | Apache-2.0 (RapidOCR and PaddleOCR) |
| ch_PP-OCRv4_rec_infer.onnx | (in .venv) | 48fc40f24f6d2a207a2b1091d3437eb3cc3eb6b676dc3ef9c37384005483683b | same | Apache-2.0 |
| ch_ppocr_mobile_v2.0_cls_infer.onnx | (in .venv) | e47acedf663230f8863ff1ab0e64dd2d82b838fceb5957146dab185a89d6215c | same | Apache-2.0 |

The EXSCLAIM Faster R-CNN is constructed with `weights=None, weights_backbone=None`, so the upstream `pretrained=True` COCO download is skipped. The checkpoint loads with all keys matched.

### Worker
`worker.py` uses FastAPI and uvicorn on 0.0.0.0:8103. Models load lazily behind a global lock. It sets `torch.use_deterministic_algorithms(True, warn_only=True)`, seeds every RNG per request,
and sets HF_HUB_OFFLINE=1 and TRANSFORMERS_OFFLINE=1. Each request is logged to `~/mcp/plots/requests.log` as JSON (tool, input sha256, args, seed, status, duration).
`/version` reports package versions, repo commits, and weight sha256s per tool.
- transformers 5.18 bug: `font_path` is not forwarded to the Pix2Struct header renderer, and the default path downloads Arial from the Hub at request time.
  The worker wraps `render_text` to use the local font, so there are no network calls.

### Smoke test (synthetic, via HTTP; `smoke/smoke_report.json`). Timings are warm except for the first call to each tool.
Data from `make_synth.py`:
- matplotlib 640x480 plots: `linear` (one black series y=2x+3), `logy` (semilogy, 10^(x/2)), `two_series` (red sin, green linear, legend), and `bar` (4 bars).
- `sem_10um`: a 1024x768 noise-and-particles image with a white 200 px bar labelled "10 µm", drawn with PIL.
- `sem_500nm`: a black 150 px bar labelled "500 nm" on a white strip.

| tool | device | result |
|---|---|---|
| read_text | CPU (onnxruntime) | Visible tick, title and axis-label recall: linear 18/18, logy 15/15, two_series 16/16. The rotated y-labels "Current (mA)", "Counts" and "Signal (a.u.)" come from the second pass on the rotated image. 1.0-1.5 s per 640x480 image (2x upscale and 2 passes). Known errors: superscripts are flattened (10^4 is read as "104"), and one x tick "4" was read as "A". |
| read_scale_bar (EXSCLAIM) | CUDA | sem_10um: bar 200.0 px (truth 200, 0.0% error), label "10 um", 20.0 px/um. sem_500nm: bar 150.0 px (truth 150, 0.0%), label "500 nm", 0.300 px/nm. Raw detector box widths were 204.6 and 151.1 px (+2.3% and +0.7%). The deterministic pixel-run refinement brings them to exact. 3.7 s on the first call (model load), 0.8 s warm. |
| read_scale_bar (`method="fallback"`) | CPU | Both images exact (200 px, "10 um"; 150 px, "500 nm"), 0.7-1.1 s. The fallback runs automatically only when EXSCLAIM finds no bar or no label, and is labelled `method=fallback_deterministic` / `exsclaim+fallback_label`. |
| chart_to_table (DePlot) | CUDA | bar: 4/4 exact. linear: 6/6 exact. two_series: 12 values, mean relative error 1.3%. **logy: mean relative error 62%** (it read 10^k ticks as 102/103 and so on; expected). 1.2-1.9 s warm, 10.8 s on the first call including load. |
| digitize_curve (LineFormer) | CUDA | Mean absolute y error vs ground-truth pixel polylines: linear 1.77 px, logy 1.41 px, two_series 1.08 / 1.13 px. Series found: 1/1/2, correct. x coverage 0.99. 0.25-0.5 s warm (2.0 s first call). |
| digitize_curve (`method="color"`, deterministic fallback) | CPU | linear 0.88 px, logy 0.87 px, two_series 0.76 / 0.65 px. Series count correct and coverage 1.0. Legend handles are masked using OCR boxes. About 1.0-1.3 s. |
| determinism | | Repeated calls with the same seed returned identical values for chart_to_table and digitize_curve. |

Caveats: the synthetic images are clean and simple, so these numbers are smoke checks, not benchmark accuracy. The colour tracer's single "dark" cluster will merge several black series,
and it can pick up gridlines or annotations on real figures. LineFormer is the primary method.

### Owner decisions needed
1. **EXSCLAIM licensing conflict.** The LICENSE file is GPL-3.0, while setup.py and PyPI 0.1.0 say MIT. The weights' license is not stated. Decide whether a GPL-3.0 dependency is acceptable (it is only called as a backend service, not vendored into git).
2. **LineFormer has no LICENSE file**, and no license is stated for its checkpoint either. Legally this means all rights are reserved. Ask the authors, or keep using `method="color"` for anything released.
3. **Arial.TTF** (proprietary font, from hf ybelkada/fonts with no license) is used only to render DePlot's prompt header, which matches how DePlot was trained. A free font such as DejaVuSans could replace it, at a small risk of distribution shift (not measured).
4. DePlot is unreliable on log axes. The orchestrator should prefer digitize_curve plus its own axis calibration from read_text tick tokens for line plots.
