# physics_htem.py (Track H, H6): physics table for the HTEM pilot systems, pre-registered and frozen (H6phys) before any key is computed.
# Skill M1/M3 audit fields: law class, inputs, target, constants with sources, model error, mode. Judgments carry a named default or a source.
# The table is per system; the generator reads it by system key (P2 transfer: table and config changes only).

LAWS = {
    'N-Sn-Zn': {
        'phase_id': {'class': 'independent', 'inputs': 'measured XRD peak centres (S4hx)', 'target': 'phase present at a position',
                     'constants': 'refs/sticks.json at 1.5418 A (COD and constructed references, REF_PHASES.json)', 'model_err_deg': 0.3,
                     'mode': 'match score >= 0.6 of the strongest 3 sticks within 0.3 deg (match_phase)', 'audit': 'pending (no paid call this round)',
                     'note': 'ZnSnN2 reference is constructed from a CALCULATED lattice (~1 %): identification only, never a value key'},
        'vegard': None,          # no measured end members sharing one structure with sourced lattice constants (D gap): no T3 inference
        'eg_fit': None,          # optical reader failed (VH-E05)
        'monotone': None,        # no observable passed separability in H5
        'signatures': None,      # T5/T6: expect none (no competing-mechanism pair decidable from XRD + Rs on one film without a model)
    },
    'Mn-Se-Te-Zn': {
        'phase_id': {'class': 'independent', 'inputs': 'measured XRD peak centres (S4hx)', 'target': 'phase present at a position',
                     'constants': 'refs/sticks.json (COD 9008857 ZnSe, 9008858 ZnTe, 9008676 / 9008855 MnSe, 1537607 MnTe, 9008579 Se, 2020222 Te)',
                     'model_err_deg': 0.3, 'mode': 'as for N-Sn-Zn', 'audit': 'pending'},
        'vegard': {'class': 'independent', 'formula': 'a(y) = (1 - y) a_ZnSe + y a_ZnTe, y = Te / (Se + Te) atomic (XRF, M); (111) 2theta from d = a / sqrt(3) at 1.5418 A',
                   'inputs': 'XRF anion fraction y at the position (M)', 'target': 'zinc-blende (111) peak centre (S4hx, M derived)',
                   'constants': {'a_ZnSe': [5.6676, 'COD 9008857'], 'a_ZnTe': [6.089, 'COD 9008858']},
                   'validity': 'Zn-rich films only: Zn / (Zn + Mn) >= 0.80 (Mn alloying also shifts the lattice; MnTe has no zinc-blende COD reference); the hidden cell must be matched to the zinc-blende (111) within the window 24.5-28.0 deg',
                   'model_err_rel_a': 0.005, 'model_err_source': 'named default: 0.5 % for film strain and composition error (the H3 ZnO check showed -0.46 % strain)',
                   'mode': 'ranking (two positions) and value (2theta) with tolerance sqrt((2 u_model)^2 + (2 u_replicate)^2), u_replicate = 0.069 deg (H4 P2 replicate route)',
                   'audit': 'pending'},
        'eg_fit': None, 'monotone': None, 'signatures': None,
    },
}
# T7 (fit) candidates: a 2-parameter linear fit of the (111) centre against y on one library, holding out a contiguous block (never an
# interior neighbour), gated by g1-g4 with the band from reading error (center_err) propagated through the fit. Pre-registered here;
# built only if g1-g4 pass.
T7 = {'Mn-Se-Te-Zn': {'law': 'vegard as a fit (intercept, slope) on 2theta(111) vs y', 'holdout': 'the 11 positions of one grid column at the y extreme (end block)',
                      'min_fit_cells': 5}, 'N-Sn-Zn': None}
REPLICATE_SPREAD_DEG = {'N-Sn-Zn': 0.060, 'Mn-Se-Te-Zn': 0.069}   # H4 replicate route (median |dpeak|), the floor of any peak comparison tolerance
