"""Stage 4 scenario selection (V5_SPEC I.5), DFT truth and physics only, no FM call. Every evaluated candidate and rejection is
written to stage4/SELECTION.json.
  python stage4/select4.py [N_EVAL]
Order: R candidates in hash order fill the R quiet slot (first that can be made quiet) and four loud slots; then H candidates fill the H
quiet slot and two loud slots. Diversity (no element pair repeats) is checked against every scenario already taken, in that order.
Loud: D(m0) >= 25 in both worlds at N = 1000. Quiet: at N_q, the largest N with max D(m0) <= 8 in both worlds (bisection on N; V5-E22), the cheapest grid plan
of the stage 1 plan grid (singles and pairs, cost <= 90 min) reaches D >= 25 in both worlds."""
import os, sys
for _v in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ.setdefault(_v, '1')
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..'))
import hashlib, itertools, json, time
from multiprocessing import Pool
from mcenv import scenarios as SC
from mcenv import stage2 as S2
from mcenv import plangrid as PG
from mcenv.separation import separation, DEFAULT

DATA = os.path.join(HERE, '..', 'data', 'stage4')
OUT = os.path.join(HERE, 'SELECTION.json')
MAX_SITES = 24
HALF = 90.0
SLOTS = {'R': dict(quiet=1, loud=4), 'H': dict(quiet=1, loud=2)}
TMP = 699                       # temporary scenario id for screening (worlds 6991, 6992)
rank = lambda ids: hashlib.sha256('|'.join(sorted(ids)).encode()).hexdigest()


def pairs():
    C = json.load(open(os.path.join(DATA, 'census4.json')))['formulas']
    R, H = [], []
    for f, v in C.items():
        if not v['rule_v2']: continue
        E = sorted(v['entries'], key=lambda e: e['e_form']); p1 = E[0]
        for e in E[1:]:
            if e['proto'] != p1['proto'] and e['e_form'] - p1['e_form'] >= 0.075:
                R.append(dict(type='R', formula=f, elements=v['elements'], a=p1, b=e, gap=round(e['e_form'] - p1['e_form'], 4), rank=rank([p1['id'], e['id']])))
        for a in E:
            if a['e_hull'] > 0.015: continue
            for b in E:
                if b['e_hull'] >= 0.125 and a['proto'] != b['proto']:
                    H.append(dict(type='H', formula=f, elements=v['elements'], a=a, b=b, rank=rank([a['id'], b['id']])))
    return sorted(R, key=lambda c: c['rank']), sorted(H, key=lambda c: c['rank'])


def register(c, N=1000.0):
    """temporary twin scenario TMP: world 6991 holds a (claim-true), 6992 holds b; sides fixed phases (I.9)."""
    sa, sb = S2.wbm(c['a']['id']), S2.wbm(c['b']['id'])
    if max(len(sa), len(sb)) > MAX_SITES: return dict(sites=[len(sa), len(sb)])
    na = S2.register_structure(f"tmp {c['a']['id']}", sa); nb = S2.register_structure(f"tmp {c['b']['id']}", sb)
    SC.SCEN[TMP] = dict(name='tmp', kind='tmp', claim='', description='', library=[na, nb],
                        worlds={TMP * 10 + 1: dict(holds=True, phases=[[(na, {}, 1.0)]]), TMP * 10 + 2: dict(holds=False, phases=[[(nb, {}, 1.0)]])},
                        claim_side=[SC.fixed([(na, {}, 1.0)], label='a')], other_side=[SC.fixed([(nb, {}, 1.0)], label='b')])
    SC.TUNE[TMP] = dict(L=100.0, N=N, bg=20.0, Nn=1000.0, bgn=50.0)
    SC.WORLD_SCEN.update({TMP * 10 + 1: TMP, TMP * 10 + 2: TMP})
    return dict(sites=[len(sa), len(sb)])


def loud_eval(c):
    t0 = time.time()
    try:
        r = register(c)
        if max(r['sites']) > MAX_SITES: return dict(rank=c['rank'], sites=r['sites'], reason=f'more than {MAX_SITES} sites')
        d = [separation(w, [DEFAULT]) for w in (TMP * 10 + 1, TMP * 10 + 2)]
        return dict(rank=c['rank'], sites=r['sites'], D_m0_N1000=[round(x, 3) for x in d], sec=round(time.time() - t0))
    except Exception as e:
        return dict(rank=c['rank'], reason=f'error: {type(e).__name__}: {str(e)[:120]}')


