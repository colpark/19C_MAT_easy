"""analyze10 on synthetic graded records (no real episode): it runs end to end, the gate and contrasts compute, a planted gap is found.
  ~/v5env/bin/python tests/test_analyze10.py"""
import json, os, random, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..'))
import analyze10 as A
rng = random.Random(1); meta = {}
for fam, base, n in (('R', 501, 20), ('H', 601, 16), ('T', 701, 14)):
    for i in range(n):
        meta[base + i] = dict(family=fam, role='bench' if i < n - 6 else 'control', slot='take' if i < n - 6 else 'control', rank=f'{i:04x}',
                              htype=('M' if i % 3 == 0 else 'E') if fam == 'H' else None, kind='window_25_35', formula=f'X{i}', flag='fresh')
A.worlds_meta = lambda: (meta, {s: rng.choice(['right', 'right', 'in band', 'wrong']) for s in meta})
P = {'sonnet:fm': 0.5, 'sonnet:noSim': 0.1, 'sonnet:fm-instruct': 0.55, 'sonnet:fm-forecast': 0.7, 'sonnet:fm-placebo': 0.5, 'S-window': 0.85,
     'S-match': 0.2, 'S-window2': 0.8, 'S-plan': 0.9, 'S-plan2': 0.85, 'S-llm-R1': 0.3, 'S-llm-H1': 0.3, 'S-llm-T1': 0.3}
G = []
for s, m in meta.items():
    for lab, p in P.items():
        res = rng.random() < p
        if lab.startswith('S-llm') and not lab.startswith(f"S-llm-{m['family']}"): continue
        model, arm = (lab.split(':')[0], 'v10-' + lab.split(':')[1]) if ':' in lab else (lab, 'v10-script')
        cells = [1, 2, 3, 4] if m['family'] == 'T' else [1, 2]
        for c in cells:
            g = dict(scen=s, k=1, model=model, arm=arm, family=m['family'], credit=res, resolved_v7x4=res or rng.random() < 0.1, V=int(res and rng.random() < 0.95),
                     null_rule=int(rng.random() < 0.7), verdict='SUPPORTED', truth='SUPPORTED', D=30.0, cost=150.0, calls=[], wrong_determinate=False,
                     free_scans_only=False, measurements=({'pre': [dict(spec=dict(radiation='xray', start=10, step=0.04, n=1501))], 'post': [dict(spec=dict(radiation='xray', start=10, step=0.04, n=1501))]}
                                                          if m['family'] == 'T' else [dict(spec=dict(radiation='xray', start=10, step=0.04, n=1501))]))
            if m['family'] == 'T': g['cell'] = c
            else: g['twin'] = c
            G.append(g)
d = tempfile.mkdtemp(); json.dump(G, open(os.path.join(d, 'g.json'), 'w'))
out = os.path.join(d, 'out.json'); sys.argv = ['analyze10.py', out, d]; A.main()
R = json.load(open(out))
gate = R['evidence']['gate_V10_S']; print('gate', gate['estimate'], gate['lb95_one_sided'], gate['passes'])
assert gate['passes'] and 0.25 < gate['estimate'] < 0.55
print('verifier qualifies:', R['verifier']['qualification']['qualifies'], R['verifier']['qualification']['stats'])
print('2x2', R['evidence']['contrasts']['4_two_by_two']['interaction'], 'S-llm best', R['evidence']['contrasts']['5_fm_minus_S-llm_best'])
print('ANALYZE10 TEST PASSED')
