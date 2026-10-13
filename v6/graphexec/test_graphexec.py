"""Self-test of the v6 reference executor on toy worlds (no environment server needed).

The toy adapters read the toy truth directly. Real adapters must not: they go through the environment server's tools.
  python test_graphexec.py
"""
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import graphexec as G  # noqa: E402

SPEC = os.path.join(os.path.dirname(HERE), 'spec')
LIB = ['P1', 'P2']
FM_E = {'P1': -0.336, 'P2': -0.217}
DFT_E = {'P1': -0.293, 'P2': -0.157}
FM_H = {'P1': 0.005, 'P2': 0.150}
DFT_H = {'P1': -0.017, 'P2': 0.134}


def task(world, key, claim_type='R', quiet=True, disp=0.0):
    return {'task_id': f'toy-{claim_type}-{world}-{disp}', 'world': world, 'library': LIB, 'm0': 'm0', 'key': key,
            'claim': 'toy claim', '_truth': {'phase': 'P1' if world == 'A' else 'P2', 'quiet': quiet, 'disp': disp}}


def sim(node, inp, t, ctx):
    plan = [{'start': 37.3, 'stop': 39.3, 'step': 0.01, 'time_per_step': 5.0}]
    return dict(outputs={'window': [37.3, 39.3], 'plan': plan, 'predicted_D': 31.2, 'predicted_cost_min': 21.75},
                cost_min=0.0, calls=[{'tool': 'simulate', 'args': {'structures': inp['library']}}])


def instrument(node, inp, t, ctx):
    ids = [f'm{i + 1}' for i, _ in enumerate(inp['plan'])]
    return dict(outputs={'measurements': ids, 'cost_min': 21.75 * len(ids)}, cost_min=21.75 * len(ids),
                calls=[{'tool': 'measure', 'args': p} for p in inp['plan']])


def fit(node, inp, t, ctx):
    tr = t['_truth']
    targeted = len(inp['measurements']) > 0
    D = 3.1 if (tr['quiet'] and not targeted) else 40.2
    other = 'P2' if tr['phase'] == 'P1' else 'P1'
    return dict(outputs={'phase': tr['phase'], 'runner_up': other, 'D': D}, cost_min=0.0, calls=[{'tool': 'fit'}])


def fm_R(node, inp, t, ctx):
    e = dict(FM_E)
    return dict(outputs=dict({'energies': e, 'stated_error': 0.045}, **G.summarize_R(e)), cost_min=0.0,
                calls=[{'tool': 'energy', 'args': {'structure_name': k}} for k in e])


def dft_R(node, inp, t, ctx):
    e = dict(DFT_E)
    cost = ctx.const['dft_price_min'] * len(e)
    return dict(outputs={'energies_dft': e, 'lowest_dft': min(e, key=e.get), 'cost_min': cost}, cost_min=cost,
                calls=[{'tool': 'energy_dft', 'args': {'structure_name': k}} for k in e])


def fm_H(node, inp, t, ctx):
    h = FM_H[inp['phase']]
    return dict(outputs={'hull_distance': h, 'decomposition': ['toy'], 'stated_error': 0.045,
                         'margin': abs(h - ctx.const['threshold'])}, cost_min=0.0, calls=[{'tool': 'hull'}])


def dft_H(node, inp, t, ctx):
    cost = ctx.const['dft_price_min']
    return dict(outputs={'hull_distance_dft': DFT_H[inp['phase']], 'cost_min': cost}, cost_min=cost,
                calls=[{'tool': 'hull_dft'}])


ADAPT_R = {'simulator': sim, 'instrument': instrument, 'fit': fit, 'fm': fm_R, 'dft': dft_R}
ADAPT_H = {'simulator': sim, 'instrument': instrument, 'fit': fit, 'fm': fm_H, 'dft': dft_H}
EXT = {'panel_fails': True, 'blindfm_pairs_resolved': 0, 'llm_probe_resolved': 0, 'llm_probe_pairs': 3,
       'probe_max_fraction': 1 / 3}


