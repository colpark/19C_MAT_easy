#!/usr/bin/env python3
"""C1 pipeline cards (skill discoveryqa v0.1 C1, D2, D3), built from the pipeline papers only.

CARD_liion.json is written from arXiv 2601.03151v1 (main text + SI in the same PDF) before any deposit value is
opened (hard rule 4). CARD_jarvis.json is written from arXiv 2205.00060v2 (npj Comput. Mater. 2022) before the
figshare JSON is opened. Every threshold carries a verbatim span (hyphenated line breaks of pdftotext joined) or
a named default; an unstated criterion is a rule gap with one frozen reading (D2).

usage: card.py liion OUT.json | card.py jarvis OUT.json | card.py check CARD.json
"""
import hashlib, json, sys

REQ = ['id', 'order', 'name', 'observable', 'comparator', 'threshold', 'unit', 'method', 'level_of_theory',
       'decision_type', 'cost_unit', 'cost', 'verbatim_span', 'span_source', 'stated_count', 'count_source',
       'rule_gap', 'audit']
DTYPES = {'static', 'recovery', 'refinement', 'escalation', 'literature', 'engine', 'outcome_class'}

LIION_SRC = {'paper': 'T. S. Thakur, L. Ercole, N. Marzari, Novel fast Li-ion conductors for solid-state electrolytes '
                      'from first-principles, Energy Environ. Sci. 2026, doi:10.1039/d5ee07336g',
             'read_from': 'arXiv:2601.03151v1 PDF (43 pp, main text pp 1-21, SI pp 22-43)',
             'pdf_sha256': '91d673a114dccaefb93528ae8aa9f7de64f1c75be5f444241d8fafc23a01d67a',
             'ees_si': 'not fetched: pubs.rsc.org is outside the allowed fetch hosts (hard rule 3); the arXiv PDF '
                       'carries the SI (MSD plots S1-S43, no tables, no numeric class criterion)'}

# D3 cost units for Li-ion. The paper states no core-hours. Unit: FPMD-ps-equivalent (one picosecond of
# Born-Oppenheimer PBEsol MD on the material's supercell). Named defaults where the paper is silent are flagged.
LIION_COST = {
    'unit': 'FPMD_ps_eq',
    'definition': 'cost of 1 ps of Born-Oppenheimer DFT-PBEsol MD on the material supercell',
    'pinball_speedup': {'value': 350, 'range': [200, 500],
                        'span': 'is on average about 200-500 times faster than DFT', 'source': 'Sec 1 p3'},
    'pinball_total_time_us': {'value': 22.1, 'materials': 851,
                              'span': '851 structures with a final iteration of the pinball MD run with converged '
                                      'coefficients and a total simulation time of 22.1 µs', 'source': 'Sec 3.1 p8'},
    'scf_named_default': {'value': 0.001, 'basis': 'named default: one SCF single point = one MD step; MD time step '
                          'not stated, named default 1 fs, so 1 SCF = 0.001 FPMD_ps_eq', 'rule_gap': True},
    'stages': {'S0-S5': 0.0, 'S6': 0.001,
               'S7_S8': round(22.1e6 / 851 / 350, 1),
               'S10': 100.0, 'S11': 125.0 + 150.0 + 180.0},
    'note': 'S7_S8 = mean pinball MD time per completed material (22.1 µs / 851) divided by the mid speedup 350; '
            'range 52-130 for speedups 500-200. Fitting-workchain DFT force calls are not counted (unstated).',
}


def st(**k):
    d = dict(rule_gap=None, audit='pending (AUDIT_PACKET_C1.md, quote Q-C1)', cost=None, cost_unit='FPMD_ps_eq',
             count_source=None, span_source=None)
    d.update(k)
    return d


