# plots backend worker (node 2, spark-0b70, port 8103)

Code-only copy. The live copy, venv, cloned repos and weights are on node 2 under `~/mcp/plots/`
(weights in `~/mcp/plots/weights/`, never in this repo).

Start (node 2):

    ~/mcp/plots/start.sh                     # lazy model loading, binds 0.0.0.0:8103
    PLOTS_PRELOAD=1 ~/mcp/plots/start.sh     # load all four models at startup
    PLOTS_DEVICE=cpu ~/mcp/plots/start.sh    # force CPU

Endpoints: `GET /health`, `GET /version`, and `POST /read_text`, `/read_scale_bar`, `/chart_to_table`,
`/digitize_curve` with body `{"image_b64": ..., "args": {...}, "seed": 0}`.

| tool | backing | key args | values |
|---|---|---|---|
| read_text | RapidOCR 1.4.4 (PP-OCRv4 ONNX, CPU) | `box`, `rotated` (default true), `upscale`, `min_score` | `tokens: [{text, box, score, rotation}]` |
| read_scale_bar | EXSCLAIM! Faster R-CNN + CRNN, with deterministic bar-length refinement. Deterministic fallback if nothing is detected | `score_threshold`, `method="fallback"` | `bar_length_px, label_value, label_unit, px_per_um, px_per_nm, nm_per_px, method, ...` |
| chart_to_table | google/deplot (Pix2Struct), greedy decoding | `max_new_tokens`, `prompt` | `raw_table`, `table{title, header, rows, numeric_columns}` |
| digitize_curve | LineFormer (mmdet 2.28.2 / mmcv-full 1.7.2 built for sm_121). `method="color"` selects the deterministic colour tracer fallback | `method`, `step`, `kp_interval`, `plot_box`, `return_overlay` | `series: [{points [[x,y],...] px, color_rgb}]` |

Every coordinate is in image pixels, with the origin at the top-left and y increasing downward. digitize_curve does no axis calibration.

Smoke test: `make_synth.py` builds the synthetic plots and SEM images with ground truth. `smoke_client.py [url]` checks
accuracy over HTTP. See `env_logs/plots.md`.