def suite(graph, adapters, claim_type='R', quiet=True, rules=None, text=None):
    ex = G.Executor(graph, adapters, rules=rules)
    twins = {'A': task('A', 'SUPPORTED', claim_type, quiet), 'B': task('B', 'REFUTED', claim_type, quiet)}
    holds = [('hold_displacement', 'A', task('A', 'SUPPORTED', claim_type, quiet, disp=0.1)),
             ('hold_displacement', 'B', task('B', 'REFUTED', claim_type, quiet, disp=0.1))]
    first = G.validate(graph, ex, twins, holds, EXT)
    lgs = list(first['logs'].values())
    rendered = {'A': (text or '', lgs)}
    return G.validate(graph, ex, twins, holds, EXT, rendered)


def rows(res):
    return {r['test']: r['pass'] for r in res['rows']}


def main():
    gR = G.Graph.load(os.path.join(SPEC, 'graph_R.json'))
    gH = G.Graph.load(os.path.join(SPEC, 'graph_H.json'))
    for g in (gR, gH):
        msg = g.check_schema()
        assert msg is None or 'skipped' in msg, msg
    assert gR.order == ['S0', 'S1a', 'S1b', 'S1c', 'S2', 'S2x', 'S3'], gR.order
    assert 'S1c' not in gR.upstream('S2') and 'S1c' in gH.upstream('S2'), 'R: S1 and S2 independent, H: S2 needs S1c'

    good = ('S1c identified P1 with D 40.2 against 25, while the free scan alone gave D 3.1. '
            'S2 put P1 lowest at -0.336 eV/atom against -0.217, a margin of 0.119 outside the band 0.045.')
    res = suite(gR, ADAPT_R, text=good)
    assert res['pass'], G.validation_table(res)
    print('R exemplar suite: PASS')
    print(G.validation_table(res))

    try:
        import jsonschema
        schema = json.load(open(os.path.join(SPEC, 'trace_schema.json')))
        for lg in res['logs'].values():
            jsonschema.validate(lg, schema)
        print('trace logs validate against trace_schema.json:', len(res['logs']))
    except ImportError:
        print('jsonschema not installed, trace schema check skipped')

    global EXT
    full = EXT
    EXT = {'panel_fails': True, 'blindfm_pairs_resolved': 0}
    assert suite(gR, ADAPT_R, text=good)['pass'], 'non-bypass without the LLM probe (amendment A)'
    print('amendment A: non-bypass passes on panel and blind FM alone')
    EXT = full

    resH = suite(gH, ADAPT_H, 'H', text='S2 gave a hull distance of 0.005 eV/atom for P1, inside 0.05.')
    assert resH['pass'], G.validation_table(resH)
    print('H exemplar suite: PASS')

    loud = rows(suite(gR, ADAPT_R, quiet=False, text=good))
    assert not loud['necessity S1a'] and not loud['necessity S1b'] and loud['prior twin'], loud
    print('negative 1, loud identification: necessity of S1a and S1b fails as it should')

    spec = copy.deepcopy(gR.spec)
    spec['nodes'][-1]['fn'] = 'R_density'
    bypass = G.Graph(spec)

    def r_density(inp, ctx, params):
        if not ctx.accepted.get('S1c'):
            return {'verdict': 'CANNOT_TELL', 'reason': 'identification not decisive'}
        return {'verdict': 'SUPPORTED' if inp['phase'] == 'P1' else 'REFUTED', 'reason': 'denser polymorph rule'}

    byp = rows(suite(bypass, ADAPT_R, rules={'R_density': r_density}, text=good))
    assert not byp['prior twin'] and not byp['necessity S2+S2x'] and byp['correctness'], byp
    print('negative 2, a rule that bypasses the FM: prior twin and necessity of S2 fail as they should')

    bad = G.number_lock('S2 gave a margin of 0.150 and S9 agreed.', list(res['logs'].values()), gR)
    assert bad == ['0.150', 'unknown node S9'], bad
    print('negative 3, number lock flags', bad)

    cyc = copy.deepcopy(gR.spec)
    cyc['nodes'][1]['inputs'].append({'name': 'x', 'type': 'float', 'from': 'S1c.D'})
    try:
        G.Graph(cyc)
        raise AssertionError('cycle not detected')
    except G.GraphError as e:
        print('negative 4, cycle detected:', e)

    print()
    print(gR.mermaid())
    print('\nALL TESTS PASSED')


if __name__ == '__main__':
    main()
