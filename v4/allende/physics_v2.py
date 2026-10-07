# Allende physics table v2 (v4 Track B rebuild from the claim ladder, v4/notes/20261006_allende_claim_ladder_stitching.md). Frozen (B10) before
# any key or decidability is computed. Keys come from our frozen procedures on the raw deposit (eds.py B1, stxm.py B2-B3, register.py B4,
# derived.py B9: derived-observable procedures, skill M2). Every item is audit_pending until a raw-data audit runs under an approved quote
# (Q1 used the paper-centric tag prompt; its verdicts on our own procedures are superseded only by that re-audit, not here).
#
# Claim ladder: rung (D, M, A, I), verbatim span, data object, verification route, decision rule.
# B12: every span is the full verbatim sentence of the paper (v4_host/allende/text/aax3009.txt, hyphenation and line breaks joined); Q1b
# rejected 10 of 12 parses because B10 stored fragments (V4-E12). Each claim is a narrower instance of its sentence. D3 split into the tilt
# sentence (D3) and the pixel-size sentence (D3b). D4 now renders its sentence (recorded at the Fe L3 edge, 707 eV) and is decided from the
# Fe stack's recorded energy range; the old D4 (absorption maximum at 707 eV) said more than any sentence. A4 had compositions no sentence
# gives; it now renders the Cliff-Lorimer method sentence. The A3 sentence is split by a figure caption in the text; joined (span_note).
S_STXM = 'STXM data were recorded with 10-ms dwell time using an 80 × 80 square scan grid that proceeded with 40-nm steps to cover a 3.2-mm by 3.2-mm field of view.'
S_DOM = ('The superimposed EDS and HAADF GENFIRE reconstructions revealed three main mineral domains: (i) iron-magnesium silicate (Fig. 2B, purple and teal), '
         '(ii) aluminum-chromium iron oxide (Fig. 2B, yellow), and (iii) iron-nickel sulfide (Fig. 2B, red).')
