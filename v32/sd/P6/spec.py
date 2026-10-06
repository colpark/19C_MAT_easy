# P6: Co-doped SrIrO3 (SrIr(x)Co(1-x)O3) catalysts for acidic oxygen evolution. Nature Communications (2024), doi 10.1038/s41467-024-46801-y, CC BY 4.0.
# Source Data: 41467_2024_46801_MOESM3_ESM.xlsx. Condition series: Co doping SI1C1, SI2C1, SI4C1, SI6C1, SI8C1 and undoped SI.
# Instruments: XRD (Fig. 1g, h), ICP-MS (Fig. 1i), HRTEM/HAADF/EELS (Fig. 1b-f), OER polarization (Fig. 2a), Tafel (Fig. 2b), PEM electrolyser (Fig. 2f).
# Levels: polarization current density (iR-corrected), ICP-MS Co:Ir and Sr:Ir ratios: M. Overpotential at 10 mA/cm2, Tafel slope, mass activity: A.
# Text vs Source Data (logged, not a key): the text states 245 mV for SI6C1 at 10 mA/cm2; the plotted bar (sheet Figure 2c) is 251 mV
# (3.75 tolerance bands: below the rule-1 threshold of 5, so no contradiction claim is made).
import numpy as np
ARTICLE = 's41467-024-46801-y'; FIGPREFIX = '41467_2024_46801'; DOI = '10.1038/s41467-024-46801-y'; JOURNAL = 'Nature Communications'; YEAR = 2024
SER = ['SI1C1', 'SI2C1', 'SI4C1', 'SI6C1', 'SI8C1', 'SI']
SAMP = 'SrIrO3 catalysts doped with increasing amounts of Co (SI1C1, SI2C1, SI4C1, SI6C1, SI8C1) and undoped SrIrO3 (SI)'
lab = lambda s: f'the {s} catalyst'
def e_at_10(curve):
    xs = np.array([a for a, _ in curve]); js = np.array([b for _, b in curve]); i = np.nonzero(js >= 10.0)[0]
    if not len(i) or i[0] == 0: return None
    k = i[0]; e = xs[k - 1] + (10.0 - js[k - 1]) * (xs[k] - xs[k - 1]) / (js[k] - js[k - 1]); return (e - 1.23) * 1000.0
PANELS = [
    dict(id='F2a', figure=2, box=[0, 0, 670, 540], layout='blocks', sheet='Figure 2a', col0=0, stride=2, nseries=6, series_row=1, data_row=2, xoff=0, yoff=1,
         quantity='j', qname='current density', unit='mA cm^-2', unit_text='mA/cm^2', scale=1.0, level='M', y_ticks=[0, 20, 40, 60, 80, 100], x_ticks=[1.3, 1.4, 1.5],
         res=0.1, xname='E - iR', xunit='V vs RHE', t1_at=[1.50, 1.52], context=f'The panel plots iR-corrected OER polarization curves (current density against E - iR vs RHE) of {SAMP}.',
         series_label=lab, desc='OER polarization curves (current density versus iR-corrected potential)', t1_n=4),
    dict(id='F1i-Co', figure=1, box=[1519, 1272, 2052, 1868], layout='cells', sheet='Figure 1i', cells=[(n, None, 3 + i, 2) for i, n in enumerate(SER)],
         quantity='CoIr', qname='Co/Ir ratio (ICP-MS)', unit='1', unit_text='(dimensionless)', scale=1.0, level='M', y_ticks=[0.0, 0.02, 0.04, 0.06, 0.08, 0.10], res=0.001,
         context=f'The panel plots the Co/Ir ratio (left axis) and the Sr/Ir ratio (right axis) measured by ICP-MS for {SAMP}.', series_label=lab,
         desc='Co/Ir (left axis) and Sr/Ir (right axis) ratios from ICP-MS', t1_n=3),
    dict(id='F1i-Sr', figure=1, box=[1519, 1272, 2052, 1868], layout='cells', sheet='Figure 1i', cells=[(n, None, 3 + i, 4) for i, n in enumerate(SER)],
         quantity='SrIr', qname='Sr/Ir ratio (ICP-MS)', unit='1', unit_text='(dimensionless)', scale=1.0, level='M', y_ticks=[0.2, 0.4, 0.6, 0.8, 1.0, 1.2], res=0.01,
         context=f'The panel plots the Co/Ir ratio (left axis) and the Sr/Ir ratio (right axis) measured by ICP-MS for {SAMP}.', series_label=lab,
         desc='Co/Ir (left axis) and Sr/Ir (right axis) ratios from ICP-MS', t1_n=3),
    dict(id='F2c', figure=2, box=[1353, 0, 2050, 540], layout='cells', sheet='Figure 2c', cells=[(n, None, 2 + i, 2) for i, n in enumerate(SER)],
         quantity='eta', qname='overpotential at 10 mA/cm2', unit='mV', unit_text='mV', scale=1.0, level='A', y_ticks=[220, 240, 260, 280, 300], res=1,
         context=f'The bar chart shows the overpotential at 10 mA/cm2 (left axis, solid bars) and the Tafel slope (right axis, hatched bars) of {SAMP}.',
         series_label=lab, desc='overpotential at 10 mA/cm2 (left axis) and Tafel slope (right axis) bars', no_t1=True, no_t4=True, xname=None, xunit=''),
]
RECOMPUTE = [
    dict(id='p6_eta', target='F2c', curve='F2a', fcurve=e_at_10, input_band=lambda T: 0.02 * 0.4 * 1000.0, max=3, inputs={},
         ftext='(E - iR at 10 mA/cm2) - 1.23 V', intext='iR-corrected polarization curve',
         span='overpotential of only 245 mV to reach a current density of 10 mA/cm2 (with the named default E0(O2/H2O) = 1.23 V vs RHE)'),
]
EXCLUDED_PANELS = {}
CROSS_CHECK = {'F2a': 'agree (overlay: Source Data curves trace the plotted curves)', 'F1i-Co': 'agree by value inspection (0.079, 0.080, 0.059, 0.053, 0.043, 0)',
               'F1i-Sr': 'agree by value inspection (0.22, 0.23, 0.33, 0.63, 0.72, 1.06)', 'F2c': 'agree (bar heights; recompute from Fig. 2a reproduces every bar within 0.2 bands)'}
