# PanelBench v0.21 LOG: v0.2 extraction on the 869 harvested open-access PDFs

Started 2026-10-01T06:54:21-05:00. Same layout engine and adapter as v0.2: MinerU 2.7.6, pipeline backend, GPU; models opendatalab/PDF-Extract-Kit-1.0 snapshot ed6b654c018d742e65a17671e379c5e6ecc87ec9 on both hosts.

## Inputs
- 869 PDFs from the OA harvest (oa_harvest/oa_manifest.csv, download_status ok), mirrored on both hosts and verified by sha256.
- Split by sha256(DOI) mod 2: host A (spark-112b) 415 papers (papers_hostA.json), host B (wcs-180522) 454 (papers_hostB.json).
- By journal: Nano_Letters 328, Advanced_Materials 165, Advanced_Functional_Materials 159, Acta_Materialia 88, Nature_Materials 57, Advanced_Energy_Materials 54, Materials_Characterization 6, Journal_of_Advanced_Ceramics 5, Biomaterials 2, Progress_in_Organic_Coatings 2, Bioactive_Materials 1, Journal_of_Magnesium_and_Alloys 1, Journal_of_Materials_Science_&_Technology 1.

## Environment
- Host A: v02/.venv-mineru (mineru 2.7.6, torch 2.14.0+cu130), driver 580.82.09.
- Host B: v021/.venv-mineru (mineru 2.7.6, torch 2.14.1+cu130; same install recipe, newer torch patch release on the index), driver 580.173.02.

## Run
- run_mineru_v021.sh (sha 977e6f2f3e8a1e03): chunks of 40 PDFs, `mineru -p <chunk> -o mineru_out -b pipeline`, resumable; a PDF without content_list.json after its chunk is marked logs/failed_<safe>.
- User services mineru-v021 (MemoryHigh 64G, MemoryMax 80G) and thermal-governor-mineru (SIGSTOP at 80 C, SIGCONT at 65 C) on both hosts; node-monitor running on both.
- Test on host A: 2 PDFs, 2 ok, 62 s including model load.

## Driver (driver_v021.py, sha ef10bf0e0ab2be02)
- setup: levels.py 7477c0bbdf798157, open.py 9d4e3683b9afacec, mineru_paras.py 7989ad0321104366 copied byte-identical into work/ (hash-checked). Paper keys P0001..P0869 (sorted DOI) in paper_keys.json; each DOI mapped to its MatMech folder through data.json (72 folder names differ from the DOI pattern). All 869 have panels/match.json.
- Owner decision 2026-10-01: Nano Letters rules (C1, M6, M7) applied journal-wide by passing the key 'Xu17' to the frozen code paths for Nano Letters papers.
- Equivalence test: the driver's build path run on the v0.2 inputs (v0.2 paras, kit nl5) gives 86 items identical to v0.2 open_items.json (all fields except crop paths).
- Smoke: 2 Acta Materialia papers converted, 2 items (L1 1, L3 1), 0 errors.

## Incident 2026-10-01: out-of-memory kills, restart with smaller batches
- 08:11 CDT host A and 13:13 UTC host B: the kernel OOM killer stopped `mineru` (global OOM; host A mem_avail 1.8 GB with NVRM NV_ERR_NO_MEMORY lines; host B mem_avail 12 GB). Neither host froze. Cause: MinerU sizes batches from the GPU's reported memory ("GPU Memory: 120 GB, Batch Ratio: 16"), but on the GB10 that memory is shared system RAM and GPU allocations are not counted by the service's MemoryMax. Large chunks (702 and 790 pages) exhausted RAM.
- Done before the kills: host A 282, host B 280 papers, 0 failures.
- Restart 08:28 CDT: MINERU_VIRTUAL_VRAM_SIZE=8 (batch ratio 4, confirmed in the MinerU log on both hosts), CHUNK=15, thermal governor 75 C / 60 C (temperatures had briefly reached 86-90 C between 5 s governor checks); host B page cache flushed first. Papers already done are skipped.
- Comparability note: about 560 papers were extracted with batch ratio 16 and the rest with batch ratio 4. Batch size can change GPU floating-point results slightly; the chunk logs in logs/ show which run produced each paper.
- 2026-10-01T09:17:48-05:00 MinerU complete: host A 415/415, host B 454/454, 0 failed; no kernel events after the restart. Host B content_list/md/images copied to host A (debug PDFs left on B).

## Items and report (2026-10-01)
- `driver_v021.py convert`: 869 converted (328 with the Nano Letters rules). `items`: 869 papers, 0 errors, 1,067 candidate items (L1 642, number 516; L2 241; L3 184), from 167 papers; all `unreviewed`.
- Body-text loss diagnosed by counts only: Advanced Materials keeps 9% of words (143/165 papers under 20%; 21 have an Introduction heading), Nature Materials 6% (51/57; 3 have one), Nano Letters 52/328 under 20%. Rule M6 reported, not patched.
- PDF versions: 824 submitted, 19 accepted, 26 published; every item comes from a submitted or accepted manuscript.
- Cross-check: Hag21 20/20 items identical to v0.2; Xu17 same counts per level, 2/14 identical (harvested copy is the OSTI submitted manuscript).
- Report: V021_REPORT.md.

## Pilot: MinerU-built panel store (2026-10-01)
- 30 papers (pilot/pilot_keys.json, seed 0, stratified; includes Hag21 and Xu17). build_mineru_store.py (rules R1-R6) -> causalmat detect_panels.py, ocr_panels.py (OCR_CUDA=0: onnxruntime in ~/panels/.venv has no CUDA provider on host A; first attempt produced empty ocr.json, deleted and rerun), match_panels.py --ocr.
- MatMech vs MinerU store: figures 235 vs 211, tier A 121 vs 75, accepted panels 575 vs 353, items 139 vs 96 (94 identical); Hag21 20/20 and Xu17 14/14 identical. Details: pilot/PILOT.md, pilot/compare_output.md.
