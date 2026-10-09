#!/usr/bin/env python3
"""census_mc22.py (v4.5 MC v2.2, MV1f; HTEM_MC2_RULES_v22.md): three reports side by side.
  (c) the MV1d v2.1 census (census_mc21) on the 346 MV1d libraries: must reproduce MC21_CENSUS.json byte for byte
  (d) v2.2 rules on the same 346 libraries
  (e) v2.2 rules on all non-dev fully cached libraries (346 plus F2)
v2.2: 27-point validity grid (L7 key decided; L1, L2, L5 stable), L8 depth tags, CO2 chemistry filter on CO1+CO2 sticks for L4 and
L6, fresh confirmation on F2 only (structural must confirm), intention pairs and probes, N-Sn-Zn share. Writes v4/htem/MC22_CENSUS.json
and .md, and v4/htem/mc22/ for (c)."""
import hashlib, json, math, os, sys
from collections import Counter, defaultdict
from itertools import combinations, product
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_mc2 as CM, keys_mc2 as KY, sample_io as SIO, co2_mc2 as CO2
import census_mc21 as M21
from readers import xrd as RX

ROOT = CM.HERE; OUTD = os.path.join(ROOT, 'mc22'); os.makedirs(OUTD, exist_ok=True)
F1 = M21.F1; F2 = set(json.load(open(os.path.join(CM.API.HOST, 'mc', 'f2_list.json'))))
TYPES = M21.TYPES; GROUPS = M21.GROUPS; EN = M21.EN
ST22 = json.load(open(os.path.join(CM.API.HOST, 'refs', 'sticks_mc22.json')))
GRID = list(product((0.99, 0.995, 0.999), (0.01, 0.02, 0.05), (2.5e-8, 5e-8, 1e-7)))
CENTRAL = (0.999, 0.02, 5e-8)
split = M21.split


# ---------------- validity grid ----------------
def fitstats(p):
    if 'fs' in p: return p['fs']
    fp = SIO.fpm(p['_s']); out = None
    if fp:
        I, V = np.asarray(fp['current_A'], float), np.asarray(fp['voltage_V'], float); m = np.isfinite(I) & np.isfinite(V); I, V = I[m], V[m]
        if I.size >= 2 and np.ptp(I) > 0:
            A = np.vstack([I, np.ones(I.size)]).T; (R, V0), *_ = np.linalg.lstsq(A, V, rcond=None); res = V - A @ np.array([R, V0])
            ss = float(np.sum((V - V.mean()) ** 2)); r2 = 1 - float(np.sum(res ** 2)) / ss if ss > 0 else 0.0
            se = math.sqrt(float(np.sum(res ** 2)) / max(I.size - 2, 1) / max(float(np.sum((I - I.mean()) ** 2)), 1e-300))
            out = {'n': int(I.size), 'imax': float(np.max(np.abs(I))), 'R': float(R), 'R_err': se, 'r2': r2,
                   'rmsf': math.sqrt(float(np.mean(res ** 2))) / (float(np.max(np.abs(V))) or 1e-300)}
        else:
            out = {'n': int(I.size), 'imax': float(np.max(np.abs(I))) if I.size else 0.0, 'R': None, 'R_err': None, 'r2': None, 'rmsf': None}
    p['fs'] = out
    return out


def valid_at(fs, g):
    r2, rms, fl = g
    return bool(fs and fs['R'] is not None and fs['n'] >= 4 and fs['imax'] >= fl and fs['R'] > 0 and fs['r2'] >= r2 and fs['rmsf'] <= rms)


def at_grid(P, g):
    Q = []
    for p in P:
        q = dict(p); fs = fitstats(p)
        q['iv'] = None if p['iv'] is None else {**p['iv'], 'valid': valid_at(fs, g)}
        Q.append(q)
    return Q


def l1_v22(P):
    o = KY.l1(P)
    if o is None: return None
    same = all((k := KY.l1(at_grid(P, g))) is not None and k['key'] == o['key'] for g in GRID if g != CENTRAL)
    return {**o, 'decided_pre': o['decided'], 'decided': o['decided'] and same, 'critical': o['critical'] and same, 'grid_stable': same}


def l2_v22(P, sig):
    o = KY.l2(P, sig)
    if o is None: return None
    same = all((k := KY.l2(at_grid(P, g), sig)) is not None and abs(k['key'] - o['key']) <= o['tol'] for g in GRID if g != CENTRAL)
    return {**o, 'decided_pre': True, 'decided': same, 'critical': o['critical'] and same, 'grid_stable': same}


