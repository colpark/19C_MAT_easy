# v3.2 error ledger (Phase 5)

Fields per entry (also in errors.jsonl): id, papers, stage, symptom, root cause, class (paper quirk | pipeline bug | rule gap), fix, files
changed, regression result.

| id | papers | stage | symptom | root cause | class | fix | files | regression |
|---|---|---|---|---|---|---|---|---|
| E01 | S039, S098, T042, T051, S048 | 5A | MinerU md not found for any paper | identity checked by sha of MinerU's `_origin.pdf`, which MinerU rewrites | pipeline bug | resolve by key set (S keys: mineru_out; others: oa2/mineru_out) | stage5a_inputs.py | all 5 found; paper 1 unaffected (own text) |
| E02 | S039, S098, T042, T051, S048 | 5A | whole figures without crops (S039 F4, F13; T042 F2–F4, F8–F9; T051 F2, F5; S098 F7; S048 F1, F4, F5, F12) | the v0.24 store writes no crops for tier-C figures (detector count != caption letters) | pipeline bug (recurring, 5/5 papers) | fallback: the detector's lettered boxes (highest score per letter), 'unverified' when the letter is in neither caption nor text letters | stage5a_inputs.py | graph panels cropped: S039 51/54, S098 44/45, T042 57/59, T051 40/48, S048 8/13 (+ unverified ids); paper 1 crops untouched |
| E03 | S039, S098, T051, S048 | 5A | micrograph crops do not match native bitmaps at NCC >= 0.80 (e.g. S098 F3a–h 0.63–0.80) | composite figure bitmaps / resampling; scale bars possibly vector | paper quirk (pending) | 600 dpi page render of the panel region where measurements need it (Stage 5D) | — | pending |
| E04 | T051 | 5A | F2b–F2i not cropped (detector found 1 box for 9 panels) | detector failure on a dense micrograph/map figure | paper quirk | none: F2 panels excluded unless needed; T051 micrographs cover only x = 0, 0.20 anyway | — | — |
