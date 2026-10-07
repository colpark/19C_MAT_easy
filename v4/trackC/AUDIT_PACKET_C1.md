# AUDIT_PACKET_C1 (blind pipeline-card audit; quote Q-C1; NOT RUN)

Auditor: a model family different from the evaluated models (I3), temperature 0, fixed prompts. The auditor sees the verbatim spans below and never the builder card, its frozen readings or any key. On disagreement the restrictive reading wins; an approved audit that changes a card triggers a refreeze and regeneration.

## System prompt (stages)

```
You audit a computational screening pipeline description. Use only the quoted text. Answer in JSON with keys: order_after (the stage this one follows, or "first"), observable, comparator (one of >, >=, <, <=, ==, in, class, computed, unstated), threshold (number or text, or "unstated"), unit, decision_type (one of static, recovery, refinement, escalation, literature, engine, outcome_class), rule_fully_stated (true/false), missing (what the text leaves unstated). When the text is ambiguous, say so; never guess.
```

## System prompt (laws)

```
You audit a law used by a computational pipeline. Use only the quoted text. Answer in JSON with keys: law_class (definition, fit, independent, agreement), inputs, target, constants_with_source, stated_assumptions, missing.
```

## CARD_liion (thakur2026_liion_pinball_fpmd)

Source: T. S. Thakur, L. Ercole, N. Marzari, Novel fast Li-ion conductors for solid-state electrolytes from first-principles, Energy Environ. Sci. 2026, doi:10.1039/d5ee07336g

### call 1: stage "sources"

Pipeline stage names in the paper's order of mention: sources, clean, occupancy, unicity, composition, atomic_distance, electronic, scf_rerun, pinball_selfconsistency, pinball_drift, pinball_conductivity, novelty, fpmd_1000K, temperature_ladder, fpmd_outcome_class.

Quoted text (Sec 2.1 p4):

> Starting from experimental structures sourced from the Crystallography Open Database (COD), Inorganic Crystal Structure Database (ICSD) and Materials Platform for Data Science (MPDS) repositories, we identify more than 30,000 lithium containing structures, which are imported as CIF files using AiiDA.

Stated count after this stage: 30229 (Fig. 3 node labels COD 8,007 + ICSD 8,917 + MPDS 13,305 (text: approximately 8,000, 9,000, and 13,000))

### call 2: stage "clean"

Pipeline stage names in the paper's order of mention: sources, clean, occupancy, unicity, composition, atomic_distance, electronic, scf_rerun, pinball_selfconsistency, pinball_drift, pinball_conductivity, novelty, fpmd_1000K, temperature_ladder, fpmd_outcome_class.

Quoted text (Sec 2.1 p4):

> We follow that protocol to clean, parse and standardise CIF files using COD-tools

Stated count after this stage: 22842 (Fig. 3 "Clean CIFs 22,842", "Unusable CIFs 7,387" (text: nearly 23,000))

### call 3: stage "occupancy"

Pipeline stage names in the paper's order of mention: sources, clean, occupancy, unicity, composition, atomic_distance, electronic, scf_rerun, pinball_selfconsistency, pinball_drift, pinball_conductivity, novelty, fpmd_1000K, temperature_ladder, fpmd_outcome_class.

Quoted text (Sec 2.1 p4 (Occupancy filter)):

> We remove structures with partial occupancies i.e. those whose stoichiometry doesn't align with the reported atomic positions

Stated count after this stage: 12198 (Fig. 3 "Integer occupancy 12,198", "Partial occupancy 9,532", "Li only partial occupancy 1,112" (text: approximately 10,600 removed, 12,000 remain))

### call 4: stage "unicity"

Pipeline stage names in the paper's order of mention: sources, clean, occupancy, unicity, composition, atomic_distance, electronic, scf_rerun, pinball_selfconsistency, pinball_drift, pinball_conductivity, novelty, fpmd_1000K, temperature_ladder, fpmd_outcome_class.

Quoted text (Sec 2.1 p4 (Unicity filter)):

> we use the CMPZ algorithm implemented within the structure matcher function of pymatgen to compare crystal structures with the same stoichiometry, to eliminate equivalent structures and retain only unique ones.

Stated count after this stage: 5239 (Fig. 3 "Unique structures 5,239", "Duplicate structures 6,959" (text: 5,200))

### call 5: stage "composition"

