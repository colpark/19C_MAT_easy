#!/usr/bin/env python3
"""census_mc23.py (v4.5 MC v2.3, MV1h; HTEM_MC2_RULES_v23.md). Census on the frozen final scope, all non-dev fully cached libraries:
L8 (v22, depth tags), L4 (v22 under CO2 on the VM-E10-fixed sticks, plus the anion-free ground-state rule, section 3), L7r (section 2),
and the L3 and L1 probe sets (section 4). Reports per type: decided, critical (systems), controls, test, C2, cheap rules (k/n, binomial p,
cap), effects, N-Sn-Zn share, L8 depth, L7r replicate Jaccard, L4 facts dropped by section 3 and changed against MV1f.
MC_DEV=1: dev libraries only (smoke test; writes nothing). Writes v4/htem/MC23_CENSUS.json and .md."""
import json, math, os, sys
from collections import Counter, defaultdict
from itertools import combinations
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_mc2 as CM, keys_mc2 as KY, iv_classes as IVC, sample_io as SIO, co2_mc2 as CO2
import census_mc21 as M21, census_mc22 as M22, census_mc2 as C2M
DEV = bool(os.environ.get('MC_DEV'))
GRID, CENTRAL, split = M22.GRID, M22.CENTRAL, M22.split
GS = {'Ba': 229, 'Co': 194, 'Cr': 229, 'Cu': 225, 'Fe': 229, 'Ga': 64, 'Nb': 229, 'Sb': 166, 'Sn': 141, 'Ta': 229, 'Ti': 194, 'Y': 194,
      'Zn': 194, 'Zr': 194}
PART1 = ('degenerate', 'points<4', 'zero sweep', 'polarity')
SCORED = ('L8', 'L4', 'L7r')


# ---------------- L7r ----------------
def iv_points(p):
    fp = SIO.fpm(p['_s']); return (fp['current_A'], fp['voltage_V']) if fp else None


def l7r_classes(P):
    """Per position with I-V points: 'fault' (part-1 fault at all 27 settings), 'valid' (valid at all 27), else 'borderline'."""
    out = {}
    for i, p in enumerate(P):
        iv = iv_points(p)
        if iv is None: continue
        c = IVC.classify(*iv); fs = M22.fitstats(p); vs = [M22.valid_at(fs, g) for g in GRID]
        if c['cls'] == 'fault' and c['why'] in PART1 and not any(vs): out[i] = ('fault', c['why'])
        elif all(vs): out[i] = ('valid', None)
        else: out[i] = ('borderline', c['cls'] if c['cls'] != 'valid' else 'grid-unstable')
    return out


def l7r_correct(ans, faults, rvalid):
    ans = set(ans); fl = len(ans & rvalid)
    if not faults: return fl <= 1
    return len(ans & faults) / len(faults) >= 0.8 and fl <= 1


def l7r_reward(ans, faults, rvalid):
    ans = set(ans) & (faults | rvalid)
    if not faults: return 1.0 if not ans else 0.0
    tp = len(ans & faults); p = tp / len(ans) if ans else 0.0; r = tp / len(faults)
    return 2 * p * r / (p + r) if p + r else 0.0


def edge_positions(P, idx):
    xy = {i: P[i]['xy'] for i in idx if P[i]['xy']}
    if not xy: return set()
    xs = [v[0] for v in xy.values()]; ys = [v[1] for v in xy.values()]
    return {i for i, (x, y) in xy.items() if min(abs(x - min(xs)), abs(x - max(xs)), abs(y - min(ys)), abs(y - max(ys))) <= 0.5}


def l7r(P):
    cl = l7r_classes(P); faults = {i for i, v in cl.items() if v[0] == 'fault'}; rvalid = {i for i, v in cl.items() if v[0] == 'valid'}
    scored = faults | rvalid
    if len(scored) < 10: return None
    imax = {i: (M22.fitstats(P[i]) or {}).get('imax', 0.0) for i in cl}
    order = sorted(cl, key=lambda i: (imax[i], i))
    nodb = {i for i in cl if not (isinstance(P[i]['_s'].get('fpm_sheet_resistance'), (int, float)) and math.isfinite(P[i]['_s']['fpm_sheet_resistance']))}
    return {'decided': True, 'key': sorted(faults), 'robust_valid': sorted(rvalid), 'borderline': {str(i): v[1] for i, v in cl.items() if v[0] == 'borderline'},
            'fault_why': {str(i): cl[i][1] for i in faults}, 'n_iv': len(cl), 'n_scored': len(scored), 'n_valid': len(rvalid),
            'critical': len(faults) >= 2, 'effect': len(faults) if len(faults) >= 2 else None, 'naive': [],
            '_order': order, '_edge': sorted(edge_positions(P, list(cl))), '_nodb': sorted(nodb), '_all': sorted(cl), 'oracle': True}


