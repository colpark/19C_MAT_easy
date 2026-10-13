"""V6-2 fast path, targeted search (V6-X7). Stage 4b pool R pairs with two or three polymorphs, at most 24 sites, dev formulas excluded,
world A = P1, world B = the first polymorph by sha256 of its id at least 75 meV/atom above P1, and a DFT gap to the nearest polymorph of
at least 0.12 eV/atom (so that an FM margin of 0.090 is reachable), in sha256 order of the twin ids. Per candidate, in order:
novelty (anonymous formula with P1's key at most twice in MP); bar 2 (the stage 4b heuristic panel fails the pair); bar 3 (FM: MACE-MP-0
relax on node A2, P1 lowest with margin >= 0.090 eV/atom); bar 1 (exact N_q, recorded; no member of the short list reached 50, so the
bar is the largest N_q reached, V6-X7); bar 4 (cheapest decisive plan at N_q: 0.2 to 0.6 of the budget on the dearer twin, at most 0.6
on both); bar 5 (blind FM resolves no pair: automatic for twins of one formula, checked). Stops at the first candidate passing all.
  python targeted.py CANDIDATES.json OUT.jsonl"""
import os, sys
for _v in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ.setdefault(_v, '1')
HERE = os.path.dirname(os.path.abspath(__file__)); V5 = os.path.join(HERE, '..', '..', '..', '..', 'v5', 'v5')
sys.path.insert(0, V5)
import json, math, subprocess, time
from multiprocessing import get_context
from mcenv import heuristics4b as H
from mcenv import energy4 as E
from mcenv import stage2 as S2
from mcenv import scenarios as SC
from mcenv import separation as SP
from mcenv import plangrid as PG

TMP = 988
BATCH = 6


def register(m, N):
    names = {e['id']: S2.register_structure(f"v6t {e['id']}", S2.wbm(e['id'])) for e in m['entries']}
    br = {i: SC.fixed([(n, {}, 1.0)], label=i) for i, n in names.items()}
    wa, wb = TMP * 10 + 1, TMP * 10 + 2
    SC.SCEN[TMP] = dict(name='v6t', kind='tmp', claim='', description='', library=list(names.values()),
                        worlds={wa: dict(holds=True, phases=[[(names[m['a']], {}, 1.0)]], other_branches=[b for i, b in br.items() if i != m['a']]),
                                wb: dict(holds=False, phases=[[(names[m['b']], {}, 1.0)]], other_branches=[b for i, b in br.items() if i != m['b']])},
                        claim_side=[br[m['a']]], other_side=[br[m['b']]])
    SC.TUNE[TMP] = dict(L=100.0, N=N, bg=20.0, Nn=1000.0, bgn=50.0)
    SC.WORLD_SCEN.update({wa: TMP, wb: TMP})


def dm0(m, N):
    register(m, N); return [SP.separation(TMP * 10 + i, [SP.DEFAULT]) for i in (1, 2)]


def n_q(m):
    lo, hi = 1e-3, 1000.0
    for _ in range(30):
        mid = math.sqrt(lo * hi)
        if max(dm0(m, mid)) < 9: lo = mid
        else: hi = mid
    return round(lo, 4)


def ident_cost(m, N):
    with get_context('spawn').Pool(12, initializer=register, initargs=(m, N)) as pool:
        ch = {w: PG.cheapest(PG.scan_world(w, pairs=True, max_cost=180.0, pool=pool)) for w in (TMP * 10 + 1, TMP * 10 + 2)}
    costs = [None if x is None else round(x[0], 2) for x in ch.values()]
    ok = all(c is not None and c <= 108 for c in costs) and max(costs) >= 36
    return dict(costs=costs, ok=ok, plans={str(w): None if x is None else [q.key() for q in x[2]] for w, x in ch.items()})


