#!/usr/bin/env python3
"""audit_c1.py (quote Q-C1, approved by David 2026-10-08): runs AUDIT_PACKET_C1.md exactly as packaged and compares
the blind answers with the frozen cards. Frozen as C1a_rule BEFORE the first call.

Run: the 30 calls of the packet in order. Messages = [system: the packet's stage or law prompt, user: the call text
between its "### call n" header and the next header]. openai/gpt-5.6-sol, temperature 0, nothing else in the body
except usage accounting. The key comes from the environment (OPENROUTER_API_KEY) and is never written. The packet
sha256 must equal FREEZE C1 (6b32578b...). Hard cap $1.00: the runner sums usage.cost after each call and stops
before any call whose worst case (2,000 in, 1,500 out at $2 / $10 per M = $0.019) could cross the cap.

Comparison (pre-registered; restrictive reading wins, I3). Per stage: comparator (normalized: >=, <=, ==, >, <, in,
class, computed, unstated), threshold (first number, else text), unit (lower case, spaces, ^ and * removed),
decision_type, rule_fully_stated.
  agree        field equal after normalization (numbers within 1e-6 relative; text thresholds when one contains
               the other); an auditor "unstated"/ambiguous answer on a stage whose card already logs a rule gap
               counts as agreement with the gap.
  disagree     anything else.
Per law: law_class, and the stated constants (Haven ratio H = 1 for nernst_einstein, mu* = 0.09 for
mcmillan_allen_dynes): a different number for a named constant is a disagreement.

Application (restrictive; recorded in audit_c1/apply.json, executed by the C1a refreeze):
  A1  rule_fully_stated false on a stage without a card rule gap: add a rule gap {what: the auditor's "missing",
      frozen_reading: the card's reading}. Annotation only (D2: a frozen reading counts for a logged rule gap).
  A2  comparator or threshold disagreement on an item-keyed stage (S8 Li-ion Arbitrate gate; J6 JARVIS Arbitrate
      stability): drop every item whose key changes between the card reading and the auditor reading; when the
      auditor reading cannot be evaluated on deposited values, mark the stage template only (all its items dropped).
      On a stage that keys no item: annotation (rule gap) only.
  A3  decision_type disagreement on an item-keyed stage where the auditor type is literature, engine or
      outcome_class (never keyed by the frozen rules): its items are dropped. Otherwise annotation.
  A4  law class: T3 needs a non-fit class (definition, independent, agreement), T7 needs fit. Card uses: tracer_D
      (L1, T1 read: definition), nernst_einstein (L2, T3: definition), arrhenius (L3, T7: fit),
      room_temperature_extrapolation (L4, no item), lambda, omega_log, mcmillan_allen_dynes (JL1-JL3, JARVIS T3),
      debye (JL4, no item). An auditor class that makes a family invalid drops that family's items for that law.
      A constant disagreement (A4 constants) drops the items using that law.
  Any reading change (A2-A4 with drops, or a changed comparator, threshold or constant) refreezes C1 as C1a and
  regenerates C2-C6; annotations alone refreeze the card files as C1a with item hashes confirmed unchanged.

usage: audit_c1.py run | compare        (run makes the calls; compare is offline on audit_c1/answers.json)
"""
import hashlib, json, os, re, sys, time, urllib.error, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PACKET = os.path.join(HERE, 'AUDIT_PACKET_C1.md')
PACKET_SHA = '6b32578b3244ff0bef429de408dca35dd37ddf8fa779766cd803a7790b06c07b'
OUT = os.path.join(HERE, 'audit_c1')
MODEL = 'openai/gpt-5.6-sol'
CAP, WORST = 1.00, 2000 * 2e-6 + 1500 * 1e-5
KEYED_STAGES = {'S8': 'liion Arbitrate', 'J6': 'jarvis Arbitrate'}
LAW_USE = {'tracer_D': ('T1', 'definition'), 'nernst_einstein': ('T3', 'definition'), 'arrhenius': ('T7', 'fit'),
           'room_temperature_extrapolation': (None, 'fit'), 'lambda': ('T3', 'definition'),
           'omega_log': ('T3', 'definition'), 'mcmillan_allen_dynes': ('T3', 'independent'), 'debye': (None, 'definition')}
CONSTS = {'nernst_einstein': ('haven', 1.0), 'mcmillan_allen_dynes': ('mu', 0.09)}


