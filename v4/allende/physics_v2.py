# Allende physics table v2 (v4 Track B rebuild from the claim ladder, v4/notes/20261006_allende_claim_ladder_stitching.md). Frozen (B10) before
# any key or decidability is computed. Keys come from our frozen procedures on the raw deposit (eds.py B1, stxm.py B2-B3, register.py B4,
# derived.py B9: derived-observable procedures, skill M2). Every item is audit_pending until a raw-data audit runs under an approved quote
# (Q1 used the paper-centric tag prompt; its verdicts on our own procedures are superseded only by that re-audit, not here).
#
# Claim ladder: rung (D, M, A, I), verbatim span, data object, verification route, decision rule.
CLAIMS = [
  # D: acquisition metadata (route: header check). Panel: a rendered acquisition record (header fields as printed in the deposit).
  {'sid': 'D1', 'rung': 'D', 'span': 'a dwell time of 10 ms', 'object': 'STXM headers (4 edges)', 'route': 'metadata', 'check': 'dwell_ms == 10 for every edge',
   'claim': 'Every STXM stack was recorded with a 10 ms dwell time.'},
  {'sid': 'D2', 'rung': 'D', 'span': '80 × 80 pixels', 'object': 'STXM headers', 'route': 'metadata', 'check': 'grid == 80 x 80 for every edge',
   'claim': 'Every STXM stack was recorded on an 80 x 80 pixel grid.'},
  {'sid': 'D3', 'rung': 'D', 'span': 'Image pixel size [nm]: 4.67', 'object': 'HAADF .txt log and .rawtlt', 'route': 'metadata', 'check': 'tilts -64..72 step 2 and pixel 4.67 nm',
   'claim': 'The HAADF tilt series runs from -64 to +72 degrees in 2 degree steps at 4.67 nm per pixel.'},
  {'sid': 'D4', 'rung': 'D', 'span': 'Fe L3 edge', 'object': 'Fe stack energy axis', 'route': 'cannot tell', 'check': 'absolute energy needs a calibration the deposit does not record',
   'claim': 'The Fe L3 absorption maximum of the grain lies at 707 eV.'},
  # M: instrument-level observations (route: our computation on raw files)
  {'sid': 'M1', 'rung': 'M', 'span': 'EDS', 'object': 'EDS 0 deg sum spectrum', 'route': 'computation', 'check': 'each of Mg, Al, Si, S, Cr, Fe, Ni net counts >= 5 sigma',
   'claim': 'The EDS sum spectrum shows Mg, Al, Si, S, Cr, Fe and Ni above background.'},
  {'sid': 'M2', 'rung': 'M', 'span': 'no visible damage', 'object': 'EDS 0 deg before (01) and after (21)', 'route': 'computation', 'check': 'all major-line count-rate ratios within 0.97-1.03 (consistent); any outside 0.90-1.10 (contradicted)',
   'claim': 'The EDS count rates of the major elements at 0 degrees are unchanged (within 3 %) between the first and the last acquisition of the tilt series.'},
  {'sid': 'M3', 'rung': 'M', 'span': None, 'template': 'probe', 'object': 'EDS 0 deg sum spectrum', 'route': 'computation', 'check': 'Ca net counts >= 5 sigma -> claim contradicted',
   'claim': 'The EDS sum spectrum shows no calcium above background.'},
  # A: author analyses re-done by our procedures
  {'sid': 'A1', 'rung': 'A', 'span': 'three domains', 'object': 'regions_v2', 'route': 'computation', 'check': 'sulfide, Al-pocket and silicate regions each >= 8 bins',
   'claim': 'The EDS maps separate three chemical domains: an Fe-Mg silicate, an Al-rich domain and an Fe-Ni sulfide.'},
  {'sid': 'A2', 'rung': 'A', 'span': 'Since L3b has a higher peak intensity than L3a', 'object': 'Fe L-edge silicate spectrum (fe_l3_features)', 'route': 'computation',
   'check': 'L3b/L3a >= 1.2 consistent; <= 0.8 contradicted', 'claim': 'In the silicate Fe L-edge spectrum, the L3b peak is more intense than the L3a peak.'},
  {'sid': 'A3', 'rung': 'A', 'span': 'two unique Fe spectra', 'object': 'Fe spectra of silicate and sulfide regions', 'route': 'computation',
   'check': 'L3b/L3a of the two regions differ by more than 3 combined bootstrap sigma -> consistent; otherwise dropped (one feature cannot carry a contradiction: two-route rule, B10b)', 'claim': 'The Fe L-edge spectra of the silicate and of the sulfide region differ in shape.'},
  {'sid': 'A4', 'rung': 'A', 'span': 'Cliff-Lorimer', 'object': 'EDS quantification', 'route': 'cannot tell', 'check': 'k-factors and thickness correction absent from the deposit',
   'claim': 'The sulfide contains 28 at% Fe, 22 at% Ni and 50 at% S.'},
  # I: interpretations -> T5 hypotheses (and untestable claims -> cannot tell)
  {'sid': 'I1', 'rung': 'I', 'span': 'nebular', 'object': 'none', 'route': 'cannot tell', 'check': 'origin not decidable from these data', 'claim': 'The phase assemblage of this grain formed at high temperature in the solar nebula.'},
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