def l7r_cheap(f, k_med):
    F, V = set(f['key']), set(f['robust_valid'])
    rules = {'none (naive)': [], 'all': f['_all'], 'grid edge': f['_edge'], f'lowest max|I| (k={k_med})': f['_order'][:k_med]}
    diag = {'lowest max|I| (true k)': f['_order'][:len(F)], 'no finite database Rs': f['_nodb']}
    return {k: l7r_correct(v, F, V) for k, v in rules.items()}, {k: l7r_correct(v, F, V) for k, v in diag.items()}


def jac(a, b):
    a, b = set(a), set(b); return 1.0 if not a and not b else len(a & b) / len(a | b)


# ---------------- L4 (section 3) ----------------
def anion_free(system):
    return not (set(system.split('-')) & CO2.ANIONS)


def gs_ok(ph):
    if len(ph['elements']) != 1: return True
    e = ph['elements'][0]
    try: return e in GS and int(ph['sg']) == GS[e]
    except (TypeError, ValueError): return False


def l4_v23(P, lid, system, tighten=True):
    phs = {p['phase']: p for p in M22.co2_phases(system)}
    pairs = [pr for pr in M22.ST22['l4_pairs'] if pr['phase_A'] in phs and pr['phase_B'] in phs]
    if tighten and anion_free(system): pairs = [pr for pr in pairs if gs_ok(phs[pr['phase_A']]) and gs_ok(phs[pr['phase_B']])]
    save = M21.ST21; M21.ST21 = {'phases': M22.ST22['phases'], 'l4_pairs': pairs}
    try: return M21.l4_general(P, lid, system)
    finally: M21.ST21 = save


# ---------------- probes ----------------
def l3_probe(P, E, sig):
    o = KY.l3(P, E, sig)
    if o is None or not o['decided']: return None
    vals = {i: KY._at(p, E) for i, p in enumerate(P)}; cov = [i for i, v in vals.items() if v]
    traps = sorted(i for i in cov if vals[i][2] > 1.05)
    if not traps: return None
    return {'traps': traps, 'naive': o['naive'], 'covering': cov, 'E_eV': E}


def l1_probe(P):
    o = M22.l1_v22(P)
    if o is None or not o['decided']: return None
    cls = {}
    for i, p in enumerate(P):
        iv = iv_points(p)
        if iv is not None: c = IVC.classify(*iv); cls[i] = c['cls'] if c['cls'] != 'fault' else ('fault' if c['why'] in PART1 else 'fault (erratic)')
    inval = sorted(i for i, c in cls.items() if c != 'valid')
    return {'invalid': inval, 'classes': {str(i): c for i, c in cls.items()}, 'l7r_faults': sorted(i for i, c in cls.items() if c == 'fault'),
            'naive': o['naive'], 'critical_v22': o['critical']}


