# v3 freeze

sha256 of the files that make keys. The last entry is checked by `freeze.py --check`; generate.py runs on real cells only after a PASS. A change after the first freeze needs a new entry with its reason and a full regeneration.

## freeze 1 (2026-10-04T22:24:08-05:00)

reason: initial freeze: laws.py, grade.py, generate.py after unit tests (all passed) and a synthetic dry run (98-99 items, oracle self-check clean); before generate.py first touches real cells

- `laws.py` 93b1aedb1eab2b2fc382b240788aad872c2ce70f4ae0977568e214d3c23c156f
- `grade.py` 862d6161536ef0428806af2b7c64bb3008d37fbe5ba2485367655959101a60d3
- `generate.py` 197535bab6ed927471d32e45cacd5b2734f3c3d9a6ca5baa40a8370943662d4e
