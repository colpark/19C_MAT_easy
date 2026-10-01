# PanelBench v0.22 report: the v0.2 pipeline on 94 published Acta Materialia papers

Run 2026-10-01 on hosts A and B; command log in `LOG.md`, full measures in `QUALITY.md` (`quality_v022.py`).
v0.22 runs MinerU 2.7.6, then `mineru_paras.py`, then the frozen v0.1 item rules (hashes as in v0.2). The rules ran against two panel stores: MatMech's, and one built from MinerU's own figures with the unchanged causalmat detect/OCR/match scripts.

## Headline

| | v0.21 (869 OA copies, 95% manuscripts) | **v0.22 (94 published Acta Materialia)** |
|---|---|---|
| MinerU success | 869 / 869 | **94 / 94** |
| Kept body text (share of MinerU words) | 6–64% by journal; Acta 58% | **61%**, no paper under 20% |
| Papers with an "Introduction" heading | 33–98% by journal | **89 / 94** |
| Papers yielding at least one item | 167 / 869 (19%) | **70 / 94 (74%)** |
| Candidate items, MatMech store | 1,067 | **355** (L1 232, L2 70, L3 53) |
| Candidate items, MinerU store | 96 vs 139 for MatMech in the 30-paper pilot (−31%) | **377 vs 355 (+6%)**, 334 identical |
| Figures captured with their caption by MinerU | 72% of MatMech's | **97.8%** (1,033 / 1,056), none needing reattachment |

**On published PDFs the whole pipeline runs from MinerU alone.** A MinerU-built panel store matches or beats MatMech on every count. The losses in the v0.21 pilot came from author manuscripts (captions listed apart from the figures, figures split into pieces), not from the method.

## Quality measures

**Q1 MinerU run.** 94 / 94 PDFs (1,062 pages) took about 11 minutes on two GB10 hosts. Settings: batch ratio 4, chunks of 15, thermal governor 75/60 °C. There were no out-of-memory kills and no new kernel events.

**Q2 Extraction.**
- 8,617 MinerU text words per paper, of which 5,273 (61%) are kept as body paragraphs. The rest is front matter, captions, references and sections outside the body.
- Paragraphs: median 37 per paper, median length 117 words. 19 of 3,747 paragraphs exceed 500 words.
- Skipped blocks: discarded (headers and footers) 2,640, image 1,058, equation 498, table 160.

**Q3 Sentence integrity against the publisher's text.** The reference is 8,273 publisher sentences (10+ words) from MatMech's figure-citing body passages, scored with the head/tail anchor test of `quote_integrity.py`:

| | Sentences | Share |
|---|---|---|
| Whole in one paragraph | 6,796 | 82.1% |
| Split across paragraphs (both anchors found, different paragraphs) | **0** | **0%** |
| One anchor only (PDF wording differs from the publisher HTML) | 1,216 | 14.7% |
| Not found | 261 | 3.2% |