# ---------------- census ----------------
def run():
    facts = defaultdict(list); lost = defaultdict(Counter); probes = {'L3': [], 'L1': []}; libs = {}; l4_nt = []
    for r in CM.ROWS:
        if DEV != (split(r['id']) == 'dev'): continue
        P = CM.positions(r['id'])
        if P is None: continue
        libs[r['id']] = (r, P); s = r['system']; lid = r['id']
        base = {'system': s, 'libs': [lid], 'test': split(lid) == 'test', 'split': split(lid)}
        o = M22.l8_v22(P, CM.sig_A(s))
        if o is None: lost['L8']['not eligible'] += 1
        elif o['decided']: facts['L8'].append({'id': lid, **base, **{k: v for k, v in o.items() if k != 'decided'}})
        out = l4_v23(P, lid, s)
        if out is None: lost['L4']['not eligible'] += 1
        for o in out or []:
            facts['L4'].append({'id': f'{lid}|x0={o["x0"]}', **base, **{k: v for k, v in o.items() if k != 'decided'}})
        if anion_free(s):
            for o in l4_v23(P, lid, s, tighten=False) or []: l4_nt.append({'id': f'{lid}|x0={o["x0"]}', 'system': s, 'critical': o['critical'], 'pair': o['pair']})
        o = l7r(P)
        if o is None: lost['L7r']['not eligible (< 10 scored)'] += 1
        else: facts['L7r'].append({'id': lid, **base, **o})
        pr = l3_probe(P, M21.EN.get(s, {}).get('E_eV', 2.5), CM.sig_A(s))
        if pr: probes['L3'].append({'id': lid, **base, **pr})
        pr = l1_probe(P)
        if pr: probes['L1'].append({'id': lid, **base, **pr})
    # L7r cheap rules (k from training-split critical facts)
    ktr = [len(f['key']) for f in facts['L7r'] if f['critical'] and f['split'] == 'train']
    k_med = int(math.floor(float(np.median(ktr)) + 0.5)) if ktr else 2
    for f in facts['L7r']: f['cheap'], f['cheap_diag'] = l7r_cheap(f, k_med)
    res = {}
    for t in SCORED:
        F = facts[t]; crit, ctrl, sel = M21.mix_of(F, t); mix = crit + sel; c = len(sel) / len(mix) if mix else 0.0
        g = M21.gate_mix(mix, c); c34 = bool(mix) and all(v['pass'] for v in g.values()) and all(f['oracle'] for f in mix)
        naive = next(iter(F[0]['cheap'])) if F else None; c1 = bool(crit) and all(not f['cheap'][naive] for f in crit)
        pairs = [(a, b) for a, b in combinations(mix, 2) if a['system'] == b['system']]
        dif = (lambda a, b: jac(a['key'], b['key']) < 0.5) if t == 'L7r' else (lambda a, b: C2M.differ(t, a, b))
        c2 = sum(dif(a, b) for a, b in pairs) / len(pairs) if pairs else None
        sysc = Counter(f['system'] for f in crit); eff = [f['effect'] for f in crit if f.get('effect') is not None]
        incl = len(crit) >= 6 and len(sysc) >= 2 and c2 is not None and c2 >= 0.5 and c34 and c1
        extra = {}
        if t == 'L8':
            for d in ('deep', 'shallow'):
                extra[d] = {'facts': sum(f['depth'] == d for f in F), 'critical': sum(f['depth'] == d for f in crit), 'mix': sum(f['depth'] == d for f in mix)}
            extra['baseline_T105'] = sum(1 for f in mix if f['baseline_T105']) / len(mix) if mix else None
        if t == 'L7r':
            extra['k_median_train'] = k_med; extra['k_train_n'] = len(ktr)
            extra['diag'] = {k: M21.binom_gate(sum(1 for f in mix if f['cheap_diag'][k]), len(mix), c) for k in mix[0]['cheap_diag']} if mix else {}
            nf = sum(len(f['key']) for f in mix); nd = sum(len(set(f['key']) & set(f['_nodb'])) for f in mix)
            extra['faults_without_db_rs'] = {'faults': nf, 'no_finite_db_rs': nd, 'share': nd / nf if nf else None}
            extra['fault_why'] = dict(Counter(w for f in mix for w in f['fault_why'].values()))
        res[t] = {'decided': len(F), 'critical': len(crit), 'critical_systems': len(sysc), 'critical_by_system': dict(sysc.most_common()),
                  'nsnzn_share': (sysc.get('N-Sn-Zn', 0) / len(crit)) if crit else None, 'control_available': len(ctrl), 'control_selected': len(sel),
                  'control_share': c, 'critical_test': sum(f['test'] for f in crit), 'mix_test': sum(f['test'] for f in mix), 'C2': c2, 'C2_pairs': len(pairs),
                  'cheap': g, 'C34': c34, 'C1_prior': c1,
                  'effect': {'median': float(np.median(eff)), 'p10': float(np.percentile(eff, 10)), 'p90': float(np.percentile(eff, 90))} if eff else None,
                  'includable': incl, 'lost': dict(lost[t]), 'mix_ids': [f['id'] for f in mix], **extra}
    # L7r replicate Jaccard (data-intrinsic, no gate)
    rep = []; why = Counter()
    byid = {f['id']: f for f in facts['L7r']}
    for (s, rk), ids in M22_groups(libs).items():
        for a, b in combinations(ids, 2):
            if a not in byid or b not in byid: continue
            A, B = libs[a][1], libs[b][1]; cat, _ = KY.comp_var(A + B)
            _, xa = KY.comp_var(A, cat) if cat else (None, None); _, xb = KY.comp_var(B, cat) if cat else (None, None)
            if cat and (xa is None or xb is None): continue
            st = max(KY.comp_step(A, xa) or 0, KY.comp_step(B, xb) or 0) if cat else 0
            fa, fb = set(byid[a]['key']), set(byid[b]['key']); sa = set(byid[a]['_all']); sb = set(byid[b]['_all'])
            m = [i for i in sa & sb if not cat or (xa[i] is not None and xb[i] is not None and abs(xa[i] - xb[i]) <= st)]
            if not m: continue
            ma, mb = fa & set(m), fb & set(m)
            for i in ma | mb: why[(byid[a]['fault_why'].get(str(i)) or byid[b]['fault_why'].get(str(i)))] += 1
            rep.append({'pair': [a, b], 'system': s, 'matched': len(m), 'faults_a': len(ma), 'faults_b': len(mb),
                        'jaccard': None if not ma and not mb else jac(ma, mb)})
    jj = [p['jaccard'] for p in rep if p['jaccard'] is not None]
    res['L7r']['replicate'] = {'pairs': len(rep), 'pairs_with_faults': len(jj), 'both_empty': len(rep) - len(jj),
                               'jaccard': {'median': float(np.median(jj)), 'p10': float(np.percentile(jj, 10)), 'p90': float(np.percentile(jj, 90))} if jj else None,
                               'matched_fault_why': dict(why), 'by_pair': rep}
    # L4: section 3 drops and the change against MV1f
    v23 = {f['id'] for f in facts['L4']}; nt = {f['id']: f for f in l4_nt}
    dropped = [f for i, f in nt.items() if i not in v23]
    mv1f = {f['id']: f for f in json.load(open(os.path.join(CM.HERE, 'MC22_CENSUS.json')))['e']['facts']['L4']} if not DEV else {}
    res['L4']['section3_dropped'] = {'facts': len(dropped), 'critical': sum(f['critical'] for f in dropped), 'by_pair': dict(Counter(f['pair'] for f in dropped))}
    v23c = {f['id'] for f in facts['L4'] if f['critical']}; m1c = {i for i, f in mv1f.items() if f['critical']}
    res['L4']['vs_MV1f'] = {'critical_MV1f': len(m1c), 'critical_v23': len(v23c), 'kept': len(v23c & m1c), 'removed': sorted(m1c - v23c), 'added': sorted(v23c - m1c),
                            'pairs_v23': dict(Counter(f['pair'] for f in facts['L4'] if f['critical']))}
    # probes and pairs
    l8ids = {f['id'] for f in facts['L8']}; l8mix = set(res['L8']['mix_ids']); l7ids = {f['id'] for f in facts['L7r']}; l7mix = set(res['L7r']['mix_ids'])
    pr = {'L3': {'set': len(probes['L3']), 'systems': len({p['system'] for p in probes['L3']}), 'with_L8_fact': sum(p['id'] in l8ids for p in probes['L3']),
                 'with_L8_item': sum(p['id'] in l8mix for p in probes['L3']), 'naive_is_trap': sum(p['naive'] in p['traps'] for p in probes['L3'])},
          'L1': {'set': len(probes['L1']), 'systems': len({p['system'] for p in probes['L1']}), 'with_L7r_fact': sum(p['id'] in l7ids for p in probes['L1']),
                 'with_L7r_item': sum(p['id'] in l7mix for p in probes['L1']), 'naive_invalid': sum(p['naive'] in p['invalid'] for p in probes['L1']),
                 'naive_on_l7r_fault': sum(p['naive'] in p['l7r_faults'] for p in probes['L1'])}}
    label = '3 types, one without fresh confirmation' if res['L7r']['includable'] else 'pilot set, 2 types'
    inc = [t for t in SCORED if res[t]['includable']]
    return {'scope_libraries': len(libs), 'types': res, 'probes': pr, 'includable': inc, 'release_label': label,
            'facts': {t: [{k: v for k, v in f.items() if not k.startswith('_')} for f in F] for t, F in facts.items()},
            'probe_sets': probes}