CLAIMS = [
  {'sid': 'D1', 'rung': 'D', 'span': S_STXM, 'span_note': 'field of view printed as 3.2-mm (micrometre sign lost in the text extraction)', 'object': 'STXM headers (4 edges)', 'route': 'metadata',
   'check': 'dwell_ms == 10 for every edge', 'claim': 'The STXM data were recorded with a 10 ms dwell time.'},
  {'sid': 'D2', 'rung': 'D', 'span': S_STXM, 'object': 'STXM headers', 'route': 'metadata', 'check': 'grid == 80 x 80 for every edge',
   'claim': 'The STXM data were recorded on an 80 × 80 scan grid.'},
  {'sid': 'D3', 'rung': 'D', 'span': 'All tilt series of projection images were typically acquired between −64° and 72°, with a linear tilt step of 2°.', 'object': 'HAADF .rawtlt',
   'route': 'metadata', 'check': 'tilts -64..72 step 2', 'claim': 'The HAADF tilt series of this grain was acquired between −64° and 72° with a tilt step of 2°.'},
  {'sid': 'D3b', 'rung': 'D', 'span': 'Image size was 1024 × 1024 pixels with a pixel size of 4.67 nm.', 'object': 'HAADF .txt acquisition log', 'route': 'metadata',
   'check': 'pixel 4.67 nm', 'claim': 'The HAADF projection images have a pixel size of 4.67 nm.'},
  {'sid': 'D4', 'rung': 'D', 'span': 'Complete STXM-XAS image stacks using the above parameters were recorded at the Fe L3-edge (707 eV), Ni L2/3-edge (865/848 eV), Mg K-edge (1302 eV), and Al K-edge (1551 eV).',
   'object': 'Fe stack energy axis (header, nominal)', 'route': 'metadata', 'check': 'recorded Fe energy range contains 707 eV',
   'claim': 'The Fe STXM image stack was recorded across the Fe L3 edge at 707 eV.'},
  {'sid': 'M1', 'rung': 'M', 'span': S_DOM, 'object': 'EDS 0 deg sum spectrum', 'route': 'computation', 'check': 'each of Mg, Al, Cr, Fe, Ni, S net counts >= 5 sigma',
   'claim': 'The EDS data of the grain show iron, magnesium, aluminum, chromium, nickel and sulfur.'},
  {'sid': 'M2', 'rung': 'M', 'span': 'We observed no visible sample damage.', 'object': 'EDS 0 deg before (01) and after (21)', 'route': 'computation',
   'check': 'all major-line count-rate ratios within 0.97-1.03 (consistent); any outside 0.90-1.10 (contradicted)', 'claim': 'The grain showed no visible damage over the measurements.'},
  {'sid': 'M3', 'rung': 'M', 'span': None, 'template': 'probe', 'object': 'EDS 0 deg sum spectrum', 'route': 'computation', 'check': 'Ca net counts >= 5 sigma -> claim contradicted',
   'claim': 'The EDS sum spectrum shows no calcium above background.'},
  {'sid': 'A1', 'rung': 'A', 'span': S_DOM, 'object': 'regions_v2', 'route': 'computation', 'check': 'sulfide, Al-pocket and silicate regions each >= 8 bins',
   'claim': 'The EDS data separate three mineral domains: an iron-magnesium silicate, an aluminum-chromium iron oxide and an iron-nickel sulfide.'},
  {'sid': 'A2', 'rung': 'A', 'span': 'Since L3b has a higher peak intensity than L3a, we concluded that the Fe in the iron silicate was mostly in its reduced Fe2+ form.',
   'object': 'Fe L-edge silicate spectrum (fe_l3_features)', 'route': 'computation', 'check': 'L3b/L3a >= 1.2 consistent; <= 0.8 contradicted',
   'claim': 'In the Fe L-edge spectrum of the iron silicate, the L3b peak has a higher intensity than the L3a peak.'},
  {'sid': 'A3', 'rung': 'A', 'span': 'PCA returned two unique Fe spectra (Fig. 3J), whose spectral signatures closely match published reference spectra (60) of iron silicate (Fig. 3J, solid purple line) and iron sulfide (Fig. 3J, dashed yellow line).',
   'span_note': 'joined across the Fig. 3 caption that the text extraction inserts after "iron silicate"', 'object': 'Fe spectra of silicate and sulfide regions', 'route': 'computation',
   'check': 'L3b/L3a of the two regions differ by more than 3 combined bootstrap sigma -> consistent; otherwise dropped (two-route rule, B10b)', 'claim': 'The Fe L-edge spectra of the iron silicate and of the iron sulfide differ.'},
  {'sid': 'A4', 'rung': 'A', 'span': ('To obtain quantitative elemental compositions at subregions of the grain, mass fractions were quantified using the Cliff-Lorimer equation (43), '
                                      'I1/I2 = k*12 C1/C2, where Ii and Ci are the integrated peak intensities and mass fractions of the ith element, respectively, and k*12 is the '
                                      'thickness-corrected Cliff-Lorimer sensitivity factor ("k-factor") between elements 1 and 2.'),
   'span_note': 'equation garbled in the text extraction (II12 ¼ k*12 CC12); restored as printed in the article', 'object': 'EDS quantification', 'route': 'cannot tell',
   'check': 'k-factors and thickness correction absent from the deposit', 'claim': 'The mass fractions of the elements in subregions of the grain follow from its EDS peak intensities through the Cliff-Lorimer equation with thickness-corrected k-factors.'},
  {'sid': 'I1', 'rung': 'I', 'span': 'Together with the silicates, the proximity of these three mineral phases confirms the high-temperature nebular environment of the grain’s accreted components (54).',
   'object': 'none', 'route': 'cannot tell', 'check': 'origin not decidable from these data', 'claim': 'The proximity of the three mineral phases of this grain confirms a high-temperature nebular environment of its accreted components.'},
]
# ---------------------------------------------------------------- T5 signature pairs (textbook directions; audit pending)
SIGNATURES = {
  'fe2_dominant': {'mechanism': 'Fe in the silicate is mostly ferrous (Fe2+)', 'relation': 'Fe L3 edge: the lower-energy L3a peak dominates for Fe2+ (L3b/L3a < 1)', 'source': 'van Aken & Liebscher 2002; Bourdelle et al. 2013 (L3 peak ratio vs Fe3+/sum Fe)', 'prior_rank': 1,
                   'predicts': {'L3b_over_L3a(silicate vs 1)': 'down'}},
  'fe3_dominant': {'mechanism': 'Fe in the silicate is mostly ferric (Fe3+)', 'relation': 'Fe L3 edge: the higher-energy L3b peak dominates for Fe3+ (L3b/L3a > 1)', 'source': 'van Aken & Liebscher 2002', 'prior_rank': 2,
                   'predicts': {'L3b_over_L3a(silicate vs 1)': 'up'}},
  'pentlandite': {'mechanism': 'The Ni-bearing sulfide is pentlandite, (Fe,Ni)9S8', 'relation': 'Ni present in the sulfide with S', 'source': 'pentlandite stoichiometry', 'prior_rank': 1,
                  'predicts': {'Ni(sulfide vs silicate)': 'up', 'S(sulfide vs silicate)': 'up'}},
  'troilite': {'mechanism': 'The sulfide is troilite, FeS, without nickel', 'relation': 'S present, no Ni', 'source': 'troilite stoichiometry', 'prior_rank': 2,
               'predicts': {'Ni(sulfide vs silicate)': 'none', 'S(sulfide vs silicate)': 'up'}},
  'olivine': {'mechanism': 'The silicate is olivine, (Mg,Fe)2SiO4', 'relation': '(Mg+Fe)/Si = 2 (atomic)', 'source': 'olivine stoichiometry', 'prior_rank': 1,
              'predicts': {'MgFe_over_Si_atomic(silicate vs 1.5)': 'up'}},
  'pyroxene': {'mechanism': 'The silicate is pyroxene, (Mg,Fe)SiO3', 'relation': '(Mg+Fe)/Si = 1 (atomic)', 'source': 'pyroxene stoichiometry', 'prior_rank': 2,
               'predicts': {'MgFe_over_Si_atomic(silicate vs 1.5)': 'down'}},
}
SIGNATURE_PAIRS = [('fe2_dominant', 'fe3_dominant'), ('pentlandite', 'troilite'), ('olivine', 'pyroxene')]
ATOMIC_NEEDS_KFACTORS = {'MgFe_over_Si_atomic(silicate vs 1.5)'}   # D gap: no k-factors -> observation undecidable -> cannot tell
T6_FROM = {'pair': ('olivine', 'pyroxene'), 'options': [
  ('separates', 'measure the Mg, Fe and Si atomic ratio of the silicate core by EDS with calibrated k-factors and thickness correction'),
  ('agree', 'measure the Fe L3b/L3a peak ratio of the silicate (both minerals hold Fe2+)'),
  ('unconstrained', 'measure the Ni distribution in the sulfide'),
  ('shown', 'repeat the EDS Mg and Si net-count maps without calibration (already shown)')]}
