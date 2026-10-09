#!/usr/bin/env python3
"""census_mc21.py (v4.5 MC v2.1, MV1d; HTEM_MC2_RULES_v21.md): census by skill group, three reports side by side.
  (a) old rules (census_mc2 at MV1b) on the MV1b scope (fully cached minus F1): must reproduce MC2_CENSUS.json byte for byte
  (b) old rules on the enlarged scope (MV1b plus F1), old sticks
  (c) v2.1 rules on the enlarged scope: S4mc6 robustness (L1, L7), binomial cheap-rule gate, L8 list and L8-deep, CO1 sticks
      (L4 generalized pairs, L6 on systems with >= 2 kept phases), includable types, groups, round go, fresh confirmation (F1 only).
Cache only, no rendering. Writes v4/htem/mc21/ (a, b outputs) and v4/htem/MC21_CENSUS.json / .md."""
import copy, hashlib, json, math, os, shutil, sys
from collections import Counter, defaultdict
from itertools import combinations
import numpy as np
from scipy.stats import binom
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_mc2 as CM, keys_mc2 as KY, iv_classes as IVC, sample_io as SIO
from readers import xrd as RX

ROOT = CM.HERE; OUTD = os.path.join(ROOT, 'mc21'); os.makedirs(OUTD, exist_ok=True)
F1 = set(json.load(open(os.path.join(CM.API.HOST, 'mc', 'f1_list.json'))))
TYPES = ['L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7', 'L8']
GROUPS = {'electrical': ['L1', 'L2', 'L5', 'L7'], 'optical': ['L3', 'L8'], 'structural': ['L4', 'L6']}
EN = json.load(open(os.path.join(ROOT, 'MC2_ENERGY.json')))
ST21 = json.load(open(os.path.join(CM.API.HOST, 'refs', 'sticks_mc21.json')))


def split(lid):
    return CM.SPL.get(lid, {}).get('split')


# ---------------- (a), (b): the frozen MV1b census code with a scope filter ----------------
def old_census(scope, tag):
    import census_mc2 as C2
    real = CM.positions
    C2.CM.positions = lambda lid: real(lid) if lid in scope else None
    here = CM.HERE; CM.HERE = os.path.join(OUTD, tag); os.makedirs(CM.HERE, exist_ok=True)
    try: C2.main()
    finally: CM.HERE = here; C2.CM.positions = real
    return os.path.join(OUTD, tag, 'MC2_CENSUS.json')


# ---------------- (c): v2.1 keys ----------------
def with_threshold(P, r2min):
    Q = []
    for p in P:
        q = dict(p); fp = SIO.fpm(p['_s'])
        q['iv'] = IVC.classify(fp['current_A'], fp['voltage_V'], r2min) if fp else None
        Q.append(q)
    return Q


def l1_robust(P):
    o = KY.l1(P)
    if o is None: return None
    keys = [KY.l1(with_threshold(P, t)) for t in (0.995, 0.99)]
    same = all(k is not None and k['key'] == o['key'] for k in keys)
    o = dict(o); o['decided_old'] = o['decided']; o['decided'] = o['decided'] and same; o['critical'] = o['critical'] and same; o['robust'] = same
    return o


def l7_robust(P):
    o = KY.l7(P)
    if o is None: return None
    cnt = {t: sum(1 for p in P if (fp := SIO.fpm(p['_s'])) and IVC.classify(fp['current_A'], fp['voltage_V'], t)['valid']) for t in (0.995, 0.99)}
    same = all(abs(v - o['key']) <= 1 for v in cnt.values())
    cls = Counter(IVC.classify(fp['current_A'], fp['voltage_V'])['cls'] for p in P if (fp := SIO.fpm(p['_s'])))
    o = dict(o); o['decided_old'] = True; o['decided'] = same; o['critical'] = o['critical'] and same; o['robust_counts'] = cnt; o['classes4'] = dict(cls)
    return o


