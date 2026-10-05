#!/usr/bin/env python3
"""unit tests for provenance.py on synthetic graphs (the eight cases of the v3.2 plan, plus eligibility checks)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import provenance as P
fails = []
def check(name, cond):
    print(('ok   ' if cond else 'FAIL ') + name)
    if not cond: fails.append(name)
SP = {'kind': 'span', 'text': 'synthetic'}
def node(i, lv, cf=(), params=(), q=None): return {'id': i, 'quantity': q or i, 'panel': 'P', 'level': lv, 'computed_from': list(cf), 'params': list(params), 'evidence': SP}

g = P.Graph([node('S', 'M'), node('rho', 'M'), node('PF', 'A', ['S', 'rho'])])
c = P.classify_law({'id': 'pf', 'inputs': ['S', 'rho'], 'target': 'PF'}, g); check('PF from S and rho: definition', c[0] == 'definition')

g = P.Graph([node('R_H', 'M'), node('rho', 'M'), node('mu', 'A', ['R_H', 'rho']), node('n', 'M')])
c = P.classify_law({'id': 'mu', 'inputs': ['R_H', 'rho'], 'target': 'mu'}, g); check('mu_H from R_H and rho: definition', c[0] == 'definition')
c = P.classify_law({'id': 'hall', 'inputs': ['n', 'mu'], 'target': 'rho'}, g); check('rho = 1/(n e mu_H) with mu_H = R_H/rho: definition (target is an ancestor of an input)', c[0] == 'definition')

g = P.Graph([node('R_H', 'M'), node('rho_Hall', 'M', q='rho'), node('rho_ZEM', 'M', q='rho'), node('mu', 'A', ['R_H', 'rho_Hall'])])
c = P.classify_law({'id': 'mu', 'inputs': ['R_H', 'rho_Hall'], 'target': 'mu'}, g); check('mu_H from R_H and rho_Hall: definition', c[0] == 'definition')
c = P.classify_law({'id': 'rho_agree', 'inputs': ['rho_Hall'], 'target': 'rho_ZEM', 'agreement': True}, g); check('rho_Hall against rho_ZEM: agreement', c[0] == 'agreement')

g = P.Graph([node('S', 'M'), node('rho', 'M'), node('ke', 'A', ['S', 'rho'])])
c = P.classify_law({'id': 'wf', 'inputs': ['S', 'rho'], 'target': 'ke'}, g); check('kappa_e by Wiedemann-Franz from S and rho: definition', c[0] == 'definition')

g = P.Graph([node('S', 'M'), node('n', 'M')])
c = P.classify_law({'id': 'spb', 'inputs': ['n'], 'target': 'S', 'params': [{'name': 'm*', 'kind': 'fit', 'by': 'authors', 'fit_on': ['S', 'n']}]}, g)
check("SPB with the authors' m*: fit", c[0] == 'fit')

g = P.Graph([node('d_TEM', 'M', q='d'), node('d_XRD', 'M', q='d')])
c = P.classify_law({'id': 'bragg', 'inputs': ['d_XRD'], 'target': 'd_TEM', 'agreement': True, 'params': [{'name': 'lambda', 'kind': 'external', 'source': 'Cu K-alpha 1.5406 A'}]}, g)
check('HRTEM against XRD d spacing: agreement', c[0] == 'agreement' and c[1] == 'value')

g = P.Graph([node('sigma_y', 'M'), node('d', 'M')])
c = P.classify_law({'id': 'hp', 'inputs': ['d'], 'target': 'sigma_y', 'params': [{'name': 'k', 'kind': 'external', 'source': 'literature', 'spread': 0.35}]}, g)
check('Hall-Petch with a literature k (spread 35%): independent, ranking only', c[0] == 'independent' and c[1] == 'ranking')
c = P.classify_law({'id': 'hp', 'inputs': ['d'], 'target': 'sigma_y', 'params': [{'name': 'k', 'kind': 'external', 'source': 'literature', 'spread': 0.10}]}, g)
check('Hall-Petch with a literature k (spread 10%): independent, value', c[0] == 'independent' and c[1] == 'value')
c = P.classify_law({'id': 'hp', 'inputs': ['d'], 'target': 'sigma_y', 'params': [{'name': 'k', 'kind': 'fit', 'by': 'us', 'fit_on': ['sigma_y', 'd']}]}, g)
check('Hall-Petch with k fitted on the same samples: fit', c[0] == 'fit')
c = P.classify_law({'id': 'x', 'inputs': ['d'], 'target': 'sigma_y', 'params': [{'name': 'k', 'kind': 'external'}]}, g)
check('external parameter without a source: dependent', c[0] == 'dependent')

g = P.Graph([node('a', 'M'), node('y', 'M'), node('w', 'M'), node('b', 'A', ['a', 'y']), node('c', 'A', ['a', 'w'])])
c = P.classify_law({'id': 'x', 'inputs': ['b'], 'target': 'c'}, g); check('A nodes sharing an M root, target needs a measurement outside the inputs: dependent', c[0] == 'dependent')
g = P.Graph([node('a', 'M'), node('b', 'A', ['a']), node('c', 'A', ['a'])])
c = P.classify_law({'id': 'x', 'inputs': ['b'], 'target': 'c'}, g); check('target computed from an ancestor of the input: definition', c[0] == 'definition')

# eligibility
def raises(f):
    try: f(); return False
    except P.ProvenanceError: return True
check('A cell in a key raises', raises(lambda: P.check_key_sources('t1', [{'kind': 'cell', 'level': 'A'}])))
check('I in a key raises', raises(lambda: P.check_key_sources('t2', [{'kind': 'cell', 'level': 'I'}])))
check('M cell allowed', P.check_key_sources('t1', [{'kind': 'cell', 'level': 'M'}]))
check('definition law in T3 raises', raises(lambda: P.check_key_sources('t3', [{'kind': 'law', 'class': 'definition'}])))
check('agreement law in T3 allowed', P.check_key_sources('t3', [{'kind': 'law', 'class': 'agreement'}]))
check('definition law in a T4 recompute allowed', P.check_key_sources('t4', [{'kind': 'law', 'class': 'definition'}, {'kind': 'audited_cell'}]))
check('audited A cell outside T4 raises', raises(lambda: P.check_key_sources('t3', [{'kind': 'audited_cell'}])))
check('fit law only in T7', raises(lambda: P.check_key_sources('t3', [{'kind': 'law', 'class': 'fit'}])) and P.check_key_sources('t7', [{'kind': 'law', 'class': 'fit'}]))
check('A node without computed_from raises', raises(lambda: P.Graph([node('x', 'A')])))
check('node without evidence raises', raises(lambda: P.Graph([{'id': 'x', 'quantity': 'x', 'panel': 'P', 'level': 'M'}])))
check('defaults: PF A, mu_H A, n_H M, kappa M', P.default_node('a', 'PF', 'P')['level'] == 'A' and P.default_node('b', 'mu_H', 'P')['level'] == 'A'
      and P.default_node('c', 'n_H', 'P')['level'] == 'M' and P.default_node('d', 'kappa', 'P')['level'] == 'M'
      and P.default_node('e', 'mu_H', 'P', separate_hall_rho=True)['level'] == 'M')
print(f'\n{len(fails)} failures' if fails else '\nall passed'); sys.exit(1 if fails else 0)