def l7_v22(P):
    o = KY.l7(P)
    if o is None: return None
    iv = [p for p in P if p['iv'] is not None]; cnt = {g: sum(valid_at(fitstats(p), g) for p in iv) for g in GRID}
    same = all(abs(v - o['key']) <= 1 for v in cnt.values())
    return {**o, 'decided_pre': True, 'decided': same, 'critical': o['critical'] and same, 'grid_range': [min(cnt.values()), max(cnt.values())]}


def l8_v22(P, sig):
    o = M21.l8_v21(P, sig)
    if o is None: return None
    return {**o, 'depth': 'deep' if abs(o['key'] - o['n_T_over']) >= 2 else 'shallow'}


def l5_v22(Ph, Pc, cat):
    o = KY.l5(Ph, Pc, cat)
    if o is None: return None
    same = all((k := KY.l5(at_grid(Ph, g), at_grid(Pc, g), cat)) is not None and k['key'] == o['key'] for g in GRID if g != CENTRAL)
    return {**o, 'decided_pre': True, 'decided': same, 'critical': o['critical'] and same, 'grid_stable': same}


# ---------------- structural under CO2 ----------------
def co2_phases(system):
    return [p for p in ST22['phases'] if p['sticks'] and CO2.admissible(p, system)]


def l6_v22(P, system):
    phs = {p['phase']: M21._stk(p) for p in co2_phases(system)}
    if len(phs) < 2: return None
    return KY.l6(P, lambda i: CM.peaks(P, i), phs, RX.match_phase)


def l4_v22(P, lid, system):
    adm = {p['phase'] for p in co2_phases(system)}
    pairs = [pr for pr in ST22['l4_pairs'] if pr['phase_A'] in adm and pr['phase_B'] in adm]
    save = M21.ST21
    M21.ST21 = {'phases': ST22['phases'], 'l4_pairs': pairs}
    try: return M21.l4_general(P, lid, system)
    finally: M21.ST21 = save


