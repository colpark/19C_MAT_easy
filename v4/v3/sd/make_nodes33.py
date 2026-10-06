#!/usr/bin/env python3
"""sd/make_nodes33.py (v3.3 A3.1): builder provenance nodes for P2-P6, one node per panel (keyed panels and the A4 candidate panels).
Each node: panel, quantity, computed_from, instrument, formula, level (D/M/A/S/I), evidence {kind: span | default, text}.
A span must occur verbatim (after ligature and whitespace normalisation) in the paper text on the host (v33_host/text/<article>.txt);
the script refuses to write a node whose span is missing. Levels follow definition 2 (F9): M = instrument output per sample and
condition, incl. specimen means reported by the test, iR-corrected current density, ICP-MS ratios, and standard instrument equations on
unplotted readings; A = computed from another plotted quantity, fits, integrals, normalisations, Tafel slopes, overpotentials, mass
activities, orientation factors, image statistics, literature values (I for literature). The blind Sol tag audit (audit33.py tags) follows;
on disagreement the more restrictive level wins.
usage: make_nodes33.py [P ...] -> sd/<P>/nodes.json"""
import json, os, re, sys
import sys as _pb_s, os as _pb_o
_pb_d = _pb_o.path.dirname(_pb_o.path.abspath(__file__))
while not _pb_o.path.exists(_pb_o.path.join(_pb_d, 'pbroot.py')) and _pb_o.path.dirname(_pb_d) != _pb_d: _pb_d = _pb_o.path.dirname(_pb_d)
_pb_s.path.insert(0, _pb_d)
from pbroot import ROOT, HOST

ART = {'P2': 's41467-024-48346-6', 'P3': 's41467-025-60705-5', 'P4': 's41467-026-77120-z', 'P5': 's41467-025-65917-3', 'P6': 's41467-024-46801-y'}

def norm(s):
    s = s.replace('ﬁ', 'fi').replace('ﬂ', 'fl').replace('ﬀ', 'ff').replace('‐', '-').replace('−', '-')
    s = re.sub(r'-\s*\n\s*', '', s)   # hyphenated line breaks
    return re.sub(r'\s+', ' ', s).strip().lower()

def N(panel, quantity, level, ev, computed_from=(), instrument=None, formula=None, default=False, note=None):
    n = {'id': panel, 'panel': panel, 'quantity': quantity, 'computed_from': list(computed_from), 'instrument': instrument, 'formula': formula,
         'level': level, 'evidence': {'kind': 'default' if default else 'span', 'text': ev}}
    if note: n['note'] = note
    return n

