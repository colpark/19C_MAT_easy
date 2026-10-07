"""Tables 1-3 of Thakur, Ercole, Marzari (arXiv 2601.03151v1, pp 10-12), typed from the PDF text (pdftotext -layout).
Level A (author outputs): reconciliation targets and second-route references only, never keys (I2).
sigma in mS/cm, gap in eV (DFT-PBEsol), Ea in eV. Database ids as printed (S1614518 repeats: PI5)."""

TABLE1 = [  # FPMD at 1000 K: no diffusion
    ('Li2Te2O5', 'ICSD', '26451, 26452'), ('Li2CsCl3', 'MPDS', 'S1022277'), ('LiKSe', 'ICSD', '67277'),
    ('LiYS2', 'MPDS', 'S537670'), ('LiInSe2', 'MPDS', 'S1214509'), ('LiAlS2', 'ICSD', '608360'),
    ('LiLuS2', 'MPDS', 'S307222'), ('Li7Te3O9F', 'MPDS', 'S1533619'), ('Li5SiP3', 'MPDS', 'S1145472'),
    ('Li6RbBiO6', 'MPDS', 'S1408313'), ('LiAuF6', 'MPDS', 'S1904723'), ('Li3Na3Ga2F12', 'MPDS', 'S1836948'),
    ('LiZrS2', 'MPDS', 'S301115'), ('Li2CdSnSe4', 'MPDS', 'S1952801'), ('LiBa4Ga5Se12', 'MPDS', 'S1021504'),
    ('Li3Na3Rh2F12', 'MPDS', 'S307582'), ('Li2HgO2', 'MPDS', 'S1702887'), ('Li2Ca2Ta3O10', 'ICSD', '88497'),
]
# (formula, db, id, gap, sigma_pinball_1000K, sigma_FPMD_1000K, note)
TABLE2 = [
    ('Li2BeF4', 'MPDS', 'S1935520', 7.49, 10, 1822, ''), ('Li2Ti4O9', 'MPDS', 'S559372', 3.2, 1042, 1348, ''),
    ('LiY2Ti2S2O5', 'COD', '4124533', 1.25, 74, 1251, ''), ('Li10BrN3', 'MPDS', 'S1614518', 1.79, 4247, 886, ''),
    ('Li2Cs3Br5', 'ICSD', '245978', 3.79, 106, 594, ''), ('Li8SeN2', 'MPDS', 'S1931016', 1.88, 467, 588, ''),
    ('Li8TeN2', 'MPDS', 'S1931019', 2.28, 214, 446, ''), ('LiCF3SO3', 'ICSD', '110018', 6.78, 40, 384, ''),
    ('Li2ZnBr4', 'COD', '1517836', 3.75, 8, 357, ''), ('LiBeP', 'ICSD', '670551', 2.75, 18, 356, ''),
    ('Li5Br2N', 'ICSD', '78836', 2.29, 1351, 344, ''), ('Li10Si2PbO10', 'ICSD', '78326', 2.86, 29, 342, ''),
    ('Li2ZnGeSe4', 'COD', '7031897', 1.89, 63, 291, ''), ('LiCs2I3', 'ICSD', '245984', 3.41, 1410, 280, ''),
    ('LiSr2Br5', 'MPDS', 'S1941469', 3.53, 176, 263, ''), ('LiGaSe2', 'COD', '1531591', 2.23, 5, 173, ''),
    ('LiP7', 'ICSD', '23621', 1.56, 11, 133, ''), ('LiMoPO6', 'COD', '7701361', 2.52, 8, 132, ''),
    ('LiY(MoO4)2', 'COD', '1008103', 3.22, 660, 68, ''), ('Li10B14Cl2O25', 'MPDS', 'S1803375', 6.30, 13, 65, ''),
    ('Li2P2PdO7', 'COD', '1000333', 1.39, 513, 48, 'FPMD value at 600 K (**)'),
    ('Li2B3PO8', 'MPDS', 'S1614518', 5.49, 45, 41, ''), ('Li2B2Se5', 'COD', '1510746', 1.84, 84, 20, ''),
    ('Li8Bi2(MoO4)7', 'ICSD', '54021', 2.95, 7, 12, ''), ('Li3AuS2', 'COD', '4319430', 1.86, 895, 8, ''),
]
# (formula, db, id, gap, sigma_500K, sigma_750K, sigma_1000K, Ea)
TABLE3 = [
    ('Li4CO4', 'ICSD', '245389', 5.26, 235, 551, 726, 0.15), ('LiCsI2', 'ICSD', '245986', 3.32, 203, 340, 698, 0.16),
    ('Li3CsBr4', 'ICSD', '245982', 3.73, 456, 1035, 1616, 0.17), ('Li3Cs2Br5', 'ICSD', '245980', 3.90, 181, 358, 844, 0.18),
    ('Li7NbO6', 'MPDS', 'S1818764', 3.58, 77, 288, 418, 0.21), ('Li3Cs2I5', 'ICSD', '245987', 3.43, 161, 554, 1112, 0.23),
    ('LiCs3Cl4', 'ICSD', '245969', 4.38, 35, 112, 283, 0.23), ('Li4Mo3O8', 'MPDS', 'S1614518', 1.17, 6, 32, 54, 0.25),
    ('Li5NaN2', 'ICSD', '92313', 1.49, 279, 1268, 3609, 0.28),
]


def reduced(f):
    from pymatgen.core import Composition
    return Composition(f).reduced_formula


def by_formula():
    out = {}
    for f, db, i in TABLE1:
        out[reduced(f)] = {'table': 1, 'class': 'no_diffusion', 'printed': f, 'db': db, 'id': i}
    for f, db, i, g, sp, sf, note in TABLE2:
        out[reduced(f)] = {'table': 2, 'class': 'high_T_only', 'printed': f, 'db': db, 'id': i, 'gap': g,
                           'sigma_pinball_1000': sp, 'sigma_fpmd_1000': sf, 'note': note}
    for f, db, i, g, s5, s7, s10, ea in TABLE3:
        out[reduced(f)] = {'table': 3, 'class': 'fast', 'printed': f, 'db': db, 'id': i, 'gap': g,
                           'sigma_fpmd_500': s5, 'sigma_fpmd_750': s7, 'sigma_fpmd_1000': s10, 'Ea': ea}
    return out