def dm0_at(c, N):
    register(c, N)
    return [separation(w, [DEFAULT]) for w in (TMP * 10 + 1, TMP * 10 + 2)]


def tune_quiet_N(c, target=8.0, lo=1e-3, hi=1000.0):
    """largest N with max D(m0) <= target (D(m0) rises with N; bisection on log N, 30 steps)."""
    import math
    for _ in range(30):
        mid = math.sqrt(lo * hi)
        if max(dm0_at(c, mid)) <= target: lo = mid
        else: hi = mid
    return round(lo, 4)


def quiet_eval(c, dm0):
    Nq = tune_quiet_N(c)
    register(c, Nq)
    out = dict(N_q=Nq, worlds={})
    with Pool(18, initializer=register, initargs=(c, Nq)) as qpool:             # workers carry this candidate at N_q
        scans = {w: PG.scan_world(w, pairs=True, max_cost=HALF, pool=qpool) for w in (TMP * 10 + 1, TMP * 10 + 2)}
    for w, rows in scans.items():
        ch = PG.cheapest(rows)
        out['worlds'][str(w)] = dict(D_m0=round(rows[0][1], 3), cheapest=None if ch is None else dict(cost=round(ch[0], 2), D=round(ch[1], 2),
                                                                                                      plan=[m.key() for m in ch[2]]))
    ok = all(v['D_m0'] < 9 and v['cheapest'] and v['cheapest']['cost'] <= HALF for v in out['worlds'].values())
    out['quiet_ok'] = ok
    return out


def epairs(els): return {frozenset(p) for p in itertools.combinations(els, 2)}


def main():
    n_eval = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    R, H = pairs()
    log = dict(rule='V5_SPEC I.5', n_R_pairs=len(R), n_H_pairs=len(H), evaluated=[], chosen=[])
    used = set(); chosen = []
    with Pool(18) as pool:
        for typ, L in (('R', R), ('H', H)):
            slots = dict(SLOTS[typ]); i = 0
            while slots['quiet'] + slots['loud'] > 0 and i < len(L):
                # cheap filters and diversity first, then D(m0) for a batch in parallel
                batch = []
                while len(batch) < 18 and i < len(L):
                    c = L[i]; i += 1
                    if epairs(c['elements']) & used or any(c['formula'] == x['formula'] for x in chosen):
                        log['evaluated'].append(dict(type=typ, formula=c['formula'], ids=[c['a']['id'], c['b']['id']], rank=c['rank'],
                                                     reason='diversity (element pair or formula already used)'))
                        continue
                    batch.append(c)
                res = pool.map(loud_eval, batch, chunksize=1)
                for c, r in zip(batch, res):
                    rec = dict(type=typ, formula=c['formula'], ids=[c['a']['id'], c['b']['id']], protos=[c['a']['proto'], c['b']['proto']],
                               e_form=[c['a']['e_form'], c['b']['e_form']], e_hull=[c['a']['e_hull'], c['b']['e_hull']], **r)
                    log['evaluated'].append(rec)
                    if 'reason' in r: continue
                    if slots['quiet'] + slots['loud'] == 0: rec['reason'] = 'slots full'; continue
                    if epairs(c['elements']) & used: rec['reason'] = 'diversity (pair taken earlier in this batch)'; continue
                    take = None
                    if slots['quiet']:
                        q = quiet_eval(c, r['D_m0_N1000']); rec['quiet'] = q
                        if q['quiet_ok']: take = 'quiet'
                    if take is None and slots['loud'] and min(r['D_m0_N1000']) >= 25: take = 'loud'
                    if take is None: rec['reason'] = 'neither slot (not loud at N 1000, quiet test failed or slot full)'; continue
                    slots[take] -= 1; rec['taken'] = take; used |= epairs(c['elements']); chosen.append(rec)
                    print(typ, take, c['formula'], c['a']['id'], c['b']['id'], r['D_m0_N1000'], flush=True)
                json.dump(dict(log, chosen=chosen), open(OUT, 'w'), indent=1)
                if len([e for e in log['evaluated'] if e['type'] == typ]) > n_eval * 4: break
    json.dump(dict(log, chosen=chosen), open(OUT, 'w'), indent=1)
    print(len(chosen), 'chosen')


if __name__ == '__main__':
    main()