def l8_v21(P, sig):
    o = KY.l8(P, sig)
    if o is None: return None
    o = dict(o); base = o['cheap'].pop('T>1.05 only'); o['baseline_T105'] = base
    o['deep'] = o['critical'] and abs(o['key'] - o['n_T_over']) >= 2
    return o


PH = {p['cod_id']: p for p in ST21['phases']}


def _stk(p):
    return [(s[0], s[1]) for s in p['sticks']]


def sys_phases(system):
    el = set(system.split('-'))
    return {p['phase']: _stk(p) for p in ST21['phases'] if set(p['elements']) <= el and p['sticks']}


def _hkl_map(p):
    m = {}
    for t, i, hk in p['sticks']:
        for h in hk: m.setdefault(tuple(abs(v) for v in h), (t, i))
    return m


def l4_general(P, lid, system):
    el = set(system.split('-')); cands = []
    for pr in ST21['l4_pairs']:
        A, B = pr['A'], pr['B']
        pa = next(p for p in ST21['phases'] if p['phase'] == pr['phase_A']); pb = next(p for p in ST21['phases'] if p['phase'] == pr['phase_B'])
        if not (set(pa['elements']) | set(pb['elements'])) <= el: continue
        anion = A in SIO.ANIONS and B in SIO.ANIONS
        xs = []
        for p in P:
            src = p['an'] if anion else p['comp']
            xs.append(src[A] / (src[A] + src[B]) if src and src.get(A, 0) + src.get(B, 0) > 0 and A in src and B in src else None)
        v = [x for x in xs if x is not None]
        if len(v) >= 10: cands.append((-(max(v) - min(v)), pr['ids'], pr, pa, pb, xs))
    if not cands: return None
    _, _, pr, pa, pb, xP = sorted(cands, key=lambda c: (c[0], c[1]))[0]
    ma, mb = _hkl_map(pa), _hkl_map(pb); shared = set(ma) & set(mb)
    if not shared: return None
    hkl = max(sorted(shared), key=lambda h: (ma[h][1] + mb[h][1]) / 2)
    dA = KY.LAM / (2 * math.sin(math.radians(ma[hkl][0]) / 2)); dB = KY.LAM / (2 * math.sin(math.radians(mb[hkl][0]) / 2))
    cubic = pa['cubic'] and pb['cubic']; mult = math.sqrt(sum(h * h for h in hkl)) if cubic else 1.0
    QA, QB = dA * mult, dB * mult
    xs, Q = [], []
    for i, p in enumerate(P):
        if xP[i] is None: continue
        pk = CM.peaks(P, i)
        if not pk: continue
        dv = xP[i] * dA + (1 - xP[i]) * dB; tv = 2 * math.degrees(math.asin(KY.LAM / (2 * dv)))
        c = min(pk, key=lambda q: abs(q['center'] - tv))
        if abs(c['center'] - tv) > 1.0: continue
        xs.append(xP[i]); Q.append(mult * KY.LAM / (2 * math.sin(math.radians(c['center']) / 2)))
    if len(xs) < 10: return None
    xs, Q = np.array(xs), np.array(Q); s = KY.comp_step(P, xP) or 0.02
    grid = [g for g in (0.2, 0.35, 0.5, 0.65, 0.8) if xs.min() + s <= g <= xs.max() - s]
    grid = sorted(grid, key=lambda g: KY.h(f'mv2-x0|{lid}|{g}'))[:2]
    if not grid: return None
    X = np.vstack([xs, np.ones_like(xs)]).T; b, *_ = np.linalg.lstsq(X, Q, rcond=None); r = Q - X @ b
    cov = float(r @ r) / max(len(xs) - 2, 1) * np.linalg.inv(X.T @ X); out = []
    for x0 in grid:
        key = float(b[0] * x0 + b[1]); se = math.sqrt(float(np.array([x0, 1]) @ cov @ np.array([x0, 1])))
        th = math.asin(KY.LAM * mult / (2 * key)); delta = key / math.tan(th) * math.radians(KY.DT_REP / 2)
        tol = math.hypot(2 * se, delta); nv = x0 * QA + (1 - x0) * QB
        out.append({'x0': x0, 'decided': True, 'key': key, 'tol': tol, 'naive': nv, 'critical': abs(nv - key) > tol, 'n_valid': len(xs),
                    'pair': f"{pr['A']}/{pr['B']} {pr['ids']}", 'hkl': list(hkl), 'quantity': 'a' if cubic else 'd',
                    'effect': abs(nv - key), 'cheap': {'Vegard': abs(nv - key) <= tol}, 'oracle': True})
    return out