# ---------------- census ----------------
def census_v22(scope, fresh_set):
    facts = defaultdict(list); lost = defaultdict(Counter); libs = {}; probes = []
    for r in CM.ROWS:
        if split(r['id']) == 'dev' or r['id'] not in scope: continue
        P = CM.positions(r['id'])
        if P is None: continue
        libs[r['id']] = (r, P); s = r['system']
        run = {'L1': lambda: l1_v22(P), 'L2': lambda: l2_v22(P, CM.sig_logrs(s)), 'L3': lambda: KY.l3(P, EN[s]['E_eV'], CM.sig_A(s)),
               'L7': lambda: l7_v22(P), 'L8': lambda: l8_v22(P, CM.sig_A(s)), 'L4': lambda: l4_v22(P, r['id'], s), 'L6': lambda: l6_v22(P, s)}
        for t, f in run.items():
            out = f()
            if out is None: lost[t]['not eligible'] += 1; continue
            for o in (out if isinstance(out, list) else [out]):
                if not o['decided']:
                    lost[t]['robustness (grid)' if o.get('decided_pre') else 'key not decided'] += 1
                    continue
                fid = r['id'] + (f'|x0={o["x0"]}' if 'x0' in o else '')
                facts[t].append({'id': fid, 'system': s, 'libs': [r['id']], 'test': split(r['id']) == 'test', 'fresh': r['id'] in fresh_set,
                                 **{k: v for k, v in o.items() if k not in ('decided',)}})
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
        o = l5_v22(libs[hot][1], libs[cold][1], cat)
        if o is None: lost['L5']['not eligible'] += 1; continue
        used[a] += 1; used[b] += 1
        if not o['decided']: lost['L5']['robustness (grid)'] += 1; continue
        facts['L5'].append({'id': f'{hot}>{cold}', 'system': s, 'libs': [hot, cold], 'test': split(hot) == 'test' or split(cold) == 'test',
                            'fresh': hot in fresh_set or cold in fresh_set, **{k: v for k, v in o.items() if k != 'decided'}})
    res, mixes = {}, {}
    for t in TYPES:
        F = facts.get(t, []); crit, ctrl, sel = M21.mix_of(F, t); mix = crit + sel; mixes[t] = mix; c = len(sel) / len(mix) if mix else 0.0
        g = M21.gate_mix(mix, c); c34 = bool(mix) and all(v['pass'] for v in g.values()) and all(f['oracle'] for f in mix)
        nr = next(iter(F[0]['cheap'])) if F else None; c1 = all(not f['cheap'][nr] for f in crit) if crit else False
        import census_mc2 as C2
        pairs = [(a, b) for a, b in combinations(mix, 2) if a['system'] == b['system']]
        c2 = sum(C2.differ(t, a, b) for a, b in pairs) / len(pairs) if pairs else None
        sysc = Counter(f['system'] for f in crit); eff = [f['effect'] for f in crit if f.get('effect') is not None]
        fm = [f for f in mix if f['fresh']]; fc = sum(1 for f in fm if not f['critical']) / len(fm) if fm else 0.0
        fg = M21.gate_mix(fm, fc) if len(fm) >= 6 else None
        fst = 'unconfirmed (< 6 fresh items)' if fg is None else ('pass' if all(v['pass'] for v in fg.values()) else 'fail')
        base = (c2 is not None and c2 >= 0.5) and c34 and c1 and len(crit) >= 6 and len(sysc) >= 2
        incl = base and fst != 'fail' and (fst == 'pass' if t in GROUPS['structural'] else True)
        extra = {}
        if t == 'L8':
            for tag in ('deep', 'shallow'):
                extra[tag] = {'facts': sum(1 for f in F if f['depth'] == tag), 'critical': sum(1 for f in crit if f['depth'] == tag), 'mix': sum(1 for f in mix if f['depth'] == tag)}
            extra['baseline_T105'] = sum(1 for f in mix if f['baseline_T105']) / len(mix) if mix else None
        res[t] = {'decided': len(F), 'critical': len(crit), 'critical_systems': len(sysc), 'critical_by_system': dict(sysc.most_common()),
                  'nsnzn_share': sysc.get('N-Sn-Zn', 0) / len(crit) if crit else None,
                  'naive_failure_rate': len(crit) / len(F) if F else None, 'control_available': len(ctrl), 'control_selected': len(sel), 'control_share': c,
                  'critical_test': sum(f['test'] for f in crit), 'critical_fresh': sum(f['fresh'] for f in crit), 'C2': c2, 'C2_pairs': len(pairs),
                  'cheap': g, 'C34': c34, 'C1_prior': c1, 'gates_pass': base,
                  'effect': {'median': float(np.median(eff)), 'p10': float(np.percentile(eff, 10)), 'p90': float(np.percentile(eff, 90))} if eff else None,
                  'fresh': {'n': len(fm), 'critical': sum(f['critical'] for f in fm), 'gate': fg, 'status': fst}, 'includable': incl, 'lost': dict(lost[t]), **extra}
    grp = {}
    for gname, ts in GROUPS.items():
        inc = [t for t in ts if res[t]['includable']]; crit = [f for t in inc for f in facts.get(t, []) if f['critical']]
        sysg = {f['system'] for f in crit}
        grp[gname] = {'includable': inc, 'critical': len(crit), 'systems': len(sysg), 'critical_test': sum(f['test'] for f in crit), 'builds': len(crit) >= 20 and len(sysg) >= 3}
    built = [g for g, v in grp.items() if v['builds']]; types_b = [t for g in built for t in grp[g]['includable']]
    ncrit = sum(grp[g]['critical'] for g in built); ntest = sum(grp[g]['critical_test'] for g in built)
    fresh_ok = all(res[t]['fresh']['status'] != 'fail' for t in types_b)
    go = {'groups_built': built, 'types': types_b, 'critical': ncrit, 'critical_test': ntest,
          'criteria': {'1 groups >= 2': len(built) >= 2, '2 types >= 3': len(types_b) >= 3, '3 critical >= 60': ncrit >= 60, '4 test >= 15': ntest >= 15, '5 fresh': fresh_ok}}
    go['GO'] = all(go['criteria'].values())
    # intention pairs (rules v22 section 4) and probes
    ip = {}
    for emb, aud in (('L2', 'L7'), ('L3', 'L8')):
        E = {f['libs'][0]: f for f in mixes[emb]}; A = {f['libs'][0]: f for f in mixes[aud]}
        Eall = {f['libs'][0]: f for f in facts.get(emb, [])}; Aall = {f['libs'][0]: f for f in facts.get(aud, [])}
        libs_p = sorted((set(E) & set(Aall)) | (set(A) & set(Eall)), key=int)
        ip[f'{emb}+{aud}'] = {'pairs': len(libs_p), 'embedded_critical': sum(Eall[l]['critical'] for l in libs_p), 'audit_critical': sum(Aall[l]['critical'] for l in libs_p), 'libraries': libs_p}
    probe = {'L1': {'libraries': len(facts.get('L1', [])), 'critical': sum(f['critical'] for f in facts.get('L1', [])),
                    'naive_invalid': sum(1 for f in facts.get('L1', []) if f.get('naive_invalid'))},
             'L3_trap': {'items': len(mixes['L3']), 'naive_impossible': sum(1 for f in mixes['L3'] if f.get('naive_impossible'))}}
    return {'libraries_in_scope': len(libs), 'fresh_libraries': sum(1 for l in libs if l in fresh_set), 'types': res, 'groups': grp, 'go': go,
            'intention_pairs': ip, 'probes': probe, 'facts': {t: [{k: v for k, v in f.items() if k != 'cheap'} for f in F] for t, F in facts.items()},
            'mix_ids': {t: [f['id'] for f in m] for t, m in mixes.items()}}


