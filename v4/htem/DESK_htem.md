# DESK HTEM (Track H, H1; host A spark-112b; 2026-10-07)

## Sources (R3), hashed in `v4_host/htem/papers`
| Source | File | sha256 (first 16 hex) |
|---|---|---|
| Zakutayev et al., Sci. Data 5, 180053 (2018), PMC5881410, Europe PMC full-text XML (the PDF render returned HTML) | zakutayev2018_PMC5881410.xml | 9c59428bd928747e |
| Data infrastructure paper (arXiv 2105.05160) | arxiv_2105.05160.pdf | 4ac3083ce28b7233 |
| NREL Data Catalog submission 75 (doi:10.7799/1407128) | nlr_submission75.html | 24d212f91862f8d4 |
| Its license page | nlr_submission75_license.html | b5b062fe70effd50 |
| Named-default sources: open NREL papers with HTEM data, same workflow | arxiv_2206.03594.pdf | f81f135cd4c48a8b |
| | arxiv_2306.02233.pdf | 1733a5fa2d18b30a |

The descriptor and the data record give no instrument settings. The raw-file endpoint (`/api/sample/<id>/file?which=xrd_raw`) is not served: HTTP 502 after the kit's retries, and 404 under the `/xrd` path. Not worked around.

## D records
**XRD:**
- **Instrument and source:** "High-throughput X-ray diffraction (XRD) mapping was conducted using a Bruker D8 Discover (Cu Kα radiation) equipped with an area detector." (arXiv 2206.03594); "Each library was mapped with X-ray diffraction (XRD) using a Bruker D8 Discover with Cu Kα radiation and an area detector." (arXiv 2306.02233).
- **Wavelength:** 1.5418 Å, the Kα1/Kα2 weighted mean, unresolved on an area detector. A named default, checked against a reference phase in H3.
- **2θ range:** read from the data. Most records hold 801 points over 19-52°; some hold 661 points (library 6701).

**Optical:**
- "Transmission (T ) and reflectance (R) spectra were collected in the UV-Vis-NIR spectral ranges (300–1100 nm) using a home-built thin film optical spectroscopy system equipped with deuterium and tungsten/halogen light sources and a Si detector array. The collected spectra were then used to calculate absorbance using the relation Absorbance, A = ln [T /(1 − R)]." (arXiv 2206.03594, SI)
- The incidence geometry is not stated (D gap).
- The records carry opt_uvit/uvir (800 points) and, on some, NIR T/R channels.

**Thickness:** level A.
- "using thickness of the samples determined by XRF" (Sci. Data 2018)
- "Resistivity was calculated using XRF-measured film thickness." (arXiv 2306.02233)
- Tauc Eg is invariant to a constant thickness scale. Absorption and resistivity magnitudes are not keyed.

**Four-point probe:**
- "a custom built collinear four-point probe instrument by sweeping current between the outer two pins while measuring voltage between the inner pins (1 mm between each pin). Conventional geometric corrections were applied to convert the measured resistance into sheet resistance" (arXiv 2206.03594)
- The factor is not recorded: π/ln2 = 4.532 is the named default (D gap). Ranks are unaffected.

**XRF:**
- "Metal ratios were mapped using a Fischer XDV-SDD XRF with a Rh source and a 3 mm diameter spot size." (2022)
- "Metal ratios were mapped using a Bruker M4 Tornado XRF with a Rh source operating at 50 kV and 200 µA." (2023)
- The instrument per library is not recorded (the library record has an `xrf_type` field). Cation fractions are M; thickness from XRF is A.

**Database-processed columns (level A, validation only):** opt_direct_bandgap, opt_average_vis_trans, opt_absorption_coefficient, opt_normalized_transmittance, fpm_sheet_resistance, fpm_resistivity, fpm_conductivity, peak_count.

**License:**
- NREL Data Catalog submission 75, "Dataset License": "The user is granted the right, without any fee or cost, to use or copy the Data, provided that this entire notice appears in all copies of the Data. Further, the user agrees to credit DOE/NREL/ALLIANCE in any publication that results from the use of the Data."
- No endorsement use of the names.
- Items can be released with the full notice attached (release_eligible true, requires_notice true). Flagged for David.
- The descriptor article itself is CC BY 4.0.