Pipeline stage names in the paper's order of mention: sources, clean, occupancy, unicity, composition, atomic_distance, electronic, scf_rerun, pinball_selfconsistency, pinball_drift, pinball_conductivity, novelty, fpmd_1000K, temperature_ladder, fpmd_outcome_class.

Quoted text (Sec 2.1 p4 (Composition filter)):

> we filter out those with hydrogen, as elements lighter than lithium cannot be correctly modelled by the pinball approximation; those containing noble gas atoms; 3d-transition elements, due to their potential to changing oxidation states during simulations and become electronically conducting; and elements heavier than Polonium. Furthermore, we apply additional filtering criteria to ensure that each structure contains a specific selection of anions from the pnictogen, chalcogen and halogen families.

Stated count after this stage: 1550 (Fig. 3 node "1,550" after Composition filter)

### call 6: stage "atomic_distance"

Pipeline stage names in the paper's order of mention: sources, clean, occupancy, unicity, composition, atomic_distance, electronic, scf_rerun, pinball_selfconsistency, pinball_drift, pinball_conductivity, novelty, fpmd_1000K, temperature_ladder, fpmd_outcome_class.

Quoted text (Sec 2.1 p4 (Atomic-distance filter)):

> For each structure, we calculate the bond distances between every atom pair that is compatible with inorganic materials to filter out structures with bond lengths typically associated with organic molecules such as double bond with O or triple bond with N.

Stated count after this stage: 1499 (Fig. 3 "Pre-screened structures 1,499"; text "resulting in 1,499 structures")

### call 7: stage "electronic"

Pipeline stage names in the paper's order of mention: sources, clean, occupancy, unicity, composition, atomic_distance, electronic, scf_rerun, pinball_selfconsistency, pinball_drift, pinball_conductivity, novelty, fpmd_1000K, temperature_ladder, fpmd_outcome_class.

Quoted text (Sec 3 p7; Sec 2.2 p5 ("band gap greater than 1 eV as electronically insulating")):

> we classify a structure as an electronic insulator if its band gap exceeds 1 eV. Out of the 1,499 unique structures, 982 are identified as electronic insulators, and 39 calculations failed

Stated count after this stage: 982 (text p7 and Fig. 5 ("Electronic insulators 982", "Electronic conductors 478"))

### call 8: stage "scf_rerun"

Pipeline stage names in the paper's order of mention: sources, clean, occupancy, unicity, composition, atomic_distance, electronic, scf_rerun, pinball_selfconsistency, pinball_drift, pinball_conductivity, novelty, fpmd_1000K, temperature_ladder, fpmd_outcome_class.

Quoted text (Sec 3 p7):

> Out of these, 251 calculations fail to converge due to issues in the self-consistent electronic cycle. These are subsequently rerun using the non-linear conjugate gradient method within SIRIUS enabled Quantum ESPRESSO.

Stated count after this stage: 251 (text p7 (reruns), 39 failed after rerun)

### call 9: stage "pinball_selfconsistency"

Pipeline stage names in the paper's order of mention: sources, clean, occupancy, unicity, composition, atomic_distance, electronic, scf_rerun, pinball_selfconsistency, pinball_drift, pinball_conductivity, novelty, fpmd_1000K, temperature_ladder, fpmd_outcome_class.

Quoted text (Sec 3.1 p8):

> We ensure that the r2 correlation for the converged pinball coefficients exceeds 0.95, with the majority of cases exceeding 0.99. If this criterion is not met, additional self-consistent pinball MD iterations are performed

Stated count after this stage: 914 (text p8 "Out of 982 structures, we achieve convergence for 914, with failures occurring due to issues in the self-consistent electronic cycle when calculating DFT forces")

### call 10: stage "pinball_drift"

Pipeline stage names in the paper's order of mention: sources, clean, occupancy, unicity, composition, atomic_distance, electronic, scf_rerun, pinball_selfconsistency, pinball_drift, pinball_conductivity, novelty, fpmd_1000K, temperature_ladder, fpmd_outcome_class.

Quoted text (Sec 3.1 p8):

> An additional 63 structures failed the pinball MD simulations due to drift in the constant of motion, leading to 851 structures with a final iteration of the pinball MD run with converged coefficients

Stated count after this stage: 851 (text p8)

### call 11: stage "pinball_conductivity"

Pipeline stage names in the paper's order of mention: sources, clean, occupancy, unicity, composition, atomic_distance, electronic, scf_rerun, pinball_selfconsistency, pinball_drift, pinball_conductivity, novelty, fpmd_1000K, temperature_ladder, fpmd_outcome_class.

