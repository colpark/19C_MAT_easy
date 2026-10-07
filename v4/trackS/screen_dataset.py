#!/usr/bin/env python3
"""screen_dataset.py: score a dataset card against the PanelBench data requirements (skill M0, R1 to R12).

Usage:  python3 screen_dataset.py cards/*.json

A card is JSON (see card_template.json). Use null for anything not yet checked.
Each requirement scores pass, fail or check (unknown). Each task family then scores:
  pass   every requirement it needs passes (it can be attempted, M4 gates still decide the items)
  fail   at least one requirement it needs fails (listed)
  check  nothing fails yet, but some requirements are unknown (listed: measure these first)
Requirements are necessary, not sufficient. Standard library only.
"""
import json
import sys

PASS, FAIL, CHECK = 'pass', 'fail', 'check'
SEPARABILITY_MIN = 2.0          # R6: between-condition difference over within-condition spread


def tri(value):
    return CHECK if value is None else (PASS if value else FAIL)


def requirements(card):
    acc = card.get('access', {})
    inp = card.get('inputs_on_host', {})
    cal = card.get('calibration', {})
    des = card.get('design', {})
    obs = card.get('observables', [])
    laws = card.get('laws')
    mech = card.get('mechanisms', {})
    claims = card.get('claims', {})
    R, notes = {}, {}

    # R1 access: raw files downloadable now, license recorded
    dl, lic = acc.get('raw_downloadable'), acc.get('license')
    R['R1'] = FAIL if dl is False else (PASS if dl and lic else CHECK)
    if lic and 'NC' in lic:
        notes['R1'] = 'non-commercial license: internal only'

    # R2 readers: an open reader for every format
    R['R2'] = tri(card.get('readers', {}).get('all_formats'))

    # R3 inputs on host: the descriptor paper (needed only for paper claims). A missing claim ladder lowers yield.
    paper, ladder = inp.get('descriptor_paper'), inp.get('claim_ladder')
    R['R3'] = tri(paper)
    if paper and ladder is False:
        notes['R3'] = 'no claim ladder on the host: expect only the claims the builder extracts itself'

    # R4 calibration: absolute scales, or offset-free quantities only
    absolute, offset_free = cal.get('absolute_scales'), cal.get('offset_free_quantities')
    if absolute:
        R['R4'] = PASS
    elif absolute is False and offset_free:
        R['R4'] = PASS
        notes['R4'] = 'no absolute scale: key only differences and ratios'
    elif absolute is False and offset_free is False:
        R['R4'] = FAIL
    else:
        R['R4'] = CHECK

    # R5 validated reader: synthetic and held-out real evidence for at least one keyed observable
    validated = [o for o in obs if o.get('validated_synthetic') and o.get('validated_real')]
    if validated:
        R['R5'] = PASS
    elif any(o.get('validated_real') is None or o.get('validated_synthetic') is None for o in obs) or not obs:
        R['R5'] = CHECK
    else:
        R['R5'] = FAIL

    # R6 separability: between-condition difference over within-condition spread
    sep = des.get('separability_ratio')
    R['R6'] = CHECK if sep is None else (PASS if sep >= SEPARABILITY_MIN else FAIL)

    # R7 sampling: whole specimen or systematic fields, not curated fields
    samp = des.get('sampling')
    R['R7'] = CHECK if samp is None else (PASS if samp in ('whole_specimen', 'systematic') else FAIL)

    # R8 routes: two independent routes for a validated observable
    routes = [o.get('routes') for o in validated]
    if any(r is not None and r >= 2 for r in routes):
        R['R8'] = PASS
    elif not validated or any(r is None for r in routes):
        R['R8'] = CHECK
    else:
        R['R8'] = FAIL

    # R9 links: laws by class
    if laws is None:
        R['R9'] = CHECK
    else:
        R['R9'] = PASS if laws else FAIL

    # R10 observables: distinct validated M observables per entity
    R['R10'] = des.get('m_observables_per_entity')

    # R11 mechanisms: two or more competing mechanisms, one comparison textbook-neutral
    comp, neutral = mech.get('competing'), mech.get('textbook_neutral')
    if (comp is not None and comp < 2) or neutral is False:
        R['R11'] = FAIL
    elif comp is None or neutral is None:
        R['R11'] = CHECK
    else:
        R['R11'] = PASS

    # R12 claims: a claim source mapped to data objects
    src = claims.get('source')
    R['R12'] = CHECK if src is None else (PASS if src in ('paper', 'template') else FAIL)
    return R, notes


def max_levels(card):
    series = card.get('design', {}).get('series', [])
    levels = [s.get('levels') for s in series if s.get('shared_entities') and s.get('levels') is not None]
    return max(levels) if levels else None