def M22_groups(libs):
    g = defaultdict(list)
    for lid, (r, P) in libs.items():
        if r.get('recipe'): g[(r['system'], r['recipe'])].append(lid)
    return {k: sorted(v, key=int) for k, v in g.items() if len(v) >= 2}


def fmt(v, d=3):
    return '-' if v is None else (f'{v:.{d}g}' if isinstance(v, float) else str(v))


def write_md(o):
    T = o['types']; mv = json.load(open(os.path.join(CM.HERE, 'MC22_CENSUS.json')))['e']['types']
    L = ['# MC v2.3 census (MV1h; HTEM_MC2_RULES_v23.md)', '',
         f"Scope: {o['scope_libraries']} non-dev fully cached libraries. **Disclosure:** L7r and the L4 anion-free rule are post-hoc changes on seen data; no fresh HTEM data remains. L4 runs on the VM-E10-fixed sticks.", '',
         f"**Includable scored types:** {', '.join(o['includable']) or 'none'}. **Release label:** {o['release_label']}.", '',
         '## Side by side with MV1f (v2.2 census, (e))', '', '| Type | MV1f critical (systems) | MV1h critical (systems) | MV1h includable |', '|---|---|---|---|']
    for t, m in (('L8', 'L8'), ('L4', 'L4'), ('L7r', 'L7')):
        L.append(f"| {t} | {mv[m]['critical']} ({mv[m]['critical_systems']}){' (L7 v2.2)' if t == 'L7r' else ''} | {T[t]['critical']} ({T[t]['critical_systems']}) | {'yes' if T[t]['includable'] else 'no'} |")
    L += ['', '## Per type', '', '| Type | Decided | Critical (systems) | N-Sn-Zn share | Controls avail / kept (share) | Critical test / mix test | C2 (pairs) | C1 | C3/C4 | Effect median (p10-p90) | Lost |', '|---|---|---|---|---|---|---|---|---|---|---|']
    for t in SCORED:
        r = T[t]; e = r['effect']
        L.append(f"| {t} | {r['decided']} | {r['critical']} ({r['critical_systems']}) | {fmt(r['nsnzn_share'], 2)} | {r['control_available']} / {r['control_selected']} ({r['control_share']:.2f}) | {r['critical_test']} / {r['mix_test']} | {fmt(r['C2'], 2)} ({r['C2_pairs']}) | {'pass' if r['C1_prior'] else 'fail'} | {'pass' if r['C34'] else 'fail'} | {fmt(e['median']) + ' (' + fmt(e['p10']) + ' to ' + fmt(e['p90']) + ')' if e else '-'} | {', '.join(f'{k} {v}' for k, v in r['lost'].items()) or '-'} |")
    L += ['', '## Cheap rules: k/n, binomial p, cap', '']
    for t in SCORED:
        L.append(f"- **{t}:** " + '; '.join(f"{k} {v['k']}/{v['n']} p={v['p']:.3f}{'' if v['cap_ok'] else ' CAP FAIL'}" for k, v in T[t]['cheap'].items()))
    r7 = T['L7r']
    L.append(f"- **L7r diagnostics (no gate):** " + '; '.join(f"{k} {v['k']}/{v['n']}" for k, v in r7.get('diag', {}).items()) + f"; k (median faults, train critical) = {r7['k_median_train']} from {r7['k_train_n']} facts")
    L += ['', f"**L8 depth:** deep {T['L8']['deep']}, shallow {T['L8']['shallow']}; single-constraint baseline (T > 1.05 count) {fmt(T['L8']['baseline_T105'])}.", '',
          f"**L7r faults by reason (mix):** {r7.get('fault_why')}. **Faults without a finite database Rs:** {r7.get('faults_without_db_rs')}.", '',
          f"**L7r replicate check (no gate):** {r7['replicate']['pairs']} pairs ({r7['replicate']['pairs_with_faults']} with faults, {r7['replicate']['both_empty']} both empty); Jaccard {r7['replicate']['jaccard']}; matched faults by reason {r7['replicate']['matched_fault_why']}.", '',
          f"**L4 section 3:** dropped {T['L4']['section3_dropped']}.", '',
          f"**L4 against MV1f:** critical {T['L4']['vs_MV1f']['critical_MV1f']} -> {T['L4']['vs_MV1f']['critical_v23']} (kept {T['L4']['vs_MV1f']['kept']}); removed {T['L4']['vs_MV1f']['removed']}; added {T['L4']['vs_MV1f']['added']}.", '',
          f"**L4 critical by pair (v2.3):** {T['L4']['vs_MV1f']['pairs_v23']}.", '',
          '## Probes (diagnostic only; never scored, traced or trained on)', '',
          f"- **L3 probe:** {o['probes']['L3']}", f"- **L1 probe:** {o['probes']['L1']}", '',
          '## Critical items by system', '']
    for t in SCORED: L.append(f"- **{t}:** " + ', '.join(f'{k} {v}' for k, v in T[t]['critical_by_system'].items()))
    open(os.path.join(CM.HERE, 'MC23_CENSUS.md'), 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))


def main():
    o = run()
    if DEV:
        print(json.dumps({k: v for k, v in o.items() if k not in ('facts', 'probe_sets')}, indent=1, default=str)[:6000]); return
    json.dump(o, open(os.path.join(CM.HERE, 'MC23_CENSUS.json'), 'w'), indent=1, default=lambda v: v.item() if hasattr(v, 'item') else str(v))
    write_md(o)


if __name__ == '__main__':
    main()
