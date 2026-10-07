# Track S: SEM pilot datasets (v4.1)

Track S gets the three SEM pilots from the SEM multimodal screen ready for a build: data on the host with verified manifests, desk
checks, a magnification leak test, validated readers, separability pilots and an M0 record per dataset with GO or NO-GO. It builds
no items and calls no paid model.

| Pilot | Dataset id | Deposit | License | Tier 1 size |
|---|---|---|---|---|
| S1 | amb2022_03 | NIST mds2-2775 (SEM, EBSD, EDS sections) and the measurement PDF, plus mds2-2718 optical sections (tier 2) and mds2-2716 thermography (tier 3) | NIST open license | read from plan |
| S2 | stinville2022 | Dryad 10.5061/dryad.83bk3j9sj (version 7) | CC0 | about 4.1 GB (55 GB at tier 3) |
| S2 | anjaria2025 | Dryad 10.5061/dryad.98sf7m0tt | CC0 | about 5.5 GB |
| S3 | refodat90 | refodat 10.71758/refodat.90 (browser download) | CC BY 4.0 | 7.02 GB, 14 files |
| S3 | refodat91 | refodat 10.71758/refodat.91 (browser download) | CC BY 4.0 | 1.04 GB, 15 files |
| reserve | sa508_ebw | Mendeley j2f2dxmd5m, 58xvm8wt92, x8x628h3gs | CC BY 4.0 | read from plan |
| reserve | alsi10mg_luo2024 | Zenodo 10008435 | CC BY 4.0 | about 0.6 GB SEM files |

## Files
| File | Role |
|---|---|
| datasets_s.json | registry: repositories, identifiers, licenses, tiers, expected counts (cross-check only) |
| fetch_s.py | plan, get (resume, retry, repository checksums), verify, manual (browser downloads), inputs |
| inventory_s.py | extract archives (guarded), scan native SEM metadata, readers (R2) |
| joinrules/<id>.json | regex rules from file paths to role, entity and condition (fill from the README, then freeze) |
| join_s.py | applies the rules, writes join.csv and join_summary.json |
| magleak_s.py | Spearman or Kruskal-Wallis test of pixel size against every condition field |
| separability_s.py | adjacent pairs beyond 2 combined SE, ANOVA, bootstrap for single units, refuses unfrozen readers |
| m0_s.py | verified card fields, scorer statuses (screen_dataset.py), GO, GO WITH CHECKS or NO-GO |
| cards/<id>.json | the screen cards these checks verify |
| tests/test_kit.py | 53 offline tests on synthetic deposits and mocked repositories, 16 of them regression tests from an independent code review |

## Commands, in order
```
export HARBOR=/home/aid1/Documents/harbor
P=v4/.venv-v4/bin/python
$P v4/trackS/tests/test_kit.py                                   # 53 passed
$P v4/trackS/fetch_s.py plan --tier 1                             # sizes, disk, unresolved parts
$P v4/trackS/fetch_s.py get --tier 1 --jobs 2                     # S1 and S2 deposits
$P v4/trackS/fetch_s.py manual --dataset refodat90 --src $HARBOR/trackS_manual/refodat90
$P v4/trackS/fetch_s.py manual --dataset refodat91 --src $HARBOR/trackS_manual/refodat91
$P v4/trackS/fetch_s.py verify && $P v4/trackS/fetch_s.py inputs
$P v4/trackS/inventory_s.py extract && $P v4/trackS/inventory_s.py scan && $P v4/trackS/inventory_s.py readers
#   read each README, fill joinrules/<id>.json, freeze them, then:
$P v4/trackS/join_s.py --dataset <id> && $P v4/trackS/magleak_s.py --dataset <id>
#   build and freeze a reader per pilot (synthetic dev seeds only), validate, then:
$P v4/trackS/separability_s.py --table <pilot table.csv> --reader-freeze <label> --unit-type <track|grain|tile|specimen>
$P v4/trackS/m0_s.py --dataset <id> --pilot <pilot table>_separability.json
```

Host data stay in `$HARBOR/v4_host/trackS/<id>/` (files, extracted, manifest, inventory, readers, join, magleak). Commit code,
rules, m0 records and verified cards, never data.