def fm_batch(ids):
    L = {i: S2.wbm(i).as_dict() for i in ids}
    json.dump(L, open(os.path.join(HERE, 'tq_in.json'), 'w'))
    subprocess.run(['rsync', '-a', os.path.join(HERE, 'tq_in.json'), 'aid1@192.168.100.11:v6work/exemplar/fastpath/'], check=True)
    subprocess.run(['ssh', '-n', 'aid1@192.168.100.11', 'cd ~/v6work && ~/Documents/fmllm/.venv/bin/python exemplar/fastpath/fm_relax.py '
                    'exemplar/fastpath/tq_in.json exemplar/fastpath/tq_out.json > /dev/null 2>&1'], check=True)
    subprocess.run(['rsync', '-a', 'aid1@192.168.100.11:v6work/exemplar/fastpath/tq_out.json', HERE + '/'], check=True)
    return json.load(open(os.path.join(HERE, 'tq_out.json')))


def main():
    C = json.load(open(sys.argv[1])); out = open(sys.argv[2], 'a')
    P = json.load(open(os.path.join(V5, 'data', 'stage4b', 'pool4b.json')))
    D = H.Data(); queue = []; fmall = {}
    log = lambda r: (out.write(json.dumps(r, default=str) + '\n'), out.flush())
    for rank, f, gap, nlib, nel in C:
        ents = P[f]['entries']; a = ents[0]['id']
        bs = sorted([x for x in ents[1:] if x['e_form'] - ents[0]['e_form'] >= 0.075], key=lambda x: __import__('hashlib').sha256(x['id'].encode()).hexdigest())
        m = dict(rank=rank, formula=f, entries=ents, a=a, b=bs[0]['id'], dft_gap=gap, n_polymorphs=nlib)
        st = {e['id']: S2.wbm(e['id']) for e in ents}
        key = H.proto_key(st[a]); m['mp_cooccurrence'] = D.mp_key_counts(key.split('|')[0]).get(key, 0) if key else None
        if m['mp_cooccurrence'] is None or m['mp_cooccurrence'] > 2: m['first_failed_bar'] = 'novelty'; log(m); continue
        pa, pb = H.panel(D, 'R', f, st, a), H.panel(D, 'R', f, st, m['b'])
        m['panel'] = dict(a=pa['verdict'], b=pb['verdict'], rules_a=pa['rules'], rules_b=pb['rules'])
        if not (pa['verdict'] == pb['verdict'] or pa['verdict'] is not True or pb['verdict'] is not False):
            m['first_failed_bar'] = 'bar 2: panel resolves the pair'; log(m); continue
        queue.append(m)
        if len(queue) < BATCH: continue
        fmr = fm_batch([e['id'] for q in queue for e in q['entries']]); fmall.update(fmr)
        vals = E.fm_values(list(fmr), fmr)
        for q in queue:
            e = {x['id']: vals[x['id']]['e_form'] for x in q['entries']}; rk = sorted(e, key=e.get)
            q['fm'] = e; q['fm_margin'] = round(e[rk[1]] - e[rk[0]], 4); q['fm_lowest_is_P1'] = rk[0] == q['a']
            if not (q['fm_lowest_is_P1'] and q['fm_margin'] >= 0.090): q['first_failed_bar'] = 'bar 3: FM margin'; log(q); continue
            q['N_q'] = n_q(q); N = q['N_q']; tried = []
            for _ in range(30):                              # V6-X8: the largest N <= N_q (steps of 1.15) whose plan cost meets the window
                ic = ident_cost(q, N); tried.append(dict(N=N, costs=ic['costs']))
                if ic['ok'] or any(c is None or c > 108 for c in ic['costs']): break
                N = round(N / 1.15, 5)
            q['ident'] = ic; q['ident_tried'] = tried; q['N_ident'] = N
            if not ic['ok']: q['first_failed_bar'] = 'bar 4: identification cost'; log(q); continue
            q['bar5_blind_fm_resolves'] = 0; q['first_failed_bar'] = None; log(q)
            print('PASS', q['formula'], q['N_q'], q['N_ident'], q['fm_margin'], flush=True); return
        queue = []
    print('no candidate passed', flush=True)


if __name__ == '__main__':
    main()
