"""Self-test of kit D on toy worlds (no environment server). Kit B's own test must still pass beside it.

The toy adapters read the toy truth directly. Real adapters must not: they go through the environment server's tools.
  python test_graphexec_d.py
"""
import copy
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import graphexec as G  # noqa: E402
import graphexec_d as D  # noqa: E402

SPEC = os.path.join(os.path.dirname(HERE), 'spec')
FM_E = {'P0': -0.400, 'P1': -0.336, 'P2': -0.217}            # FM formation energies, eV/atom
FM_HULL = {'P0': -0.010, 'P1': 0.005, 'P2': 0.150}           # FM hull distances, eV/atom
DFT_E = {'P0': -0.381, 'P1': -0.293, 'P2': -0.157}
EXT = {'panel_fails': True, 'stratum': 'K', 'blindfm_pairs_resolved': 0, 'constant_prior_resolved': 0}


# ---------------------------------------------------------------- toy worlds
def world(label, key, lib, truth, m0s=('m0',), needs_two=(), quiet=True, disp=0.0, **extra):
    t = {'task_id': f'toy-{label}-{disp}', 'world': label, 'library': list(lib), 'key': key, 'claim': 'toy claim',
         '_truth': {'phase': truth, 'quiet': quiet, 'needs_two': set(needs_two), 'disp': disp}}
    for m in m0s:
        t[m] = m
    t.update(extra)
    return t


def _sample(node):
    return (node.get('params') or {}).get('sample')


def sim(node, inp, t, ctx):
    plan = [{'start': 37.3, 'stop': 39.3, 'step': 0.01, 'time_per_step': 5.0, 'sample': _sample(node)}]
    return dict(outputs={'window': [37.3, 39.3], 'plan': plan, 'predicted_D': 31.2, 'predicted_cost_min': 21.75},
                cost_min=0.0, calls=[{'tool': 'simulate', 'args': {'structures': inp['library']}}])


def instrument(node, inp, t, ctx):
    ids = [f"{node['id']}_m{i + 1}" for i, _ in enumerate(inp['plan'])]
    return dict(outputs={'measurements': ids, 'cost_min': 21.75 * len(ids)}, cost_min=21.75 * len(ids),
                calls=[{'tool': 'measure', 'args': p} for p in inp['plan']])


def fit(node, inp, t, ctx):
    tr, s = t['_truth'], _sample(node)
    phase = tr['phase'][s] if s else tr['phase']
    n = len(inp['measurements']) + len(inp.get('measurements2') or [])
    if not tr['quiet']:
        d = 40.2
    elif (s or 'one') in tr['needs_two']:
        d = 3.1 if n == 0 else (12.4 if n == 1 else 40.2)
    else:
        d = 3.1 if n == 0 else 40.2
    others = [p for p in t['library'] if p != phase]
    return dict(outputs={'phase': phase, 'runner_up': others[0], 'D': d}, cost_min=0.0, calls=[{'tool': 'fit', 'sample': s}])


def fm_energy(node, inp, t, ctx):
    e = {k: FM_E[k] for k in t['library']}
    return dict(outputs=dict({'energies': e, 'stated_error': 0.045}, **G.summarize_R(e)), cost_min=0.0,
                calls=[{'tool': 'energy', 'args': {'structure_name': k}} for k in e])


def fm_energy_ceiling(node, inp, t, ctx):
    e = {k: DFT_E[k] for k in t['library']}
    return dict(outputs=dict({'energies': e, 'stated_error': 0.0}, **G.summarize_R(e)), cost_min=0.0, calls=[])


def fm_hull(node, inp, t, ctx):
    h = FM_HULL[inp['phase']]
    return dict(outputs={'hull_distance': h, 'decomposition': ['toy'], 'stated_error': 0.045,
                         'margin': round(abs(h - ctx.const['threshold']), 6)}, cost_min=0.0, calls=[{'tool': 'hull'}])


LAB = {'simulator': sim, 'instrument': instrument, 'fit': fit}
AD_R = dict(LAB, fm=fm_energy)
AD_R_CEIL = dict(LAB, fm=fm_energy_ceiling)
AD_H = dict(LAB, fm=fm_hull)


