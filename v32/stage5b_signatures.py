#!/usr/bin/env python3
"""stage5b_signatures.py (Stage 5B): signature entries for the mechanisms the five papers name (chosen and rejected) plus standard
alternatives for the same observables. Each entry: mechanism, textbook relation, source, predicted direction per observable
('up' | 'down' | 'none') and prior rank (1 = textbook default; used only by the T5 'textbook prior' shortcut). Observables are named
changes along the paper's series variable; papers/<k>/gen_config binds them to panels and cells in Stage 5E. Entries are validated
(signatures.validate), unit-tested, and audited blind by GPT-5.6-Sol (audit32.py <k> signatures); a disagreement removes the entry.
Writes papers/<k>/signatures.json."""
import json, sys
V32 = '/home/aid1/Documents/harbor/v32'; sys.path.insert(0, V32)
import signatures as SG
U, D_, N = 'up', 'down', 'none'
TABLES = {
 's039': {   # x = Ni2+-Al3+ co-dopant content in Co0.6-xZn0.4-xNixAlxFe2O4
  'fe2_valence_expansion': {'mechanism': 'charge compensation reduces Fe3+ to the larger Fe2+, expanding the spinel lattice', 'relation': 'ionic radius r(Fe2+, 0.78 A) > r(Fe3+, 0.645 A) (Shannon 1976); Bragg: larger d -> lower 2theta',
                            'source': 'Shannon, Acta Cryst. A32 (1976) 751; Cullity, Elements of X-ray Diffraction', 'prior_rank': 2,
                            'predicts': {'xrd_311_2theta(x up)': D_, 'lattice_a(x up)': U}},
  'ionic_radius_contraction': {'mechanism': 'smaller Ni2+ (0.69 A) and Al3+ (0.535 A) replace Co2+ (0.745 A) and Zn2+ (0.74 A), contracting the lattice (Vegard-type)',
                               'relation': "Vegard's law with Shannon radii; Bragg: smaller d -> higher 2theta", 'source': 'Vegard 1921; Shannon 1976', 'prior_rank': 1,
                               'predicts': {'xrd_311_2theta(x up)': U, 'lattice_a(x up)': D_}},
  'quantum_confinement': {'mechanism': 'quantum confinement in smaller crystallites widens the optical gap', 'relation': 'Brus: E_g(R) = E_g(bulk) + h^2/(8 R^2) (1/m_e + 1/m_h) - 1.8 e^2/(4 pi eps R)',
                          'source': 'Brus, J. Chem. Phys. 80 (1984) 4403', 'prior_rank': 2, 'predicts': {'absorption_edge_energy(x up)': U, 'crystallite_size(x up)': D_}},
  'defect_band_tailing': {'mechanism': 'dopant-induced oxygen vacancies and disorder add band-tail states that narrow the effective gap', 'relation': 'Urbach tail: alpha = alpha0 exp((E - E0)/E_U), larger E_U with disorder',
                          'source': 'Urbach, Phys. Rev. 92 (1953) 1324', 'prior_rank': 1, 'predicts': {'absorption_edge_energy(x up)': D_, 'crystallite_size(x up)': N}},
  'b_site_dilution': {'mechanism': 'non-magnetic Al3+ and lower-moment Ni2+ dilute the octahedral B sublattice, lowering M_B - M_A', 'relation': "Neel two-sublattice model: M = M_B - M_A",
                      'source': 'Neel, Ann. Phys. 3 (1948) 137; Smit & Wijn, Ferrites (1959)', 'prior_rank': 1, 'predicts': {'Ms(x up)': D_}},
  'a_site_al_displacement': {'mechanism': 'Al3+ enters tetrahedral A sites and displaces Fe3+ to B sites, lowering M_A and raising the net moment', 'relation': "Neel model with A-site dilution: M = M_B - M_A rises",
                             'source': 'Smit & Wijn, Ferrites (1959)', 'prior_rank': 2, 'predicts': {'Ms(x up)': U}},
 },
 's098': {   # TOCNF : MXene ratio series
  'tocnf_intercalation': {'mechanism': 'TOCNF chains intercalate between MXene sheets, expanding the interlayer spacing', 'relation': 'Bragg: d(002) = lambda/(2 sin theta); intercalation raises d(002)',
                          'source': 'Cullity; Naguib et al., Adv. Mater. 26 (2014) 992 (MXene intercalation)', 'prior_rank': 1, 'predicts': {'mxene_002_2theta(TOCNF fraction up)': D_}},
  'no_intercalation_mixing': {'mechanism': 'physical mixing without intercalation: MXene restacks with its own spacing', 'relation': 'phase-separated blend: each phase keeps its d-spacing',
                              'source': 'standard two-phase composite picture', 'prior_rank': 2, 'predicts': {'mxene_002_2theta(TOCNF fraction up)': N}},
  'hbond_network': {'mechanism': 'hydrogen bonds between TOCNF -OH/-COOH and MXene terminations', 'relation': 'H-bonding lowers the O-H stretching frequency (red shift)',
                    'source': 'Pimentel & McClellan, The Hydrogen Bond (1960)', 'prior_rank': 1, 'predicts': {'oh_stretch_wavenumber(blend vs TOCNF)': D_}},
  'no_interaction_blend': {'mechanism': 'no specific interfacial interaction: the spectrum is the superposition of the components', 'relation': 'linear superposition of component spectra',
                           'source': 'standard non-interacting blend picture', 'prior_rank': 2, 'predicts': {'oh_stretch_wavenumber(blend vs TOCNF)': N}},
 },
 't042': {   # Zr content x in BNKT-based piezoceramics
  'electrostriction_ergodic': {'mechanism': 'ergodic relaxor: strain is mainly electrostrictive and reversible, domain switching suppressed', 'relation': 'S = Q P^2; small Pr and negative strain in ergodic relaxors',
                               'source': 'Jo et al., J. Appl. Phys. 105 (2009) 094102; Uchino, Ferroelectric Devices', 'prior_rank': 2,
                               'predicts': {'Pr(x up)': D_, 'negative_strain(x up)': D_}},
  'domain_switching_nonergodic': {'mechanism': 'irreversible domain switching / field-induced relaxor-to-ferroelectric transition produces the strain', 'relation': 'switching strain scales with Pr and the negative strain S_neg',
                                  'source': 'Jo et al., J. Appl. Phys. 105 (2009) 094102', 'prior_rank': 1, 'predicts': {'Pr(x up)': U, 'negative_strain(x up)': U}},
  'zr_lattice_softening': {'mechanism': 'Zr4+ (larger, heavier) weakens the B-O bond', 'relation': 'harmonic oscillator nu = (1/2 pi c) sqrt(k/mu): lower k -> lower wavenumber',
                           'source': 'Nakamoto, Infrared and Raman Spectra of Inorganic Compounds', 'prior_rank': 1, 'predicts': {'bo_stretch_wavenumber(x up)': D_}},
  'b_site_stiffening': {'mechanism': 'stronger Zr-O bonds stiffen the BO6 octahedra', 'relation': 'harmonic oscillator: higher k -> higher wavenumber',
                        'source': 'Nakamoto', 'prior_rank': 2, 'predicts': {'bo_stretch_wavenumber(x up)': U}},
  'zr_lattice_expansion': {'mechanism': 'larger Zr4+ (0.72 A) replaces Ti4+ (0.605 A) and expands the lattice', 'relation': "Vegard + Shannon radii; Bragg",
                           'source': 'Shannon 1976; Vegard 1921', 'prior_rank': 1, 'predicts': {'xrd_peak_2theta(x up)': D_}},
 },
 't051': {   # MnCO3 x wt% in BNT-AN
  'mn_electron_trap': {'mechanism': 'high-valence B-site Mn traps electrons and suppresses Ti4+ -> Ti3+ reduction, lowering electronic leakage', 'relation': 'fewer free electrons -> lower conductivity sigma = n e mu',
                       'source': 'Smyth, The Defect Chemistry of Metal Oxides (2000)', 'prior_rank': 2, 'predicts': {'leakage_J(x up)': D_}},
  'mn_acceptor_vacancy': {'mechanism': 'acceptor Mn on Ti sites is compensated by oxygen vacancies, raising ionic conduction', 'relation': "Kroger-Vink: Mn_Ti'' compensated by V_O^.. ; more V_O -> higher conduction",
                          'source': 'Smyth (2000); Kroger & Vink (1956)', 'prior_rank': 1, 'predicts': {'leakage_J(x up)': U}},
  'mn_soft_domains': {'mechanism': 'moderate Mn promotes ferroelectric domain formation (soft-like), raising Pr', 'relation': 'larger switchable polarization',
                      'source': 'Jaffe, Cook & Jaffe, Piezoelectric Ceramics (1971)', 'prior_rank': 2, 'predicts': {'Pr(x up)': U, 'Ec(x up)': D_}},
  'mn_acceptor_hardening': {'mechanism': 'acceptor defect dipoles clamp domain walls (classic hardening)', 'relation': 'domain-wall pinning raises Ec and lowers Pr',
                            'source': 'Jaffe, Cook & Jaffe (1971); Carl & Hardtl, Ferroelectrics 17 (1978) 473', 'prior_rank': 1, 'predicts': {'Pr(x up)': D_, 'Ec(x up)': U}},
 },
 's048': {   # TiO2 wt% in metakaolin geopolymer
  'inert_filler': {'mechanism': 'TiO2 is a chemically inert filler (dilution and pore filling)', 'relation': 'no new phase; XRD = superposition; anatase intensity proportional to its fraction',
                   'source': 'standard composite filler picture', 'prior_rank': 1, 'predicts': {'new_reflections(x up)': N, 'anatase_101_intensity(x up)': U}},
  'ti_incorporation': {'mechanism': 'TiO2 incorporates into the aluminosilicate network (Ti substitution, titanosilicate)', 'relation': 'consumption of anatase and new or shifted reflections',
                       'source': 'Davidovits, Geopolymer Chemistry and Applications', 'prior_rank': 2, 'predicts': {'new_reflections(x up)': U, 'anatase_101_intensity(x up)': N}},
  'filler_reinforcement': {'mechanism': 'TiO2 densifies the matrix and raises strength', 'relation': 'filler densification: fewer pores, higher strength (Ryshkewitch: sigma = sigma0 exp(-b P))',
                           'source': 'Ryshkewitch, J. Am. Ceram. Soc. 36 (1953) 65', 'prior_rank': 2, 'predicts': {'compressive_strength(x up)': U}},
  'binder_dilution': {'mechanism': 'TiO2 replaces reactive metakaolin, leaving less binder gel and a weaker paste', 'relation': 'strength scales with binder (gel) fraction',
                      'source': 'Duxson et al., J. Mater. Sci. 42 (2007) 2917', 'prior_rank': 1, 'predicts': {'compressive_strength(x up)': D_}},
  'third_body_lubrication': {'mechanism': 'a TiO2/gel third-body tribolayer lowers friction and wear', 'relation': 'tribolayer reduces adhesion: lower mu and wear',
                             'source': 'Godet, Wear 100 (1984) 437 (third-body approach)', 'prior_rank': 2, 'predicts': {'cof(x up)': D_, 'wear_rate(x up)': D_}},
  'abrasive_third_body': {'mechanism': 'hard anatase particles act as abrasive third bodies (ploughing)', 'relation': 'Archard/abrasive wear: harder debris raises wear and friction',
                          'source': 'Archard 1953; Rabinowicz, Friction and Wear of Materials', 'prior_rank': 1, 'predicts': {'cof(x up)': U, 'wear_rate(x up)': U}},
 },
}
if __name__ == '__main__':
    for k, t in TABLES.items():
        errs = SG.validate(t)
        if errs: print(k, 'INVALID', errs); sys.exit(1)
        json.dump(t, open(f'{V32}/papers/{k}/signatures.json', 'w'), indent=1, ensure_ascii=False); print(k, len(t), 'entries')