def reproduce_c(mv1d_scope):
    real = CM.fully_cached
    CM.fully_cached = lambda lid: real(lid) and lid in mv1d_scope
    save = (M21.ROOT, M21.OUTD); M21.ROOT = os.path.join(OUTD, 'c_v21'); M21.OUTD = os.path.join(M21.ROOT, 'mc21'); os.makedirs(M21.OUTD, exist_ok=True)
    import shutil; shutil.copy(os.path.join(ROOT, 'MC2_CENSUS.json'), os.path.join(M21.ROOT, 'MC2_CENSUS.json'))   # (a) inside (c) compares against MV1b
    try: M21.main()
    finally: CM.fully_cached = real; M21.ROOT, M21.OUTD = save
    a = os.path.join(OUTD, 'c_v21', 'MC21_CENSUS.json'); b = os.path.join(ROOT, 'MC21_CENSUS.json')
    return hashlib.sha256(open(a, 'rb').read()).hexdigest() == hashlib.sha256(open(b, 'rb').read()).hexdigest()


def main():
    allc = {r['id'] for r in CM.ROWS if CM.fully_cached(r['id'])}; s346 = allc - F2
    same = reproduce_c(s346)
    D = census_v22(s346, set()); E = census_v22(allc, F2)
    out = {'c_reproduces_MV1d': same, 'scope': {'d': len(s346), 'e': len(allc), 'f2_fully_cached': len(F2 & allc)},
           'c': {t: {k: v for k, v in json.load(open(os.path.join(ROOT, 'MC21_CENSUS.json')))['c']['types'][t].items() if k in ('critical', 'critical_systems', 'includable')} for t in TYPES},
           'd': {k: v for k, v in D.items() if k not in ('facts', 'mix_ids')}, 'e': E}
    json.dump(out, open(os.path.join(ROOT, 'MC22_CENSUS.json'), 'w'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
    write_md(out)


def write_md(o):
    E, D = o['e'], o['d']; R = E['types']
    L = ['# MC v2.2 census (MV1f; HTEM_MC2_RULES_v22.md)', '',
         f"Scope: (d) {o['scope']['d']} libraries (MV1d); (e) {o['scope']['e']} (F2 fully cached {o['scope']['f2_fully_cached']}). Dev never yields facts. (c) reproduces MV1d byte for byte: **{'yes' if o['c_reproduces_MV1d'] else 'NO'}**.", '',
         f"**Round (e): {'GO' if E['go']['GO'] else 'NO-GO'}.** " + '; '.join(f"{k}: {'met' if v else 'not met'}" for k, v in E['go']['criteria'].items()) +
         f". Built groups: {', '.join(E['go']['groups_built']) or 'none'}; types {', '.join(E['go']['types']) or 'none'}; critical {E['go']['critical']}, in test {E['go']['critical_test']}.", '',
         '## Side by side: critical items (systems), includable', '', '| Type | (c) v2.1, 346 | (d) v2.2, 346 | (e) v2.2, all | (e) fresh F2 | (e) includable |', '|---|---|---|---|---|---|']
    for t in TYPES:
        c, d, e = o['c'][t], D['types'][t], R[t]
        L.append(f"| {t} | {c['critical']} ({c['critical_systems']}){' inc' if c['includable'] else ''} | {d['critical']} ({d['critical_systems']}){' inc' if d['includable'] else ''} | {e['critical']} ({e['critical_systems']}) | {e['fresh']['status']} ({e['fresh']['n']}) | {'yes' if e['includable'] else 'no'} |")
    L.append(f"| Round | GO (structural held) | {'GO' if D['go']['GO'] else 'NO-GO'} | {'GO' if E['go']['GO'] else 'NO-GO'} | | |")
    L += ['', '## (e) per type', '', '| Type | Decided | Critical (systems) | N-Sn-Zn share | Naive fails | Controls avail / kept (share) | Critical test / fresh | C2 | C1 | C3/C4 | Effect median (p10-p90) | Losses |', '|---|---|---|---|---|---|---|---|---|---|---|---|']
    for t in TYPES:
        r = R[t]; e = r['effect']; es = f"{e['median']:.3g} ({e['p10']:.3g} to {e['p90']:.3g})" if e else '-'
        c2 = '-' if r['C2'] is None else f"{r['C2']:.2f} ({r['C2_pairs']})"; ns = '-' if r['nsnzn_share'] is None else f"{r['nsnzn_share']:.0%}"
        L.append(f"| {t} | {r['decided']} | {r['critical']} ({r['critical_systems']}) | {ns} | {(r['naive_failure_rate'] or 0):.0%} | {r['control_available']} / {r['control_selected']} ({r['control_share']:.2f}) | {r['critical_test']} / {r['critical_fresh']} | {c2} | {'pass' if r['C1_prior'] else 'fail'} | {'pass' if r['C34'] else 'fail'} | {es} | {', '.join(f'{k} {v}' for k, v in r['lost'].items())} |")
    L += ['', '## (e) cheap rules: k/n, binomial p, cap', '']
    for t in TYPES: L.append(f"- **{t}:** " + ('; '.join(f"{k} {v['k']}/{v['n']} p={v['p']:.3f}{'' if v['cap_ok'] else ' CAP'}{'' if v['pass'] else ' FAIL'}" for k, v in R[t]['cheap'].items()) or '-'))
    r8 = R['L8']
    L += ['', f"L8 depth: deep {r8.get('deep')}, shallow {r8.get('shallow')}; single-constraint baseline (T > 1.05 count) {r8.get('baseline_T105')}.", '',
          '## (e) fresh confirmation (F2 only)', '', '| Type | Fresh items | Fresh critical | Status | Worst rule |', '|---|---|---|---|---|']
    for t in TYPES:
        f = R[t]['fresh']; w = min(f['gate'].items(), key=lambda kv: kv[1]['p']) if f['gate'] else None
        ws = f"{w[0]} {w[1]['k']}/{w[1]['n']}, p={w[1]['p']:.3f}" if w else '-'
        L.append(f"| {t} | {f['n']} | {f['critical']} | {f['status']} | {ws} |")
    L += ['', '## (e) groups', '', '| Group | Includable | Critical | Systems | In test | Builds |', '|---|---|---|---|---|---|']
    for g, v in E['groups'].items(): L.append(f"| {g} | {', '.join(v['includable']) or '-'} | {v['critical']} | {v['systems']} | {v['critical_test']} | {'yes' if v['builds'] else 'no'} |")
    L += ['', '## (e) intention pairs and probes', '']
    for k, v in E['intention_pairs'].items(): L.append(f"- **{k}:** {v['pairs']} libraries carry both (embedded critical {v['embedded_critical']}, audit critical {v['audit_critical']})")
    L.append(f"- **L1 probe:** {E['probes']['L1']['libraries']} decided libraries ({E['probes']['L1']['critical']} critical; naive pick invalid in {E['probes']['L1']['naive_invalid']}). **L3 trap:** {E['probes']['L3_trap']['items']} items, naive pick has T > 1.05 in {E['probes']['L3_trap']['naive_impossible']}.")
    L += ['', '## (e) critical items by system', '']
    for t in TYPES: L.append(f"- **{t}:** " + (', '.join(f'{s} {n}' for s, n in R[t]['critical_by_system'].items()) or 'none'))
    open(os.path.join(ROOT, 'MC22_CENSUS.md'), 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L[:24]))


if __name__ == '__main__':
    main()
