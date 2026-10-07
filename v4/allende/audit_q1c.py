#!/usr/bin/env python3
"""audit_q1c.py (v4 Track B, quote Q1c-v4-reaudit-allende-claims; NOT RUN until approved): blind GPT-5.6-Sol parse audits of the rebuilt
full-sentence claims (B12) that can still become items (D1, D2, D3, D3b, D4, A4, I1) and cannot-tell audits of the rebuilt A4 and I1.
Claims resting on procedures Q1b rejected (M2, A1, A2, A3) and the undecided M1 are not audited. Same prompts as Q1b (span vs claim only;
route and check withheld). Outputs record the audited span and claim, so a later span change invalidates them (B12). Hard cap $0.50."""
import json, os, sys
sys.path.insert(0, '/home/aid1/Documents/harbor/v4/v3'); from audit32 import call, parse_json
D = os.path.dirname(os.path.abspath(__file__)); A = f'{D}/audit_q1c'; os.makedirs(f'{A}/outputs', exist_ok=True)
sys.path.insert(0, D); import physics_v2 as PH
sys.path.insert(0, D); from audit_q1b_prompts import DEPOSIT, CQ
CAP = 0.50; WORST = 0.044; spent = 0.0; log = []
def go(prompt, tag):
    global spent
    if spent + WORST > CAP: raise SystemExit(f'cap: spent {spent:.4f}, next call could exceed ${CAP}')
    r = call(prompt, None, tag); r['parsed'] = parse_json(r.get('reply')); c = (r.get('usage') or {}).get('cost') or 0; spent += c
    log.append({'tag': tag, 'cost': c, 'model': r.get('model'), 'id': r.get('id'), 'error': r.get('error'), 'usage': r.get('usage')}); return r
PARSE = open('/home/aid1/Documents/harbor/v4/v3/audit/prompts33/parse.txt').read(); C = {c['sid']: c for c in PH.CLAIMS}
pr = {}; outs = []
for sid in ('D1', 'D2', 'D3', 'D3b', 'D4', 'A4', 'I1'):
    c = C[sid]; p = PARSE.replace('{span}', c['span']).replace('{claim}', c['claim']).replace('{predicate}', json.dumps({'object': c['object'], 'rung': c['rung']}))
    r = go(p, f'q1c:parse:{sid}'); outs.append(r); pr[sid] = {'span': c['span'], 'claim': c['claim'], 'agree': (r['parsed'] or {}).get('agree') is True, 'reason': (r['parsed'] or {}).get('reason')}
json.dump(outs, open(f'{A}/outputs/parse.json', 'w'), indent=1); json.dump(pr, open(f'{A}/parse.json', 'w'), indent=1); print('parse', {k: v['agree'] for k, v in pr.items()})
ct = {}; outs = []
for sid in ('A4', 'I1'):
    r = go(CQ.format(dep=DEPOSIT, claim=C[sid]['claim']), f'q1c:ct:{sid}'); outs.append(r); v = (r['parsed'] or {}).get('verdict')
    ct[sid] = {'claim': C[sid]['claim'], 'verdict': v, 'agree': v == 'undecidable', 'reason': (r['parsed'] or {}).get('reason')}
json.dump(outs, open(f'{A}/outputs/cannot_tell.json', 'w'), indent=1); json.dump(ct, open(f'{A}/cannot_tell.json', 'w'), indent=1); print('cannot_tell', {k: v['verdict'] for k, v in ct.items()})
json.dump({'quote': 'Q1c-v4-reaudit-allende-claims', 'cap': CAP, 'spent': spent, 'n_calls': len(log), 'calls': log}, open(f'{A}/spend.json', 'w'), indent=1); print('SPENT $%.4f in %d calls' % (spent, len(log)))
