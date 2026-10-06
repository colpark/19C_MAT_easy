# Track D shortlist (preliminary, 2026-10-06)

Source: two Undermind deep searches in workspace "PanelBench v4 database search (Track D)"
(https://app.undermind.ai/projects/a176df59-1b52-4443-9a50-c693060cc3c9):
- "Open micrograph datasets with processing series": 56 relevant papers.
- "Open multimodal characterization deposits on sample series": 146 relevant papers.

Scores come from abstracts only. Each candidate still needs the M0 screen on its deposit: license span, file-level metadata,
the printed-number check and sample-ID correspondence.

**Yield predictor** = (number of law links between M quantities on shared entities) x (separable conditions >= 3). A missing link gives T1/T4 only.

| Rank | Candidate | Conditions | Instruments (M) | Law links | Predicted families | Notes |
|---|---|---|---|---|---|---|
| 1 | Schneider et al. 2019, CrCoNi grain size vs strength (Data in Brief) | 16 grain sizes, several T | micrographs/EBSD grain size; tensile | Hall-Petch (independent: grain size -> yield stress) | T3, T7, T2, T4, T1 | same group: MnFeNi (2019), CrFeNi (2021), a domain pack reused three times |
| 2 | Laplanche 2020, sigma-phase growth in CrMnFeCoNi (Data in Brief) | 600-1000 C x 0.05-1000 h | BSE micrographs; EDX profiles | growth law with Arrhenius; diffusion estimates | T3, T7, T5 (growth exponent), T1 | strongest kinetic series found |
| 3 | Bastidas et al. 2023, 915 electrodeposited Ni/Ni-Fe films | process and composition library | XRD, XRF, nanoindentation, tribology | Vegard (XRF composition -> lattice parameter); hardness vs grain size | T3, T4, T7 | >160,000 files; check license and IDs |
| 4 | Ruiz-Yi et al. 2021, (AlFeNiTiVZr)1-xCrx composition spread | continuous x, oxidation/anneal | WDS, synchrotron XRD, Raman | Vegard; phase vs composition | T3, T4 | |
| 5 | Han et al. 2017, Cu2O films (Cambridge repository) | annealing conditions | Hall, XRD, SEM | sigma = n e mu (definition); defect chemistry | T4, T3 | |
| 6 | Fowler et al. 2024, AM Kovar EBSD (IMMI) | > 600 process sets | EBSD | grain size vs energy density (empirical) | T1, T2 | single instrument |
| 7 | UHCSDB (Hecht/DeCost) | anneal T, t, cooling | SEM only | coarsening (derived observables) | blocked: reader fails held-out validation (V4-E04) | Track C |

**Next:** fetch the deposits of ranks 1-3, run the M0 screen, and estimate yield before building.
