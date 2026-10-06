# TAG_DIFF (v3.3 A3): provenance levels of the P2-P6 panels

v3.2 level = the level declared in sd/<P>/spec.py (v3.2 build). Builder = sd/make_nodes33.py (A3.1, every node with a verified Methods/caption span
or a named default). Sol = blind GPT-5.6-Sol tag audit (audit33.py tags; Methods + captions only; prompt audit/prompts33/tags.txt). Final = the
more restrictive of builder and Sol (hard rule 3). Panels marked "new" are A4 candidate panels not keyed in v3.2.

| Paper | Panel | Quantity | v3.2 | Builder | Sol | Final | Change | Evidence (span or default) |
|---|---|---|---|---|---|---|---|---|
| P2 | F3a | electrical conductivity sigma(T) | M | M | M | **M** | - | "The in-plane electrical conductivity and Seebeck coefficient were simultaneously measured in a helium atmosphe" |
| P2 | F3b | Seebeck coefficient S(T) | M | M | M | **M** | - | "The in-plane electrical conductivity and Seebeck coefficient were simultaneously measured in a helium atmosphe" |
| P2 | F3c | power factor PF(T) | A | A | A | **A** | - | "TE thick films have high performance in power factor (PF = S2σ)" |
| P2 | F3d | total thermal conductivity kappa(T) | M | M | M | **M** | - | "the D was measured by the laser flash method (LFA-467, NETZSCH), and the typical Cp values of 159 J" |
| P2 | F3e | kappa - kappa_e (lattice plus bipolar) | A | A | A | **A** | - | "Based on the electrical conductivity and Seebeck coefficient, the electronic thermal conductivity was calculat" |
| P2 | F3f | figure of merit ZT(T) | A | A | A | **A** | - | "figure of merit (ZT = S2σT/κ" |
| P2 | F2c | Te content (EDS) | M | M | M | **M** | - | "The element content and crystal structure were analyzed by EDS (X-act SDD, Oxford Instruments)" |
| P2 | F2b | compressive stress-strain curves (bulk molded vs zone melted) | new | M | M | **M** | - | "the compressive strain-stress curves of these Bi2Te3 samples were measured by an electro-mechanical universal " |
| P3 | F3b | lateral resistivity rho(f) | M | M | M | **M** | - | "The resistivity of the device under dark conditions was recorded by a Keithley 4200 source meter." |
| P3 | F3c | vertical resistivity rho(f) | M | M | M | **M** | - | "The resistivity of the device under dark conditions was recorded by a Keithley 4200 source meter." |
| P3 | F3d | lateral resistivity near threshold (data points) | M | M | M | **M** | - | "The resistivity of the device under dark conditions was recorded by a Keithley 4200 source meter." |
| P3 | F3e | vertical resistivity near threshold (data points) | M | M | M | **M** | - | "The resistivity of the device under dark conditions was recorded by a Keithley 4200 source meter." |
| P3 | F2c | nanoindentation load-depth curves | new | M | M | **M** | - | "The hardness and modulus of the membranes were probed by the nanoindentation measurement (Bruker Hysitron TI 9" |
| P3 | F2d-hardness | nanoindentation hardness H | M | A | A | **A** | v3.2 M -> A | "The Young’s modulus (E) and hardness (H) values were then derived from load (P)–displacement (h) curves follow" |
| P3 | F2d-modulus | Young's modulus E (nanoindentation) | M | A | A | **A** | v3.2 M -> A | "The Young’s modulus (E) and hardness (H) values were then derived from load (P)–displacement (h) curves follow" |
| P3 | F2b | tensile stress-strain curve (composite) | new | M | M | **M** | - | "Representative stress–strain curves obtained from the tensile test in Fig. 2b" |
| P3 | F2f | XRD patterns under strain (perovskite) | new | M | M | **M** | - | "XRD patterns of (f) perovskite membranes and (g) composite membranes under applied strain" |
| P3 | F2g | XRD patterns under strain (composite) | new | M | M | **M** | - | "XRD patterns of (f) perovskite membranes and (g) composite membranes under applied strain" |
| P3 | F2h | (100) peak position 2theta versus strain | M | A | A | **A** | v3.2 M -> A | "XRD peaks of (100) plane as a function of applied strain. Error bars represent SD." |
| P3 | F3f | photocurrent versus bias (mu-tau measurement, data points) | new | M | M | **M** | - | "The photoconductivity current of the device was recorded by using a Keithley 2400 digital source meter." |
| P3 | F4b | X-ray response current density versus dose rate (data points) | new | M | A | **A** | Sol A vs builder M | "The X-ray response current was measured using a Keithley 2400 digital source meter." |
| P3 | F4h | dark current versus bending strain | new | M | M | **M** | - | "The X-ray response current was measured using a Keithley 2400 digital source meter." |
| P3 | F4i | normalized sensitivity versus bending strain | new | A | A | **A** | - | "The sensitivity of the X-ray detector, calculated by the linear fitting of the dose rate dependent response cu" |
| P3 | F1h | mu-tau product versus 1/E (literature compilation) | new | I | I | **I** | - | "and Young’s modulus (E) for different materials. PCF and SC refer to polycrystalline film and single crystal" |
| P4 | F2c | density | M | M | M | **M** | - | default: named default: bulk density of the cut prisms from mass and geometric volume (specimen dimensions 40 mm x 40 m |
| P4 | F3e | thermal conductivity (Hot Disk) | M | M | M | **M** | - | "the thermal conductivity along the depth direction was quantitatively measured using a Hot Disk TPS 2500S (Swe" |
| P4 | F3b | backside temperature versus heating time | M | M | M | **M** | - | "an infrared camera was positioned 10 cm away from the opposite side of the specimen to record the temperature " |
| P4 | F2a | specific load versus midspan displacement (3PB) | new | A | A | **A** | - | "Representative 3-point bending (3PB) curves" |
| P4 | F2e | specific load versus displacement (SENB) | new | A | A | **A** | - | "Representative SENB test curves" |
| P4 | F2b | strain at failure | A | A | A | **A** | - | "The details of the mechanical parameter calculation including MOR, Flexural toughness, KIC, and KJC are given " |
| P4 | F2d | specific MOR | new | A | A | **A** | - | "the specific modulus of rupture (specific MOR) was not significantly affected" |
| P4 | F2f | specific K_IC | new | A | A | **A** | - | "The details of the mechanical parameter calculation including MOR, Flexural toughness, KIC, and KJC are given " |
| P4 | F2g | flexural toughness | new | A | A | **A** | - | "The details of the mechanical parameter calculation including MOR, Flexural toughness, KIC, and KJC are given " |
| P4 | F2h | specific K_JC | new | A | A | **A** | - | "The values corresponding to this limit on the curves were used to calculate the fracture toughness KJC." |
| P4 | F2j | J-R curves | new | A | A | **A** | - | "Representative crack-resistance curves (J-R curves)" |
| P4 | F4b | weak-phase thickness and length distributions (X-CT) | new | A | A | **A** | - | "The thickness distributions of the weakness phase and the solid phase were determined by creating five equally" |
| P5 | F2a | tensile stress-strain curves (15 wt%) | new | M | M | **M** | - | "All tensile tests of the hydrogels with a dumbbell shape were conducted on a universal tensile machine (Instro" |
| P5 | F2b-strength | tensile strength (15 wt%) | M | M | M | **M** | - | "All tensile tests of the hydrogels with a dumbbell shape were conducted on a universal tensile machine (Instro" |
| P5 | F2b-elongation | elongation at break (15 wt%) | M | M | M | **M** | - | "All tensile tests of the hydrogels with a dumbbell shape were conducted on a universal tensile machine (Instro" |
| P5 | F2c | modulus and toughness | new | A | A | **A** | - | "The area under the stressstrain curves to failure is defined as the “toughness”" |
| P5 | F2d | tensile stress-strain curves (20 wt%) | new | M | M | **M** | - | "All tensile tests of the hydrogels with a dumbbell shape were conducted on a universal tensile machine (Instro" |
| P5 | F2e-strength | tensile strength (10/20 wt%) | M | M | M | **M** | - | "All tensile tests of the hydrogels with a dumbbell shape were conducted on a universal tensile machine (Instro" |
| P5 | F2g | water content | M | M | M | **M** | - | "The hydrogel was dried at 37 °C until a constant weight, and the initial and dried mass of the hydrogel were e" |
| P5 | F2h | fracture energy | new | A | M | **A** | Sol M vs builder A | "The fracture energy can be calculated by" |
| P5 | F3d | WAXS azimuthal intensity profiles | new | M | M | **M** | - | "Wide-angle X-ray scattering (WAXS) and small-angle X-ray scattering (SAXS) measurements were conducted using a" |
| P5 | F3j | crystallinity (dry, swollen) | new | A | A | **A** | - | "The crystallinity of the dried sample (Xdry) is calculated as" |
| P5 | F4a | crack extension per cycle versus energy release rate | new | A | A | **A** | - | "The energy release rate (G) is calculated by" |
| P5 | F4f | fatigue threshold | new | A | A | **A** | - | "The fatigue threshold was linearly extrapolated" |
| P6 | F2a | iR-corrected OER polarization current density | M | M | M | **M** | - | "E - iR (V) vs.RHE" |
| P6 | F2b | Tafel plots (overpotential versus log j) | new | A | A | **A** | - | "OER polarization curves of SI1C1, SI2C1, SI4C1, SI6C1, SI8C1, and SI samples with a mass loading of 0.025 mg/c" |
| P6 | F2c | overpotential at 10 mA/cm2 | A | A | A | **A** | - | "Comparison of overvoltages and Tafel slopes" |
| P6 | F2c-tafel | Tafel slope | new | A | A | **A** | - | "Comparison of overvoltages and Tafel slopes" |
| P6 | F2d | mass activity | new | A | A | **A** | - | "Comparison of OER mass activity" |
| P6 | F1i-Co | Co/Ir ratio (ICP-MS) | M | M | M | **M** | - | "the proportions of each element in SrIrO3 were determined by ICP-MS (iCAP RQ) analysis." |
| P6 | F1i-Sr | Sr/Ir ratio (ICP-MS) | M | M | M | **M** | - | "the proportions of each element in SrIrO3 were determined by ICP-MS (iCAP RQ) analysis." |
| P6 | F4a | 18O16O percentage (DEMS) | new | M | A | **A** | Sol A vs builder M | "differential electrochemical mass spectrometry (DEMS) measurements were conducted using the QAS 100 apparatus" |
| P6 | F4b | in situ ICP-MS dissolved Sr, Co, Ir | new | M | M | **M** | - | "In situ ICP-MS experiments were performed using a Thermo Scientific iCAP RQ instrument." |
| P6 | F2f | PEM electrolyser polarization | new | M | M | **M** | - | "A home-made PEM water electrolysis cell with a proton exchange membrane was used to evaluate the performance o" |

## Settled cases (plan A3.2)

- **P2, which instrument measured κ, and the L(S) relation behind κe.** κ = ρ·D·Cp, with D from the LFA-467 laser flash, ρ from mass and geometry (a constant: 7.54 g/cm³), and a typical Cp (a constant: 159 J/(kg K)). That is a standard instrument equation on an unplotted reading, so κ is M (Sol agrees). κe = L(S)·σ·T, with L(S) given in Supplementary Fig. 4 (the SI is not on the host; Source Data sheet "Supplementary Figure 4" lists L(T) per film). κ − κe is A, and its panel F3e stays excluded (the sheet disagrees with the figure).
- **P3, Fig. 2d against Fig. 2c.** "The Young's modulus (E) and hardness (H) values were then derived from load (P)–displacement (h) curves following the Oliver-Pharr method (Fig. 2c, d)", so H and E are A (v3.2 had M). They now give no T1 or T4 matrix items, and Voigt/Reuss bound items cannot be keyed on them (A4).
- **P4, the density method and the specimen dimensions.** The density method is not stated, so the named default applies: mass over geometric volume of the cut prisms (M, three specimens per bar in the Source Data). Dimensions: 40 × 40 × 160 mm prisms with a 100 mm span (3PB and SENB); 40 × 40 × 35 mm for the flame and Hot Disk tests.
- **P5, Fig. 2b against the Fig. 2a curves.** Strength and elongation at break are specimen means of repeated Instron 3367 tests (n = 3), so they are M under definition 2. The Fig. 2a curves are representative (definition 3), so no recompute audit is built from them. Modulus and toughness (Fig. 2c) are slope and integral, so A.
- **P6, iR correction and reference electrode.** The axis is "E - iR (V) vs.RHE". The caption lists the resistances (3.9, 3.7, 3.6, 4.7, 3.2, 4.6 and 4.4 Ω). The reference was Hg/HgCl2 in 0.5 M H2SO4 (saturated Ag/AgCl for DEMS), converted to RHE. Current density is therefore iR-corrected and M (definition 2). The Tafel plot (Fig. 2b) is a transform of the Fig. 2a curves, so A; overpotential, Tafel slope and mass activity are A.

## Sol disagreements (restrictive choice applied)

- P3 F4b, X-ray response current density against dose rate: builder M, Sol A (current over the electrode area defined by a metal mask). Final A. Consequence: the A4 candidate "T7 detector linearity (Fig. 4b)" is not keyable.
- P6 F4a, DEMS 18O16O percentage: builder M, Sol A (a ratio of isotopologue signals). Final A.
- P5 F2h, fracture energy: builder A, Sol M. Stays A (the builder was already restrictive).

Sol cost (5 calls, openai/gpt-5.6-sol): $0.1272.
