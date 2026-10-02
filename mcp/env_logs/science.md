# science (node 2, ~/mcp/science, port 8104) - 2026-10-02

STATUS: all 7 tools work. MACE, Orb and abTEM run on the GPU (CUDA, GB10); the rest run on the CPU.
xrd_phase_match uses a FALLBACK method, not Dara/BGMN (see below). The worker was stopped after a short HTTP test, and start.sh is in place.

## Env (~/mcp/science/.venv, uv, CPython 3.12) - full freeze: env_logs/science_freeze.txt (copy of ~/mcp/science/freeze.txt)
torch 2.14.0+cu130 (download.pytorch.org/whl/cu130, same as ~/panels), numpy 2.5.3, scipy 1.18.1, pymatgen 2026.9.24, lmfit 1.3.4,
xraylarch 2026.2.2, mace-torch 0.3.16 (e3nn 0.4.4), orb-models 0.7.0, pycalphad 0.11.2, abtem 1.0.10, cupy-cuda13x 14.2.0,
ase 3.29.0, pybaselines 1.2.1, dara-xrd 1.3.0 (from clone), fastapi 0.142.2, uvicorn 0.54.0.
Licenses: pymatgen MIT, lmfit BSD-3, xraylarch MIT, mace-torch MIT, orb-models Apache-2.0, pycalphad MIT, abTEM GPL-3.0
(internal use only), cupy MIT, ase LGPL-2.1, dara MIT.

## Repos cloned (~/mcp/science/repos)
- https://github.com/CederGroupHub/dara @ 1fd9bed26798072f9aa1e7356dcb9bca44a5dbae, LICENSE (MIT). Installed with pip. It is used only
  for its COD index (cod_filtered_info_2024.json.gz), which helped pick CIF IDs.
- https://github.com/pycalphad/pycalphad @ 1a1732b7631620c700b8c296869d2d125926c1c6 (depth-1), LICENSE.txt (MIT). Cloned only
  to get TDB files. The package itself comes from PyPI (0.11.2).

## Weights (~/mcp/science/weights; not copied to harbor/mcp)
| file | bytes | sha256 | source | license |
|---|---|---|---|---|
| mace-mpa-0-medium.model | 79462305 | 75428afe3a1d7d8062e19bcaabd5c433623cabf308242ec9fb493e38604fb638 | https://github.com/ACEsuit/mace-foundations/releases/download/mace_mpa_0/mace-mpa-0-medium.model | MIT |
| orb-v3-conservative-inf-mpa-20250404.ckpt | 102097517 | bd1840d1488f3cd01d213970d9618a63f971590ad45e5e83bf5404d4b95d216a | https://orbitalmaterials-public-models.s3.us-west-1.amazonaws.com/forcefields/orb-v3/orb-v3-conservative-inf-mpa-20250404.ckpt | Apache-2.0 (orb-models) |
The Orb variant is conservative-inf-mpa, trained on MPtrj+Alexandria. It is the same data family as MACE-MPA-0, so energies are on a comparable MP-compatible PBE scale.

## Dara / BGMN: why xrd_phase_match is a fallback
Dara's search and refinement call BGMN. Dara's downloader fetches https://cedergrouphub.github.io/dara/_static/bgmnwin_Linux.zip,
which contains an x86-64 ELF binary ("cannot execute binary file: Exec format error" on this aarch64 node). BGMN is closed-source
freeware with no aarch64 build. This node has no qemu-user or box64, and installing one would need sudo or an emulator plus an x86-64 glibc sysroot.
I deleted the downloaded binary.
Fallback method (labeled method="fallback_peak_list_match (Dara/BGMN unavailable)" in every response, plus a warning):
SNIP baseline (pybaselines), then scipy find_peaks on the observed pattern. Each structlib phase gets a pymatgen-simulated stick
pattern at the requested wavelength, optionally filtered to the given elements. Each phase is scored over a zero-shift grid of
+/-0.3 deg with a matching tolerance of 0.25 deg, using FoM = frac_sim_intensity_matched * sqrt(frac_obs_intensity_explained).
The tool returns the top k phases, a greedy multi-phase combination (up to 3 phases), and the unexplained peaks.
It only knows the 43 library phases and does no Rietveld refinement or quantification.

