"""v6 kit D (2026-10-18): task families beyond claim R, in the 19C scope (lab, simulator and FMs, no priced DFT).

New files only. Kit B (graphexec.py, graph_R_v2.json, graph_schema.json) stays byte-identical and is imported.

Adds
  rules        settle_identity (S1g: the accepted identification, remeasure first), T_lower_after (claim T)
  helpers      final_phases (one entry per sample), decision_margin
  validate_d   the validation suite for any number of worlds per compound (R and H twins, T quads):
                 selection rows   correctness, necessity of the measurement nodes, measurement factorial, hold
                 FM rows          necessity of the prior, prior flip, abstention (squeeze into the band), sufficiency,
                                  non-bypass, faithfulness (number lock)
               A world may carry
                 accept       the verdicts that count as correct (default [key]). In band, B1's rule gives [key, CANNOT_TELL]
                 fm_decides   whether the FM decides this world (default True). In a T quad the no-change worlds have
                              False: the rule refutes them from the measurement alone, so FM interventions must leave them
                              unchanged.
Escalation to priced DFT is out of scope. The kit B 'escalation' row becomes 'abstention': a squeezed FM gives
CANNOT_TELL wherever the FM decides.

  python graphexec_d.py check ../spec/graph_T.json      load a kit D graph and check it against graph_schema_d.json
  python graphexec_d.py mermaid ../spec/graph_T.json    print a Mermaid diagram
"""
from __future__ import annotations

import os
import sys
from typing import Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import graphexec as G  # noqa: E402  (kit B, unchanged)

SCHEMA_D = os.path.join(G.SPEC_DIR, 'graph_schema_d.json')
DETERMINATE = G.DETERMINATE
OPPOSITE = {'SUPPORTED': 'REFUTED', 'REFUTED': 'SUPPORTED'}


def load(path: str) -> G.Graph:
    return G.Graph.load(path)


def check(graph: G.Graph) -> Optional[str]:
    return graph.check_schema(SCHEMA_D)


# ----------------------------------------------------------------------------------------------------------------
# Rules
# ----------------------------------------------------------------------------------------------------------------
def rule_settle_identity(inp, ctx, params):
    """S1g: the first entry [node, phase_input, D_input] whose node ran and was accepted gives the phase and D.
    Otherwise phase and D are None (the node is not accepted) and D_best keeps the largest D seen, for the log."""
    best = None
    for node, ph, dname in params['entries']:
        d = inp.get(dname)
        if d is not None:
            best = d if best is None else max(best, d)
        if ctx.ran.get(node) and ctx.accepted.get(node) and inp.get(ph) is not None:
            return {'phase': inp[ph], 'D': d, 'D_best': best, 'source': node}
    return {'phase': None, 'D': None, 'D_best': best, 'source': None}


def rule_T_lower_after(inp, ctx, params):
    pri, band = params.get('prior', 'S2'), ctx.const['band']
    pre = G._identified({'phase': inp.get('phase_pre')}, ctx, {'identify': params['identify_pre']})
    post = G._identified({'phase': inp.get('phase_post')}, ctx, {'identify': params['identify_post']})
    if pre is None or post is None:
        return {'verdict': 'CANNOT_TELL', 'reason': 'a sample is not identified decisively', 'margin_used': None}
    if pre == post:
        return {'verdict': 'REFUTED', 'reason': f'both samples hold {pre}: the polymorph did not change', 'margin_used': None}
    e = inp.get('energies')
    if not ctx.ran.get(pri) or not e or pre not in e or post not in e:
        return {'verdict': 'CANNOT_TELL', 'reason': 'no energy ranking for the two polymorphs', 'margin_used': None}
    d = round(e[post] - e[pre], 6)
    m = abs(d)
    if m < band:
        return {'verdict': 'CANNOT_TELL', 'reason': f'{post} minus {pre} is {d} eV/atom, inside the band {band}', 'margin_used': m}
    v = 'SUPPORTED' if d < 0 else 'REFUTED'
    return {'verdict': v, 'reason': f'{pre} became {post}, FM difference {d} eV/atom against the band {band}', 'margin_used': m}


