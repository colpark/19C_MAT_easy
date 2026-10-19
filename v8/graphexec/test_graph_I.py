"""Toy tests of graph I (kit D machinery). The toy adapters read the toy truth directly; real adapters must go through the
server's tools. Kit B and kit D tests must still pass beside this one.
  python test_graph_I.py
"""
import copy
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'mcenv'))
import graphexec as G  # noqa: E402
import graphexec_d as D  # noqa: E402
from rule_I import rule_I_registry_match, fold_dist  # noqa: E402

SPEC = os.path.join(os.path.dirname(HERE), 'spec')
RULES = {'I_registry_match': rule_I_registry_match}
EXT = {'panel_fails': True, 'stratum': 'K', 'blindfm_pairs_resolved': 0, 'constant_prior_resolved': 0}
TH = 12.0          # toy theta_match relative to the lattice, degrees


def world(label, key, rod_angle, fm_margin=0.40, lattice_in_plan=True, needs_two=False, disp=0.0, **extra):
    t = {'task_id': f'toy-{label}-{disp}', 'world': label, 'key': key, 'claim': 'toy claim', 'sample_text': 'toy sample',
         'm0': 'm0', '_truth': {'rod': rod_angle, 'fm_margin': fm_margin, 'lattice': lattice_in_plan, 'needs_two': needs_two,
                                'disp': disp}}
    t.update(extra)
    return t


def sim(node, inp, t, ctx):
    plan = [{'kind': 'afm_scan', 'size_nm': 500, 'px': 512}]
    if t['_truth']['lattice']:
        plan.append({'kind': 'lattice_scan', 'size_nm': 20, 'px': 256})
    return dict(outputs={'window': [0.0, 60.0], 'plan': plan, 'predicted_D': 31.2, 'predicted_cost_min': 40.0}, cost_min=0.0,
                calls=[{'tool': 'simulate'}])


def instrument(node, inp, t, ctx):
    ids = [f"{node['id']}_{p['kind']}{i + 1}" for i, p in enumerate(inp['plan'])]
    return dict(outputs={'measurements': ids, 'cost_min': 20.0 * len(ids)}, cost_min=20.0 * len(ids),
                calls=[{'tool': p['kind'], 'args': p} for p in inp['plan']])


def fit(node, inp, t, ctx):
    tr = t['_truth']
    ids = list(inp['measurements']) + list(inp.get('measurements2') or [])
    has_lat = any('lattice_scan' in i for i in ids)
    n_afm = sum('afm_scan' in i for i in ids)
    if not has_lat or n_afm == 0:           # the angle relative to the lattice is undefined without a lattice scan
        return dict(outputs={'phase': None, 'angle_rel_deg': None, 'angle_se_deg': None, 'runner_up': None, 'D': 3.1}, cost_min=0.0, calls=[])
    d = 40.2 if (not tr['needs_two'] or node['id'] == 'S1f') else 12.4
    a = tr['rod'] % 60
    return dict(outputs={'phase': str(round(a)), 'angle_rel_deg': a + 0.4, 'angle_se_deg': 1.1, 'runner_up': str(round((a + 30) % 60)), 'D': d},
                cost_min=0.0, calls=[{'tool': 'fit'}])


def fm_structure(node, inp, t, ctx):
    return dict(outputs={'carboxylate_geometry': {'n': 12, 'rows': 3}, 'n_carboxylate': 12.0, 'stated_error': 0.8}, cost_min=0.0,
                calls=[{'tool': 'structure'}])


def fm_registry(node, inp, t, ctx, flip=False):
    m = t['_truth']['fm_margin']
    e = {'reg_a': -1.0, 'reg_b': -1.0 + m}
    ang = {'reg_a': TH, 'reg_b': TH + 30.0}
    if flip:
        ang = {'reg_a': TH + 30.0, 'reg_b': TH}
    s = G.summarize_R(e)
    return dict(outputs={'energies': e, 'registry_angles': ang, 'theta_match': ang[s['lowest']], 'stated_error': 0.05, **s}, cost_min=0.0,
                calls=[{'tool': 'registry_energy'}])


