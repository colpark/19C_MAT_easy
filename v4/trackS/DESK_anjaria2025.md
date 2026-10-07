# DESK anjaria2025 (Dryad 10.5061/dryad.98sf7m0tt, version 348782; CC0)

Evidence: README.md (3,872 bytes, repository sha256 verified) and the extracted archive. Tier 1: 4 files, 5.50 GB, all verified.

## Answers to the screen's questions
| Question | Answer | Evidence |
|---|---|---|
| Tile layout per strain level | Folders step0 (before deformation) and step1-step4 (total strain 0.38, 0.62, 1.02, 1.95 %), each an 8 x 8 grid. Names end in `P<row>_<col>.tif.tif`. Steps 3 and 4 repeat the prefix (`step3_step3_...`). | join.csv (64 tiles per level, 320 total) |
| Reference images | step0 (`E00`), taken before loading. | README, file names |
| Pixel size tags | None. The tiles carry only baseline TIFF tags (no FEI, OME or resolution tag). The README states 33.4 nm (HFW 137 um at 4096 px). The tiles are 8-bit, although the README says 16-bit: deviation from the deposit description. | tifffile tag dump; inventory_summary.json |
| Registration of 718_SS.ang to the tiles | Not described. The README gives none, and no transform or fiducial file is deposited. | README |
| Does Calvat et al. 2026 describe this deposit? | Not confirmed. Calvat et al., Adv. Eng. Mater. 2026 (10.1002/adem.202503166), with Anjaria and Stinville among the authors, concerns slip localization intensified by grain boundary sliding in 600 C fatigue. The deposit is a room-temperature in-situ tensile test. The Dryad record cites no descriptor. | web search, 2026-10-07 |

## Join (S2j-dryad, then S2j-dryad-b)
- Roles: sem_montage_tile 320, ebsd_export 1, ebsd_map 1, document 1. Unmatched: 0 data files.
- Unit: tile; 64 per level.

## Magnification (S3)
- magleak verdict: missing (no native pixel size).
- Every tile is 4096 x 4096, and the README states one HFW. There are no scale bars (raw speckle images), so no scale-bar reader can be built.
- Decision: any observable is scale-free (orderings across strain only). The README's 33.4 nm is recorded as an author statement, never used for keys.

## Reader (pilot S2): deferred
- The tiles are raw speckle images for DIC. At the highest strain (step4), a 1024 px crop (34 um) shows only the gold nanoparticle speckle, with no visible slip traces, so slip-trace density cannot be read from the raw BSE tiles.
- It needs DIC first (a DIC reader validated on synthetic speckle and held-out evidence). This run has no DIC reader, and FM readers are out of scope.
- The aged-vs-solutionized contrast at matched strain is not run: no observable passed S4 in both deposits.