def binom_gate(k, n, c):
    p0 = c + 0.10; p = float(binom.sf(k - 1, n, min(p0, 1.0))) if n else 1.0
    return {'k': k, 'n': n, 'acc': k / n if n else None, 'p': p, 'cap_ok': (k / n if n else 0) <= c + 0.20 + 1e-12, 'pass': p >= 0.05 and (k / n if n else 0) <= c + 0.20 + 1e-12}


def mix_of(F, t):
    crit = [f for f in F if f['critical']]; ctrl = [f for f in F if not f['critical']]
    nctrl = round(3 / 7 * len(crit)); sel = sorted(ctrl, key=lambda f: KY.h(f'mv2-ctrl|{t}|{f["id"]}'))[:nctrl]
    return crit, ctrl, sel


def gate_mix(mix, c):
    rules = sorted({k for f in mix for k in f['cheap']})
    return {k: binom_gate(sum(1 for f in mix if f['cheap'].get(k)), len(mix), c) for k in rules}


def census_v21(scope):
    facts = defaultdict(list); lost = defaultdict(Counter); libs = {}
    for r in CM.ROWS:
        if split(r['id']) == 'dev' or r['id'] not in scope: continue
        P = CM.positions(r['id'])
        if P is None: continue
        libs[r['id']] = (r, P); s = r['system']; phs = sys_phases(s)
        run = {'L1': lambda: l1_robust(P), 'L2': lambda: KY.l2(P, CM.sig_logrs(s)), 'L3': lambda: KY.l3(P, EN[s]['E_eV'], CM.sig_A(s)),
               'L7': lambda: l7_robust(P), 'L8': lambda: l8_v21(P, CM.sig_A(s)), 'L4': lambda: l4_general(P, r['id'], s)}
        if len(phs) >= 2: run['L6'] = lambda: KY.l6(P, lambda i: CM.peaks(P, i), phs, RX.match_phase)
        for t, f in run.items():
            out = f()
            if out is None: lost[t]['not eligible'] += 1; continue
            for o in (out if isinstance(out, list) else [out]):
                if not o['decided']: lost[t]['key not decided' + (' (robustness)' if o.get('decided_old') else '')] += 1; continue
                fid = r['id'] + (f'|x0={o["x0"]}' if 'x0' in o else '')
                facts[t].append({'id': fid, 'system': s, 'libs': [r['id']], 'test': split(r['id']) == 'test', 'fresh': r['id'] in F1,
                                 **{k: v for k, v in o.items() if k != 'decided'}})
    by_sys = defaultdict(list)
    for lid, (r, P) in libs.items():
        if r.get('temp_c') not in (None, '', 'None'): by_sys[r['system']].append(lid)
    cand = []
    for s, ids in by_sys.items():
        for a, b in combinations(sorted(ids, key=int), 2):
            ta, tb = float(libs[a][0]['temp_c']), float(libs[b][0]['temp_c'])
            if ta != tb: cand.append((KY.h(f'mv2-L5|{a}|{b}'), s, a, b, ta, tb))
    used = Counter()
    for _, s, a, b, ta, tb in sorted(cand):
        if used[a] >= 2 or used[b] >= 2: lost['L5']['library cap 2'] += 1; continue
        hot, cold = (a, b) if ta > tb else (b, a); cat, _ = KY.comp_var(libs[hot][1] + libs[cold][1])
        o = KY.l5(libs[hot][1], libs[cold][1], cat)
        if o is None: lost['L5']['not eligible'] += 1; continue
        used[a] += 1; used[b] += 1
        facts['L5'].append({'id': f'{hot}>{cold}', 'system': s, 'libs': [hot, cold], 'test': split(hot) == 'test' or split(cold) == 'test',
                            'fresh': hot in F1 or cold in F1, **{k: v for k, v in o.items() if k != 'decided'}})
    res = {}
    for t in TYPES:
        F = facts.get(t, []); crit, ctrl, sel = mix_of(F, t); mix = crit + sel; c = len(sel) / len(mix) if mix else 0.0
        g = gate_mix(mix, c); c34 = bool(mix) and all(v['pass'] for v in g.values()) and all(f['oracle'] for f in mix)
        naive_rule = next(iter(F[0]['cheap'])) if F else None
        c1 = all(not f['cheap'][naive_rule] for f in crit) if crit else False
        pairs = [(a, b) for a, b in combinations(mix, 2) if a['system'] == b['system']]
        import census_mc2 as C2
        c2 = sum(C2.differ(t, a, b) for a, b in pairs) / len(pairs) if pairs else None
        sysc = Counter(f['system'] for f in crit); eff = [f['effect'] for f in crit if f.get('effect') is not None]
        incl = (c2 is not None and c2 >= 0.5) and c34 and c1 and len(crit) >= 6 and len(sysc) >= 2
        fm = [f for f in mix if f['fresh']]; fc = sum(1 for f in fm if not f['critical']) / len(fm) if fm else 0.0
        fresh = {'n': len(fm), 'critical': sum(f['critical'] for f in fm), 'gate': gate_mix(fm, fc) if len(fm) >= 6 else None}
        fresh['status'] = ('unconfirmed (< 6 fresh items)' if len(fm) < 6 else ('pass' if all(v['pass'] for v in fresh['gate'].values()) else 'fail'))
        extra = {}
        if t == 'L8':
            extra['baseline_T105'] = sum(1 for f in mix if f['baseline_T105']) / len(mix) if mix else None
            deep = [f for f in crit if f['deep']]; extra['deep'] = {'n': len(deep), 'systems': dict(Counter(f['system'] for f in deep))}
        if t in ('L1', 'L7'):
            extra['decided_old'] = sum(1 for f in F) + lost[t].get('key not decided (robustness)', 0)
            extra['robustness_dropped'] = lost[t].get('key not decided (robustness)', 0)
        res[t] = {'decided': len(F), 'critical': len(crit), 'critical_systems': len(sysc), 'critical_by_system': dict(sysc.most_common()),
                  'naive_failure_rate': len(crit) / len(F) if F else None, 'control_available': len(ctrl), 'control_selected': len(sel), 'control_share': c,
                  'critical_test': sum(f['test'] for f in crit), 'critical_fresh': sum(f['fresh'] for f in crit), 'C2': c2, 'C2_pairs': len(pairs),
                  'cheap': g, 'C34': c34, 'C1_prior': c1,
                  'effect': {'median': float(np.median(eff)), 'p10': float(np.percentile(eff, 10)), 'p90': float(np.percentile(eff, 90))} if eff else None,
                  'includable': incl, 'fresh': fresh, 'lost': dict(lost[t]), **extra}
    grp = {}
    for gname, ts in GROUPS.items():
        inc = [t for t in ts if res[t]['includable']]; crit = [f for t in inc for f in facts.get(t, []) if f['critical']]
        sysg = {f['system'] for f in crit}
        grp[gname] = {'includable': inc, 'critical': len(crit), 'systems': len(sysg), 'critical_test': sum(f['test'] for f in crit),
                      'builds': len(crit) >= 20 and len(sysg) >= 3}
    built = [g for g, v in grp.items() if v['builds']]; types_b = [t for g in built for t in grp[g]['includable']]
    ncrit = sum(grp[g]['critical'] for g in built); ntest = sum(grp[g]['critical_test'] for g in built)
    fresh_ok = all(res[t]['fresh']['status'] != 'fail' for t in types_b)
    go = {'groups_built': built, 'types': types_b, 'critical': ncrit, 'critical_test': ntest, 'fresh_confirmation': fresh_ok,
          'criteria': {'1 groups >= 2': len(built) >= 2, '2 types >= 3': len(types_b) >= 3, '3 critical >= 60': ncrit >= 60, '4 test >= 15': ntest >= 15, '5 fresh': fresh_ok}}
    go['GO'] = all(go['criteria'].values())
    return {'libraries_in_scope': len(libs), 'fresh_libraries': sum(1 for l in libs if l in F1), 'types': res, 'groups': grp, 'go': go,
            'facts': {t: [{k: v for k, v in f.items() if k != 'cheap'} for f in F] for t, F in facts.items()}}