def liion():
    S = []
    S.append(st(id='S0', order=0, name='sources', observable='Li-containing experimental structure', comparator='in',
                threshold='COD, ICSD, MPDS', unit=None, method='repository query, CIF import with AiiDA',
                level_of_theory='none (data analysis)', decision_type='static', cost=0.0,
                verbatim_span='Starting from experimental structures sourced from the Crystallography Open Database '
                              '(COD), Inorganic Crystal Structure Database (ICSD) and Materials Platform for Data '
                              'Science (MPDS) repositories, we identify more than 30,000 lithium containing structures, '
                              'which are imported as CIF files using AiiDA.',
                span_source='Sec 2.1 p4', stated_count=30229,
                count_source='Fig. 3 node labels COD 8,007 + ICSD 8,917 + MPDS 13,305 (text: approximately 8,000, '
                             '9,000, and 13,000)'))
    S.append(st(id='S1', order=1, name='clean', observable='CIF parses after COD-tools cleaning (Mounet et al. protocol)',
                comparator='==', threshold='parseable', unit=None, method='COD-tools clean, parse, standardise',
                level_of_theory='none (data analysis)', decision_type='static', cost=0.0,
                verbatim_span='We follow that protocol to clean, parse and standardise CIF files using COD-tools',
                span_source='Sec 2.1 p4', stated_count=22842,
                count_source='Fig. 3 "Clean CIFs 22,842", "Unusable CIFs 7,387" (text: nearly 23,000)'))
    S.append(st(id='S2', order=2, name='occupancy', observable='all site occupancies integer', comparator='==',
                threshold=True, unit=None, method='CIF occupancy check', level_of_theory='none (data analysis)',
                decision_type='static', cost=0.0,
                verbatim_span='We remove structures with partial occupancies i.e. those whose stoichiometry doesn\'t '
                              'align with the reported atomic positions',
                span_source='Sec 2.1 p4 (Occupancy filter)', stated_count=12198,
                count_source='Fig. 3 "Integer occupancy 12,198", "Partial occupancy 9,532", "Li only partial '
                             'occupancy 1,112" (text: approximately 10,600 removed, 12,000 remain)'))
    S.append(st(id='S3', order=3, name='unicity', observable='structure-matcher equivalence class representative',
                comparator='==', threshold='unique', unit=None,
                method='pymatgen StructureMatcher (CMPZ algorithm), same stoichiometry only',
                level_of_theory='none (data analysis)', decision_type='static', cost=0.0,
                verbatim_span='we use the CMPZ algorithm implemented within the structure matcher function of '
                              'pymatgen to compare crystal structures with the same stoichiometry, to eliminate '
                              'equivalent structures and retain only unique ones.',
                span_source='Sec 2.1 p4 (Unicity filter)', stated_count=5239,
                count_source='Fig. 3 "Unique structures 5,239", "Duplicate structures 6,959" (text: 5,200)',
                rule_gap={'what': 'matcher tolerances not stated (Sec 1: "tightening the tolerances")',
                          'frozen_reading': 'not reconstructed (parent CIFs not deposited; ICSD/MPDS licensed)'}))
    S.append(st(id='S4', order=4, name='composition', observable='element set', comparator='excludes/requires',
                threshold={'exclude': ['H', 'noble gases (He Ne Ar Kr Xe Rn)', '3d transition elements (Sc-Zn)',
                                       'elements heavier than Po (Z > 84)'],
                           'require': 'anions from the pnictogen, chalcogen and halogen families ("a specific '
                                      'selection")'},
                unit=None, method='composition rule', level_of_theory='none (data analysis)',
                decision_type='static', cost=0.0,
                verbatim_span='we filter out those with hydrogen, as elements lighter than lithium cannot be '
                              'correctly modelled by the pinball approximation; those containing noble gas atoms; '
                              '3d-transition elements, due to their potential to changing oxidation states during '
                              'simulations and become electronically conducting; and elements heavier than Polonium. '
                              'Furthermore, we apply additional filtering criteria to ensure that each structure '
                              'contains a specific selection of anions from the pnictogen, chalcogen and halogen '
                              'families.',
                span_source='Sec 2.1 p4 (Composition filter)', stated_count=1550,
                count_source='Fig. 3 node "1,550" after Composition filter',
                rule_gap={'what': '"a specific selection of anions" is not enumerated; "heavier than Polonium" '
                                  'comparator (Po itself) unstated; Sc and Zn membership in "3d-transition" unstated',
                          'frozen_reading': 'exclude Z > 84 (Po kept), exclude Sc-Zn, require >= 1 of N P As Sb Bi O S '
                                            'Se Te F Cl Br I. Checked on deposited survivors only (consistency, not a '
                                            'recount).'}))
    S.append(st(id='S5', order=5, name='atomic_distance', observable='pair distances typical of organic bonds',
                comparator='absent', threshold='bond lengths "typically associated with organic molecules such as '
                                               'double bond with O or triple bond with N"',
                unit='Å', method='pair-distance check', level_of_theory='none (data analysis)',
                decision_type='static', cost=0.0,
                verbatim_span='For each structure, we calculate the bond distances between every atom pair that is '
                              'compatible with inorganic materials to filter out structures with bond lengths '
                              'typically associated with organic molecules such as double bond with O or triple bond '
                              'with N.',
                span_source='Sec 2.1 p4 (Atomic-distance filter)', stated_count=1499,
                count_source='Fig. 3 "Pre-screened structures 1,499"; text "resulting in 1,499 structures"',
                rule_gap={'what': 'no numeric distance cutoffs stated', 'frozen_reading': 'not keyed'}))
    S.append(st(id='S6', order=6, name='electronic', observable='Kohn-Sham band gap at experimental geometry',
                comparator='>', threshold=1.0, unit='eV', method='pw.x SCF, SSSP efficiency 1.2.1, MV cold smearing, '
                'k density 0.15 1/Å, +20% bands', level_of_theory='DFT-PBEsol', decision_type='static',
                cost=LIION_COST['stages']['S6'],
                verbatim_span='we classify a structure as an electronic insulator if its band gap exceeds 1 eV. Out of '
                              'the 1,499 unique structures, 982 are identified as electronic insulators, and 39 '
                              'calculations failed',
                span_source='Sec 3 p7; Sec 2.2 p5 ("band gap greater than 1 eV as electronically insulating")',
                stated_count=982, count_source='text p7 and Fig. 5 ("Electronic insulators 982", "Electronic '
                                               'conductors 478")'))
    S.append(st(id='S6r', order=6.5, name='scf_rerun', observable='SCF convergence of the band-gap single point',
                comparator='==', threshold='converged', unit=None,
                method='rerun with non-linear conjugate gradient (SIRIUS-enabled QE)', level_of_theory='DFT-PBEsol',
                decision_type='recovery', cost=LIION_COST['stages']['S6'],
                verbatim_span='Out of these, 251 calculations fail to converge due to issues in the self-consistent '
                              'electronic cycle. These are subsequently rerun using the non-linear conjugate gradient '
                              'method within SIRIUS enabled Quantum ESPRESSO.',
                span_source='Sec 3 p7', stated_count=251, count_source='text p7 (reruns), 39 failed after rerun'))
    S.append(st(id='S7', order=7, name='pinball_selfconsistency',
                observable='r2 between DFT and pinball forces at converged pinball coefficients', comparator='>',
                threshold=0.95, unit=None, method='aiida-flipper ConvergeDiffusion (Fitting + LinDiffusion loop)',
                level_of_theory='pinball (non-local) fitted to DFT-PBEsol forces', decision_type='refinement',
                cost=LIION_COST['stages']['S7_S8'],
                verbatim_span='We ensure that the r2 correlation for the converged pinball coefficients exceeds 0.95, '
                              'with the majority of cases exceeding 0.99. If this criterion is not met, additional '
                              'self-consistent pinball MD iterations are performed',
                span_source='Sec 3.1 p8', stated_count=914,
                count_source='text p8 "Out of 982 structures, we achieve convergence for 914, with failures occurring '
                             'due to issues in the self-consistent electronic cycle when calculating DFT forces"'))
    S.append(st(id='S7d', order=7.5, name='pinball_drift', observable='drift in the MD constant of motion',
                comparator='acceptable', threshold=None, unit=None, method='pinball MD, stochastic velocity rescaling',
                level_of_theory='pinball', decision_type='recovery', cost=0.0,
                verbatim_span='An additional 63 structures failed the pinball MD simulations due to drift in the '
                              'constant of motion, leading to 851 structures with a final iteration of the pinball MD '
                              'run with converged coefficients',
                span_source='Sec 3.1 p8', stated_count=851, count_source='text p8',
                rule_gap={'what': 'no drift tolerance stated; no rerun policy stated for drift failures',
                          'frozen_reading': 'drift failures are dropped (the text reports them as failures)'}))
    S.append(st(id='S8', order=8, name='pinball_conductivity',
                observable='Li-ion conductivity from the final pinball MD MSD slope via Nernst-Einstein (H = 1)',
                comparator='>=', threshold=1.0, unit='mS/cm', method='pinball MD at 1000 K, eq. (1)-(2)',
                level_of_theory='pinball (non-local)', decision_type='static', cost=0.0,
                verbatim_span='Ionic conductivity of 1 mS/cm at 1000 K is chosen as the threshold to categorise '
                              'potential fast ionic conductors at the pinball level. At the end of this process, 132 '
                              'structures are identified for further study using first-principles calculations.',
                span_source='Sec 3.1 p8', stated_count=132,
                count_source='text p8 and Fig. 5 ("Potential fast-diffusers 132", "Non-diffusive structures 738", '
                             '"Failed calculations 170")',
                rule_gap={'what': 'comparator at exactly 1 mS/cm not stated (">=" vs ">")',
                          'frozen_reading': '>= ; items within rounding of 1 mS/cm reported apart'}))
    S.append(st(id='S9', order=9, name='novelty', observable='reported in the literature as a Li-ion conductor',
                comparator='==', threshold=False, unit=None, method='manual literature review',
                level_of_theory='literature', decision_type='literature', cost=0.0,
                verbatim_span='Out of these 132 structures, we rediscover 77 known Li-ion conductors and as such we '
                              'exclude them from FPMD investigations.',
                span_source='Sec 3.2.1 p8', stated_count=55,
                count_source='text p8 (77 known), Sec 4 p14 ("The remaining 55 materials")',
                rule_gap={'what': 'judgement by literature review; not computable by code',
                          'frozen_reading': 'template only (C4): never keyed'}))
    S.append(st(id='S10', order=10, name='fpmd_1000K', observable='Li tracer diffusion at 1000 K from FPMD MSD',
                comparator='>', threshold=1e-9, unit='cm^2/s', method='Born-Oppenheimer MD, 100 ps, 1000 K, NVT SVR',
                level_of_theory='DFT-PBEsol', decision_type='outcome_class', cost=LIION_COST['stages']['S10'],
                verbatim_span='the structures that exhibit high Li-ion diffusivity at 1000 K with the pinball model '
                              'are subsequently studied with FPMD at the same temperature for 100 ps. ... We find 18 '
                              'materials that do not exhibit Li-ion diffusion in our FPMD simulations at 1000 K.',
                span_source='Sec 2.3.2 p6; Sec 3.2.2 p10; Table 1', stated_count=18,
                count_source='text p10 and Table 1 (18 rows)',
                rule_gap={'what': 'no numeric criterion for "do not exhibit Li-ion diffusion" in text or SI',
                          'frozen_reading': 'diffusive iff D_FPMD(1000 K) > 1e-9 cm^2/s. Evidence: Fig. 15 caption '
                                            '"The bold-grey line represents the threshold below which MSD convergence '
                                            'cannot be achieved with FPMD, serving as the lower bound for diffusion"; '
                                            'the line sits on the 10^-9 tick (figure read, not text). Items within '
                                            'one decade of 1e-9 reported apart.'}))
    S.append(st(id='S11', order=11, name='temperature_ladder',
                observable='FPMD validates the material as a fast ionic conductor at 1000 K',
                comparator='==', threshold=True, unit=None,
                method='FPMD at 750, 600, 500 K for 125, 150, 180 ps', level_of_theory='DFT-PBEsol',
                decision_type='escalation', cost=LIION_COST['stages']['S11'],
                verbatim_span='The structures validated by FPMD as fast ionic conductors are then studied at three '
                              'lower temperatures: 750 K , 600 K and 500 K for 125 ps, 150 ps and 180 ps respectively.',
                span_source='Sec 2.3.2 p6', stated_count=34,
                count_source='derived: 9 (Table 3) + 25 (Table 2) studied at lower temperatures; exception Li2P2PdO7 '
                             'only at 600 K (Table 2 footnote **, SI Fig. S15 caption)',
                rule_gap={'what': 'escalation condition is the S10 outcome, itself a rule gap',
                          'frozen_reading': 'escalate iff S10 frozen reading says diffusive'}))
    S.append(st(id='S12', order=12, name='fpmd_outcome_class', observable='diffusion resolved at lower temperatures',
                comparator='class', threshold={'fast': 'diffusion resolved at low T, activation barrier estimated '
                                                       '(Table 3)',
                                               'high_T_only': 'significant diffusion at 1000 K but not at lower '
                                                              'temperatures (Table 2)',
                                               'no_diffusion': 'S10 fails (Table 1)'},
                unit=None, method='FPMD ladder + Arrhenius fit', level_of_theory='DFT-PBEsol',
                decision_type='outcome_class', cost=0.0,
                verbatim_span='We have identified 25 structures that exhibit significant diffusion at 1000 K in our '
                              'FPMD simulations, but do not display the same behaviour at lower temperatures. ... '
                              'These materials are of particular interest due to their potential applications, '
                              'characterised by their fast ionic conduction, which allows us to resolve Li-ion '
                              'diffusion even at low temperatures and estimate activation barriers',
                span_source='Sec 3.2.3 p10; Sec 3.2.4 p11', stated_count={'no_diffusion': 18, 'high_T_only': 25,
                                                                         'fast': 9},
                count_source='Tables 1-3 (18 + 25 + 9 = 52 rows of 55)',
                rule_gap={'what': 'no numeric criterion separates fast from high_T_only; Li10Si2PbO10 and Li2B3PO8 '
                                  'are in Table 2 yet the text reports their low-T diffusion and barriers',
                          'frozen_reading': 'Outcome class family not built (skill C5: criterion stated, else rule '
                                            'gap); classes used only as deposited labels for reconciliation'}))
    derived = [
        {'id': 'L1', 'name': 'tracer_D', 'law': 'D_tr = lim 1/(6t) <MSD(t)> (eq. 1), linear regression of MSD(t)',
         'span': 'By performing a linear regression of the mean square displacement MSD(t) with time we can accurately '
                 'estimate the diffusion coefficient from the slope of the MSD', 'source': 'Sec 2.3 p5',
         'rule_gap': {'what': 'fit window (start, end, block averaging) not stated; SAMOS defaults used by the authors',
                      'frozen_reading': 'our msd.py window frozen on synthetic data (C2)'}},
        {'id': 'L2', 'name': 'nernst_einstein', 'law': 'sigma = N (Ze)^2 D_tr / (Omega k_B T H) (eq. 2), H = 1',
         'span': 'In the dilute limit, we assume it to be 1, though in practice it is often less than 1, implying that '
                 'correlated motion can enhance conductivity', 'source': 'Sec 2.3 p5',
         'model_error': 'Haven ratio fixed at 1 (stated assumption); every T3 stem states it'},
        {'id': 'L3', 'name': 'arrhenius', 'law': 'ln D = ln D0 - Ea/(k_B T), linear fit over 1000, 750, 600, 500 K',
         'span': 'The activation barrier for these structures is estimated from a linear fit of the Arrhenius '
                 'behaviour and the error is obtained with Bayesian propagation', 'source': 'Sec 2.3.2 p7',
         'rule_gap': {'what': 'whether the fit is on D or on sigma*T, and which temperatures enter, not stated',
                      'frozen_reading': 'fit ln D vs 1/T on the temperatures where D is resolved (Figs. 11-12 plot '
                                        'D vs 1000/T)'}},
        {'id': 'L4', 'name': 'room_temperature_extrapolation', 'law': 'Arrhenius line extrapolated to 300 K',
         'span': 'it is important to note that this estimation is based on the extrapolation of the Arrhenius plot, '
                 'where a change of slope is possible', 'source': 'Sec 4 p14',
         'rule_gap': {'what': 'room temperature value (293/298/300 K) not stated', 'frozen_reading': '300 K'}},
    ]
    inconsistencies = [
        {'id': 'PI1', 'what': 'FPMD outcomes cover 52 of 55 (Tables 1-3: 18 + 25 + 9); Li4CO4 "in four distinct '
                              'crystal structures" may account for 3', 'class': 'paper inconsistency'},
        {'id': 'PI2', 'what': 'abstract and Sec 3.2.4 discuss 9 fastest; Sec 4 lists "seven promising materials" '
                              'including LiY(MoO4)2, Li8SeN2 and Li8TeN2, which sit in Table 2 (high_T_only), and '
                              'omits Li4CO4 and three Cs halides of Table 3', 'class': 'paper inconsistency'},
        {'id': 'PI3', 'what': 'Fig. 5: 132 + 738 + 170 + 478 = 1,518 != 1,499; 982 - 131 failures = 851 but 851 - 132 '
                              '= 719 != 738 non-diffusive', 'class': 'paper inconsistency'},
        {'id': 'PI4', 'what': 'LiCF3SO3 is listed among the 77 known conductors (Sec 3.2.1) and in Table 2 (FPMD '
                              'studied, high_T_only)', 'class': 'paper inconsistency'},
        {'id': 'PI5', 'what': 'MPDS id S1614518 is printed for Li10BrN3, Li2B3PO8 (Table 2) and Li4Mo3O8 (Table 3)',
         'class': 'paper inconsistency'},
        {'id': 'PI6', 'what': 'variable-cell relaxation on "about 20%" (Sec 2.2) vs "25% of these 1,499" (Sec 3)',
         'class': 'paper inconsistency'},
        {'id': 'PI7', 'what': 'Li2P2PdO7 FPMD conductivity is at 600 K, not 1000 K (Table 2 footnote **)',
         'class': 'rule exception'},
        {'id': 'PI8', 'what': 'Fig. 5 shows "Fast Li-ion conductors 9", conference abstracts cite "7 fastest"',
         'class': 'paper inconsistency (prompt; abstracts not on host)'},
    ]
    return {'card': 'CARD_liion', 'pipeline_id': 'thakur2026_liion_pinball_fpmd', 'source': LIION_SRC,
            'written_before_deposit_values': True, 'stages': S, 'derived_laws': derived,
            'cost_units': LIION_COST, 'inconsistencies': inconsistencies,
            'engine_twin': {'pipeline_id': 'thakur2026_liion_petmad', 'deposit': 'materialscloud:1c-13',
                            'card': 'not built: its paper is not on the host (R3 fails for the twin); 1c-13 '
                                    'description gives only the survivor criterion (> 1 mS/cm at room temperature, '
                                    'barrier 0.20-0.25 eV for its top three)',
                            'use': 'reference engine route in C2 only'}}


def check(card):
    errs = []
    for s in card['stages']:
        miss = [k for k in REQ if k not in s]
        if miss:
            errs.append((s.get('id'), 'missing', miss))
        if s.get('decision_type') not in DTYPES:
            errs.append((s.get('id'), 'decision_type', s.get('decision_type')))
        if s.get('threshold') is not None and not s.get('verbatim_span'):
            errs.append((s.get('id'), 'threshold without span'))
    return errs


def main():
    cmd, out = sys.argv[1], sys.argv[2]
    if cmd == 'check':
        c = json.load(open(out))
        e = check(c)
        print('card check', out, 'PASS' if not e else e)
        sys.exit(1 if e else 0)
    if cmd == 'liion':
        c = liion()
    elif cmd == 'jarvis':
        import card_jarvis
        c = card_jarvis.jarvis()
    e = check(c)
    if e:
        raise SystemExit(f'card check failed: {e}')
    s = json.dumps(c, indent=1, ensure_ascii=False, sort_keys=False)
    open(out, 'w').write(s + '\n')
    print(out, hashlib.sha256((s + '\n').encode()).hexdigest())


if __name__ == '__main__':
    main()
