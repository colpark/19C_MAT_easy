# P2: Bi2Te3 thick films for micro-thermoelectric coolers. Nature Communications (2024), doi 10.1038/s41467-024-48346-6, CC BY 4.0.
# Source Data: 41467_2024_48346_MOESM5_ESM.xlsx. Panel boxes are pixels of the published full-size figure PNGs (FIGPREFIX_FigN_HTML.png).
# Levels: sigma, S, kappa (laser flash), Te content (EDS), compressive stress: M; PF = S^2 sigma, kappa - kappa_e, ZT: A (author-derived).
ARTICLE = 's41467-024-48346-6'; FIGPREFIX = '41467_2024_48346'; DOI = '10.1038/s41467-024-48346-6'; JOURNAL = 'Nature Communications'; YEAR = 2024
SAMPLES = 'Bi2Te3 thick films annealed at different temperature-time settings (labelled annealing temperature in C - annealing time in min: 360-90, 400-90, 440-90, 450-90, 440-70, 440-110)'
CTX = f'The panel plots a property of {SAMPLES} against temperature.'
lab = lambda s: f'the {s} film'
X_T = [320, 360, 400, 440]   # detected major ticks inside the frame (280 and 480 sit on the frame edges)
def F3(pid, k, quantity, qname, unit, unit_text, scale, level, yt, res, desc, **kw):
    box = {'a': [0, 0, 655, 525], 'b': [655, 0, 1330, 525], 'c': [1330, 0, 2000, 525], 'd': [0, 525, 655, 1114], 'e': [655, 525, 1330, 1114], 'f': [1330, 525, 2000, 1114]}[pid[-1]]
    return dict(id=pid, figure=3, box=box, layout='blocks', sheet='Figure 3', col0=24 * k, stride=4, nseries=6, series_row=1, data_row=3, xoff=0, yoff=1,
                quantity=quantity, qname=qname, unit=unit, unit_text=unit_text, scale=scale, level=level, x_ticks=X_T, y_ticks=yt, res=res,
                xname='T', xunit='K', context=CTX, series_label=lab, desc=desc, t1_n=4, **kw)
PANELS = [
    F3('F3a', 0, 'sigma', 'electrical conductivity', '1e4 S m^-1', '10^4 S m^-1', 1e-4, 'M', [6, 8, 10, 12, 14, 16, 18, 20, 22], 0.1, 'electrical conductivity versus temperature (six annealing conditions)'),
    F3('F3b', 1, 'S', 'Seebeck coefficient', 'uV K^-1', 'uV K^-1', 1.0, 'M', [-220, -200, -180, -160, -140, -120, -100], 1.0, 'Seebeck coefficient versus temperature'),
    F3('F3c', 2, 'PF', 'power factor', 'uW cm^-1 K^-2', 'uW cm^-1 K^-2', 1.0, 'A', [15, 20, 25, 30, 35, 40], 0.1, 'power factor versus temperature'),
    F3('F3d', 3, 'kappa', 'total thermal conductivity', 'W m^-1 K^-1', 'W m^-1 K^-1', 1.0, 'M', [1.20, 1.25, 1.30, 1.35, 1.40, 1.45, 1.50, 1.55, 1.60], 0.01, 'total thermal conductivity versus temperature'),
    F3('F3e', 4, 'kappa_L', 'lattice-plus-bipolar thermal conductivity (kappa - kappa_e)', 'W m^-1 K^-1', 'W m^-1 K^-1', 1.0, 'A', [0.2, 0.4, 0.6, 0.8, 1.0, 1.2], 0.01, 'kappa - kappa_e versus temperature'),
    F3('F3f', 5, 'ZT', 'figure of merit ZT', '1', '(dimensionless)', 1.0, 'A', [0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0], 0.01, 'figure of merit ZT versus temperature'),
    dict(id='F2c', figure=2, box=[0, 580, 640, 1060], layout='cells', sheet='Figure 2b-e', cells=[(s, None, r, 7) for s, r in (('360-90', 3), ('400-90', 4), ('450-90', 5), ('440-70', 6), ('440-90', 7), ('440-110', 8))],
         quantity='Te', qname='Te content', unit='%', unit_text='%', scale=1.0, level='M', y_ticks=[57, 58, 59, 60, 61], res=0.01, xname=None, xunit='',
         context=f'The bar chart shows the Te content (EDS) of {SAMPLES}.', series_label=lab, desc='Te content of the films (bar chart)', t1_n=3, no_t4=False, text_recoverable=True),
]
RECOMPUTE = [
    dict(id='p2_pf', target='F3c', inputs={'S': 'F3b', 'sigma': 'F3a'}, f=lambda v, T: v['S'] ** 2 * v['sigma'] * 1e-4, ftext='S^2 sigma',
         intext='Seebeck coefficient and electrical conductivity values', span='TE thick films have high performance in power factor (PF = S2σ)', max=2),
    dict(id='p2_zt', target='F3f', inputs={'S': 'F3b', 'sigma': 'F3a', 'kappa': 'F3d'}, f=lambda v, T: v['S'] ** 2 * v['sigma'] * 1e-8 * T / v['kappa'], ftext='S^2 sigma T / kappa',
         intext='Seebeck coefficient, electrical conductivity and total thermal conductivity values', span='figure of merit (ZT = S2σT/κ', max=2),
]
EXCLUDED_PANELS = {'F3e': 'Source Data sheet (labelled lattice thermal conductivity) disagrees with the plotted kappa - kappa_e beyond 3u: e.g. 440-70 at 300 K sheet 0.466 vs plotted ~0.93; 450-90 sheet 1.053 vs plotted ~0.29'}
CROSS_CHECK = {'F3a': 'agree (overlay on markers)', 'F3c': 'agree (overlay)', 'F3f': 'agree (overlay)', 'F2c': 'agree (bar labels and overlay)',
               'F3b': 'agree (sheet values vs plotted markers by inspection; overlay calibration mis-assigned the inverted axis ticks)',
               'F3d': 'agree (by inspection; overlay calibration dropped an edge tick)', 'F3e': 'DISAGREES beyond 3u: excluded'}
