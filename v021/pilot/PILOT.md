# v0.21 pilot: MinerU-built panel store vs MatMech panel store (30 papers)

Question: can PanelBench take text, figures and subpanels all from MinerU, instead of figures from MatMech?
The item rules use only MatMech's panel store (figure numbers, tier, subpanel crops, caption span per panel). They do not use the MatMech mechanism links (`mechanism`, `casual_chain`).

## Method
- **Papers:** 30 from the 869, seed 0, stratified by journal; they include Hag21 (P0460) and Xu17 (P0589), which are also in v0.2.
- **MinerU store** (`build_mineru_store.py`, rules R1–R6): MinerU image blocks of at least 120 px with their "Fig. N" caption. Captions MinerU left as loose text were reattached to the nearest uncaptioned image on the same page, then by reading order when the counts matched. Body passages citing each figure were collected as `image_description`.
- **Panel pipeline:** the unchanged causalmat scripts `detect_panels.py` (MatMMExtract YOLO12), `ocr_panels.py` and `match_panels.py --ocr`. OCR ran with `OCR_CUDA=0` (CPU), because ONNX Runtime has no CUDA provider in host A's panels venv; the same model, on CPU.
- **Items:** the frozen item rules on the same v0.21 paragraphs, with only the panel store swapped.

## Result
| 30 pilot papers | MatMech store | MinerU store |
|---|---|---|
| figures | 235 | 211 |
| tier A figures | 121 | 75 |
| tier B figures | 60 | 49 |
| tier C figures | 54 | 87 |
| accepted panels | 575 | 353 |
| tier-A panels | 486 | 285 |
| panels with crop and caption span | 525 | 309 |
| panels cited in text (use) | 401 | 212 |
| items L1 / L2 / L3 | 69 / 43 / 27 | 51 / 23 / 22 |
| items total | 139 | 96 |
| papers with >= 1 item | 11 | 10 |
| item-rule errors | 0 | 0 |
| items identical in both (level, question, key) | 94 | 94 |

- **19 of the 30 papers yield no items with either store.** That is text loss (rule M6, Finding 1 in V021_REPORT.md), not panels.
- **Items:** Hag21 gives 20 → 20 and Xu17 14 → 14 (identical sets). 94 items are identical across the two stores. The MinerU store loses 43 items, 30 of them from one paper (P0123: 32 → 2).
- **Why figures fall to tier C:**

| Tier, reason | MatMech | MinerU |
|---|---|---|
| C1_count_mismatch | 18 | 31 |
| C3_caption_swap | 7 | 23 |
| C6_unresolved | 15 | 24 |

  - P0123 is a 76-page manuscript. MinerU captioned 4 of its 18 images and left 13 captions as loose text, so the reading-order pairing was wrong.
  - MinerU often splits one figure into several image blocks, and the store keeps only the captioned part.

  `match_panels.py` quarantined these mismatches (tier C) instead of producing wrong items.

## What a MinerU-only store needs
1. **Figure assembly:** merge the MinerU image blocks that belong to one figure (same page, between captions), or crop the page region around the figure, before detection.
2. **Better caption pairing for manuscripts:** pair by figure number and page proximity, and drop images that are not figures, before any reading-order fallback.
3. **Re-run this pilot** and accept the switch if tier-A figures and items come within about 10% of MatMech, with Hag21 and Xu17 unchanged.

**What MatMech cannot give for these papers:** 95% of the v0.21 PDFs are manuscripts, and MatMech figures are the published ones. A MinerU store keeps text and figures from the same document, so the panel letters in an item refer to the figure the text describes.