RULES_D = {'settle_identity': rule_settle_identity, 'T_lower_after': rule_T_lower_after}
INTERVENTIONS_D = {'R': (G.flip_R, G.squeeze_R), 'H': (G.flip_H, G.squeeze_H), 'T': (G.flip_R, G.squeeze_R)}


def executor(graph: G.Graph, adapters, rules=None, constants=None, source='gold') -> G.Executor:
    rr = dict(RULES_D)
    rr.update(rules or {})
    return G.Executor(graph, adapters, rules=rr, constants=constants, source=source)


# ----------------------------------------------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------------------------------------------
def final_phases(log: dict, graph: G.Graph) -> tuple:
    """The finally identified phase per sample: the re-identification node's when it ran and was accepted, else the
    identification node's. One entry for single-sample graphs."""
    samples = graph.spec.get('samples')
    if not samples:
        return (G.final_phase(log, graph),)
    out = []
    for s in samples:
        rid, idn = graph.roles.get(f'reidentify_{s}'), graph.roles[f'identify_{s}']
        ph = None
        if rid:
            st = G.step_of(log, rid)
            if st.get('status') == 'ran' and st.get('accepted'):
                ph = st['outputs'].get('phase')
        out.append(ph if ph is not None else G.out_of(log, idn, 'phase'))
    return tuple(out)


def decision_margin(log: dict, graph: G.Graph):
    m = G.out_of(log, graph.spec['final'], 'margin_used')
    return m if m is not None else G.out_of(log, graph.roles['prior'], 'margin')


def _accepts(world: dict) -> List[str]:
    return list(world.get('accept') or [world['key']])


def _fm_decides(world: dict) -> bool:
    return bool(world.get('fm_decides', True))