def rows(res):
    return {r['test']: r['pass'] for r in res['rows']}


def render_check(graph, ex, worlds, holds, text):
    first = D.validate_d(graph, ex, worlds, holds, EXT)
    return D.validate_d(graph, ex, worlds, holds, EXT, {'w': (text, list(first['logs'].values()))})


# ---------------------------------------------------------------- suites
def suite_R():
    g = D.load(os.path.join(SPEC, 'graph_R_v2_nodft.json'))
    assert D.check(g) in (None, 'jsonschema not installed, schema check skipped')
    assert 'S2x' not in g.nodes and 'escalation' not in g.roles
    ex = D.executor(g, AD_R)
    tw = {'A': world('A', 'SUPPORTED', ['P1', 'P2'], 'P1'), 'B': world('B', 'REFUTED', ['P1', 'P2'], 'P2')}
    hd = [('hold_displacement', k, world(k, t['key'], ['P1', 'P2'], t['_truth']['phase'], disp=0.1)) for k, t in tw.items()]
    txt = 'S1c identified P1 with D 40.2 against 25. S2 put P1 lowest at -0.336 against -0.217, a margin of 0.119.'
    res = render_check(g, ex, tw, hd, txt)
    assert res['pass'], D.validation_table(res)
    print('R no-DFT suite: PASS')
    # in band: the FM margin shrinks below the band, gold answers CANNOT_TELL, which B1's band rule accepts
    near = dict(FM_E, P2=-0.316)
    ad = dict(LAB, fm=lambda n, i, t, c: dict(outputs=dict({'energies': {k: near[k] for k in t['library']}, 'stated_error': 0.045},
                                                          **G.summarize_R({k: near[k] for k in t['library']})), cost_min=0.0, calls=[]))
    tw_band = {k: dict(t, accept=[t['key'], 'CANNOT_TELL']) for k, t in tw.items()}
    rb = rows(D.validate_d(g, D.executor(g, ad), tw_band, hd, EXT))
    assert rb['correctness'] and not rb['prior flip'] and not rb['sufficiency'], rb
    print('R no-DFT, FM in band: gold answers CANNOT_TELL, correctness holds under the band rule, prior flip and sufficiency report the band')
    sel = D.validate_d(g, D.executor(g, AD_R_CEIL), tw, hd, rows='selection')
    assert sel['pass'] and [r['test'] for r in sel['rows']] == ['correctness', 'necessity S1a+S1d', 'necessity S1b+S1e',
                                                                'necessity S1c+S1d+S1e+S1f', 'measurement factorial', 'hold'], sel['rows']
    print('R no-DFT selection rows (ceiling adapters): PASS')