## Structure library (~/mcp/science/structlib, 43 CIFs + index.json sha256 c9a6dc0c...d0d7)
All CIFs come from the Crystallography Open Database (COD). COD data is public domain (CC0); see crystallography.net/cod.
How each was picked: Dara's COD index was filtered by chemical system, formula and space group, and the lowest e_above_hull entry was taken.
Each CIF was downloaded from crystallography.net and checked with pymatgen (reduced formula, plus the space group at symprec 0.1).
Notes: hydroxyapatite CIF 9011091 includes H (Ca5P3HO13, P6_3/m). SiO2 quartz is P3_221 (152).
BaTiO3 is included in both the tetragonal (P4mm) and the cubic form. ZrO2 has the m and t forms, and SiC has 3C and 6H.
| key | formula | SG# | COD id | source URL |
|---|---|---|---|---|
| Si | Si | 227 | 9013102 | https://www.crystallography.net/cod/9013102.cif |
| Al | Al | 225 | 9012955 | https://www.crystallography.net/cod/9012955.cif |
| Cu | Cu | 225 | 9013014 | https://www.crystallography.net/cod/9013014.cif |
| Fe_bcc | Fe | 229 | 9008536 | https://www.crystallography.net/cod/9008536.cif |
| Fe_fcc | Fe | 225 | 9008469 | https://www.crystallography.net/cod/9008469.cif |
| Ni | Ni | 225 | 9013024 | https://www.crystallography.net/cod/9013024.cif |
| Ti_hcp | Ti | 194 | 9008517 | https://www.crystallography.net/cod/9008517.cif |
| Mg | Mg | 194 | 9012434 | https://www.crystallography.net/cod/9012434.cif |
| Zn | Zn | 194 | 9012435 | https://www.crystallography.net/cod/9012435.cif |
| Au | Au | 225 | 9013035 | https://www.crystallography.net/cod/9013035.cif |
| Ag | Ag | 225 | 9013045 | https://www.crystallography.net/cod/9013045.cif |
| Al2O3_corundum | Al2O3 | 167 | 2300448 | https://www.crystallography.net/cod/2300448.cif |
| TiO2_anatase | TiO2 | 141 | 7206075 | https://www.crystallography.net/cod/7206075.cif |
| TiO2_rutile | TiO2 | 136 | 9007432 | https://www.crystallography.net/cod/9007432.cif |
| ZnO_wurtzite | ZnO | 186 | 9004178 | https://www.crystallography.net/cod/9004178.cif |
| SiO2_quartz | SiO2 | 152 | 1011097 | https://www.crystallography.net/cod/1011097.cif |
| Fe2O3_hematite | Fe2O3 | 167 | 1011267 | https://www.crystallography.net/cod/1011267.cif |
| Fe3O4_magnetite | Fe3O4 | 227 | 9010939 | https://www.crystallography.net/cod/9010939.cif |
| CeO2 | CeO2 | 225 | 4343161 | https://www.crystallography.net/cod/4343161.cif |
| ZrO2_monoclinic | ZrO2 | 14 | 1010912 | https://www.crystallography.net/cod/1010912.cif |
| ZrO2_tetragonal | ZrO2 | 137 | 1525705 | https://www.crystallography.net/cod/1525705.cif |
| BaTiO3_tetragonal | BaTiO3 | 99 | 1559964 | https://www.crystallography.net/cod/1559964.cif |
| BaTiO3_cubic | BaTiO3 | 221 | 1559963 | https://www.crystallography.net/cod/1559963.cif |
| SrTiO3 | SrTiO3 | 221 | 2310687 | https://www.crystallography.net/cod/2310687.cif |
| NaCl | NaCl | 225 | 4300180 | https://www.crystallography.net/cod/4300180.cif |
| CaCO3_calcite | CaCO3 | 167 | 1547347 | https://www.crystallography.net/cod/1547347.cif |
| hydroxyapatite | Ca5P3HO13 | 176 | 9011091 | https://www.crystallography.net/cod/9011091.cif |
| MgO | MgO | 225 | 9000499 | https://www.crystallography.net/cod/9000499.cif |
| NiO | NiO | 225 | 1010093 | https://www.crystallography.net/cod/1010093.cif |
| CuO_tenorite | CuO | 15 | 1011194 | https://www.crystallography.net/cod/1011194.cif |
| Cu2O_cuprite | Cu2O | 224 | 1010941 | https://www.crystallography.net/cod/1010941.cif |
| Co3O4 | Co3O4 | 227 | 9005896 | https://www.crystallography.net/cod/9005896.cif |
| MnO2_pyrolusite | MnO2 | 136 | 1514110 | https://www.crystallography.net/cod/1514110.cif |
| graphite | C | 194 | 1011060 | https://www.crystallography.net/cod/1011060.cif |
| SiC_3C | SiC | 216 | 1011031 | https://www.crystallography.net/cod/1011031.cif |
| SiC_6H | SiC | 186 | 1558038 | https://www.crystallography.net/cod/1558038.cif |
| Si3N4_beta | Si3N4 | 176 | 2102550 | https://www.crystallography.net/cod/2102550.cif |
| WC | WC | 187 | 2102244 | https://www.crystallography.net/cod/2102244.cif |
| TiN | TiN | 225 | 1101081 | https://www.crystallography.net/cod/1101081.cif |
| AlN | AlN | 186 | 1010514 | https://www.crystallography.net/cod/1010514.cif |
| LiFePO4 | LiFePO4 | 62 | 4001845 | https://www.crystallography.net/cod/4001845.cif |
| LiCoO2 | LiCoO2 | 166 | 4505482 | https://www.crystallography.net/cod/4505482.cif |
| MoS2_2H | MoS2 | 194 | 1010993 | https://www.crystallography.net/cod/1010993.cif |