Quoted text (Sec 3.1 p8):

> Ionic conductivity of 1 mS/cm at 1000 K is chosen as the threshold to categorise potential fast ionic conductors at the pinball level. At the end of this process, 132 structures are identified for further study using first-principles calculations.

Stated count after this stage: 132 (text p8 and Fig. 5 ("Potential fast-diffusers 132", "Non-diffusive structures 738", "Failed calculations 170"))

### call 12: stage "novelty"

Pipeline stage names in the paper's order of mention: sources, clean, occupancy, unicity, composition, atomic_distance, electronic, scf_rerun, pinball_selfconsistency, pinball_drift, pinball_conductivity, novelty, fpmd_1000K, temperature_ladder, fpmd_outcome_class.

Quoted text (Sec 3.2.1 p8):

> Out of these 132 structures, we rediscover 77 known Li-ion conductors and as such we exclude them from FPMD investigations.

Stated count after this stage: 55 (text p8 (77 known), Sec 4 p14 ("The remaining 55 materials"))

### call 13: stage "fpmd_1000K"

Pipeline stage names in the paper's order of mention: sources, clean, occupancy, unicity, composition, atomic_distance, electronic, scf_rerun, pinball_selfconsistency, pinball_drift, pinball_conductivity, novelty, fpmd_1000K, temperature_ladder, fpmd_outcome_class.

Quoted text (Sec 2.3.2 p6; Sec 3.2.2 p10; Table 1):

> the structures that exhibit high Li-ion diffusivity at 1000 K with the pinball model are subsequently studied with FPMD at the same temperature for 100 ps. ... We find 18 materials that do not exhibit Li-ion diffusion in our FPMD simulations at 1000 K.

Stated count after this stage: 18 (text p10 and Table 1 (18 rows))

### call 14: stage "temperature_ladder"

Pipeline stage names in the paper's order of mention: sources, clean, occupancy, unicity, composition, atomic_distance, electronic, scf_rerun, pinball_selfconsistency, pinball_drift, pinball_conductivity, novelty, fpmd_1000K, temperature_ladder, fpmd_outcome_class.

Quoted text (Sec 2.3.2 p6):

> The structures validated by FPMD as fast ionic conductors are then studied at three lower temperatures: 750 K , 600 K and 500 K for 125 ps, 150 ps and 180 ps respectively.

Stated count after this stage: 34 (derived: 9 (Table 3) + 25 (Table 2) studied at lower temperatures; exception Li2P2PdO7 only at 600 K (Table 2 footnote **, SI Fig. S15 caption))

### call 15: stage "fpmd_outcome_class"

Pipeline stage names in the paper's order of mention: sources, clean, occupancy, unicity, composition, atomic_distance, electronic, scf_rerun, pinball_selfconsistency, pinball_drift, pinball_conductivity, novelty, fpmd_1000K, temperature_ladder, fpmd_outcome_class.

Quoted text (Sec 3.2.3 p10; Sec 3.2.4 p11):

> We have identified 25 structures that exhibit significant diffusion at 1000 K in our FPMD simulations, but do not display the same behaviour at lower temperatures. ... These materials are of particular interest due to their potential applications, characterised by their fast ionic conduction, which allows us to resolve Li-ion diffusion even at low temperatures and estimate activation barriers

Stated count after this stage: {'no_diffusion': 18, 'high_T_only': 25, 'fast': 9} (Tables 1-3 (18 + 25 + 9 = 52 rows of 55))

### call 16: law "tracer_D"

Quoted text (Sec 2.3 p5):

> By performing a linear regression of the mean square displacement MSD(t) with time we can accurately estimate the diffusion coefficient from the slope of the MSD

### call 17: law "nernst_einstein"

Quoted text (Sec 2.3 p5):

> In the dilute limit, we assume it to be 1, though in practice it is often less than 1, implying that correlated motion can enhance conductivity

### call 18: law "arrhenius"

Quoted text (Sec 2.3.2 p7):

> The activation barrier for these structures is estimated from a linear fit of the Arrhenius behaviour and the error is obtained with Bayesian propagation

### call 19: law "room_temperature_extrapolation"

Quoted text (Sec 4 p14):

> it is important to note that this estimation is based on the extrapolation of the Arrhenius plot, where a change of slope is possible