def packet():
    t = open(PACKET).read()
    assert hashlib.sha256(t.encode()).hexdigest() == PACKET_SHA, 'packet differs from FREEZE C1'
    sys_stage = re.search(r'## System prompt \(stages\)\n\n```\n(.*?)\n```', t, re.S).group(1)
    sys_law = re.search(r'## System prompt \(laws\)\n\n```\n(.*?)\n```', t, re.S).group(1)
    calls = []
    parts = re.split(r'\n(?=### call \d+: |## CARD_|Total calls:)', t)
    card = None
    for p in parts:
        if p.startswith('## CARD_'):
            card = p.split()[1]
            continue
        m = re.match(r'### call (\d+): (stage|law) "([^"]+)"\n\n(.*)', p, re.S)
        if m:
            calls.append({'n': int(m.group(1)), 'kind': m.group(2), 'name': m.group(3), 'card': card,
                          'system': sys_stage if m.group(2) == 'stage' else sys_law, 'user': m.group(4).strip()})
    assert [c['n'] for c in calls] == list(range(1, 31)), [c['n'] for c in calls]
    return calls


def call(system, user, tag):
    body = {'model': MODEL, 'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': user}],
            'temperature': 0, 'usage': {'include': True}}
    for attempt in range(4):
        req = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions', data=json.dumps(body).encode(),
                                     headers={'Authorization': 'Bearer ' + os.environ['OPENROUTER_API_KEY'],
                                              'Content-Type': 'application/json'})
        try:
            r = json.load(urllib.request.urlopen(req, timeout=300))
            return {'tag': tag, 'reply': r['choices'][0]['message']['content'], 'usage': r.get('usage'),
                    'model': r.get('model'), 'id': r.get('id'), 'provider': r.get('provider')}
        except urllib.error.HTTPError as e:
            ra = e.headers.get('Retry-After')
            if e.code in (429, 500, 502, 503) and attempt < 3:
                time.sleep(float(ra) if ra else 10 * (attempt + 1))
                continue
            return {'tag': tag, 'error': f'HTTP {e.code}: {e.read().decode()[:300]}'}
    return {'tag': tag, 'error': 'retries exhausted'}


def parse_json(t):
    if not t:
        return None
    t = re.sub(r'^```(?:json)?\s*|\s*```$', '', t.strip())
    try:
        return json.loads(t)
    except Exception:
        m = re.search(r'\{.*\}', t, re.S)
        try:
            return json.loads(m.group(0)) if m else None
        except Exception:
            return None


def run():
    os.makedirs(OUT, exist_ok=True)
    calls, spent, ans = packet(), 0.0, []
    for c in calls:
        if spent + WORST > CAP:
            print(f'STOP before call {c["n"]}: spent {spent:.4f} + worst {WORST:.4f} > cap {CAP}')
            break
        r = call(c['system'], c['user'], f'c1:{c["n"]}:{c["name"]}')
        cost = ((r.get('usage') or {}).get('cost') or 0.0)
        spent += cost
        ans.append({**{k: c[k] for k in ('n', 'kind', 'name', 'card')}, **r, 'parsed': parse_json(r.get('reply')),
                    'cost': cost, 'spent': spent})
        print(c['n'], c['name'], r.get('model'), f'${cost:.5f}', 'ERR ' + r['error'] if r.get('error') else '')
        json.dump({'model_requested': MODEL, 'temperature': 0, 'spent_usd': spent, 'answers': ans},
                  open(os.path.join(OUT, 'answers.json'), 'w'), indent=1)
    print(f'total ${spent:.5f} over {len(ans)} calls')


def norm_cmp(x):
    x = str(x or '').strip().lower()
    return {'≥': '>=', '≤': '<=', '=': '==', 'greater than': '>', 'exceeds': '>', 'less than': '<'}.get(x, x)


def num(x):
    if isinstance(x, (int, float)) and not isinstance(x, bool):
        return float(x)
    m = re.search(r'[-+]?\d+(?:[.,]\d+)?(?:[eE][-+]?\d+)?', str(x or '').replace(',', ''))
    return float(m.group(0)) if m else None


def norm_unit(u):
    return re.sub(r'[\s^*·]', '', str(u or '').lower()).replace('²', '2').replace('kelvin', 'k')


UNSTATED = ('unstated', 'ambiguous', 'not stated', 'unclear', 'none', '')


