# Validation with known answers (synthetic; through the hub, the same path as the gateway)

Run 2026-10-02 on node 2 (`validation/validate.py`, inputs from `validation/make_synthetic.py` and the science build). No thresholds gate the build; **flag** = relative error above 10% on the tool's own synthetic test. Single deterministic run (seed 0).

## Scale bar and particle size (myscope renders with burned-in data bar)

| Image | px/um true | read_scale_bar | error | mean diameter true (um) | particle_stats (SAM) | error | particles |
|---|---|---|---|---|---|---|---|
| spheres_2000.png | 16.13 | 16.4 | 1.7% | 5.2917 | 4.7026 | 11.1% **flag** | 112 |
| spheres_5000.png | 40.31 | 41.0 | 1.7% | 2.1167 | 1.8782 | 11.3% **flag** | 112 |
| spheres_10000.png | 80.63 | 82.0 | 1.7% | 1.0583 | 0.9429 | 10.9% **flag** | 117 |
| spheres_20000.png | 161.26 | 164.0 | 1.7% | 0.5292 | 0.4724 | 10.7% **flag** | 121 |
| spheres_40000.png | 322.52 | 328.0 | 1.7% | 0.2646 | 0.2363 | 10.7% **flag** | 119 |
| particles_2000.png | 16.13 | 16.4 | 1.7% | 3.175 | 3.3764 | 6.3% | 84 |
| particles_5000.png | 40.31 | 39.8 | 1.3% | 1.27 | 1.3801 | 8.7% | 84 |
| particles_10000.png | 80.63 | 82.0 | 1.7% | 0.635 | 0.6770 | 6.6% | 81 |
| particles_20000.png | 161.26 | 164.0 | 1.7% | 0.3175 | 0.3393 | 6.9% | 86 |
| particles_40000.png | 322.52 | 328.0 | 1.7% | 0.1588 | 0.1677 | 5.6% | 89 |

Scale bars: 1.3-1.7% error on all 10 renders. Particle diameters: myscope `particles` 5.6-8.7%; `spheres` 10.7-11.3% too small at every magnification (SAM masks sit inside the shaded sphere rim): a consistent underestimate, **flagged**.

## sem_optics vs the README formula (field of view = 127000 / M um)

| Magnification | FOV returned (um) | 127000/M | error |
|---|---|---|---|
| 1000 | 127.0 | 127.000 | 0.0% |
| 2000 | 63.5 | 63.500 | 0.0% |
| 5000 | 25.4 | 25.400 | 0.0% |
| 10000 | 12.7 | 12.700 | 0.0% |
| 50000 | 2.54 | 2.540 | 0.0% |

## Plots (30 matplotlib figures with known values)

`axis_calibrate` relative RMS residual of the tick fit; metric error on the digitized curve (LineFormer + calibration) and on the true xy (curve_metrics alone). Peaks: worst centre error as a fraction of the 70 deg axis span.

| Plot | kind | x fit rel. RMS | y fit rel. RMS (scale) | metric error, digitized | metric error, true xy |
|---|---|---|---|---|---|
| linear_0 | linear | 0.0% | 0.1% (linear) | 2.3% | 0.0% |
| linear_1 | linear | 0.1% | 0.1% (linear) | 2.1% | 0.0% |
| linear_2 | linear | 0.1% | 0.1% (linear) | 1.8% | 0.0% |
| linear_3 | linear | 0.0% | 0.0% (linear) | 2.0% | 0.0% |
| linear_4 | linear | 0.1% | 0.1% (linear) | 1.7% | 0.0% |
| linear_5 | linear | 0.0% | 0.1% (linear) | 1.7% | 0.0% |
| linear_6 | linear | 0.1% | 0.1% (linear) | 2.9% | 0.0% |
| linear_7 | linear | 0.1% | 0.1% (linear) | 1.7% | 0.0% |
| linear_8 | linear | 0.1% | 0.1% (linear) | 1.6% | 0.0% |
| linear_9 | linear | 0.1% | 0.0% (linear) | 1.9% | 0.0% |
| logy_0 | logy | 0.1% | 0.1% (log) | 11.6% **flag** | 0.3% |
| logy_1 | logy | 0.1% | 0.1% (log) | 6.6% | 0.1% |
| logy_2 | logy | 0.1% | 23.0% (linear) | 44.0% **flag** | 0.5% |
| logy_3 | logy | 0.1% | 0.0% (log) | 18.5% **flag** | 0.7% |
| logy_4 | logy | 0.1% | 0.0% (log) | 8.5% | 0.2% |
| logy_5 | logy | 0.1% | 0.1% (log) | 13.3% **flag** | 0.5% |
| stressstrain_0 | stress_strain | 0.1% | 0.1% (linear) | 2.6% | 0.1% |
| stressstrain_1 | stress_strain | 0.1% | 0.1% (linear) | 1.9% | 0.2% |
| stressstrain_2 | stress_strain | 0.1% | 0.1% (linear) | 0.4% | 0.0% |
| stressstrain_3 | stress_strain | 0.1% | 0.1% (linear) | 0.7% | 0.1% |
| stressstrain_4 | stress_strain | 0.1% | 0.1% (linear) | 3.0% | 0.1% |
| stressstrain_5 | stress_strain | 0.1% | 0.1% (linear) | 1.4% | 0.2% |
| stressstrain_6 | stress_strain | 0.1% | 0.1% (linear) | 3.7% | 0.1% |
| peaks_0 | peaks | 0.1% | 0.1% (linear) | 0.8% | 0.0% |
| peaks_1 | peaks | 0.1% | 0.1% (linear) | 0.9% | 0.0% |
| peaks_2 | peaks | 0.1% | 0.0% (linear) | 4.0% | 0.0% |
| peaks_3 | peaks | 0.1% | 0.0% (linear) | 1.1% | 0.0% |
| peaks_4 | peaks | 0.1% | 0.1% (linear) | 1.3% | 0.0% |
| peaks_5 | peaks | 0.1% | 0.1% (linear) | 1.3% | 0.0% |
| peaks_6 | peaks | 0.1% | 0.1% (linear) | 1.1% | 0.0% |