def suite_H():
    g = D.load(os.path.join(SPEC, 'graph_H_v2.json'))
    assert D.check(g) in (None, 'jsonschema not installed, schema check skipped')
    assert 'S1g' in g.upstream('S2') and 'S1c' in g.upstream('S2'), 'H is a chain: S2 needs the settled phase'
    ex = D.executor(g, AD_H)
    txt = 'S1g settled P1 with D 40.2 against 25. S2 gave a hull distance of 0.005 for P1, inside 0.05.'
    # E type: the true twin holds the lowest polymorph
    tw = {'A': world('A', 'SUPPORTED', ['P1', 'P2'], 'P1'), 'B': world('B', 'REFUTED', ['P1', 'P2'], 'P2')}
    hd = [('hold_displacement', k, world(k, t['key'], ['P1', 'P2'], t['_truth']['phase'], disp=0.1)) for k, t in tw.items()]
    res = render_check(g, ex, tw, hd, txt)
    assert res['pass'], D.validation_table(res)
    print('H v2 suite, E type: PASS')
    # M type: a lower polymorph P0 exists, so the true twin is not the lowest
    lib = ['P0', 'P1', 'P2']
    tm = {'A': world('A', 'SUPPORTED', lib, 'P1'), 'B': world('B', 'REFUTED', lib, 'P2')}
    hm = [('hold_displacement', k, world(k, t['key'], lib, t['_truth']['phase'], disp=0.1)) for k, t in tm.items()]
    res = render_check(g, ex, tm, hm, txt)
    assert res['pass'], D.validation_table(res)
    print('H v2 suite, M type: PASS')
    # negative: answering H with R reasoning (SUPPORTED iff the settled phase is the FM lowest) fails the M type
    spec = copy.deepcopy(g.spec)
    spec['nodes'][-1]['fn'] = 'H_by_rank'

    def h_by_rank(inp, ctx, params):
        ph = G._identified(inp, ctx, params)
        if ph is None:
            return {'verdict': 'CANNOT_TELL', 'reason': 'no phase'}
        return {'verdict': 'SUPPORTED' if ph == min(FM_E, key=lambda k: FM_E[k] if k in lib else 9) else 'REFUTED', 'reason': 'rank'}

    gr = G.Graph(spec)
    bad = rows(D.validate_d(gr, D.executor(gr, AD_H, rules={'H_by_rank': h_by_rank}), tm, hm, EXT))
    assert not bad['correctness'], bad
    print('negative H1, R reasoning on an M-type compound: correctness fails as it should')
    # remeasure path: the first measurement falls short, S1d to S1f run, S1g settles on S1f, S2 uses it
    tw2 = {'A': world('A', 'SUPPORTED', ['P1', 'P2'], 'P1', needs_two=('one',)),
           'B': world('B', 'REFUTED', ['P1', 'P2'], 'P2', needs_two=('one',))}
    res = render_check(g, ex, tw2, hd, 'S1c gave D 12.4 against 25, S1f reached 40.2 and S2 gave 0.005 against 0.05.')
    assert res['pass'], D.validation_table(res)
    b = res['logs']['base_A']
    assert [G.step_of(b, n)['status'] for n in ('S1d', 'S1e', 'S1f')] == ['ran'] * 3
    assert G.out_of(b, 'S1g', 'source') == 'S1f'
    print('H v2 remeasure path: suite PASS, S1g settles on S1f')