- **Paragraph integrity is 100%:** every sentence whose two ends are found sits in one paragraph. (v0.2's metric did not separate splits from one-anchor matches, so the closest v0.2 figure is 198 of 203 hand-verified quotes whole in one paragraph.)
- **The 14.7% one-anchor cases are text differences, not splits.** Typical causes are reference markers, special characters and formula formatting between the PDF and the HTML.

**Q4 Figure capture.** MinerU captioned 1,033 of MatMech's 1,056 figures (97.8%), all through MinerU's own caption attachment.

**Q5 Panel stores.**

| | MatMech store | MinerU store |
|---|---|---|
| Figures | 1,056 | 1,033 |
| Tier A | 349 | **359** |
| Tier B | 469 | 468 |
| Tier C | 238 | **206** |
| Accepted panels | 1,677 | **1,740** |
| Panels in tier-A figures | 1,014 | **1,052** |
| Panels with a caption span | 1,656 | 1,728 |
| Panels cited in the text | 743 | 796 |
| OCR letter read | 1,123 / 2,150 crops | 1,133 / 2,112 |
| OCR letter agrees with the detector | 1,033 | 1,042 |

**Q6 Items** (frozen rules; all `unreviewed`):

| | MatMech store | MinerU store |
|---|---|---|
| L1 / L2 / L3 | 232 / 70 / 53 | 247 / 75 / 55 |
| Items | 355 | 377 |
| Papers with items | 70 | 70 |
| Items identical in both stores | 334 | 334 |
| Source within 0.90 similarity of the publisher sentence: L1 | 81.0% | 79.4% |
| Same, L2 | 84.3% | 82.7% |
| Same, L3 (`key` sentence) | 84.9% | 83.6% |
| L1 key visible elsewhere in the question (leak; build_bench would exclude) | 14 | 13 |

The similarity check compares each item sentence (L1/L2 `source`, L3 `key`) with the most similar publisher sentence in MatMech. MatMech only holds figure-citing passages, so a low score can mean the sentence is absent there rather than garbled.

## What remains

1. **No benchmark tasks yet.** All 355–377 items are `unreviewed`, and `build_bench.py` takes only hand-labelled sound items. This set (published versions, both stores agreeing on 334 items) is the natural candidate for the next labelling pass.
2. **24 papers yield no items (diagnosed by counts):**
   - **Few usable figures.** Their eligible text has 474 figure-citing sentences, but only 15 resolve to a tier-A panel. They average 1.9 tier-A figures, against 4.3 in productive papers, and 4 papers have none.
   - **Single-panel figures dominate.** About half their figures are single-panel figures (`B3_single`: 49–50% in both stores, against 33–34% in productive papers). Single-panel figures are tier B by design, and rule C3 uses tier A only. Across all 94 papers, 616 citations point at a single-panel figure without a panel letter (145 of them in the 24 papers). Admitting single-panel figures as whole-figure panels would be a rule change.
   - **Unresolved figures.** `C6_unresolved` (caption, detector and text letters disagree in an uncovered way) is two to three times as common: 12–14% against 5–6%.
   - **M092 has no eligible paragraphs.** Its headings are unnumbered and mostly all-caps (6 of 16), and rule C1's section pattern `Result|Discussion|Conclusion` is case-sensitive, so "RESULTS AND DISCUSSION"-style labels never match. Reported, not patched (frozen rule).
3. **Choosing a panel store.** For published PDFs the MinerU store is at least as good as MatMech and removes the dependency. For manuscripts (v0.21) it still needs figure assembly and caption pairing.

## Files

`papers_v022.json`, `paper_keys.json` (M001–M094 with DOI, sha256 and pages), `mineru_out/`, `work/*.paras.json`, `store/` (MinerU panel store), `panel_runs/`, `open_items_matmech.json`, `open_items_mineru.json`, `QUALITY.md`, `driver_v022.py`, `quality_v022.py`, `run_mineru.sh`, `LOG.md`.

## Rules revision r1 (owner decision 2026-10-01)

r1 is applied by `make_rules_r1.py` to copies of the frozen files, in `work_r1/` (levels.py d871001f59464ccd, open.py c81301c0c4a904da). The frozen files and the frozen v0.22 results are unchanged.

| Change | Frozen | r1 |
|---|---|---|
| R1-C1 eligible sections | `Result\|Discussion\|Conclusion` case-sensitive | case-insensitive |
| R1-REF0 letterless references | never matched: the frozen REF pattern requires a panel letter | new pattern for "Fig. 2", "Figure 2", "Figs. 2 and 3" (not "Fig. 2a", "Fig. S2") |
| R1-C3 single-panel figures | unusable (tier B, `B3_single`) | a letterless reference resolves to one whole-figure panel `F<n>` |
| R1-P whole-figure panel | none | crop = full figure image; caption = the figure's caption |

- **Stems unchanged.** References in item text stay as written. Rewriting letterless references to `[F<n>]` was considered and dropped, because it would change the wording of existing items.
- **Regression on the six v0.2 papers:** all 86 frozen items kept identical, plus 1 new L2 item.

| v0.22 items | Frozen, MatMech store | **r1, MatMech store** | Frozen, MinerU store | **r1, MinerU store** |
|---|---|---|---|---|
| L1 / L2 / L3 | 232 / 70 / 53 | **429 / 145 / 88** | 247 / 75 / 55 | **449 / 148 / 90** |
| Items | 355 | **662** | 377 | **687** |
| Papers with items | 70 | **87** | 70 | **87** |
| Items using a whole-figure panel | – | 313 | – | 317 |
| Frozen items kept unchanged | – | 352 / 355 | – | 372 / 377 |
| Source within 0.90 of publisher text (L1 / L2 / L3) | 81 / 84 / 85% | 78 / 77 / 82% | 79 / 83 / 84% | 77 / 76 / 82% |
| L1 key visible elsewhere in question (leak) | 14 | 22 | 13 | 21 |

- **Missing crops:** none; every whole-figure crop file exists.
- **Changed frozen items** (3 MatMech-store, 5 MinerU-store): sentences that cite a whole figure now count as panel citations, which changes L1 distractor eligibility and L3 source paragraphs.
- **M092** yields 1 item under r1.
- Full measures: `QUALITY_r1.md`; items in `open_items_matmech_r1.json` and `open_items_mineru_r1.json`.

## Labelling pass and benchmark (2026-10-01)

These are model labels; see `labeling/LABELING.md`.
- **Calibration** against 66 hand-labelled v0.2 items: 71% exact agreement (kappa 0.47); 97% precision for "sound" (30/31); 65% recall. The model is stricter than the hand labels, mostly on L3.
- **v0.22 benchmark:** 171 sound items (L1 92, L2 66, L3 13) from 62 papers, 513 tasks in `panelbench_v022/`. The Harbor-runnable copy is `panelbench_v022-openrouter/` (OpenRouter judge, web blocked in the agent phase).
