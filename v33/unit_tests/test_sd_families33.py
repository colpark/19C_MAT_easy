#!/usr/bin/env python3
"""test_sd_families33.py (v3.3 A2.6): every Source Data family generator on synthetic bundles, including a T2 set that fails the
ambiguity-class gate and a T7 law that fails gate 2 (fit-set mean / nearest condition)."""
import json, math, os, sys, tempfile
from types import SimpleNamespace as NS
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, R); sys.path.insert(0, f'{R}/sd')
import bundle as BD, families as FM, grade as G
fails = []
def ok(cond, msg):
    if not cond: fails.append(msg)
CONDS = ['c1', 'c2', 'c3', 'c4', 'c5']
def panel(pid, q, unit, yt, xt=None, **kw):
    return dict(dict(id=pid, quantity=q, qname=q, unit=unit, unit_text=unit, y_ticks=yt, x_ticks=xt, res=0.01, xname='T' if xt else None, xunit='K' if xt else '',
                     context=f'The panel plots {q} of five synthetic samples.', desc=f'{q} panel', series_label=lambda s: f'the {s} sample'), **kw)
spec = NS(YEAR=2025, PANELS=[panel('Fa', 'sigma', 'S/m', [0, 50], [300, 400]), panel('Fb', 'S', 'uV/K', [0, 250], [300, 400]), panel('Fc', 'PF', 'uW', [0, 400], [300, 400]),
                             panel('Fd', 'rho', 'g/cm3', [0, 5]), panel('Fe', 'E', 'GPa', [0, 30]), panel('Ff', 'y', 'mV', [0, 100], [0, 10])], EXCLUDED_PANELS={})
tol = {p.id if hasattr(p, 'id') else p['id']: {'tol': 0.02 * (max(p['y_ticks']) - min(p['y_ticks'])), 'span': 1} for p in spec.PANELS}
sig = {'c1': 5, 'c2': 10, 'c3': 20, 'c4': 21, 'c5': 40}; S = {'c1': 200, 'c2': 160, 'c3': 120, 'c4': 119, 'c5': 80}
cells = []
for c in CONDS:
    for T in (300, 400):
        cells += [dict(id=f'Fa:{c}:{T}', panel='Fa', series=c, x=T, value=sig[c] * (1 + (T - 300) / 1000)), dict(id=f'Fb:{c}:{T}', panel='Fb', series=c, x=T, value=S[c]),
                  dict(id=f'Fc:{c}:{T}', panel='Fc', series=c, x=T, value=S[c] ** 2 * sig[c] * (1 + (T - 300) / 1000) * 1e-3)]
    cells += [dict(id=f'Fd:{c}', panel='Fd', series=c, x=None, value={'c1': 1.0, 'c2': 2.0, 'c3': 3.0, 'c4': 3.05, 'c5': 4.0}[c]),
              dict(id=f'Fe:{c}', panel='Fe', series=c, x=None, value={'c1': 4.0, 'c2': 9.0, 'c3': 14.0, 'c4': 14.2, 'c5': 20.0}[c])]
