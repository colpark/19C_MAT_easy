# V8-2 instrument calibration log

Instrument status: **uncalibrated for rod geometry, drift, tip and rates; noise partly calibrated.**
Reason: the rod-assembly paper (doi 10.1038/s41467-026-69170-0) gives only rod centres and order
parameters as source data (no raw images); its Methods name the instrument (video-rate scanning on a
commercial AFM, ultra-high-frequency cantilevers) but give no tip radius, line rate or noise. The other
paper (doi 10.1038/s41467-026-76923-4) did resolve and its Supplementary Data 1 raw images (WSxM .stp,
floating-point heights) were used to calibrate the noise scale only. Neither paper's data is used as a task.

## Downloads (curl, 60 s limit, from host A node 1, under ~/v8_data/calib/)
| item | result |
|---|---|
| doi 10.1038/s41467-026-76923-4 (landing) | resolved, http 200 |
| Supplementary Data 1 (media file MOESM3, zip, 4.5 MB: 6 raw .stp images) | downloaded |
| Supplementary Data 2 (media file MOESM4, zip, 31 MB: raw .stp images) | downloaded, listed only |
| doi 10.1038/s41467-026-69170-0 (landing) | resolved, http 200 |
| Source data (media file MOESM9, zip, 10 MB: order-parameter tables, .xls and .txt) | downloaded; .xls not read (no xlrd in v8env); not used |
| its Supplementary Data 1, 2 (MOESM5 PNG figures 520 MB; MOESM6 notebooks) | downloaded by mistake of scope, unused |

## Fitted values (from Supplementary Data 1 raw images, topography, double precision)
White noise sigma = 1.4826 * MAD(horizontal pixel differences)/sqrt 2; line-offset sigma = std of the
row-median residual about a 9-row running mean (an upper bound, it includes topography).
| image | fov nm | px | px nm | white sigma nm | line-offset sigma nm |
|---|---|---|---|---|---|
| Fig 2a | 500 | 512 | 0.977 | 0.088 | 0.295 |
| Fig 2c | 60 | 512 | 0.117 | 0.015 | 0.017 |
| Fig 2f | 30 | 256 | 0.117 | 0.012 | 0.017 |
| Fig 3a | 60 | 128 | 0.469 | 0.030 | 0.066 |
| Fig 3b | 10 | 256 | 0.039 | 0.003 | 0.006 |
| Fig 4a | 20 | 128 | 0.156 | 0.021 | 0.070 |

## Values used in the world (value, source)
| quantity | value | source |
|---|---|---|
| rod-scan white noise sigma (nuisance) | 0.05 to 0.30 nm, uniform | fitted: 0.088 nm at 500 nm/512 px; widened upward (video-rate scanning is noisier than the low-noise FM system); assumed |
| line-offset / white ratio | 1.5 (plus half-size slope term) | fitted: ratios 1.4 to 3.3 (upper bounds) |
| lattice-scan white sigma | 0.1 x the world noise (0.005 to 0.03 nm) | fitted: 0.003 to 0.03 nm in fields of 10 to 60 nm |
| tip apex radius (nuisance) | 3 to 10 nm, uniform | paper (a) Methods: nominal apex radius about 7 nm; paper (b) names UHF cantilevers, radius not given; assumed range |
| tip cone half-angle | 10 deg | afmize default used in V8-0 dilation check (instrument/dilation.py) |
| sample drift (nuisance) | 0.02 to 0.20 nm/min, field correlation length 3 x field of view | assumed typical post-equilibration drift; not in either paper |
| line rate reference | 1 Hz, up to 5 Hz, overhead 1 min per scan | assumed typical tapping-mode values; paper (b) used video-rate scanning (far faster), so the benchmark time axis is a model, not the paper's |
| rod orientation concentration kappa (axial, on doubled angle) | 1.5 to 10, log-uniform | assumed; paper (b) reports strongly ordered rods on lattice-matched mica |
| isotropic fraction | 0 to 0.15 | pre-registered |
| coverage | 0.10 to 0.30 | pre-registered |
| minimum rod gap | 3 nm | assumed |
| lattice constant | a = 5.19 A, b = 9.02 A (hexagonal description, b = sqrt 3 a = 8.99 A) | task brief |
| lattice corrugation | 0.05 nm peak | assumed; fitted z-range of lattice-resolved images 0.3 nm (Fig 3b, includes noise) |
| rod length/width | from tiled PDB geometry (~/v8_data/rods/dims.json) | tile_rod.py |
| rod stamp pixel | 0.3 nm | afmize, probe 0.1 A sharp, tip dilation added in render.py |
