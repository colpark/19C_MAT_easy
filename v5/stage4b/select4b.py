"""Stage 4b selection of the primary stratum P (V5_SPEC J.3, J.5, J.6), DFT truth, physics and the heuristic panel only; no FM call.
Every evaluated candidate and its reason is written to stage4b/SELECTION.json.
  python stage4b/select4b.py
Candidates per type, ranked by sha256 of the sorted WBM ids of the twin pair:
  R: formulas with 3 to 5 polymorphs (one per prototype key); world A = P1, world B = the first polymorph by sha256 of its id at least
     75 meV/atom above P1. H: A <= 15 meV/atom above the hull, B >= 125, quaternary or magnetic, hull decomposition of the formula holds
     at least two phases, 2 to 5 polymorphs. G: A gap >= 1.0 eV, B gap 0, 2 to 5 polymorphs.
Cheap filters (sites, quotas, diversity), then the knowledge-gap filter (panel, analog, novelty), then identification tuning."""
import os, sys
for _v in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ.setdefault(_v, '1')
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..'))
import hashlib, itertools, json, math, time
from multiprocessing import Pool, get_context
from pymatgen.core import Composition
from mcenv import scenarios as SC
from mcenv import stage2 as S2
from mcenv import plangrid as PG
from mcenv import heuristics4b as H
from mcenv import separation as SP

POOL = os.path.join(HERE, '..', 'data', 'stage4b', 'pool4b.json')
OUT = os.path.join(HERE, 'SELECTION.json')
MAX_SITES = 24
SLOTS = [('R', 'quiet')] * 6 + [('H', 'quiet')] * 2 + [('H', 'loud'), ('G', 'quiet')] + [('G', 'loud')] * 2      # amendment A (X57, X59)
NEED4, NEEDMAG = 6, 6
TMP = 799                              # temporary scenario id (worlds 7991, 7992)
COST_LO, COST_HI = 54.0, 108.0
sha = lambda s: hashlib.sha256(s.encode()).hexdigest()
rank = lambda ids: sha('|'.join(sorted(ids)))


def stage4_pairs():
    sel = json.load(open(os.path.join(HERE, '..', 'stage4', 'SELECTION.json')))['chosen']
    return {frozenset(p) for c in sel for p in itertools.combinations([e.symbol for e in Composition(c['formula']).elements], 2)}


def epairs(f): return {frozenset(p) for p in itertools.combinations([e.symbol for e in Composition(f).elements], 2)}


def candidates(P):
    from mcenv import energy4 as E
    out = {'R': [], 'H': [], 'G': []}
    ppd = None
    for f, v in P.items():
        if v['dev']: continue
        ents = v['entries']; n = len(ents)
        if n < 2 or n > 5 or any(e['sites'] is None or e['sites'] > MAX_SITES for e in ents): continue
        base = dict(formula=f, n_elements=v['n_elements'], magnetic=v['magnetic'] or v['mixed_valence'], entries=ents)
        if n >= 3:
            p1 = ents[0]
            bs = sorted([e for e in ents[1:] if e['e_form'] - p1['e_form'] >= 0.075], key=lambda e: sha(e['id']))
            if bs: out['R'].append(dict(base, type='R', a=p1, b=bs[0], rank=rank([p1['id'], bs[0]['id']])))
        if v['n_elements'] >= 4 or base['magnetic']:
            A = [e for e in ents if e['e_hull'] <= 0.015]; B = [e for e in ents if e['e_hull'] >= 0.125]
            if A and B:
                if ppd is None: ppd = E.ppd()
                try: ndec = len(ppd.get_decomposition(Composition(f)))
                except Exception: ndec = 0
                if ndec >= 2:
                    for a in A:
                        for b in B: out['H'].append(dict(base, type='H', a=a, b=b, n_decomposition=ndec, rank=rank([a['id'], b['id']])))
        A = [e for e in ents if e['gap'] >= 1.0]; B = [e for e in ents if e['gap'] == 0.0]
        for a in A:
            for b in B: out['G'].append(dict(base, type='G', a=a, b=b, rank=rank([a['id'], b['id']])))
    for t in out: out[t].sort(key=lambda c: c['rank'])
    return out


def truth_holds(c, which):
    e = c[which]
    if c['type'] == 'R': return e['id'] == c['entries'][0]['id']
    if c['type'] == 'H': return e['e_hull'] <= 0.050
    return e['gap'] > 0.5