for k in range(8): cells.append(dict(id=f'Ff:c1:{k}', panel='Ff', series='c1', x=float(k), value=10 + 8 * k))   # linear law y = a + b x
for c, off in zip(CONDS, (0, 3, 30, 33, 60)): cells.append(dict(id=f'Ff:{c}:9', panel='Ff', series=c, x=9.0, value=10 + off))
cells = [dict(c, unit='', quantity='', name='', level='M', source='synthetic', addr='') for c in cells]
nodes = [{'panel': p['id'], 'level': 'A' if p['id'] == 'Fc' else 'M'} for p in spec.PANELS]
tmp = tempfile.mkdtemp(); os.makedirs(f'{tmp}/sd/SYN/audit')
json.dump({'Fa': {'pass': True}, 'Fb': {'pass': True}, 'Fc': {'pass': True}, 'Fd': {'pass': True}}, open(f'{tmp}/sd/SYN/audit/identity.json', 'w'))
json.dump({'tc1': {'agree': True}, 'tc2': {'agree': False}}, open(f'{tmp}/sd/SYN/audit/parse.json', 'w'))
json.dump({'cn1': {'decides': False}, 'cn2': {'decides': True}}, open(f'{tmp}/sd/SYN/audit/cannot.json', 'w'))
json.dump({'removed': []}, open(f'{tmp}/sd/SYN/audit/signatures.json', 'w'))
json.dump({k: {'agree': True} for k in ('pass', 'fail', 'rank', 'bound', 'lin', 'flat')}, open(f'{tmp}/sd/SYN/audit/laws.json', 'w'))   # v3.3 A4: law class audit
physics = NS(SERIES_TEXT='five synthetic samples (c1-c5)',
    T2_SETS=[dict(id='pass', target='Fb', refs={'sigma': 'Fa', 'PF': 'Fc'}, link='definition', predict=lambda v, s, x: math.sqrt(v['PF'] / v['sigma'] * 1e3), ring_x=[300], question='PF = S^2 sigma links the panels.'),
             dict(id='fail', target='Fe', refs={'rho': 'Fd'}, link='independent', predict=lambda v, s, x: 5 * v['rho'], ring_x=[None], ref_same_x=True, question='E rises with density.', scatter={c: 3.0 for c in CONDS})],
    T3=[dict(id='rank', binding='b', **{'class': 'independent'}, subtype='ranking', hidden='Fe', shown=['Fd'], pairs=[(('c1', None), ('c5', None)), (('c3', None), ('c4', None))],
             predict=lambda B, c: B.cell('Fd', *c)['value'], question='Which of {a} and {b} has the larger modulus?', label_by='series'),
        dict(id='bound', binding='vr', **{'class': 'independent'}, subtype='bound', hidden='Fe', shown=['Fd'], conds=[('c3', None), ('c1', None)],
             bounds=lambda B, c: (10.0, 18.0, 0.6, 0.6) if c[0] == 'c3' else (4.3, 9.0, 0.6, 0.6), question='Give the Voigt and Reuss bounds of the modulus of {c}.')],
    T7=[dict(id='lin', f=lambda v, c, p: p[0] + p[1] * c['x'], inputs=[], target='Ff', rows=[('c1', float(k)) for k in range(8)], holdout='condition',
             params=[{'name': 'a', 'unit': 'mV', 'lo': -100, 'hi': 100, 'init': 0}, {'name': 'b', 'unit': 'mV', 'lo': -100, 'hi': 100, 'init': 1}], model_err=0.0, law_text='y = a + b x'),
        dict(id='flat', f=lambda v, c, p: p[0], inputs=[], target='Ff', rows=[(c, 9.0) for c in CONDS], holdout='sample', order=CONDS,
             params=[{'name': 'a', 'unit': 'mV', 'lo': -100, 'hi': 200, 'init': 0}], model_err=0.0, law_text='y = a for all samples')],
    SIGNATURE_PAIRS=[dict(id='sp', mechanisms=['m1', 'm2'], cause_panels=['Fd'], outcome_panels=['Fe', 'Fa', 'Fb'], authors_choice='m1', unconstrained='the colour of the sample',
                          comparisons=[{'obs': 'E(up)', 'panel': 'Fe', 'quantity': 'modulus', 'a': ('c1', None), 'b': ('c5', None)},
                                       {'obs': 'sigma(up)', 'panel': 'Fa', 'quantity': 'sigma', 'a': ('c1', 300), 'b': ('c5', 300)},
                                       {'obs': 'S(up)', 'panel': 'Fb', 'quantity': 'S', 'a': ('c1', 300), 'b': ('c5', 300)}])],
    TEXT_CLAIMS=[dict(sid='tc1', span='sigma of c5 is 40 S/m', claim='The conductivity of c5 at 300 K is 40 S/m.', panel='Fa', relation='equals', cells=[('c5', 300)], value=40.0, panels=['Fa', 'Fb']),
                 dict(sid='tc2', span='x', claim='bad parse', panel='Fa', relation='equals', cells=[('c5', 300)], value=40.0, panels=['Fa']),
                 dict(sid='tc3', span='y', claim='c3 has a higher S than c5 at 300 K.', panel='Fb', relation='greater', cells=[('c3', 300)], ref=('c5', 300), panels=['Fb', 'Fa']),
                 dict(sid='tc4', span='z', claim='c3 S equals 121.', panel='Fb', relation='equals', cells=[('c3', 300)], value=121.0 + 3 * 5.0, panels=['Fb'])],
    CANNOT=[dict(sid='cn1', claim='The c3 sample has the highest hardness.', panels=['Fa', 'Fb'], closest='Fa', withheld='hardness', why='no hardness panel'),
            dict(sid='cn2', claim='x', panels=['Fa'], closest='Fa', withheld='y', why='y')])
sigs = {'m1': {'mechanism': 'densification', 'relation': 'E ~ rho', 'source': 'textbook', 'prior_rank': 1, 'predicts': {'E(up)': 'up', 'sigma(up)': 'up', 'S(up)': 'down'}},
        'm2': {'mechanism': 'microcracking', 'relation': 'E ~ (1-Nd)', 'source': 'textbook', 'prior_rank': 2, 'predicts': {'E(up)': 'down', 'sigma(up)': 'up', 'S(up)': 'down'}}}