CTA = 'The in-plane electrical conductivity and Seebeck coefficient were simultaneously measured in a helium atmosphere from 300 to 460 K using a TE testing system (CTA-3S'
NODES = {
 'P2': [
    N('F3a', 'electrical conductivity sigma(T)', 'M', CTA, instrument='CTA-3S'),
    N('F3b', 'Seebeck coefficient S(T)', 'M', CTA, instrument='CTA-3S'),
    N('F3c', 'power factor PF(T)', 'A', 'TE thick films have high performance in power factor (PF = S2σ)', ['F3a', 'F3b'], formula='PF = S^2 sigma'),
    N('F3d', 'total thermal conductivity kappa(T)', 'M', 'the D was measured by the laser flash method (LFA-467, NETZSCH), and the typical Cp values of 159 J',
      ['D (laser flash, not plotted)', 'rho (mass and geometry, constant 7.54 g/cm3)', 'Cp (typical constant)'], instrument='LFA-467 laser flash', formula='kappa = rho D Cp',
      note='standard instrument equation on an unplotted reading (D) times constants: M under definition 2'),
    N('F3e', 'kappa - kappa_e (lattice plus bipolar)', 'A', 'Based on the electrical conductivity and Seebeck coefficient, the electronic thermal conductivity was calculated as shown in Supplementary Fig. 4.',
      ['F3d', 'F3a', 'F3b', 'L(S) relation of Supplementary Fig. 4 (not on the host)'], formula='kappa - L(S) sigma T',
      note='L(S) relation in Supplementary Fig. 4 (SI not on the host; the Source Data sheet "Supplementary Figure 4" lists L(T) per film). Panel excluded (sheet disagrees with figure).'),
    N('F3f', 'figure of merit ZT(T)', 'A', 'figure of merit (ZT = S2σT/κ', ['F3a', 'F3b', 'F3d'], formula='ZT = S^2 sigma T / kappa'),
    N('F2c', 'Te content (EDS)', 'M', 'The element content and crystal structure were analyzed by EDS (X-act SDD, Oxford Instruments)', instrument='EDS'),
    N('F2b', 'compressive stress-strain curves (bulk molded vs zone melted)', 'M', 'the compressive strain-stress curves of these Bi2Te3 samples were measured by an electro-mechanical universal testing machine',
      instrument='RGM-6300 universal testing machine', note='representative curves (definition 3)'),
 ],
 'P3': [
    N('F3b', 'lateral resistivity rho(f)', 'M', 'The resistivity of the device under dark conditions was recorded by a Keithley 4200 source meter.', instrument='Keithley 4200'),
    N('F3c', 'vertical resistivity rho(f)', 'M', 'The resistivity of the device under dark conditions was recorded by a Keithley 4200 source meter.', instrument='Keithley 4200'),
    N('F3d', 'lateral resistivity near threshold (data points)', 'M', 'The resistivity of the device under dark conditions was recorded by a Keithley 4200 source meter.', instrument='Keithley 4200',
      note='the sheet\'s "fitting curve" columns are the authors\' percolation fit: A, never read'),
    N('F3e', 'vertical resistivity near threshold (data points)', 'M', 'The resistivity of the device under dark conditions was recorded by a Keithley 4200 source meter.', instrument='Keithley 4200',
      note='the sheet\'s "fitting curve" columns are the authors\' percolation fit: A, never read'),
    N('F2c', 'nanoindentation load-depth curves', 'M', 'The hardness and modulus of the membranes were probed by the nanoindentation measurement (Bruker Hysitron TI 950)',
      instrument='Bruker Hysitron TI 950', note='representative curves'),
    N('F2d-hardness', 'nanoindentation hardness H', 'A', 'The Young’s modulus (E) and hardness (H) values were then derived from load (P)–displacement (h) curves following the Oliver-Pharr method',
      ['F2c'], formula='Oliver-Pharr', note='settled: derived from the plotted load-depth curves of Fig. 2c -> A (v3.2 had M)'),
    N('F2d-modulus', "Young's modulus E (nanoindentation)", 'A', 'The Young’s modulus (E) and hardness (H) values were then derived from load (P)–displacement (h) curves following the Oliver-Pharr method',
      ['F2c'], formula='Oliver-Pharr', note='settled: derived from the plotted load-depth curves of Fig. 2c -> A (v3.2 had M)'),
    N('F2b', 'tensile stress-strain curve (composite)', 'M', 'Representative stress–strain curves obtained from the tensile test in Fig. 2b', instrument='LGD500 universal testing machine'),
    N('F2f', 'XRD patterns under strain (perovskite)', 'M', 'XRD patterns of (f) perovskite membranes and (g) composite membranes under applied strain', instrument='XRD'),
    N('F2g', 'XRD patterns under strain (composite)', 'M', 'XRD patterns of (f) perovskite membranes and (g) composite membranes under applied strain', instrument='XRD'),
    N('F2h', '(100) peak position 2theta versus strain', 'A', 'XRD peaks of (100) plane as a function of applied strain. Error bars represent SD.', ['F2f', 'F2g'],
      formula='peak position of the (100) reflection', note='peak positions taken from the plotted patterns (Fig. 2f, g) -> A (v3.2 had M); derived-observable route available (definition 7)'),
    N('F3f', 'photocurrent versus bias (mu-tau measurement, data points)', 'M', 'The photoconductivity current of the device was recorded by using a Keithley 2400 digital source meter.',
      instrument='Keithley 2400', note='"fitting curve" columns (Hecht fit) are A'),
    N('F4b', 'X-ray response current density versus dose rate (data points)', 'M', 'The X-ray response current was measured using a Keithley 2400 digital source meter.',
      instrument='Keithley 2400; dose rate calibrated by RaySafe X2', note='"fitting curve" columns are A; sensitivity (slope) is A'),
    N('F4h', 'dark current versus bending strain', 'M', 'The X-ray response current was measured using a Keithley 2400 digital source meter.', instrument='Keithley 2400', default=False),
    N('F4i', 'normalized sensitivity versus bending strain', 'A', 'The sensitivity of the X-ray detector, calculated by the linear fitting of the dose rate dependent response current', ['F4b'],
      formula='slope of I(D) / A, normalised'),
    N('F1h', 'mu-tau product versus 1/E (literature compilation)', 'I', 'and Young’s modulus (E) for different materials. PCF and SC refer to polycrystalline film and single crystal',
      note='literature compilation'),
 ],
 'P4': [
    N('F2c', 'density', 'M', 'named default: bulk density of the cut prisms from mass and geometric volume (specimen dimensions 40 mm x 40 mm x 160 mm stated; the density method itself is not stated in the paper)',
      ['mass', 'dimensions'], formula='rho = m / V', default=True, note='settled: method not stated -> named default; specimen means of three specimens (Source Data lists the three values)'),
    N('F3e', 'thermal conductivity (Hot Disk)', 'M', 'the thermal conductivity along the depth direction was quantitatively measured using a Hot Disk TPS 2500S (Sweden) at room temperature',
      instrument='Hot Disk TPS 2500S', note='middle bar = literature value for lightweight concrete (I), not keyed'),
    N('F3b', 'backside temperature versus heating time', 'M', 'an infrared camera was positioned 10 cm away from the opposite side of the specimen to record the temperature evolution on the specimen’s back surface',
      instrument='IR camera', note='representative curves'),
    N('F2a', 'specific load versus midspan displacement (3PB)', 'A', 'Representative 3-point bending (3PB) curves', ['load (not plotted)', 'F2c'], formula='load / density',
      note='normalised by density -> A; representative curves'),
    N('F2e', 'specific load versus displacement (SENB)', 'A', 'Representative SENB test curves', ['load (not plotted)', 'F2c'], formula='load / density'),
    N('F2b', 'strain at failure', 'A', 'The details of the mechanical parameter calculation including MOR, Flexural toughness, KIC, and KJC are given in the Suppl. method 1.', ['F2a'],
      formula='computed from the load-displacement record'),
    N('F2d', 'specific MOR', 'A', 'the specific modulus of rupture (specific MOR) was not significantly affected', ['load', 'F2c', 'b, d, L'], formula='3PL/(2bd^2) / rho',
      note='specimen dimensions 40 x 40 mm, span 100 mm stated in Methods'),
    N('F2f', 'specific K_IC', 'A', 'The details of the mechanical parameter calculation including MOR, Flexural toughness, KIC, and KJC are given in the Suppl. method 1.', ['F2e', 'F2c']),
    N('F2g', 'flexural toughness', 'A', 'The details of the mechanical parameter calculation including MOR, Flexural toughness, KIC, and KJC are given in the Suppl. method 1.', ['F2a'], formula='integral of the load-displacement curve'),
    N('F2h', 'specific K_JC', 'A', 'The values corresponding to this limit on the curves were used to calculate the fracture toughness KJC.', ['F2j', 'F2c']),
    N('F2j', 'J-R curves', 'A', 'Representative crack-resistance curves (J-R curves)', ['F2e'], formula='J-integral'),
    N('F4b', 'weak-phase thickness and length distributions (X-CT)', 'A', 'The thickness distributions of the weakness phase and the solid phase were determined by creating five equally spaced slices',
      formula='image statistics'),
 ],
 'P5': [
    N('F2a', 'tensile stress-strain curves (15 wt%)', 'M', 'All tensile tests of the hydrogels with a dumbbell shape were conducted on a universal tensile machine (Instron Model 3367, USA)',
      instrument='Instron 3367', note='representative curves'),
    N('F2b-strength', 'tensile strength (15 wt%)', 'M', 'All tensile tests of the hydrogels with a dumbbell shape were conducted on a universal tensile machine (Instron Model 3367, USA)',
      instrument='Instron 3367', note='specimen means reported by the test (n = 3)'),
    N('F2b-elongation', 'elongation at break (15 wt%)', 'M', 'All tensile tests of the hydrogels with a dumbbell shape were conducted on a universal tensile machine (Instron Model 3367, USA)',
      instrument='Instron 3367', note='specimen means reported by the test (n = 3)'),
    N('F2c', 'modulus and toughness', 'A', 'The area under the stressstrain curves to failure is defined as the “toughness”', ['F2a'], formula='slope; integral'),
    N('F2d', 'tensile stress-strain curves (20 wt%)', 'M', 'All tensile tests of the hydrogels with a dumbbell shape were conducted on a universal tensile machine (Instron Model 3367, USA)', instrument='Instron 3367'),
    N('F2e-strength', 'tensile strength (10/20 wt%)', 'M', 'All tensile tests of the hydrogels with a dumbbell shape were conducted on a universal tensile machine (Instron Model 3367, USA)', instrument='Instron 3367'),
    N('F2g', 'water content', 'M', 'The hydrogel was dried at 37 °C until a constant weight, and the initial and dried mass of the hydrogel were expressed as ma and mb',
      ['ma', 'mb (not plotted)'], formula='(ma - mb)/ma', note='gravimetric: standard equation on unplotted masses'),
    N('F2h', 'fracture energy', 'A', 'The fracture energy can be calculated by', ['notched and un-notched loading curves'], formula='pure shear'),
    N('F3d', 'WAXS azimuthal intensity profiles', 'M', 'Wide-angle X-ray scattering (WAXS) and small-angle X-ray scattering (SAXS) measurements were conducted using a NanoSTAR instrument',
      instrument='Bruker NanoSTAR', formula='azimuthal integration of the 2D pattern (instrument software)'),
    N('F3j', 'crystallinity (dry, swollen)', 'A', 'The crystallinity of the dried sample (Xdry) is calculated as', ['DSC enthalpy', 'F2g'], formula='dH/dH0; X_dry (1 - phi_water)'),
    N('F4a', 'crack extension per cycle versus energy release rate', 'A', 'The energy release rate (G) is calculated by', ['unnotched loading curves'], formula='G = 2k(lambda) c W',
      note='G (x) computed from unnotched cyclic curves -> A'),
    N('F4f', 'fatigue threshold', 'A', 'The fatigue threshold was linearly extrapolated', ['F4a'], formula='linear extrapolation to dc/dN = 0'),
 ],
 'P6': [
    N('F2a', 'iR-corrected OER polarization current density', 'M', 'E - iR (V) vs.RHE', ['current', 'iR correction with the stated resistances'], instrument='CHI 760E; LSV at 10 mV/s',
      note='settled: iR-corrected (axis label "E - iR (V) vs.RHE"; caption: "The resistance values for SI1C1, SI2C1, SI4C1, SI6C1, SI8C1, SI and IrO2 were 3.9, 3.7, 3.6, 4.7, 3.2, 4.6 and 4.4 Ω"); '
           'reference electrode: "The reference electrode used was an Hg/HgCl2 electrode in a 0.5 M H2SO4 electrolyte" (DEMS: saturated Ag/AgCl), converted to RHE'),
    N('F2b', 'Tafel plots (overpotential versus log j)', 'A', 'OER polarization curves of SI1C1, SI2C1, SI4C1, SI6C1, SI8C1, and SI samples with a mass loading of 0.025 mg/cm2 in 0.5 M H2SO4 and (b) corresponding Tafel slopes',
      ['F2a'], formula='eta = E - 1.23 V vs log j', note='transform of the plotted polarization curves -> A'),
    N('F2c', 'overpotential at 10 mA/cm2', 'A', 'Comparison of overvoltages and Tafel slopes', ['F2a'], formula='E(10 mA/cm2) - 1.23 V'),
    N('F2c-tafel', 'Tafel slope', 'A', 'Comparison of overvoltages and Tafel slopes', ['F2b'], formula='slope of eta vs log j'),
    N('F2d', 'mass activity', 'A', 'Comparison of OER mass activity', ['F2a', 'loading'], formula='j / loading'),
    N('F1i-Co', 'Co/Ir ratio (ICP-MS)', 'M', 'the proportions of each element in SrIrO3 were determined by ICP-MS (iCAP RQ) analysis.', instrument='ICP-MS iCAP RQ'),
    N('F1i-Sr', 'Sr/Ir ratio (ICP-MS)', 'M', 'the proportions of each element in SrIrO3 were determined by ICP-MS (iCAP RQ) analysis.', instrument='ICP-MS iCAP RQ'),
    N('F4a', '18O16O percentage (DEMS)', 'M', 'differential electrochemical mass spectrometry (DEMS) measurements were conducted using the QAS 100 apparatus', instrument='DEMS QAS 100',
      formula='share of m/z 34 in the O2 signal'),
    N('F4b', 'in situ ICP-MS dissolved Sr, Co, Ir', 'M', 'In situ ICP-MS experiments were performed using a Thermo Scientific iCAP RQ instrument.', instrument='ICP-MS iCAP RQ'),
    N('F2f', 'PEM electrolyser polarization', 'M', 'A home-made PEM water electrolysis cell with a proton exchange membrane was used to evaluate the performance of SI series catalyst.', instrument='PEM cell'),
 ],
}

def main(ps):
    for P in ps:
        txt = norm(open(f'{HOST}/text/{ART[P]}.txt').read()); bad = []
        for n in NODES[P]:
            if n['evidence']['kind'] == 'span' and norm(n['evidence']['text']) not in txt: bad.append((n['panel'], n['evidence']['text'][:90]))
        if bad:
            for b in bad: print(P, 'SPAN NOT FOUND', b)
            raise SystemExit(f'{P}: {len(bad)} spans not found')
        json.dump(NODES[P], open(f'{ROOT}/sd/{P}/nodes.json', 'w'), indent=1, ensure_ascii=False)
        print(P, 'nodes', len(NODES[P]), {lv: sum(n['level'] == lv for n in NODES[P]) for lv in 'DMASI'})

if __name__ == '__main__':
    main(sys.argv[1:] or list(ART))