# ----------------------------------------------------------------------------------------------------------------
# Validation suite
# ----------------------------------------------------------------------------------------------------------------
def validate_d(graph: G.Graph, ex: G.Executor, worlds: Dict[str, dict], holds: List[tuple] = (),
               external: Optional[dict] = None, rendered: Optional[Dict[str, tuple]] = None, rows: str = 'all') -> dict:
    """worlds: {label: task}, each with key (and optionally accept, fm_decides). holds: [(label, world_label, task)].
    rows: 'selection' (FM-independent rows, run with the ceiling adapters before any FM call) or 'all'.
    external: {'panel_fails': bool, 'stratum': 'K' or 'E', 'blindfm_pairs_resolved': int,
               'constant_prior_resolved': int, ...}. Extra keys are reported."""
    pri = graph.roles['prior']
    flip, squeeze = INTERVENTIONS_D[graph.spec['claim_type']]
    base = {k: ex.run(t) for k, t in worlds.items()}
    logs = {f'base_{k}': v for k, v in base.items()}
    out = []

    out.append(G._row('correctness', all(base[k]['verdict'] in _accepts(worlds[k]) for k in worlds),
                      {k: [base[k]['verdict'], _accepts(worlds[k])] for k in worlds}))

    for nid in graph.spec['necessity_nodes']:
        if nid == pri and rows == 'selection':
            continue
        group = [nid] + [m for m in graph.order if m != nid and (graph.nodes[m].get('trigger', {}).get('node') == nid
                                                                  or graph.nodes[m].get('fallback_for') == nid)]
        name = '+'.join(group)
        res = {k: ex.run(t, {'kind': 'ablate', 'nodes': group, 'label': f'ablate_{name}'}) for k, t in worlds.items()}
        logs.update({f'ablate_{name}_{k}': v for k, v in res.items()})
        if nid == pri:
            ok = all((r['verdict'] == 'CANNOT_TELL') if _fm_decides(worlds[k]) else (r['verdict'] == base[k]['verdict'])
                     for k, r in res.items())
        else:
            ok = all(r['verdict'] == 'CANNOT_TELL' for r in res.values())
        out.append(G._row(f'necessity {name}', ok, {k: r['verdict'] for k, r in res.items()}))

    ids = {k: final_phases(base[k], graph) for k in worlds}
    verdicts = {k: base[k]['verdict'] for k in worlds}
    distinct = len(set(ids.values())) == len(ids) and all(None not in v for v in ids.values())
    both_sides = {'SUPPORTED', 'REFUTED'} <= set(worlds[k]['key'] for k in worlds)
    ok = distinct and both_sides and all(verdicts[k] in DETERMINATE and verdicts[k] == worlds[k]['key'] for k in worlds)
    out.append(G._row('measurement factorial', ok, {k: {'identified': list(ids[k]), 'verdict': verdicts[k]} for k in worlds}))

    hold_detail, hold_ok = {}, True
    for label, k, t in holds:
        r = ex.run(t, {'kind': 'hold', 'label': label})
        logs[f'{label}_{k}'] = r
        same = r['verdict'] == base[k]['verdict'] and final_phases(r, graph) == ids[k]
        hold_ok &= same
        hold_detail[f'{label}_{k}'] = r['verdict']
    out.append(G._row('hold', hold_ok and len(holds) > 0, hold_detail or 'no hold worlds given'))

    if rows == 'selection':
        return {'graph_id': graph.spec['graph_id'], 'rows': out, 'pass': all(r['pass'] for r in out), 'logs': logs}

    det, ok = {}, True
    for k, t in worlds.items():
        r = ex.run(t, {'kind': 'override', 'node': pri, 'fn': flip, 'label': 'prior_flip'})
        logs[f'prior_flip_{k}'] = r
        b = base[k]['verdict']
        ok &= (r['verdict'] == OPPOSITE.get(b)) if _fm_decides(worlds[k]) else (r['verdict'] == b)
        det[k] = [b, r['verdict']]
    out.append(G._row('prior flip', ok, det))

    det, ok = {}, True
    for k, t in worlds.items():
        r = ex.run(t, {'kind': 'override', 'node': pri, 'fn': squeeze, 'label': 'prior_squeeze'})
        logs[f'prior_squeeze_{k}'] = r
        b = base[k]['verdict']
        ok &= (r['verdict'] == 'CANNOT_TELL') if _fm_decides(worlds[k]) else (r['verdict'] == b)
        det[k] = [b, r['verdict']]
    out.append(G._row('abstention', ok, det))

    c = ex.constants
    factor, band, budget = c.get('exemplar_margin_factor', 2), c['band'], c['budget_min']
    suff = {k: {'margin': decision_margin(base[k], graph), 'cost_min': base[k]['cost_min']} for k in worlds}
    ok = all(v['cost_min'] <= budget for v in suff.values()) and all(
        suff[k]['margin'] is not None and suff[k]['margin'] >= factor * band for k in worlds if _fm_decides(worlds[k]))
    out.append(G._row('sufficiency', ok, suff))

    ext = external or {}
    if ext:
        ok = (ext.get('blindfm_pairs_resolved', 0) == 0 and ext.get('constant_prior_resolved', 0) == 0
              and (bool(ext.get('panel_fails')) or ext.get('stratum') == 'E'))
        out.append(G._row('non-bypass', ok, dict(ext)))
    else:
        out.append(G._row('non-bypass', False, 'no external evidence given'))

    if rendered:
        bad = {name: G.number_lock(text, lgs, graph) for name, (text, lgs) in rendered.items()}
        out.append(G._row('faithfulness', all(not b for b in bad.values()), bad))
    else:
        out.append(G._row('faithfulness', False, 'no rendered trace given'))

    return {'graph_id': graph.spec['graph_id'], 'rows': out, 'pass': all(r['pass'] for r in out), 'logs': logs}


validation_table = G.validation_table

if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] not in ('mermaid', 'check'):
        print(__doc__)
        sys.exit(2)
    g = load(sys.argv[2])
    if sys.argv[1] == 'mermaid':
        print(g.mermaid())
    else:
        msg = check(g)
        print('order:', ' -> '.join(g.order))
        print(msg or 'schema ok')