def knowledge_gap(D, c):
    lib = {e['id']: S2.wbm(e['id']) for e in c['entries']}
    res = {}
    for w in ('a', 'b'):
        res[w] = H.panel(D, c['type'], c['formula'], lib, c[w]['id'])
    truth = {w: truth_holds(c, w) for w in ('a', 'b')}
    pv = {w: res[w]['verdict'] for w in ('a', 'b')}
    panel_fails = pv['a'] == pv['b'] or any(pv[w] != truth[w] for w in ('a', 'b'))
    an = {w: res[w]['rules'].get('analog') for w in ('a', 'b')}
    analog_wrong = any(an[w] is not None and an[w] != truth[w] for w in ('a', 'b'))
    keyA = res['a']['keys'][c['a']['id']]
    novelty = D.mp_key_counts(keyA.split('|')[0]).get(keyA, 0) if keyA else 0
    return dict(panel={w: dict(verdict=pv[w], rules={k: v for k, v in res[w]['rules'].items()}) for w in ('a', 'b')}, truth=truth,
                panel_fails=panel_fails, analog_wrong=analog_wrong, mp_cooccurrence=novelty,
                passes=panel_fails and analog_wrong and novelty <= 2)


# ---------------------------------------------------------------- identification (temporary scenario TMP)
def register(c, N=1000.0):
    names = {e['id']: S2.register_structure(f"tmp4b {e['id']}", S2.wbm(e['id'])) for e in c['entries']}
    br = {i: SC.fixed([(n, {}, 1.0)], label=i) for i, n in names.items()}
    wa, wb = TMP * 10 + 1, TMP * 10 + 2
    SC.SCEN[TMP] = dict(name='tmp4b', kind='tmp', claim='', description='', library=list(names.values()),
                        worlds={wa: dict(holds=True, phases=[[(names[c['a']['id']], {}, 1.0)]], other_branches=[b for i, b in br.items() if i != c['a']['id']]),
                                wb: dict(holds=False, phases=[[(names[c['b']['id']], {}, 1.0)]], other_branches=[b for i, b in br.items() if i != c['b']['id']])},
                        claim_side=[br[c['a']['id']]], other_side=[br[c['b']['id']]])
    SC.TUNE[TMP] = dict(L=100.0, N=N, bg=20.0, Nn=1000.0, bgn=50.0)
    SC.WORLD_SCEN.update({wa: TMP, wb: TMP})


def dm0_max(c, N):
    """per world, the maximum over the other polymorphs of D(m0) (X56), and the minimum (the grader's D)."""
    register(c, N); out = []
    for w in (TMP * 10 + 1, TMP * 10 + 2):
        tr = SP.world_truth(w); ob = SC.SCEN[TMP]['worlds'][w]['other_branches']; ds = []
        for b in ob:
            SC.SCEN[TMP]['worlds'][w]['other_branches'] = [b]; ds.append(SP.separation(w, [SP.DEFAULT], tr))
        SC.SCEN[TMP]['worlds'][w]['other_branches'] = ob; out.append((max(ds), min(ds)))
    return out


def ident(c, want):
    """loud: min D(m0) >= 25 in both worlds at N 1000. quiet: N on the log grid 1000 / 1.15^i, the largest with max D(m0) < 9 in both
    worlds, both cheapest decisive plans at most 108 min and the more expensive one at least 54 min (X60)."""
    if want == 'loud':
        d = dm0_max(c, 1000.0)
        return dict(ok=all(mn >= 25 for mx, mn in d), N=1000.0, D_m0=[[round(mx, 2), round(mn, 2)] for mx, mn in d])
    N = 1000.0
    for i in range(80):
        d = dm0_max(c, N)
        if all(mx < 9 for mx, mn in d): break
        N = round(N / 1.15, 5)
    else:
        return dict(ok=False, reason='no N with max D(m0) < 9')
    tried = []
    for j in range(40):
        with get_context('spawn').Pool(12, initializer=register, initargs=(c, N)) as pool:      # spawn: no copy of the panel data (V5-E28)
            rows = {w: PG.scan_world(w, pairs=True, max_cost=180.0, pool=pool) for w in (TMP * 10 + 1, TMP * 10 + 2)}
        ch = {w: PG.cheapest(r) for w, r in rows.items()}
        costs = [None if x is None else round(x[0], 2) for x in ch.values()]
        tried.append(dict(N=N, costs=costs, D_m0=[[round(a, 2), round(b, 2)] for a, b in dm0_max(c, N)]))
        if any(x is None for x in costs) or max(costs) > COST_HI: return dict(ok=False, reason='cheapest decisive plan above 108 min', tried=tried)
        if max(costs) >= COST_LO:                          # X60: the window applies to the scenario's more expensive twin; both <= 108
            return dict(ok=True, N=N, tried=tried, plans={str(w): dict(cost=round(x[0], 2), D=round(x[1], 2), plan=[m.key() for m in x[2]]) for w, x in ch.items()})
        N = round(N / 1.15, 5)
    return dict(ok=False, reason='no N in the cost window', tried=tried)