def main():
    allc = {r['id'] for r in CM.ROWS if CM.fully_cached(r['id'])}; mv1b = allc - F1; enl = allc
    pa = old_census(mv1b, 'a_old_mv1b'); ref = os.path.join(ROOT, 'MC2_CENSUS.json')
    same = hashlib.sha256(open(pa, 'rb').read()).hexdigest() == hashlib.sha256(open(ref, 'rb').read()).hexdigest()
    pb = old_census(enl, 'b_old_enlarged')
    A, B = json.load(open(pa)), json.load(open(pb)); Cc = census_v21(enl)
    out = {'a_reproduces_MV1b': same, 'scope': {'mv1b': len(mv1b), 'enlarged': len(enl), 'f1_fully_cached': len(F1 & allc)},
           'a': {t: {k: A['types'][t][k] for k in ('decided', 'critical', 'critical_systems', 'critical_test', 'builds')} for t in TYPES} | {'GO': A['GO']},
           'b': {t: {k: B['types'][t][k] for k in ('decided', 'critical', 'critical_systems', 'critical_test', 'builds')} for t in TYPES} | {'GO': B['GO']},
           'c': Cc}
    json.dump(out, open(os.path.join(ROOT, 'MC21_CENSUS.json'), 'w'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
    write_md(out)


def write_md(o):
    C = o['c']; R = C['types']; names = {'L1': 'best conductor', 'L2': 'resistivity trend', 'L3': 'most transparent at E', 'L4': 'lattice/d at x0',
                                         'L5': 'temperature, matched comp.', 'L6': 'single-phase range', 'L7': 'valid Rs readings', 'L8': 'impossible optical data'}
    L = ['# MC v2.1 census by skill group (MV1d; HTEM_MC2_RULES_v21.md)', '',
         f"Scope: MV1b {o['scope']['mv1b']} fully cached libraries; enlarged {o['scope']['enlarged']} (F1 fully cached {o['scope']['f1_fully_cached']}). Dev libraries never yield facts. (a) reproduces MV1b byte for byte: **{'yes' if o['a_reproduces_MV1b'] else 'NO'}**.", '',
         f"**Round (c): {'GO' if C['go']['GO'] else 'NO-GO'}.** " + '; '.join(f"{k}: {'met' if v else 'not met'}" for k, v in C['go']['criteria'].items()) +
         f". Built groups: {', '.join(C['go']['groups_built']) or 'none'}; types {', '.join(C['go']['types']) or 'none'}; critical {C['go']['critical']}, in test {C['go']['critical_test']}.", '',
         '## Side by side: critical items (systems) and build', '', '| Type | (a) old rules, MV1b scope | (b) old rules, enlarged | (c) v2.1 rules, enlarged | (c) includable |', '|---|---|---|---|---|']
    for t in TYPES:
        a, b, c = o['a'][t], o['b'][t], R[t]
        L.append(f"| {t} {names[t]} | {a['critical']} ({a['critical_systems']}){' built' if a['builds'] else ''} | {b['critical']} ({b['critical_systems']}){' built' if b['builds'] else ''} | {c['critical']} ({c['critical_systems']}) | {'yes' if c['includable'] else 'no'} |")
    L.append(f"| Round | {'GO' if o['a']['GO'] else 'NO-GO'} | {'GO' if o['b']['GO'] else 'NO-GO'} | {'GO' if C['go']['GO'] else 'NO-GO'} | |")
    L += ['', '## (c) per type', '', '| Type | Decided | Critical (systems) | Naive fails | Controls avail / kept (share) | Critical test / fresh | C2 | C1 prior | C3/C4 | Effect median (p10-p90) | Includable |', '|---|---|---|---|---|---|---|---|---|---|---|']
    for t in TYPES:
        r = R[t]; e = r['effect']; es = f"{e['median']:.3g} ({e['p10']:.3g} to {e['p90']:.3g})" if e else '-'
        c2 = '-' if r['C2'] is None else f"{r['C2']:.2f} ({r['C2_pairs']})"
        L.append(f"| {t} | {r['decided']} | {r['critical']} ({r['critical_systems']}) | {(r['naive_failure_rate'] or 0):.0%} | {r['control_available']} / {r['control_selected']} ({r['control_share']:.2f}) | {r['critical_test']} / {r['critical_fresh']} | {c2} | {'pass' if r['C1_prior'] else 'fail'} | {'pass' if r['C34'] else 'fail'} | {es} | {'yes' if r['includable'] else 'no'} |")
    L += ['', '## (c) cheap rules: k/n, binomial p (H0: acc <= control share + 0.10), cap (acc <= share + 0.20)', '']
    for t in TYPES:
        L.append(f"- **{t}:** " + ('; '.join(f"{k} {v['k']}/{v['n']} p={v['p']:.3f}{'' if v['cap_ok'] else ' CAP'}{'' if v['pass'] else ' FAIL'}" for k, v in R[t]['cheap'].items()) or '-'))
    r8 = R['L8']; L += ['', f"L8 single-constraint baseline (count T > 1.05 only): {r8.get('baseline_T105') if r8.get('baseline_T105') is None else round(r8['baseline_T105'], 2)}; L8-deep subset: {r8.get('deep', {}).get('n')} critical items, systems {r8.get('deep', {}).get('systems')}.",
                        f"S4mc6 robustness: L1 decided {R['L1'].get('decided_old')} -> {R['L1']['decided']} ({R['L1'].get('robustness_dropped')} dropped); L7 decided {R['L7'].get('decided_old')} -> {R['L7']['decided']} ({R['L7'].get('robustness_dropped')} dropped).", '',
          '## (c) groups', '', '| Group | Includable types | Critical | Systems | In test | Builds |', '|---|---|---|---|---|---|']
    for g, v in C['groups'].items(): L.append(f"| {g} | {', '.join(v['includable']) or '-'} | {v['critical']} | {v['systems']} | {v['critical_test']} | {'yes' if v['builds'] else 'no'} |")
    L += ['', '## (c) fresh confirmation (F1 libraries only)', '', '| Type | Fresh items | Fresh critical | Status | Worst rule (k/n, p) |', '|---|---|---|---|---|']
    for t in TYPES:
        f = R[t]['fresh']; w = min(f['gate'].items(), key=lambda kv: kv[1]['p']) if f['gate'] else None
        ws = f"{w[0]} {w[1]['k']}/{w[1]['n']}, p={w[1]['p']:.3f}" if w else '-'
        L.append(f"| {t} | {f['n']} | {f['critical']} | {f['status']} | {ws} |")
    L += ['', '## (c) critical items by system', '']
    for t in TYPES: L.append(f"- **{t}:** " + (', '.join(f'{s} {n}' for s, n in R[t]['critical_by_system'].items()) or 'none'))
    L += ['', '## (c) losses', '']
    for t in TYPES: L.append(f"- **{t}:** " + (', '.join(f'{k} {v}' for k, v in R[t]['lost'].items()) or 'none'))
    open(os.path.join(ROOT, 'MC21_CENSUS.md'), 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L[:30]))


if __name__ == '__main__':
    main()
