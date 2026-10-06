#!/usr/bin/env python3
"""build_nodes.py (mo21): the provenance node graph of paper 1, every tag with a verbatim Methods/caption span (checked by code against
the extracted text) or a named default rule (provenance.DEFAULT_LEVEL). Writes nodes.json and law_bindings.json; prints the law classes.
Hall setup: Methods names a four-probe Van der Pauw Hall-coefficient measurement and mu_H = sigma R_H with sigma from the ZEM-3; it does
not state a separate Hall resistivity, so mu_H is A computed from R_H and rho (ZEM), and rho = 1/(n_H e mu_H) is a definition."""
import sys as _pb_s, os as _pb_o
_pb_d = _pb_o.path.dirname(_pb_o.path.abspath(__file__))
while not _pb_o.path.exists(_pb_o.path.join(_pb_d, 'pbroot.py')) and _pb_o.path.dirname(_pb_d) != _pb_d: _pb_d = _pb_o.path.dirname(_pb_d)
_pb_s.path.insert(0, _pb_d)
from pbroot import ROOT, HOST
import json, os, re, sys
sys.path.insert(0, f'{ROOT}')
import provenance as P, laws as L
PD = os.path.dirname(os.path.abspath(__file__)); TEXT = f'{HOST}/papers/mo21/text/Mo21_raw.txt'
norm = lambda s: re.sub(r'\s+', ' ', s).strip()
def span(t): return {'kind': 'span', 'text': t}
def default(q): return {'kind': 'default', 'text': P.DEFAULT_LEVEL[q][1]}
ZEM = 'The electrical conductivity (σ ) and Seebeck coefficient (S) from 300 to 623 K were measured simultaneously on a ZEM3 system (ZEM-3, ULVAC Riko, Japan)'
NODES = [
    # design records
    {'id': 'x', 'quantity': 'x', 'panel': None, 'level': 'D', 'evidence': span('of Mg3.2 Bi1.4 Sb0.6- x Sex (x = 0, 0.005, 0.01, 0.02, 0.04)')},
    {'id': 'T', 'quantity': 'T', 'panel': None, 'level': 'D', 'evidence': span('from 300 to 623 K were measured simultaneously')},
    # measurements
    {'id': 'R_H', 'quantity': 'R_H', 'panel': None, 'level': 'M', 'instrument': 'four-probe Van der Pauw, 1.5 T',
     'evidence': span('A four-probe Van der Pauw method was used for Hall coefficient (RH ) measurement under a magnetic field of 1.5 T.')},
    {'id': 'n_H', 'quantity': 'n_H', 'panel': 'F4a', 'level': 'M', 'instrument': 'Hall (R_H)', 'formula': 'n_H = 1/(e R_H)', 'computed_from': ['R_H'],   # instrument equation: stays M
     'evidence': span('The Hall carrier concentration (nH ) was obtained by nH = 1/(eRH )')},
    {'id': 'rho', 'quantity': 'rho', 'panel': 'F5a', 'level': 'M', 'instrument': 'ZEM-3', 'evidence': span(ZEM)},
    {'id': 'S', 'quantity': 'S', 'panel': 'F5b', 'level': 'M', 'instrument': 'ZEM-3', 'evidence': span(ZEM)},
    {'id': 'kappa', 'quantity': 'kappa', 'panel': 'F5d', 'level': 'M', 'instrument': 'LFA 457 + DSC 404 C + Archimedes', 'formula': 'kappa = d D Cp',
     'evidence': span('The thermal conductivity κ was calculated via κ = dDCp , where d is sample density estimated by the Archimedes method.')},
    {'id': 'xrd', 'quantity': 'XRD pattern', 'panel': 'F1b', 'level': 'M', 'instrument': 'D2 PHASER', 'evidence': span('The phase characterization was performed by X-ray diffraction (XRD, D2 PHASER, Bruker)')},
    {'id': 'sem', 'quantity': 'SEM/EDS (x = 0.01 only)', 'panel': 'F3', 'level': 'M', 'instrument': 'SEM/EDS',
     'evidence': span('The freshly broken surface of the sample Mg3.2 Bi1.4 Sb0.59 Se0.01 was observed by a scanning electron')},
    # author-derived
    {'id': 'mu_H', 'quantity': 'mu_H', 'panel': 'F4b', 'level': 'A', 'computed_from': ['R_H', 'rho'], 'formula': 'mu_H = sigma R_H = R_H / rho',
     'evidence': span('and the Hall mobility (μH ) was estimated by μH = σ RH .')},
    {'id': 'PF', 'quantity': 'PF', 'panel': 'F5c', 'level': 'A', 'computed_from': ['S', 'rho'], 'formula': 'PF = S^2/rho', 'evidence': default('PF')},
    {'id': 'kappa_e', 'quantity': 'kappa_e', 'panel': 'F5e', 'level': 'A', 'computed_from': ['rho', 'S'], 'formula': 'kappa_e = L T / rho, L from SPB (uses S)',
     'evidence': span('κ e was estimated according to the Wiedemann–Franz law, κ e = LT/ρ, where L is the Lorenz number. The Lorenz number was determined by the SPB model assuming acoustic phonon scattering')},
    {'id': 'kappa_Lb', 'quantity': 'kappa_Lb', 'panel': 'F5f', 'level': 'A', 'computed_from': ['kappa', 'kappa_e'], 'formula': 'kappa_L + kappa_b = kappa - kappa_e', 'evidence': default('kappa_Lb')},
    {'id': 'ZT', 'quantity': 'ZT', 'panel': 'F6a', 'level': 'A', 'computed_from': ['S', 'rho', 'kappa'], 'formula': 'ZT = S^2 T/(rho kappa)', 'evidence': default('ZT')},
    {'id': 'm_star', 'quantity': 'm*', 'panel': None, 'level': 'A', 'computed_from': ['S', 'n_H'], 'formula': 'SPB fit',
     'params': [{'name': 'm*', 'kind': 'fit', 'by': 'authors', 'fit_on': ['S', 'n_H']}],
     'evidence': span('Based on the experimental Seebeck coefficients and carrier concentrations, a density of state (DOS) effective mass m∗ ∼1.2 me was derived')},
    {'id': 'nH_vs_mu', 'quantity': 'n_H vs mu_H with literature', 'panel': 'F4c', 'level': 'A', 'computed_from': ['n_H', 'mu_H'], 'formula': 'compilation (this work + literature)',
     'evidence': span('The relationships of experimental nH and μH n-Mg3 Sb2 TE materials with different dopants are compared in Fig. 4c')},
    {'id': 'pisarenko', 'quantity': 'S vs n_H with SPB curves', 'panel': 'F4d', 'level': 'A', 'computed_from': ['S', 'n_H'], 'formula': 'SPB curves + literature',
     'evidence': span('The curves are generated by SPB model.')},
    {'id': 'bands', 'quantity': 'band structure (DFT)', 'panel': 'F2', 'level': 'S', 'evidence': span('Calculated electronic band structure of (a) Mg3 Bi2 and (b) Mg3 Sb2 by PBE functional')},
    {'id': 'zt_compare', 'quantity': 'peak ZT comparison', 'panel': 'F6b', 'level': 'A', 'computed_from': ['ZT'], 'formula': 'literature compilation',
     'evidence': span('(b) comparison of peak ZT between different material composition')},
    {'id': 'eng', 'quantity': 'PF_eng, ZT_eng, efficiency', 'panel': 'F7', 'level': 'A', 'computed_from': ['S', 'rho', 'kappa'], 'formula': 'engineering integrals',
     'evidence': span('Calculated (a) PFeng , (b) ZTeng , and (c) maximal conversion efficiency')},
]
# law bindings: library law -> node ids (inputs, target); parameters with provenance
BINDINGS = [
    {'id': 'mo21_hall_rho', 'inputs': ['n_H', 'mu_H'], 'target': 'rho', 'methods_span': 'and the Hall mobility (μH ) was estimated by μH = σ RH .'},
    {'id': 'mo21_mu_recompute', 'inputs': ['n_H', 'rho'], 'target': 'mu_H', 'methods_span': 'and the Hall mobility (μH ) was estimated by μH = σ RH .'},
    {'id': 'mo21_pf', 'inputs': ['S', 'rho'], 'target': 'PF', 'methods_span': None},
    {'id': 'mo21_kappa_e', 'inputs': ['S', 'rho'], 'target': 'kappa_e', 'methods_span': 'κ e was estimated according to the Wiedemann–Franz law, κ e = LT/ρ',
     'substitution': {'what': 'Lorenz number: Kim et al. approximation L = 1.5 + exp(-|S|/116) instead of the authors\' SPB L', 'model_err': 0.05}},
    {'id': 'mo21_kappa_Lb', 'inputs': ['kappa', 'kappa_e'], 'target': 'kappa_Lb', 'methods_span': None},
    {'id': 'mo21_zt', 'inputs': ['S', 'rho', 'kappa'], 'target': 'ZT', 'methods_span': None},
    {'id': 'mo21_spb_S', 'inputs': ['n_H'], 'target': 'S', 'params': [{'name': 'm*', 'kind': 'fit', 'by': 'authors', 'fit_on': ['S', 'n_H']}],
     'methods_span': 'Based on the experimental Seebeck coefficients and carrier concentrations, a density of state (DOS) effective mass m∗ ∼1.2 me was derived'},
]