## TDB files (~/mcp/science/tdb). Only files with an explicit open license are shipped.
| name | file | sha256 | source | license |
|---|---|---|---|---|
| nist_solder | nist_solder.tdb | 56a0b25021f5dd4d2efbb9ed89ad8ad06929796e963c40ede857fcc9f72df8f3 | https://www.metallurgy.nist.gov/phase/solder/solder.tdb (U.R. Kattner, NIST, upd. 2017; Ag-Bi-Cu-Pb-Sb-Sn) | US Government work, not subject to US copyright (17 USC 105) |
| mc_fe | mc_fe_v2.059.pycalphad.tdb | 467211ab854400ac6d247bdfb97069d37e021cfced6b8dbb30c0334b74ee1508 | pycalphad repo examples/databases (MatCalc steel DB 2.059) | ODbL-1.0 + DbCL-1.0, stated in the file header (share-alike/attribution) |
| mc_fecocrnbti | mc_fecocrnbti.tdb | 7f8bcaccaa518296b4e22e54cc68f15975b81b000c1ec1e3acfbff8636a0e044 | pycalphad repo tests/databases (MatCalc 2.060 subset) | ODbL-1.0, stated in the file header |
Excluded because the license is unclear: all other pycalphad example and test TDBs. These include the NIMS CPDDB-derived alzn_mey, Al-Mg_Zhong,
Fe-O, alfe_sei and nbre_liu files, plus Al-Cu-Y, CrFeNb_Jacob2016, NI_AL_DUPIN_2001, COST507 and others. None of them has a license statement.

## Tools: status, smoke results (synthetic or tutorial inputs, seed 0)
- xrd_simulate: WORKS, CPU. It uses pymatgen XRDCalculator with wavelength as a name (CuKa default) or in Angstrom. Input is cif, phase or formula.
  Si/CuKa gave 111 at 28.469 deg (d 3.1352), 220 at 47.348 and 311 at 56.178, in 0.56 s. TiO2 picks anatase (lowest e_hull) and warns about polymorphs.
- xrd_phase_match: WORKS (FALLBACK), CPU. The test pattern was synthetic anatase + 0.45 rutile with background and noise.
  The top two matches were TiO2_anatase (FoM 0.81) and TiO2_rutile (0.63). The combination was anatase + rutile, which explained 100% of the observed intensity. It took 0.5 s on the first call (library cache) and 0.02 s after that.
- peak_fit: WORKS, CPU. Uses lmfit gauss/lorentz/voigt with a linear/constant/no baseline, and seeds from savgol-smoothed find_peaks.
  Test: two Gaussians with true centers 6.0/9.5, sigma 0.4/0.6 and areas 40.11/37.60. Fitted centers were 6.0003+/-0.0013 and 9.4999+/-0.0026,
  sigma 0.3990/0.5999 and areas 39.89+/-0.13 and 37.71+/-0.15, with R2 0.9967, in 0.19 s.
- xas_edge: WORKS, CPU. Uses larch pre_edge. On a synthetic Cu-K-like edge it gave E0 8979.0 (true 8979), edge step 1.003 (true 1.0) and white line at 8995.0 eV
  (true 8995), with normalized height 1.41, in 0.2 s.
- mlip_energy: WORKS, GPU (cuda). MACE-MPA-0 medium runs in float64, Orb v3 in float32-highest. Tasks are energy, relax (FIRE + FrechetCellFilter),
  eos (9 points at +/-6% volume, Birch-Murnaghan) and elastic (+/-0.5/1% strains with ion relaxation, Voigt/Reuss/Hill).
  Si at the experimental lattice: MACE -5.4124 eV/atom (stress -1.83 GPa), Orb -5.4129 eV/atom.
  MACE relax of Si gave a = 5.466 A (PBE-like) in 7 steps.
  Cu bulk modulus by EOS: MACE 130.1 GPa, Orb 131.3 GPa (exp. about 140). MgO EOS through HTTP: 147 GPa.
  Al elastic constants (MACE): C11 114.3, C12 64.4, C44 29.2 GPa (exp. 107/61/28).
  Timing: 0.5 to 2 s per call after load. The first load takes about 3 s (MACE) or 5 s (Orb).