# ---------------------------------------------------------------- T7 tilt-series path-length law (per tilt side), held-out extreme tilt
T7 = {'law': 'ln(Mg Ka / Si Ka) = a - b (1/cos(tilt) - 1): the softer Mg line is absorbed more along the longer path at higher tilt (Beer-Lambert, slab)',
      'class': 'fit', 'params': ['a', 'b'], 'model_err': 0.03, 'sides': {'negative': 'tilts < 0 (excluding 0)', 'positive': 'tilts > 0'},
      'holdout': 'each tilt in turn; kept by gates g1-g3; at most 2 per side'}
# ---------------------------------------------------------------- T1 reads
T1 = [{'id': 'fe_l3l2', 'what': 'Fe L3-L2 separation (silicate)', 'tol_eV': 0.6}, {'id': 'ni_l3l2', 'what': 'Ni L3-L2 separation (sulfide)', 'tol_eV': 0.6},
      {'id': 'fe_l3_recorded', 'what': 'recorded energy of the Fe L3 maximum (silicate spectrum, as on the axis)', 'tol_eV': 0.5},
      {'id': 'fe_l3b_l3a', 'what': 'L3b/L3a peak-height ratio of the silicate Fe spectrum after the pre-edge slope', 'tol_rel': 0.25},
      {'id': 'tilt0_mgsi', 'what': 'Mg Ka / Si Ka net-count ratio at 0 degrees (sum spectrum)', 'tol_rel': 0.15}]