LAB = {'simulator': sim, 'instrument': instrument, 'fit': fit}


def ad(fm_reg=fm_registry, **kw):
    a = dict(LAB, fm=lambda n, i, t, c: (fm_structure if n['id'] == 'S2a' else fm_reg)(n, i, t, c))
    a.update(kw)
    return a


def ex_for(g, adapters):
    return D.executor(g, adapters, rules=RULES)


def rows(res):
    return {r['test']: r['pass'] for r in res['rows']}


def twins(**kw):
    return {'A': world('A', 'SUPPORTED', TH, **kw), 'B': world('B', 'REFUTED', TH + 30, **kw)}


def holds(tw):
    return [('hold_displacement', k, world(k, t['key'], t['_truth']['rod'], disp=0.1)) for k, t in tw.items()]


def main():
    g = D.load(os.path.join(SPEC, 'graph_I.json'))
    assert D.check(g) in (None, 'jsonschema not installed, schema check skipped')
    up = g.upstream('S3')
    assert {'S1c', 'S2a', 'S2b'} <= up
    assert not (g.upstream('S2b') & {'S1a', 'S1b', 'S1c'}) and not (g.upstream('S1c') & {'S2a', 'S2b'}), 'S1 and S2 are independent links'
    print('graph I loads, schema ok, S1 and the S2a to S2b chain are independent and join at S3')

    # rule unit tests, modulo the lattice period
    assert fold_dist(58, 5, 60) == 7 and fold_dist(5, 35, 60) == 30
    # exemplar suite
    tw = twins()
    hd = holds(tw)
    ex = ex_for(g, ad())
    txt = ('S1c fitted 12.4 deg relative to the lattice with D 40.2 against 25. S2b put the matched registry at 12.0 deg with a margin of 0.4 '
           'against the band 0.1, so the rods lie in the matched registry.')
    first = D.validate_d(g, ex, tw, hd, EXT)
    res = D.validate_d(g, ex, tw, hd, EXT, {'w': (txt, list(first['logs'].values()))})
    print(D.validation_table(res))
    assert res['pass'], 'exemplar suite failed'
    assert res['logs']['base_A']['verdict'] == 'SUPPORTED' and res['logs']['base_B']['verdict'] == 'REFUTED'
    print('exemplar suite (twins A rods at theta_match, B rods 30 deg away): PASS')
    # selection rows with the same adapters
    sel = D.validate_d(g, ex, tw, hd, rows='selection')
    assert sel['pass'], D.validation_table(sel)
    print('selection rows: PASS')

    # remeasure path
    tw2 = twins(needs_two=True)
    r2 = D.validate_d(g, ex, tw2, holds(tw2), EXT)
    b = r2['logs']['base_A']
    assert rows(r2)['correctness'] and rows(r2)['measurement factorial'], D.validation_table(r2)
    assert [G.step_of(b, n)['status'] for n in ('S1d', 'S1e', 'S1f')] == ['ran'] * 3 and b['verdict'] == 'SUPPORTED'
    print('remeasure path: S1c short of D_accept, S1d to S1f run, verdict as the key')

    # (a) negative control: no lattice scan -> CANNOT_TELL, never determinate (the planner never buys one)
    nl = twins(lattice_in_plan=False)
    for k, t in nl.items():
        lg = ex.run(t)
        assert lg['verdict'] == 'CANNOT_TELL', (k, lg['verdict'])
        assert G.out_of(lg, 'S1c', 'angle_rel_deg') is None
    # even the best possible shortcut (an angle in the sample frame) is not accepted as a lattice-referenced angle by the rule
    lg = ex.run(nl['A'], {'kind': 'ablate', 'nodes': ['S1b', 'S1e']})
    assert lg['verdict'] == 'CANNOT_TELL'
    print('negative control (a): no lattice scan gives CANNOT_TELL in both worlds')

    # (b) negative control: FM margin inside the band -> CANNOT_TELL
    inb = twins(fm_margin=0.03)
    for k, t in inb.items():
        lg = ex.run(t)
        assert lg['verdict'] == 'CANNOT_TELL', (k, lg['verdict'])
        assert G.step_of(lg, 'S2b')['accepted'] is False
    print('negative control (b): FM margin 0.03 inside the band 0.1 gives CANNOT_TELL in both worlds')

    # (c) negative control: flipped FM (theta_match swapped with the other registry) -> verdict flips
    exf = ex_for(g, ad(fm_reg=lambda n, i, t, c: fm_registry(n, i, t, c, flip=True)))
    for k, t in tw.items():
        v0, v1 = ex.run(t)['verdict'], exf.run(t)['verdict']
        assert v1 == {'SUPPORTED': 'REFUTED', 'REFUTED': 'SUPPORTED'}[v0], (k, v0, v1)
    print('negative control (c): flipped FM flips both verdicts (A to REFUTED, B to SUPPORTED)')

    # angle matching neither registry -> CANNOT_TELL; wrap-around across the lattice period
    lg = ex.run(world('X', 'CANNOT_TELL', TH + 15))
    assert lg['verdict'] == 'CANNOT_TELL'
    lg = ex.run(world('W', 'SUPPORTED', TH + 60 - 3))
    assert lg['verdict'] == 'SUPPORTED'
    print('angle halfway between registries gives CANNOT_TELL; angle one period away still matches')

    # shortcuts fail
    def neg(name, fn):
        spec = copy.deepcopy(g.spec)
        spec['nodes'][-1]['fn'] = name
        gg = G.Graph(spec)
        return D.validate_d(gg, D.executor(gg, ad(), rules={name: fn}), tw, hd, EXT)

    def fm_only(inp, ctx, params):
        return {'verdict': 'SUPPORTED', 'reason': 'FM says matched', 'margin_used': inp.get('margin')}

    def const_ref(inp, ctx, params):
        return {'verdict': 'REFUTED', 'reason': 'constant', 'margin_used': None}

    def angle_only(inp, ctx, params):
        a = inp.get('angle_rel_deg')
        if a is None:
            return {'verdict': 'CANNOT_TELL', 'reason': 'x', 'margin_used': None}
        return {'verdict': 'SUPPORTED' if fold_dist(a, 0.0, 60) < 15 else 'REFUTED', 'reason': 'angle only', 'margin_used': None}

    for name, fn in (('I_fm_only', fm_only), ('I_const', const_ref)):
        r = neg(name, fn)
        assert not rows(r)['correctness'], name
    r = neg('I_angle_only', angle_only)           # ignores the FM: correct on the toy but the prior twin and necessity rows fail
    rr = rows(r)
    assert not rr['necessity S2b'] and not rr['prior flip'], rr
    print('negative shortcuts: FM only and constant fail correctness; angle only (no FM) fails the necessity of S2b and the prior flip')

    # ablating the lattice-referenced identification or either FM node blocks every world
    a = rows(res)
    for n in ('necessity S1a+S1d', 'necessity S1b+S1e', 'necessity S1c+S1d+S1e+S1f', 'necessity S2a', 'necessity S2b'):
        assert a[n], n
    print('necessity: S1a, S1b, S1c (with remeasure path), S2a and S2b are each necessary')

    try:
        import json
        import jsonschema
        schema = json.load(open(os.path.join(SPEC, 'trace_schema.json')))
        for lg in res['logs'].values():
            jsonschema.validate(lg, schema)
        print('trace logs validate against trace_schema.json:', len(res['logs']))
    except ImportError:
        print('jsonschema not installed, trace schema check skipped')
    print('\nALL GRAPH I TESTS PASSED')


if __name__ == '__main__':
    main()