## CARD_jarvis (choudhary2022_jarvis_bcs_epc)

Source: K. Choudhary, K. Garrity, Designing high-TC superconductors with BCS-inspired screening, density functional theory and deep-learning, npj Comput. Mater. 8, 244 (2022), doi:10.1038/s41524-022-00933-1

### call 20: stage "sources"

Pipeline stage names in the paper's order of mention: sources, debye, dos_fermi, natoms, epc, tc, dynamic_stability.

Quoted text (Sec 2.1 p3):

> Currently, there are electronic DOS database available for 55723 materials and elastic tensors for 17419 materials (using the v08.18.2021 version of JARVIS-DFT database at the time of writing).

Stated count after this stage: 55723 (Fig. 1 arrow "55723"; text p3 (17419 with elastic tensors))

### call 21: stage "debye"

Pipeline stage names in the paper's order of mention: sources, debye, dos_fermi, natoms, epc, tc, dynamic_stability.

Quoted text (Sec 2.1 p3):

> Out of 17419 materials, we find 5618 of them with θD greater than 300 K.

Stated count after this stage: 5618 (text p3 and Fig. 1 "5618")

### call 22: stage "dos_fermi"

Pipeline stage names in the paper's order of mention: sources, debye, dos_fermi, natoms, epc, tc, dynamic_stability.

Quoted text (Sec 2.1 p3):

> Furthermore, selecting materials with electronic DOS at the Fermi level greater than 1 states/eV/Nelect, we find 1736 materials.

Stated count after this stage: 1736 (text p3 and Fig. 1 "1736")

### call 23: stage "natoms"

Pipeline stage names in the paper's order of mention: sources, debye, dos_fermi, natoms, epc, tc, dynamic_stability.

Quoted text (Sec 2.1 p8):

> Next, we apply the J-Scr workflow on materials with number of atoms less than equal to 5, θD >300K and N (0) >1 as discussed in the previous section. As of now, we have applied J-Scr to 1058 materials.

Stated count after this stage: 1058 (text p8 and Fig. 1 "1058" (the atoms gate is not drawn in Fig. 1))

### call 24: stage "epc"

Pipeline stage names in the paper's order of mention: sources, debye, dos_fermi, natoms, epc, tc, dynamic_stability.

Quoted text (Sec 2.1 p6):

> During this step, we use the same k-points grid found during the JARVIS-DFT total energy convergence, as well as a q-point grid of at least 2 × 2 × 2 with a broadening of 0.05 Rydberg (≈ 0.68 eV).

Stated count after this stage: 1058 (text p8)

### call 25: stage "tc"

Pipeline stage names in the paper's order of mention: sources, debye, dos_fermi, natoms, epc, tc, dynamic_stability.

Quoted text (Abstract; Sec 2.1 p8; Fig. 1 ("TC ≥ 5 K" -> 283)):

> we identify 105 dynamically stable materials with transition temperatures, TC ≥ 5 K. ... only 626 of them are dynamically stable (i.e. no imaginary phonon modes) and 105 of them have TC >5 K

Stated count after this stage: 283 (Fig. 1 arrow "283" after "TC ≥ 5 K")

### call 26: stage "dynamic_stability"

Pipeline stage names in the paper's order of mention: sources, debye, dos_fermi, natoms, epc, tc, dynamic_stability.

Quoted text (Sec 2.1 p8; Fig. 1 ("Dynamically stable" -> 105)):

> As of now, we have applied J-Scr to 1058 materials. Out of these, only 626 of them are dynamically stable (i.e. no imaginary phonon modes)

Stated count after this stage: 105 (Fig. 1 arrow "105"; text: 626 of 1058 stable)

### call 27: law "lambda"

Quoted text (Sec 3.2 p15):

> lambda = 2 int alpha2F(w)/w dw (eq. 6)

### call 28: law "omega_log"

Quoted text (Sec 3.2 p15):

> omega_log = exp[(2/lambda) int dw alpha2F(w)/w ln w] (eq. 8)

### call 29: law "mcmillan_allen_dynes"

Quoted text (Sec 2.1 p6):

> the TC from the McMillan-Allen-Dynes formula, using µ∗ = 0.09, from our J-Scr workflow has an excellent agreement

### call 30: law "debye"

Quoted text (Sec 3.1 p14):

> theta_D = h/kB (3 n NA rho / (4 pi M))^(1/3) v_m (eq. 2)

Total calls: 30