def main():
    P = json.load(open(POOL)); C = candidates(P)
    cont = '--continue-noquota' in sys.argv          # X61: fill the remaining slots without the composition quota, keeping what was chosen
    D = H.Data(); used = set(stage4_pairs()); chosen = []; formulas = set()
    slots = list(SLOTS); n4 = nmag = 0
    if cont:
        log = json.load(open(OUT)); chosen = log.pop('chosen'); slots = [tuple(x) for x in log.pop('slots_left')]
        log['continuation_noquota'] = dict(after=len(log['evaluated']), rule='X61: composition quota infeasible; remaining slots filled in hash order under every other rule')
        for c in chosen: formulas.add(c['formula']); used |= epairs(c['formula'])
        done = {e['rank'] for e in log['evaluated']}
    else:
        log = dict(rule='V5_SPEC J.5', n_candidates={t: len(v) for t, v in C.items()}, evaluated=[], chosen=[]); done = set()
    print(log['n_candidates'], flush=True)
    for typ in ('R', 'H', 'G'):
        my = [s for s in slots if s[0] == typ]
        for c in C[typ]:
            if not [s for s in slots if s[0] == typ]: break
            if cont and c['rank'] in done and not any(e['rank'] == c['rank'] and e.get('reason') == 'quota feasibility' for e in log['evaluated']): continue
            rec = dict(type=typ, formula=c['formula'], ids=[c['a']['id'], c['b']['id']], rank=c['rank'], n_elements=c['n_elements'], magnetic=c['magnetic'])
            log['evaluated'].append(rec)
            if c['formula'] in formulas or epairs(c['formula']) & used: rec['reason'] = 'diversity'; continue
            left = len(slots); is4 = c['n_elements'] >= 4; ism = c['magnetic']
            if not cont and (max(0, NEED4 - n4 - is4) > left - 1 or max(0, NEEDMAG - nmag - ism) > left - 1): rec['reason'] = 'quota feasibility'; continue
            t0 = time.time()
            try: kg = knowledge_gap(D, c)
            except Exception as e: rec['reason'] = f'panel error {type(e).__name__}: {str(e)[:100]}'; continue
            rec['knowledge_gap'] = kg
            if not kg['passes']:
                rec['reason'] = 'knowledge gap (panel, analog or novelty)'
                if len(log['evaluated']) % 10 == 0: json.dump(dict(log, chosen=chosen, slots_left=slots), open(OUT, 'w'), indent=1, default=str)
                continue
            take = None
            for want in ('quiet', 'loud'):
                if (typ, want) not in slots: continue
                r = ident(c, want); rec[f'ident_{want}'] = r
                if r['ok']: take = want; break
            rec['sec'] = round(time.time() - t0)
            if not take:
                rec['reason'] = 'identification (no quiet or loud slot it meets)'
                json.dump(dict(log, chosen=chosen, slots_left=slots), open(OUT, 'w'), indent=1, default=str); continue
            slots.remove((typ, take)); rec['taken'] = take; chosen.append(rec); formulas.add(c['formula']); used |= epairs(c['formula'])
            n4 += is4; nmag += ism
            print(typ, take, c['formula'], c['a']['id'], c['b']['id'], 'N', rec[f'ident_{take}'].get('N'), flush=True)
            json.dump(dict(log, chosen=chosen, slots_left=slots), open(OUT, 'w'), indent=1, default=str)
        json.dump(dict(log, chosen=chosen, slots_left=slots), open(OUT, 'w'), indent=1, default=str)
    print(len(chosen), 'chosen; slots left', slots)


if __name__ == '__main__':
    main()