Linear plots 1.6-2.9%, stress-strain 0.2% offset yield 0.4-3.7%, peaks 0.8-4.0% on digitized curves; curve_metrics on the true data 0.0-0.7%. Log-y plots: OCR flattens superscripts (10^4 -> "104"); the first run fitted linear axes (errors up to 5,484%). After reading runs of "10"+exponent as powers of ten, 5 of 6 log axes calibrate (residual <0.1%) with value errors 6.6-18.5%; logy_2 still falls back to linear. **Log-y digitizing is flagged.**

## TEM (abTEM simulations, 200 kV, 5 nm)

| Image | tool | known d (A) | recovered (A, strongest first) | rel. error per known d |
|---|---|---|---|---|
| si_110_hrtem.png | fft_dspacing | 3.1352, 2.7152, 1.9199, 1.6373, 1.3576, 1.5676 | 3.194, 3.194, 1.889, 1.357, 1.645, 1.645 | 3.1352: 1.9%, 2.7152: 17.6%, 1.9199: 1.6%, 1.6373: 0.5%, 1.3576: 0.0%, 1.5676: 5.0% |
| al_001_hrtem.png | fft_dspacing | 2.0203, 1.4286, 1.0102 | 1.429, 1.429, 1.01, 1.01, 2.02, 2.02 | 2.0203: 0.0%, 1.4286: 0.0%, 1.0102: 0.0% |
| si_110_diffraction.png | saed_rings | 3.1352, 2.7152, 1.9199, 1.6373, 1.3576, 1.2458, 1.1085 | 3.162, 1.976, 1.605, 1.291, 1.096 | 3.1352: 0.9%, 2.7152: 16.5%, 1.9199: 2.9%, 1.6373: 1.9%, 1.3576: 4.9%, 1.2458: 3.6%, 1.1085: 1.1% |

Si [110] HRTEM: 111, 220, 113, 004 within 0-1.9%; 002 (kinematically forbidden) and 222 not resolved. Al [001]: all three spacings exact. Si [110] diffraction (spot pattern): first version (radial profile) found 1 of 7; with spot mode 6 of 7 within 0.9-4.9% (002 not resolved).

## XRD phase identification (pymatgen patterns, 0.15 deg FWHM, 3% noise)

| Phase | top-1 | top-3 |
|---|---|---|
| Si | Si | Si |
| Al2O3 | Al2O3 | Al2O3, Al |
| ZnO | ZnO | ZnO, Zn |
| NaCl | NaCl | NaCl |
| MgO | MgO | MgO, Mg |
| CeO2 | CeO2 | CeO2 |
| Cu | Cu | Cu |
| TiO2 | TiO2 | TiO2, TiO2, Ti |
| Fe3O4 | Fe3O4 | Fe3O4, Fe2O3, Fe |
| BaTiO3 | BaTiO3 | BaTiO3, BaTiO3, TiO2 |

Top-1 accuracy 10/10 with the **fallback** matcher (Dara/BGMN unavailable on aarch64). The test phases are in the matcher's own 43-phase library, so this checks the matcher, not open-world identification.

## OmniXAS (tutorial Cu FEFF)

Test split (416 Cu sites): MSE 0.003962 (x1000 training scale; predicting the mean spectrum gives 0.014746). Repo example mp-1005792 Cu site 8 via the tool: MSE 0.002187. Energy grid identical to the stored one; repeated calls bit-identical (omnixas build log).

## Refocus

Not run: the three reviewer checkpoints are on a Google Drive folder that requires sign-in. Architecture-only GPU smoke test (base MAE weights, random MoE): 3.56 s for a 1020x688 image. PSNR/SSIM on the bundled sample pairs pending the checkpoints.

## classify_modality probe

13 census classes, 3,843 MatMech crops (papers outside every PanelBench version), labels from the causalmat panel_modalities caption rules. 80/20 split: held-out top-1 48.4%, top-3 74.8% (chance 7.7%). Weak, mostly because caption-derived labels are noisy. It sets the A2 placebo pools.

## Placebo

A2 output for a crop equals A1 output for its mapped placebo crop: 5/5 checks (read_text, through the hub with image_ref vs inline bytes). placebo_map.json: 590 panel uses, all with the same top-1 modality, 0 from the same paper, smallest pool 11.

## Other unit checks from the family builds

peak_fit two Gaussians: centres 6.0003/9.4999 (true 6.0/9.5), areas within 0.6%. xas_edge synthetic Cu K: E0 8979.0 (true 8979), step 1.003. mlip_energy: Cu bulk modulus MACE 130.1 / Orb 131.3 GPa (exp. ~140); Al C11/C12/C44 114/64/29 (exp. 107/61/28). read_scale_bar on drawn bars: 200.0/200 px and 150.0/150 px. LineFormer mean pixel error 1.1-1.8 px on synthetic plots. segment (SAM 2) point prompts: areas 11262/20059 vs 11310/20106 px. grain_size_astm: 78 of 80 grains. find_atoms: 90-99% of atoms across 6-30 px spacings (with auto-rescale).