def combine(parts):
    """parts: list of (label, status). Returns (status, reasons)."""
    failed = [label for label, s in parts if s == FAIL]
    unknown = [label for label, s in parts if s == CHECK]
    if failed:
        return FAIL, failed
    if unknown:
        return CHECK, unknown
    return PASS, []


def count_req(label, value, minimum):
    if value is None:
        return (f'{label} >= {minimum} (unknown)', CHECK)
    return (f'{label} >= {minimum} (has {value})', PASS if value >= minimum else FAIL)


def families(card):
    R, notes = requirements(card)
    laws = card.get('laws') or []
    laws_unknown = card.get('laws') is None or any(law.get('class') is None for law in laws)
    classes = {law.get('class') for law in laws} - {None}
    levels = max_levels(card)
    cross_modal = card.get('design', {}).get('cross_modal_identity')
    paper_claims = card.get('claims', {}).get('source') == 'paper'
    F = {}

    F['T1'] = combine([('R1', R['R1']), ('R2', R['R2']), ('R4', R['R4']), ('R5', R['R5'])])

    link = PASS if (classes or cross_modal) else (CHECK if laws_unknown else FAIL)
    match_classes = card.get('design', {}).get('match_classes', levels)
    F['T2'] = combine([('R1', R['R1']), ('R2', R['R2']), ('R5', R['R5']), ('R6', R['R6']),
                       count_req('match classes', match_classes, 3),
                       ('R9 or cross-modal identity', link)])

    t3_law = PASS if classes & {'agreement', 'independent'} else (CHECK if laws_unknown else FAIL)
    F['T3'] = combine([('R5', R['R5']), ('R6', R['R6']), ('R8', R['R8']), ('R9 agreement or independent law', t3_law)])

    t4 = [('R5', R['R5']), ('R12', R['R12'])]
    if paper_claims:
        t4.append(('R3', R['R3']))
    F['T4'] = combine(t4)

    t5 = [('R5', R['R5']), ('R6', R['R6']), count_req('R10', R['R10'], 3), ('R11', R['R11'])]
    F['T5'] = combine(t5)
    F['T6'] = combine(t5[:2] + [count_req('R10', R['R10'], 4), ('R11', R['R11'])])

    fit_laws = [law for law in laws if law.get('class') == 'fit']
    if not fit_laws:
        t7_law = ('R9 fit law', CHECK if laws_unknown else FAIL)
        t7_levels = ('levels (params + 4)', CHECK if (levels is None or laws_unknown) else FAIL)
    else:
        best = max(fit_laws, key=lambda law: (law.get('validated') is True, -(law.get('params') or 2)))
        t7_law = ('R9 fit law validated on real data', tri(best.get('validated')))
        need = (best.get('params') or 2) + 4
        series_levels = best.get('levels', levels)
        t7_levels = count_req('levels (params + 4)', series_levels, need)
    F['T7'] = combine([('R5', R['R5']), ('R6', R['R6']), ('R7', R['R7']), t7_law, t7_levels])
    return R, notes, F


def report(path):
    card = json.load(open(path))
    R, notes, F = families(card)
    print(f"\n## {card.get('name', path)}")
    if card.get('state'):
        print(f"State: {card['state']}")
    print('Requirements: ' + ', '.join(f"{k} {'unknown' if v is None else v}" for k, v in R.items()))
    for k, v in notes.items():
        print(f'  note {k}: {v}')
    print('| Family | Status | Reasons |')
    print('|---|---|---|')
    for fam, (status, reasons) in F.items():
        print(f"| {fam} | {status} | {', '.join(reasons)} |")
    open_inference = [f for f in ('T2', 'T3', 'T5', 'T6', 'T7') if F[f][0] == PASS]
    possible = [f for f in ('T2', 'T3', 'T5', 'T6', 'T7') if F[f][0] == CHECK]
    to_check = {r for f in F.values() if f[0] == CHECK for r in f[1]}
    print(f"Inference families open: {len(open_inference)} of 5 ({', '.join(open_inference) or 'none'})"
          f"{'  possible after checks: ' + ', '.join(possible) if possible else ''}")
    if to_check:
        # desk checks first, then pilot measurements, then laws
        order = ['R1', 'R2', 'R3', 'R4', 'R12', 'R11', 'R10', 'match', 'levels', 'R5', 'R8', 'R6', 'R7', 'R9']
        rank = lambda r: order.index(r.split()[0]) if r.split()[0] in order else len(order)
        print('Check, in this order: ' + '; '.join(sorted(to_check, key=rank)))
    return F


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for p in sys.argv[1:]:
        report(p)
