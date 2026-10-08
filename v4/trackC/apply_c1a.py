#!/usr/bin/env python3
"""apply_c1a.py (C1a): writes the Q-C1 audit into the cards with the frozen application rules of audit_c1.py (A1-A4).
Reads audit_c1/answers.json and audit_c1/compare.json; rewrites CARD_liion.json and CARD_jarvis.json in place (the C1
versions stay in git, FREEZE C1). Restrictive changes:
  A1  stages the auditor finds not fully stated and the card had no gap get a rule gap (frozen reading kept, D2).
  A3  J6 dynamic_stability: decision_type static -> outcome_class (auditor); the frozen rules never key an outcome class,
      so decisions.py marks J6 template only and generate_c.py builds no JARVIS Arbitrate.
  A4  tracer_D (L1): law_class fit (auditor); T1 needs a non-fit law, so generate_c.py builds no Li-ion T1.
Every stage and law records its audit row (call number, field agreement, auditor answer). Idempotent.
usage: apply_c1a.py"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
A = json.load(open(os.path.join(HERE, 'audit_c1', 'answers.json')))
C = json.load(open(os.path.join(HERE, 'audit_c1', 'compare.json')))
LAW_USE = {'tracer_D': 'definition', 'nernst_einstein': 'definition', 'arrhenius': 'fit', 'room_temperature_extrapolation': 'fit',
           'lambda': 'definition', 'omega_log': 'definition', 'mcmillan_allen_dynes': 'independent', 'debye': 'definition'}
for fn, cname in (('CARD_liion.json', 'CARD_liion'), ('CARD_jarvis.json', 'CARD_jarvis')):
    p = os.path.join(HERE, fn); card = json.load(open(p))
    for r in [r for r in C['rows'] if r['card'] == cname]:
        if 'id' in r:
            s = next(x for x in card['stages'] if x['id'] == r['id'])
            s['audit'] = {'q_c1_call': r['n'], 'agree': r['agree'], 'auditor': r['auditor']}
            ap = [a for a in C['apply'] if a.get('stage') == r['id']]
            for a in ap:
                if a['rule'] == 'A1' and not s.get('rule_gap'):
                    s['rule_gap'] = {'what': 'Q-C1 auditor: ' + str(a.get('missing')), 'frozen_reading': 'the C1 reading (D2)', 'source': 'C1a'}
                if a['rule'] == 'A3' and a['effect'] == 'drop items':
                    s['decision_type_C1'] = s['decision_type']; s['decision_type'] = a['auditor']
                    s['c1a_effect'] = f"decision_type {a['card']} -> {a['auditor']} (restrictive, A3): template only, its items dropped"
        else:
            d = next(x for x in card['derived_laws'] if x['name'] == r['name'])
            d['audit'] = {'q_c1_call': r['n'], 'card_class': r['card_class'], 'auditor_class': r['auditor_class'],
                          'class_agree': r['class_agree'], 'constant_disagree': r['constant_disagree'], 'auditor': r['auditor']}
            d['law_class'] = r['auditor_class'] if (r['family_invalid'] or not r['class_agree']) and r['auditor_class'] == 'fit' else LAW_USE[r['name']]
            if r['family_invalid']:
                d['c1a_effect'] = f"law_class fit (auditor, A4): family {r['family']} items on this law dropped"
    card['audit_C1a'] = {'quote': 'Q-C1', 'model': 'openai/gpt-5.6-sol', 'temperature': 0, 'calls': len([a for a in A['answers'] if a['card'] == cname]),
                         'spent_usd_total': round(A['spent_usd'], 5), 'rules': 'audit_c1.py A1-A4 (frozen C1a_rule, C1a_rule2)'}
    json.dump(card, open(p, 'w'), indent=1, ensure_ascii=False); print(fn, 'written')
