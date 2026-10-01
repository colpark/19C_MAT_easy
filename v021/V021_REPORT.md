# PanelBench v0.21 report: v0.2 extraction on the 869 harvested open-access papers

Run 2026-10-01 on hosts A (spark-112b) and B (wcs-180522). Command log: `LOG.md`.
v0.21 uses the v0.2 pipeline unchanged: MinerU 2.7.6 (pipeline backend, GPU, model snapshot ed6b654c), then `mineru_paras.py`, then the frozen v0.1 item rules. Hashes: levels.py 7477c0bbdf798157, open.py 9d4e3683b9afacec, mineru_paras.py 7989ad0321104366. All three were copied byte-identical and run through `driver_v021.py`.

## Result

| | Count |
|---|---|
| Papers extracted by MinerU | **869 / 869** (0 failed) |
| Papers converted to paragraphs | 869 (328 with the Nano Letters rules) |
| Papers yielding at least one item | **167** |
| Candidate items | **1,067**: L1 642 (number 516, trend 126), L2 241, L3 184 |
| Item-rule errors | 0 |
| Items with a hand label | 0 (all `unreviewed`) |
| Benchmark tasks | 0 (`build_bench.py` takes sound items only; v0.21 needs a labelling pass) |

| Journal | Papers | MinerU words/paper | Kept words/paper | Kept % | L1 | L2 | L3 |
|---|---|---|---|---|---|---|---|
| Nano Letters | 328 | 6,260 | 2,827 | 45% | 43 | 20 | 21 |
| Advanced Materials | 165 | 7,671 | 710 | **9%** | 35 | 12 | 11 |
| Advanced Functional Materials | 159 | 9,572 | 4,734 | 49% | 243 | 95 | 67 |
| Acta Materialia | 88 | 8,992 | 5,188 | 58% | 216 | 74 | 47 |
| Nature Materials | 57 | 9,960 | 602 | **6%** | 0 | 0 | 0 |
| Advanced Energy Materials | 54 | 9,346 | 3,433 | 37% | 55 | 21 | 19 |
| Materials Characterization | 6 | 10,670 | 6,880 | 64% | 15 | 6 | 5 |
| J. Advanced Ceramics | 5 | 9,056 | 3,772 | 42% | 24 | 9 | 8 |
| Other journals (5) | 7 | | | | 11 | 4 | 6 |

"Kept" means body paragraphs after `mineru_paras.py`. A share of 40–65% is normal once front matter, captions, references and sections outside the body are dropped.

## Finding 1: rule M6 drops almost all text for some journals (reported, not patched)

M6 starts the body at a heading containing "Introduction". For Nano Letters it instead starts after the KEYWORDS block, or after the abstract. Some journal formats have neither:

| Journal | Papers with an "Introduction" heading | Papers keeping under 20% of their words |
|---|---|---|
| Advanced Materials | 21 / 165 | 143 |
| Nature Materials | 3 / 57 | 51 |
| Nano Letters (with its own start rule) | 33 / 328 | 52 |

Under the v0.2 rules a misbehaving rule is reported, not patched. These figures were measured from block types, heading flags and word counts only; no text was read. A fix needs a decision, for example a journal-level start rule "after the abstract" for Advanced Materials and Nature Materials, like the existing Nano Letters branch.

## Finding 2: 95% of the PDFs are submitted manuscripts, not published articles

| Version (from Unpaywall) | Papers | Items |
|---|---|---|
| repository, submittedVersion | 824 | 1,031 |
| repository, acceptedVersion | 19 | 36 |
| publisher, publishedVersion | 20 | 0 |
| repository, publishedVersion | 6 | 0 |

Most legal free copies are author manuscripts on OSTI. The panel crops come from the **published** figures (MatMech), but the item sentences and figure references come from the **manuscript**. Between submission and publication, figure numbers, panel letters and wording can change, so an item's panel ids may point to the wrong published panel, and its key may not be the published wording. Before review, check figure-reference consistency per paper, for example the figure count in the manuscript against MatMech's figure count.

## Cross-check with v0.2 (two papers are in both sets)

| Paper | v0.2 (published PDF) | v0.21 (harvested copy) | Identical items |
|---|---|---|---|
| Hag21, Acta Mater. 2021 (Osaka repository, submitted version) | 20 items (L1 10, L2 6, L3 4), 5,276 words | 20 items, 5,276 words | **20 / 20** |
| Xu17, Nano Lett. 2017 (OSTI, submitted version, 29 pages) | 14 items (L1 4, L2 5, L3 5), 5,907 words | 14 items, 6,136 words | 2 / 14 |

The pipeline reproduces v0.2 exactly when the text is the same (Hag21). Xu17 differs because the manuscript text differs from the published article, which is Finding 2 in practice.

## Run notes

- **Out-of-memory kills, no freezes.** Both hosts had MinerU killed once by the kernel OOM killer (host A 08:11 CDT, host B 13:13 UTC). MinerU sized its batches for 120 GB of GPU memory ("Batch Ratio: 16"), but on the GB10 that memory is shared system RAM. The run was restarted with `MINERU_VIRTUAL_VRAM_SIZE=8` (batch ratio 4), chunks of 15 PDFs, and the thermal governor at 75 °C / 60 °C. There were no further kernel events, and all 869 finished.
- **Two batch settings.** About 560 papers were extracted at batch ratio 16 and the rest at batch ratio 4. Batch size can change GPU floating-point results slightly; the chunk logs record which run produced each paper.
- **Environment.** Host A used torch 2.14.0+cu130 and host B torch 2.14.1+cu130; MinerU and model snapshot were the same on both.
- **Driver checks.** On the v0.2 inputs the driver reproduces v0.2's 86 items exactly. The Nano Letters rules were applied journal-wide by owner decision (rule text C1, M6 and M7 is journal-level; the code tested key 'Xu17').
- **Disk.** `mineru_out/` takes 8.6 GB on host A (content_list, markdown and images for all 869; MinerU's debug PDFs are only on the host that produced them).

## Files

`open_items_v021.json` (1,067 candidate items, all unreviewed), `paper_keys.json` (P0001–P0869 mapped to DOI, journal and MatMech folder), `stats_v021.md`, `item_errors.json` (empty), `driver_v021.py`, `run_mineru_v021.sh`, `LOG.md`, `work/<key>.paras.json`, `mineru_out/`.
