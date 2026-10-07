# refodat physics pre-registration (Track S round 3, desk items 5 and 10). Written before any reader output or separability number.
# Mechanism pairs with signatures (direction of each observable). Textbook directions; prior ranks are named defaults. Claims come from
# templates only (no claim ladder in either deposit, R12).

# refodat90: CEM I mortar, interfacial transition zone. Observables vs distance from the aggregate surface (0-100 um, frozen bins
# 0-10, 10-20, 20-30, 30-50, 50-100 um). 'slope' = sign of d(observable)/d(distance).
ITZ_PAIR = {
    'wall_effect_packing': {
        'mechanism': 'Wall effect: cement grains pack loosely against the aggregate, so the paste next to it is more porous and holds less anhydrous clinker',
        'source': 'Scrivener, Crumbie and Laugesen 2004, Interface Science 12:411 (ITZ porosity and anhydrous gradients)', 'prior_rank': 1,
        'predicts': {'porosity_slope': 'down', 'anhydrous_fraction_slope': 'up', 'indent_modulus_slope': 'up', 'portlandite_fraction_slope': 'none'}},
    'ch_enrichment_bleeding': {
        'mechanism': 'Bleeding water collects at the aggregate and portlandite nucleates there, so the paste next to it is enriched in CH',
        'source': 'Maso 1980; Monteiro and Mehta 1985 (CH orientation and enrichment at the interface)', 'prior_rank': 2,
        'predicts': {'porosity_slope': 'none', 'anhydrous_fraction_slope': 'none', 'indent_modulus_slope': 'down', 'portlandite_fraction_slope': 'down'}},
}
# A comparison decides only where the two signatures differ and the observed slope exceeds 2 SE: porosity, anhydrous fraction and
# indent modulus here. The portlandite slope needs a validated CH/C-S-H split (S4r step 4) and is otherwise undecidable.

# refodat91: CEM III/B concrete, carbonated (C) vs uncarbonated (H) at w/c 0.40 (21) and 0.60 (25). 'diff' = carbonated minus
# uncarbonated at the same w/c.
CARBONATION_PAIR = {
    'calcite_densification': {
        'mechanism': 'Calcite precipitates in the pores during carbonation and densifies the paste',
        'source': 'Ngala and Page 1997, CCR 27:995 (carbonation reduces porosity in Portland cement pastes)', 'prior_rank': 2,
        'predicts': {'bse_porosity_diff': 'down', 'ltdsc_pore_size_diff': 'down', 'ltdsc_freezable_water_diff': 'down'}},
    'csh_decalcification_coarsening': {
        'mechanism': 'Carbonation decalcifies C-S-H in the low-portlandite CEM III/B paste and coarsens its pores',
        'source': 'Borges et al. 2010, CCR 40:284 (carbonation coarsens slag-blend pastes)', 'prior_rank': 1,
        'predicts': {'bse_porosity_diff': 'up', 'ltdsc_pore_size_diff': 'up', 'ltdsc_freezable_water_diff': 'up'}},
}
# The LTDSC comparison is at mix level only (paste III.70.04 / III.70.06 against concrete M38 / M44), by direction and ranking, never
# tile against curve. Accumulated ice mass in baseline.csv is author-derived (A); raw heat flow (*_raw_data.csv) is M.
