#!/usr/bin/env python3
"""C4 decision mining (skill C4). A decision point is keyable for a material only when its rule is stated (D2, a
frozen reading counts for a logged rule gap) AND its deciding value is deposited for that material; otherwise it is a
template only. Outputs decisions.jsonl (one row per material x decision point) and a count per decision type.

usage: AIIDA_PATH=... decisions.py OUT_DIR   (reads CARD_*.json, materials_*.jsonl, TOLERANCES_trackC.json, AiiDA trackC)
"""
import json, os, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))


def li7nbo6_graph():
    """Decision points visible in the one full provenance graph (Li7NbO6): process labels with exit states."""
    from aiida import load_profile, orm
    load_profile('trackC')
    c = defaultdict(Counter)
    iters = Counter()
    for n in orm.load_group('xm46_Li7NbO6').nodes:
        if isinstance(n, orm.ProcessNode):
            c[n.process_label][f'{n.process_state.value if n.process_state else None}:{n.exit_status}'] += 1
            if n.process_label == 'FlipperCalculation':
                iters['md_iterations'] += 1
    return {k: dict(v) for k, v in c.items()}, dict(iters)


def main():
    out = sys.argv[1]
    cl = json.load(open(os.path.join(HERE, 'CARD_liion.json')))
    cj = json.load(open(os.path.join(HERE, 'CARD_jarvis.json')))
    tol = json.load(open(os.path.join(HERE, 'TOLERANCES_trackC.json')))
    ml = [json.loads(l) for l in open(os.path.join(HERE, 'materials_liion.jsonl'))]
    mj = [json.loads(l) for l in open(os.path.join(HERE, 'materials_jarvis.jsonl'))]
    graph, iters = li7nbo6_graph()
    rows = []

    def add(m, src, stage, dtype, keyable, reason, outcome=None, deciding=None):
        rows.append({'material_id': m, 'source': src, 'stage': stage, 'decision_type': dtype, 'keyable': keyable,
                     'reason': reason, 'outcome': outcome, 'deciding_value': deciding})

    for m in ml:
        mid, fp = m['material_id'], m['stages']['FPMD']
        # recovery (S6r SCF reruns, S7d drift), refinement (S7 pinball loop): outcomes deposited for Li7NbO6 only
        for st, dt in [('S6r', 'recovery'), ('S7', 'refinement'), ('S7d', 'recovery')]:
            if m['reduced_formula'] == 'Li7NbO6':
                add(mid, 'liion', st, dt, False, 'one material only (CR4 one): below any family floor; template', 'graph')
            else:
                add(mid, 'liion', st, dt, False, 'outcome not deposited (provenance for Li7NbO6 only)')
        add(mid, 'liion', 'S9', 'literature', False, 'literature judgement, not computable (template only)', 'kept (deposited)')
        # escalation S11: the rule is stated; the deciding value (D at 1000 K) is deposited only for escalated materials
        if '1000' in fp:
            esc = len(fp) >= 2
            add(mid, 'liion', 'S11', 'escalation', True, 'rule stated (frozen S10 reading), 1000 K panel deposited',
                'go' if esc else 'stop', fp['1000']['D'])
        else:
            add(mid, 'liion', 'S11', 'escalation', False, 'no deposited 1000 K panel (VC-E18)')
        add(mid, 'liion', 'S10', 'outcome_class', False, 'S12 class criterion unstated (rule gap); S10 panels missing for '
            'Table 1 materials')
        add(mid, 'liion', 'engine', 'engine', False, 'engine choice (pinball vs FPMD vs PET-MAD) is not a per-material '
            'rule; overlap of engines on keyed materials is 0 (template)')
    for m in mj:
        mid, s = m['material_id'], m['stages']
        add(mid, 'jarvis', 'J1', 'static', False, 'J1 recount fails (+45 %, VC-E17): rule ambiguity')
        add(mid, 'jarvis', 'J2', 'static', False, 'no deposited N(0)')
        add(mid, 'jarvis', 'J3', 'static', False, 'cell basis ambiguous (194 of 1,058 deposited with > 5 atoms)')
        add(mid, 'jarvis', 'J4', 'escalation', False, 'every deposited material was escalated (no stop class deposited)', 'go')
        add(mid, 'jarvis', 'J5', 'static', bool(m['route_agree_Tc'] and not s['J5']['near_threshold']),
            'Tc >= 5 K (frozen reading); keyable when the alpha2F route agrees and Tc is not within tau of 5 K',
            'pass' if s['J5']['pass'] else 'fail', s['J5']['Tc_dep'])
        add(mid, 'jarvis', 'J6', 'static', True, 'deposited stability label (frozen reading)',
            'pass' if s['J6']['pass'] else 'fail', s['J6']['stability'])
    with open(os.path.join(out, 'decisions.jsonl'), 'w') as f:
        for r in rows:
            f.write(json.dumps(r, default=str) + '\n')
    cnt = defaultdict(Counter)
    for r in rows:
        cnt[(r['source'], r['stage'], r['decision_type'])]['keyable' if r['keyable'] else 'template'] += 1
        if r['keyable']:
            cnt[(r['source'], r['stage'], r['decision_type'])][f"outcome:{r['outcome']}"] += 1
    rep = {'li7nbo6_graph_processes': graph, 'li7nbo6_iterations': iters,
           'counts': {f'{a}|{b}|{c}': dict(v) for (a, b, c), v in sorted(cnt.items())}}
    json.dump(rep, open(os.path.join(out, 'DECISIONS_counts.json'), 'w'), indent=1)
    print(json.dumps(rep['counts'], indent=1))


if __name__ == '__main__':
    main()