if __name__ == '__main__':
    raw = norm(open(TEXT).read()); bad = []
    for nd in NODES:
        if nd['evidence']['kind'] == 'span' and norm(nd['evidence']['text']) not in raw: bad.append(nd['id'])
    for b in BINDINGS:
        if b.get('methods_span') and norm(b['methods_span']) not in raw: bad.append('binding ' + b['id'])
    if bad: print('SPAN NOT FOUND:', bad); sys.exit(1)
    g = P.Graph(NODES); out = []
    for b in BINDINGS:
        cls, mode, why = P.classify_law({'id': b['id'], 'inputs': b['inputs'], 'target': b['target'], 'params': b.get('params', []),
                                         'agreement': L.LIBRARY[b['id']].get('agreement', False)}, g)
        out.append(dict(b, law_class=cls, mode=mode, reason=why)); print(f"{b['id']:16} {cls:11} {mode or '':7} {why}")
    json.dump(NODES, open(f'{PD}/nodes.json', 'w'), indent=1, ensure_ascii=False); json.dump(out, open(f'{PD}/law_bindings.json', 'w'), indent=1, ensure_ascii=False)
    print(len(NODES), 'nodes;', sum(n['evidence']['kind'] == 'span' for n in NODES), 'with Methods/caption spans,', sum(n['evidence']['kind'] == 'default' for n in NODES), 'by default rule')