def suite_T():
    g = D.load(os.path.join(SPEC, 'graph_T.json'))
    assert D.check(g) in (None, 'jsonschema not installed, schema check skipped')
    up = g.upstream('S3')
    assert {'S1g_pre', 'S1g_post', 'S2'} <= up and not (g.upstream('S2') & {'S1c_pre', 'S1c_post'}), 'T: two chains and S2 in parallel'
    ex = D.executor(g, AD_R)
    lib = ['P1', 'P2']                       # P1 lower (L), P2 higher (H) in both FM and DFT

    def quad(**kw):
        cells = {'HL': ('P2', 'P1', 'SUPPORTED', True), 'LL': ('P1', 'P1', 'REFUTED', False),
                 'HH': ('P2', 'P2', 'REFUTED', False), 'LH': ('P1', 'P2', 'REFUTED', True)}
        return {k: world(k, key, lib, {'pre': pre, 'post': post}, m0s=('m0_pre', 'm0_post'), fm_decides=fd, **kw)
                for k, (pre, post, key, fd) in cells.items()}

    W = quad()
    hd = [('hold_displacement', k, dict(copy.deepcopy(t), task_id=t['task_id'] + '-hold')) for k, t in W.items()]
    txt = ('S1g_pre settled P2 and S1g_post settled P1, each with D 40.2 against 25. '
           'S2 put P1 at -0.336 and P2 at -0.217, so P2 became P1, lower by 0.119 against the band 0.045.')
    res = render_check(g, ex, W, hd, txt)
    assert res['pass'], D.validation_table(res)
    print('T suite (quad H to L, L to L, H to H, L to H): PASS')
    print(D.validation_table(res))
    try:
        import json
        import jsonschema
        schema = json.load(open(os.path.join(SPEC, 'trace_schema.json')))
        for lg in res['logs'].values():
            jsonschema.validate(lg, schema)
        print('T trace logs validate against trace_schema.json:', len(res['logs']))
    except ImportError:
        print('jsonschema not installed, trace schema check skipped')
    # remeasure on the post sample only
    W2 = {k: dict(t, _truth=dict(t['_truth'], needs_two={'post'})) for k, t in W.items()}
    res2 = D.validate_d(g, ex, W2, hd, EXT)
    assert rows(res2)['correctness'] and rows(res2)['measurement factorial'], D.validation_table(res2)
    b = res2['logs']['base_HL']
    assert [G.step_of(b, n)['status'] for n in ('S1d_post', 'S1e_post', 'S1f_post')] == ['ran'] * 3
    assert [G.step_of(b, n)['status'] for n in ('S1d_pre', 'S1e_pre', 'S1f_pre')] == ['skipped'] * 3
    print('T remeasure on the post sample: S1d_post to S1f_post run, the pre chain does not')

    # negative controls: every shortcut fails exactly the world it should
    def neg(name, fn):
        spec = copy.deepcopy(g.spec)
        spec['nodes'][-1]['fn'] = name
        gg = G.Graph(spec)
        return D.validate_d(gg, D.executor(gg, AD_R, rules={name: fn}), W, hd, EXT)

    def post_only(inp, ctx, params):
        post = G._identified({'phase': inp.get('phase_post')}, ctx, {'identify': params['identify_post']})
        e = inp.get('energies')
        if post is None or not e:
            return {'verdict': 'CANNOT_TELL', 'reason': 'x', 'margin_used': None}
        return {'verdict': 'SUPPORTED' if post == min(e, key=e.get) else 'REFUTED', 'reason': 'post is lowest', 'margin_used': None}

    def pre_only(inp, ctx, params):
        pre = G._identified({'phase': inp.get('phase_pre')}, ctx, {'identify': params['identify_pre']})
        e = inp.get('energies')
        if pre is None or not e:
            return {'verdict': 'CANNOT_TELL', 'reason': 'x', 'margin_used': None}
        return {'verdict': 'REFUTED' if pre == min(e, key=e.get) else 'SUPPORTED', 'reason': 'pre was not lowest', 'margin_used': None}

    def downhill(inp, ctx, params):
        pre = G._identified({'phase': inp.get('phase_pre')}, ctx, {'identify': params['identify_pre']})
        post = G._identified({'phase': inp.get('phase_post')}, ctx, {'identify': params['identify_post']})
        if pre is None or post is None:
            return {'verdict': 'CANNOT_TELL', 'reason': 'x', 'margin_used': None}
        return {'verdict': 'SUPPORTED' if pre != post else 'REFUTED', 'reason': 'a change means downhill', 'margin_used': None}

    r = neg('T_post_only', post_only)
    assert not rows(r)['correctness'] and r['logs']['base_LL']['verdict'] == 'SUPPORTED', 'post only fails L to L'
    r = neg('T_pre_only', pre_only)
    assert not rows(r)['correctness'] and r['logs']['base_HH']['verdict'] == 'SUPPORTED', 'pre only fails H to H'
    r = neg('T_downhill', downhill)
    rr = rows(r)
    assert not rr['correctness'] and r['logs']['base_LH']['verdict'] == 'SUPPORTED' and not rr['necessity S2'] and not rr['prior flip'], rr
    print('negative T1 to T3: post only fails L to L, pre only fails H to H, "a change means downhill" fails L to H, '
          'S2 necessity and the prior flip')
    # ablating one sample's chain blocks every world
    a = rows(res)
    assert a['necessity S1c_pre+S1d_pre+S1e_pre+S1f_pre'] and a['necessity S1c_post+S1d_post+S1e_post+S1f_post'], a
    print('T necessity: each sample chain and S2 are necessary')
    bad = G.number_lock('S2 gave 0.120 and S1g_mid agreed.', list(res['logs'].values()), g)
    assert bad == ['0.120', 'unknown node S1g_mid'], bad
    print('negative T4, number lock flags', bad)


def main():
    suite_R()
    suite_H()
    suite_T()
    g = D.load(os.path.join(SPEC, 'graph_T.json'))
    print()
    print(g.mermaid())
    print('\nALL KIT D TESTS PASSED')


if __name__ == '__main__':
    main()