def compare():
    A = json.load(open(os.path.join(OUT, 'answers.json')))
    cards = {'CARD_liion': json.load(open(os.path.join(HERE, 'CARD_liion.json'))),
             'CARD_jarvis': json.load(open(os.path.join(HERE, 'CARD_jarvis.json')))}
    rows, apply = [], []
    for a in A['answers']:
        p, card = a.get('parsed') or {}, cards[a['card']]
        if a['kind'] == 'stage':
            s = next(x for x in card['stages'] if x['name'] == a['name'])
            gap = bool(s.get('rule_gap'))
            r = {'n': a['n'], 'card': a['card'], 'id': s['id'], 'name': s['name'], 'card_gap': gap,
                 'keyed': KEYED_STAGES.get(s['id']), 'auditor': {k: p.get(k) for k in (
                     'comparator', 'threshold', 'unit', 'decision_type', 'rule_fully_stated', 'missing')}}
            ac, cc = norm_cmp(p.get('comparator')), norm_cmp(s['comparator'])
            at, ct = p.get('threshold'), s['threshold']
            an, cn = num(at), num(ct) if not isinstance(ct, (dict, list)) else None
            und = str(at or '').strip().lower() in UNSTATED or ac in UNSTATED
            f = {}
            f['comparator'] = ac == cc or (und and gap)
            if an is not None and cn is not None:
                f['threshold'] = abs(an - cn) <= 1e-6 * max(1.0, abs(cn))
            else:
                ta, tc = str(at or '').lower(), json.dumps(ct).lower()
                f['threshold'] = bool(ta) and (ta in tc or tc.strip('"') in ta) or (und and gap)
            f['unit'] = (norm_unit(p.get('unit')) == norm_unit(s['unit'])) or (not p.get('unit') and not s['unit']) or \
                (str(p.get('unit') or '').lower() in UNSTATED and s['unit'] is None) or (und and gap)
            f['decision_type'] = p.get('decision_type') == s['decision_type']
            f['rule_stated'] = not (p.get('rule_fully_stated') is False and not gap)
            r['agree'] = f
            rows.append(r)
            if not f['rule_stated']:
                apply.append({'rule': 'A1', 'stage': s['id'], 'effect': 'annotation', 'missing': p.get('missing')})
            if not (f['comparator'] and f['threshold'] and f['unit']):
                apply.append({'rule': 'A2', 'stage': s['id'], 'effect': 'evaluate drops' if r['keyed'] else 'annotation',
                              'card': {'comparator': s['comparator'], 'threshold': ct, 'unit': s['unit']},
                              'auditor': {'comparator': p.get('comparator'), 'threshold': at, 'unit': p.get('unit')}})
            if not f['decision_type']:
                drop = bool(r['keyed']) and p.get('decision_type') in ('literature', 'engine', 'outcome_class')
                apply.append({'rule': 'A3', 'stage': s['id'], 'effect': 'drop items' if drop else 'annotation',
                              'card': s['decision_type'], 'auditor': p.get('decision_type')})
        else:
            fam, ccls = LAW_USE[a['name']]
            acls = str(p.get('law_class') or '').strip().lower()
            ok_cls = acls == ccls
            invalid = fam is not None and ((fam == 'T7' and acls != 'fit') or (fam in ('T1', 'T3') and acls == 'fit'))
            cons = json.dumps(p.get('constants_with_source'), ensure_ascii=False) + ' ' + json.dumps(p.get('stated_assumptions'), ensure_ascii=False)   # VC-E31: no \u escapes
            cdis = None
            if a['name'] in CONSTS:
                key, val = CONSTS[a['name']]
                nums = [float(x) for x in re.findall(r'(?:' + ('haven[^0-9]{0,40}' if key == 'haven' else
                        r'(?:\bmu\b|µ|μ)[^0-9]{0,20}') + r')(\d+(?:\.\d+)?)', cons, re.I)]
                cdis = any(abs(v - val) > 1e-9 for v in nums)
            rows.append({'n': a['n'], 'card': a['card'], 'name': a['name'], 'family': fam, 'card_class': ccls,
                         'auditor_class': acls, 'class_agree': ok_cls, 'family_invalid': invalid,
                         'constant_disagree': cdis, 'auditor': p})
            if invalid or cdis:
                apply.append({'rule': 'A4', 'law': a['name'], 'effect': 'drop items' if fam else 'annotation',
                              'family': fam, 'auditor_class': acls, 'constant_disagree': cdis})
            elif not ok_cls:
                apply.append({'rule': 'A4', 'law': a['name'], 'effect': 'annotation', 'card_class': ccls,
                              'auditor_class': acls})
    json.dump({'spent_usd': A['spent_usd'], 'rows': rows, 'apply': apply}, open(os.path.join(OUT, 'compare.json'), 'w'),
              indent=1, default=str)
    for r in rows:
        print(r['n'], r.get('id', ''), r['name'], r.get('agree') or {k: r[k] for k in ('auditor_class', 'class_agree', 'family_invalid', 'constant_disagree')})
    print('apply:', json.dumps(apply, default=str)[:3000])


if __name__ == '__main__':
    {'run': run, 'compare': compare}[sys.argv[1]]()
