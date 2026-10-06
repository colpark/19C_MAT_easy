# UHCSDB intake screen (skill M0), 2026-10-06

Source: Ultrahigh Carbon Steel Micrographs, NIST MDR 11256/940 (Hecht, DeCost, Francis, Holm, Picard, Webler).
- The handle no longer resolves; the files come from the Internet Archive snapshots (v4_host/uhcsdb/nist940/manifest.json).
- Descriptor: DeCost et al., IMMI 6, 197 (2017), doi 10.1007/s40192-017-0097-0.

| Criterion | Result | Evidence |
|---|---|---|
| >= 3 conditions on the same entities | **pass** | one alloy (UHCS, AC1 stock), anneal schedules: 800 C x {5 min, 90 min, 3 h, 8 h, 24 h, 85 h}; 970 C x {5 min, 90 min, 3 h, 8 h, 24 h, 48 h}; 5 min x {700, 750, 800, 900, 970, 1000 C}; 3 h and 24 h x {800, 900, 970 C}; cooling Q / WQ / FC / AR / WC / 650C-1H |
| >= 2 instruments with M data | **fail as stated** | SEM only (SE 845, BSE 84, unknown 32). Both measured quantities come from images by our frozen procedures (M2 micrographs: two methods). The database has no second instrument; a second route can come only from the Hecht papers' reported measurements (to be checked) |
| A law linking two M quantities | **pass (derived observables)** | particle coarsening d^n - d0^n = k t (n = 3 volume diffusion, n = 4 grain-boundary diffusion) with k = k0 exp(-Q/RT); links our particle size across time and temperature. The time exponent separates the mechanisms (T5) |
| >= 3 M observables per entity (T5), 4 (T6) | **partial** | particle size, particle number density, area fraction of carbide, network presence (two-method image measures). Four only if the network thickness is measurable |
| Conditions as separate series (T2) | **pass** | micrographs per sample, same magnifications (1964X, 4910X) across schedules |
| Printed-number check | n/a | database: metadata fields only. Scale check: micron_bar / micron_bar_px against the drawn bar, on a sample before keying (M2) |
| License | **CC BY 3.0 US** | license_rdf in the deposit (resolves the plan's watch-out) |
| Year | 2017 data, images public since 2017 | contamination risk: images likely in training data; use image-swap counterfactuals and the textbook-prior gate |
| Annotations | I level | primary_microconstituent labels (human) never key |

Decision: proceed as the condition-series seed. Missing for the claims layer: the Hecht et al. papers (carbide network and cementite coarsening), which are not on the host yet.