- phase_equilibria: WORKS, CPU. Uses pycalphad equilibrium on the shipped TDBs, with T scalar or a list of up to 60 values, X dict and P.
  Sn-3.8at%Ag (nist_solder): BCT_A5 0.950 + EPSILON(Ag3Sn) 0.050 at 450 K, all LIQUID at 500 and 600 K (eutectic about 494 K). Took 0.5 s.
  Fe-1at%C (mc_fe): BCC + graphite at 900 K, FCC at 1200 K. Took 2.1 s.
- simulate_tem: WORKS, GPU (abTEM device=gpu via cupy-cuda13x). CPU fallback with SCIENCE_DEVICE=cpu: Si HRTEM took 9.6 s on CPU vs 1-3 s on GPU.
  Modes are hrtem (plane wave + CTF; Cs 1 mm and Scherzer defocus by default; 25 mrad aperture; 30 A focal spread), diffraction
  (plane-wave SAED, log-scaled PNG, spot list with d values) and haadf (probe 21 mrad, 60-200 mrad ADF, 2x2 unit cells).
  Zone-axis cell: unimodular reorientation (v1, v2, [uvw]), then [uvw] is rotated onto z, then an exact orthogonal supercell is built with
  ase.make_supercell. When no exact orthogonal cell exists (oblique cases such as CuO [001]), it falls back to abtem.orthogonalize_cell and warns.
  Checked by diffraction spot d-spacings: Si[110], Al[001], ZnO[100]/[001], anatase[010], graphite[001] and Fe-bcc[111] all give the
  expected reflections.
  Metadata returns sampling_A_per_px (HRTEM/HAADF) or sampling_mrad/invA_per_px (diffraction), plus FFT fringe d-spacings for HRTEM.
  Default thickness is 5 nm. Si [110] at 10 nm is strongly dynamical and suppresses the 111 fringes at Scherzer.

## Validation set (~/mcp/science/validation, made by make_validation.py; 200 kV, 5 nm, structlib CIFs)
- si_110_hrtem.png is 869x922 px at 0.04999 x 0.04998 A/px. Known d: 111 3.1352, 002 2.7152, 220 1.9199, 113 1.6373, 222 1.5676, 004 1.3576.
  The image FFT contains 1.920 (rel. 1.00), 3.135 (0.96), 1.358, 1.637 and 1.246.
- al_001_hrtem.png is 809x809 px at 0.04995 A/px. Known d: 200 2.0203, 220 1.4286, 400 1.0102. The image FFT contains 1.429, 1.010 and 2.020.
- si_110_diffraction.png is 313x295 px at 0.01535 x 0.01628 1/A per px, with the direct beam at the center (log10 over 4 decades).
  Strongest spots are at d 3.1352 (111), 1.9199 (220), 1.3576 (004) and 1.6373 (113).
- validation.json holds the args, known d-spacings, simulation metadata and provenance.

## Worker
~/mcp/science/worker.py (FastAPI, 0.0.0.0:8104). It serves GET /health, GET /version (package versions, weight/TDB/structlib sha256s) and POST /<tool>.
Requests are serialized by a lock and seeded, with torch deterministic (warn_only), and logged to ~/mcp/science/requests.log. HF/Transformers offline mode is set.
image_b64 is ignored with a warning. Errors come back as values=null plus an error string.
The HTTP test passed: health, version, xrd_simulate, mlip_energy eos on GPU, simulate_tem haadf on GPU, and a bad-input error. The worker was then stopped (own PID only).
Code copy: harbor/mcp/backends/science/ (worker.py, start.sh, build_structlib.py, make_validation.py, README.md).

## Owner decisions
1. Dara/BGMN on aarch64. Options: (a) keep the fallback; (b) run Dara on an x86-64 host; (c) allow installing qemu-user-static plus an amd64
   libc sysroot under ~/mcp/science (no sudo, but fragile). BGMN's own license is freeware and closed-source, so it would need checking before (b) or (c).
2. The TDB coverage is narrow: solders and steels only. More open DBs could be added if wanted (for example other MatCalc ODbL releases such as
   mc_al and mc_ni from matcalc.at, after checking their license text). The NIMS CPDDB files were excluded because their license is unclear.
3. abTEM is GPL-3.0. It is used internally behind HTTP only and not redistributed.