B = BD.SDBundle('SYN', root=tmp, cells=cells, tol=tol, nodes=nodes, spec=spec, physics=physics)
ok(abs(B.cell('Fa', 'c1', 300)['u'] - tol['Fa']['tol'] / 2) < 1e-12, 'definition 1: u = tol / 2')
t2, l2 = FM.make_t2(B, f'{tmp}/img')
ok(any(i['provenance']['set'] == 'pass' for i in t2), f'T2 passing set generated: {[(l["set"], l.get("dropped"), len(l.get("classes", []))) for l in l2]}')
ok(not any(i['provenance']['set'] == 'fail' for i in t2) and any(l['set'] == 'fail' and 'fewer than 3' in str(l.get('dropped')) for l in l2), 'T2 failing set dropped by the class gate')
for i in t2: ok(G.grade(i['oracle'], i['expected'])['reward'] == 1.0, 'T2 oracle grades 1')
t3, l3 = FM.make_t3(B)
ok(sum(i['expected'].get('subtype') == 'ranking' for i in t3) == 1, f'T3 ranking: c1/c5 kept, c3/c4 dropped ({[round(l.get("margin_combined_tol", 0), 1) for l in l3]})')
ok(sum(i['expected'].get('subtype') == 'bound' for i in t3) == 1, f'T3 bound: inside kept, outside dropped ({[round(l.get("inside_tol", 0), 2) for l in l3 if "inside_tol" in l]})')
for i in t3: ok(G.grade(i['oracle'], i['expected'])['reward'] == 1.0, 'T3 oracle grades 1')
t7, l7 = FM.make_t7(B)
ok(any(i['provenance']['law'] == 'lin' for i in t7), f'T7 extrapolation law passes: {[(l["law"], l["held_out"], l["g1"], l["g2"], l["g3"]) for l in l7 if l["law"] == "lin"][:3]}')
ok(not any(i['provenance']['law'] == 'flat' for i in t7) and any(l['law'] == 'flat' and not l['g2'] for l in l7), 'T7 constant law fails gate 2')
ok(max(sum(1 for i in t7 if i['provenance']['held_out'][1] == h) for h in range(8)) <= 2, 'T7 <= 2 items per held-out condition')
for i in t7: ok(G.grade(i['oracle'], i['expected'])['reward'] == 1.0, 'T7 oracle grades 1')
t5, t6, l5 = FM.make_t5_t6(B, sigs)
ok(len(t5) == 1 and t5[0]['expected']['mechanism'] in ('A', 'B'), f'T5 decidable pair keyed: {l5}')
for i in t5 + t6: ok(G.grade(i['oracle'], i['expected'])['reward'] == 1.0, 'T5/T6 oracle grades 1')
tt, lt = FM.make_t4_text(B)
v = {i['provenance']['evidence']['predicate']['sid']: i['expected']['verdict'] for i in tt}
ok(v.get('tc1') == 'consistent' and 'tc2' not in v and v.get('tc3') == 'consistent', f'T4 text claims keyed by rule 1 thresholds: {v} {lt}')
ok('tc4' not in v, 'T4 text claim at 3 bands on one cell dropped (between 0.5 and 5)')
tc, lc = FM.make_t4_cannot(B)
ok(len(tc) == 1 and tc[0]['expected']['verdict'] == 'cannot tell', f'cannot tell: Sol "decides" removes the item: {lc}')
items = tt + tc + [dict(tt[0], expected=dict(tt[0]['expected'], verdict='contradicted'), tags=dict(tt[0]['tags'], claim_source='matrix'))] * 6
bal, info = FM.balance_t4(items)
ok(all(c / info['n'] <= 0.38 for c in info['final'].values()) or info['n'] < 3, f'T4 balance trims to <= 38%: {info["final"]}')
# v3.3 A4: a law binding Sol did not agree with (or never audited) makes no item
json.dump({k: {'agree': True} for k in ('pass', 'rank', 'bound', 'flat')}, open(f'{tmp}/sd/SYN/audit/laws.json', 'w'))
t7x, l7x = FM.make_t7(B)
ok(not t7x and any(l.get('law') == 'lin' and 'law class audit' in str(l.get('dropped')) for l in l7x), 'T7 law without an agreeing class audit is excluded')

print('sd families:', 'PASS' if not fails else 'FAIL'); [print('  -', f) for f in fails]; sys.exit(1 if fails else 0)
