# P4: puff-pastry-inspired architected cementitious material (PPAC). Nature Communications (2026), doi 10.1038/s41467-026-77120-z, CC BY 4.0.
# Source Data: 41467_2026_77120_MOESM7_ESM.xlsx. Condition series: Cast, Fold-3, Fold-5, Fold-7. Instruments: SEM (Fig. 1, 4), density, 3-point
# bending and SENB (Fig. 2), IR camera flame test (Fig. 3a-d), thermal conductivity (Fig. 3e).
# Levels: density, thermal conductivity, backside temperature: M. Strain at failure (6 delta W / L^2), specific MOR, specific K_IC/K_JC and
# flexural toughness are computed from the load-displacement records and divided by density: A (no keys; no recompute binding, the
# specimen dimensions are not on the panels). Fig. 3e's middle bar is a literature value (lightweight concrete, refs 52-55): not keyed.
ARTICLE = 's41467-026-77120-z'; FIGPREFIX = '41467_2026_77120'; DOI = '10.1038/s41467-026-77120-z'; JOURNAL = 'Nature Communications'; YEAR = 2026
SAMP = 'cementitious specimens made by casting (Cast) or by folding a coated cement sheet 3, 5 or 7 times (Fold-3, Fold-5, Fold-7)'
lab = lambda s: f'the {s} specimen'
PANELS = [
    dict(id='F2c', figure=2, box=[1290, 0, 1660, 600], layout='cells', sheet='Fig.2 c', cells=[(n, None, r, 4) for n, r in (('Cast', 3), ('Fold-3', 4), ('Fold-5', 5), ('Fold-7', 6))],
         quantity='rho', qname='density', unit='g cm^-3', unit_text='g/cm^3', scale=1.0, level='M', y_ticks=[1.0, 1.5, 2.0, 2.5], res=0.01,
         context=f'The bar chart shows the density (mean of three specimens, with standard deviation) of {SAMP}.', series_label=lab, desc='density bar chart', t1_n=3),
    dict(id='F3e', figure=3, box=[1700, 560, 1998, 1100], layout='cells', sheet='Fig. 3 e', cells=[(n, None, r, 4) for n, r in (('Cast', 3), ('Fold-7', 5))],
         quantity='kappa', qname='thermal conductivity', unit='W m^-1 K^-1', unit_text='W/(m K)', scale=1.0, level='M', y_ticks=[0.0, 0.5, 1.0, 1.5], res=0.01,
         context=f'The bar chart shows the thermal conductivity of {SAMP} (Cast and Fold-7 shown) together with a literature value for lightweight concrete.',
         series_label=lab, desc='thermal conductivity bar chart (Cast, literature lightweight concrete, Fold-7)', t1_n=2),
    dict(id='F3b', figure=3, box=[1220, 0, 1998, 560], layout='cells', sheet='Fig.3 b', cells=[(n, 'col0', r, c) for n, c in (('Cast', 1), ('Fold-7', 2)) for r in range(3, 11)],
         quantity='T_back', qname='backside temperature', unit='C', unit_text='degC', scale=1.0, level='M', y_ticks=[20, 30, 40, 50, 60, 70, 80, 90, 100],
         x_ticks=[0, 5, 10, 15, 20], res=0.1, xname='heating time', xunit='min',
         context='The panel plots the backside temperature of a Cast and a Fold-7 cementitious specimen against heating time while the front face is heated by a flame.',
         series_label=lab, desc='backside temperature versus heating time (flame test)', t1_n=4),
    dict(id='F2b', figure=2, box=[903, 0, 1300, 600], layout='cells', sheet='Fig. 2 b', cells=[], quantity='eps_f', qname='strain at failure', unit='%', unit_text='%',
         level='A', y_ticks=[0, 0.4], res=0.001, context='', desc='strain at failure bar chart', no_t1=True, no_t4=True),
]
RECOMPUTE = []
EXCLUDED_PANELS = {}
CROSS_CHECK = {'F2c': 'agree by value inspection (bars 2.02, 1.99, 1.81, 1.67 g/cm3 = sheet means); overlay calibration failed',
               'F3e': 'agree by value inspection (Cast 1.20, Fold-7 0.38 W/mK)', 'F3b': 'agree (sheet = values printed in the Fig. 3c/d thermal images and the text: 94.4, 78.1, 52.5 C)'}
