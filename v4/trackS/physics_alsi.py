# AlSi10Mg pilot S1b physics table (pre-registered; frozen as S4d-phys before any per-set value is computed by our readers).
# Level tags: M = our reader on raw images / instrument stress; A = author-derived.
LAWS = {
  'cell_vs_LED': {'class': 'fit', 'formula': 'd_cell = a * (P/v)^n', 'params': ['a', 'n'], 'x': 'LED = P/v (J/mm, design record D)', 'y': 'mean cell spacing per set (reader S4d, M)',
                  'note': 'cooling-rate proxy: larger P/v -> slower cooling -> coarser cells (n > 0 expected); fit on sets, hold out sets for T7 only if R7 passes (it does not: fields chosen)'},
  'yield_vs_cell': {'class': 'fit', 'formula': 'sigma_y = sigma0 + k * d_cell^(-1/2)', 'params': ['sigma0', 'k'], 'x': 'mean cell spacing per set (S4d, M)', 'y': 'yield per set (S4e on author DIC strain: level A)',
                    'usable': 'T4 only (yield is A)'},
  'uts_vs_cell': {'class': 'fit', 'formula': 'UTS = u0 + ku * d_cell^(-1/2)', 'params': ['u0', 'ku'], 'x': 'mean cell spacing per set (S4d, M)', 'y': 'maximum engineering stress per specimen (M)',
                  'note': 'added at pre-registration because yield is A (strain from author DIC); same form as yield_vs_cell'},
  'xct_vs_archimedes': {'class': 'agreement', 'formula': 'porosity_XCT == porosity_Archimedes', 'x': 'Archimedes porosity (author table, A)', 'y': 'XCT porosity (author segmentation, A)',
                        'usable': 'T4 only (both sides A)'},
}
CONDITIONS = 'processing parameter sets 1-32 (small hatch group, h = 0.1 mm), ordered by P/v (LED)'
