#!/usr/bin/env python3
"""readers_mv2.py (v4.5 MC v2.2, MV2; prompt MV2 and the MC3 reader table of the v4.5 MC prompt). Frozen before any real-data run.
Scope: the (e) census libraries (non-dev, fully cached). Dev seeds (MC_DEV=1) are for debugging only and never the gate.

S4mc3 (T + R balance, A = 1 - T - R; mc_keys.balance), used by L3 and L8.
  synthetic (fresh base 931000, N = 200; half coherent film on substrate, half incoherent multilayer): |A_read - A_true| <= 0.01 at a
    random in-run energy on >= 90 % of seeds (validate_mc.film / edge; T and R noise from config synth.P1).
  real 1, transparent region: positions with optical data and max T <= 1.05 (the MC3 artifact exclusion) in libraries carrying an L3
    or L8 fact; transparent region = T > 0.9 max T with >= 10 points; sigma_A = hypot(SD of A over the region, sigma_A_rep(system));
    pass if |median A over the region| <= 2 sigma_A on >= 90 % of positions. All-position rate (no T exclusion) reported, not gated.
  real 2, replicate agreement: non-dev replicate groups (same system and recipe, >= 2 libraries), positions matched by composition
    (census_mc.matched, L-inf <= 0.02), both with optical data and max T <= 1.05; at the system's L3 energy E,
    pass if |A_a(E) - A_b(E)| <= 2 sqrt(2) sigma_A with sigma_A = hypot(mean of the two transparent SDs, sigma_A_rep) on >= 90 % of
    pairs; fewer than 50 pairs -> insufficient (reported, not a failure).
L6 second-phase detector (the per-position flag of keys_mc2.l6, copied verbatim in flags()).
  synthetic (fresh base 932000, N = 200 injected + 200 null): system and main phase drawn from the (e) L6 facts (a random fact);
    second phase drawn from the other CO2-admissible phases of that system whose strongest stick in 22-49 deg lies > 0.3 deg from every
    main stick (otherwise redraw; a phase hidden under the main pattern is not detectable by definition). Pattern = synth.xrd_pattern
    background and super-Poisson noise; sticks with >= 1 % relative intensity as pseudo-Voigt peaks (one FWHM U(0.15, 0.6) and eta
    U(0.2, 0.8) per pattern); main strongest height = base * exp U(ln 0.4, ln 6); second phase strongest = r * main strongest,
    r ~ U(0.03, 0.20). Reader S4hx (readers.xrd.read, frozen config). Pass: injected flagged on >= 90 %, null flagged on <= 5 %.
    Recovery per r band (3-5, 5-10, 10-20 %) reported.
  real, replicate agreement: non-dev replicate groups in systems with an L6 fact, matched positions as above, both with peaks; call =
    (library main phase, flag); pass if calls agree on >= 90 % of pairs; fewer than 50 pairs -> insufficient.
If a reader fails a gate, its types drop (S4mc3: L3 and L8; L6 detector: L6), with no iteration. Writes v4/htem/MV2_READERS.json/.md."""
import json, math, os, sys
from collections import defaultdict
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_mc2 as CM, keys_mc2 as KY, co2_mc2 as CO2
import census_mc22 as M22, census_mc21 as M21
import validate_mc as VM, census_mc as CMC, mc_keys as K, synth as SY
from readers import xrd as RX
DEV = bool(os.environ.get('MC_DEV')); N = 200
B3 = 0 if DEV else 931000; B6 = 100000 if DEV else 932000
XCFG = CM.API.CFG['readers']['xrd']; TN, RN = VM.TN, VM.RN


def flags(P, peaks_of, sticks, main, idx):
    """keys_mc2.l6 per-position second-phase flag, verbatim logic, for positions idx."""
    phases = list(sticks); mtt = [t for t, _ in sticks[main]]; out = {}
    for i in idx:
        pk = peaks_of(i)
        if pk is None: continue
        sc = {ph: RX.match_phase(pk, sticks[ph], tol_deg=0.3, top=5) for ph in phases}
        top = max((q['height'] for q in pk), default=0); f = False
        for ph in phases:
            if ph == main or sc[ph][0] < 0.5: continue
            for st, meas in sc[ph][1]:
                q = min(pk, key=lambda q: abs(q['center'] - meas))
                if min(abs(meas - t) for t in mtt) > 0.3 and q['height'] >= 0.05 * top and q['snr'] >= 6: f = True
        out[i] = f
    return out


# ---------------- S4mc3 ----------------
def s4mc3_synth():
    ok = 0
    for k in range(N):
        r = np.random.default_rng(B3 + k); a = VM.edge(r); coh = k % 2 == 0
        T, R, A = VM.film(r, a, r.uniform(0.1, 0.6), coherent=coh)
        Tn, Rn = T + r.normal(0, TN, VM.E.size), R + r.normal(0, RN, VM.E.size); idx = np.flatnonzero(Tn >= 0.01)
        i = int(r.choice(idx)); Ar, _, _ = K.balance(VM.E, Tn, Rn); ok += abs(Ar[i] - A[i]) <= 0.01
    return {'fresh_base': B3, 'n': N, 'within_0.01': ok / N, 'pass': ok / N >= 0.9}


def at_E(o, E):
    e, t, r = o; k = int(np.argmin(np.abs(e - E))); return 1 - t[k] - r[k]


def s4mc3_real(libs, opt_libs):
    n = ok = n_all = ok_all = 0
    for lid in opt_libs:
        r, P = libs[lid]; sa = CM.sig_A(r['system'])
        for p in P:
            if not p.get('opt'): continue
            A, sd, tr = K.balance(*p['opt'])
            if sd is None: continue
            good = abs(float(np.median(A[tr]))) <= 2 * math.hypot(sd, sa); n_all += 1; ok_all += good
            if float(np.nanmax(p['opt'][1])) > 1.05: continue
            n += 1; ok += good
    t1 = {'positions': n, 'within_band': ok / n if n else None, 'all_positions': n_all, 'all_within_band': ok_all / n_all if n_all else None,
          'pass': bool(n and ok / n >= 0.9)}
    m = ok2 = 0
    for (s, rk), ids in groups(libs).items():
        E = M21.EN.get(s, {}).get('E_eV', 2.5); sa = CM.sig_A(s)
        for a in range(len(ids)):
            for b in range(a + 1, len(ids)):
                for pa, pb in CMC.matched(libs[ids[a]][1], libs[ids[b]][1]):
                    if not (pa.get('opt') and pb.get('opt')): continue
                    if max(float(np.nanmax(pa['opt'][1])), float(np.nanmax(pb['opt'][1]))) > 1.05: continue
                    _, sda, _ = K.balance(*pa['opt']); _, sdb, _ = K.balance(*pb['opt'])
                    if sda is None or sdb is None: continue
                    ea, eb = pa['opt'][0], pb['opt'][0]
                    if not (ea[0] <= E <= ea[-1] and eb[0] <= E <= eb[-1]): continue
                    m += 1; ok2 += abs(at_E(pa['opt'], E) - at_E(pb['opt'], E)) <= 2 * math.sqrt(2) * math.hypot((sda + sdb) / 2, sa)
    t2 = {'pairs': m, 'agree': ok2 / m if m else None,
          'status': 'insufficient (< 50 pairs)' if m < 50 else ('pass' if ok2 / m >= 0.9 else 'fail')}
    return t1, t2


# ---------------- L6 detector ----------------
def render(r, phs):
    """phs: list of (sticks, scale_of_strongest); returns x, y with synth.xrd_pattern background and noise."""
    x = SY.XRD_GRID; base = 8000 + 3000 * r.random(); cv = r.uniform(1.3, 1.5) - 1
    y = base * (1 + cv * np.exp(-(x - 19) / 12)) + 1500 * r.random() * np.exp(-0.5 * ((x - 30) / 4) ** 2)
    fw, eta = r.uniform(0.15, 0.6), r.uniform(0.2, 0.8); h0 = base * math.exp(r.uniform(math.log(0.4), math.log(6)))
    for st, sc in phs:
        top = max(i for _, i in st)
        for tt, it in st:
            if it >= 0.01 * top and 19 <= tt <= 52: y = y + SY.pv(x, tt, fw, h0 * sc * it / top, eta)
    y = np.clip(y, 0, None); y = y + r.normal(0, 1, y.size) * np.sqrt(y)
    return x, y


def l6_synth(l6facts):
    inj, null, band = [], [], defaultdict(list)
    for k in range(2 * N):
        r = np.random.default_rng(B6 + k); f = l6facts[int(r.integers(len(l6facts)))]
        phs = {p['phase']: M21._stk(p) for p in M22.co2_phases(f['system'])}; main = f['main']
        mtt = [t for t, _ in phs[main]]
        def strongest(st):
            w = [(i, t) for t, i in st if 22 <= t <= 49]; return max(w)[1] if w else None
        cand = sorted(ph for ph in phs if ph != main and strongest(phs[ph]) is not None and min(abs(strongest(phs[ph]) - t) for t in mtt) > 0.3)
        if k < N:
            if not cand: inj.append(None); continue
            sec = cand[int(r.integers(len(cand)))]; rr = r.uniform(0.03, 0.20)
            x, y = render(r, [(phs[main], 1.0), (phs[sec], rr)])
        else:
            x, y = render(r, [(phs[main], 1.0)])
        pk = RX.read(x, y, XCFG)['peaks']; fl = flags([None], lambda i: pk, phs, main, [0]).get(0, False)
        if k < N:
            inj.append(fl); band['3-5' if rr < 0.05 else '5-10' if rr < 0.10 else '10-20'].append(fl)
        else: null.append(fl)
    ii = [v for v in inj if v is not None]; rec = sum(ii) / len(ii) if ii else None; fp = sum(null) / len(null)
    return {'fresh_base': B6, 'n_injected': len(ii), 'no_candidate': inj.count(None), 'recovery': rec, 'false_flags': fp,
            'by_band': {b: {'n': len(v), 'recovery': sum(v) / len(v)} for b, v in sorted(band.items())},
            'pass': bool(rec is not None and rec >= 0.9 and fp <= 0.05)}


def l6_real(libs, l6facts):
    main = {f['libs'][0]: f['main'] for f in l6facts}; systems = {f['system'] for f in l6facts}
    m = ag = 0; conf = defaultdict(int)
    for (s, rk), ids in groups(libs).items():
        if s not in systems: continue
        phs = {p['phase']: M21._stk(p) for p in M22.co2_phases(s)}
        ids = [i for i in ids if i in main]
        for a in range(len(ids)):
            for b in range(a + 1, len(ids)):
                A, B = libs[ids[a]][1], libs[ids[b]][1]
                for pa, pb in CMC.matched(A, B):
                    ia, ib = A.index(pa), B.index(pb)
                    fa = flags(A, lambda i: CM.peaks(A, i), phs, main[ids[a]], [ia]).get(ia)
                    fb = flags(B, lambda i: CM.peaks(B, i), phs, main[ids[b]], [ib]).get(ib)
                    if fa is None or fb is None: continue
                    ca, cb = (main[ids[a]], fa), (main[ids[b]], fb); m += 1; ag += ca == cb; conf[f'{fa}|{fb}|same_main={ca[0] == cb[0]}'] += 1
    return {'pairs': m, 'agree': ag / m if m else None, 'confusion': dict(conf),
            'status': 'insufficient (< 50 pairs)' if m < 50 else ('pass' if ag / m >= 0.9 else 'fail')}


def groups(libs):
    g = defaultdict(list)
    for lid, (r, P) in libs.items():
        if r.get('recipe'): g[(r['system'], r['recipe'])].append(lid)
    return {k: sorted(v, key=int) for k, v in g.items() if len(v) >= 2}


def main():
    cen = json.load(open(os.path.join(CM.HERE, 'MC22_CENSUS.json')))['e']   # (e) scope = every fully cached non-dev library
    libs = {}
    for r in CM.ROWS:
        if DEV != (M22.split(r['id']) == 'dev'): continue   # MC_DEV: dev libraries only
        P = CM.positions(r['id'])
        if P is not None: libs[r['id']] = (r, P)
    assert DEV or len(libs) == cen['libraries_in_scope'], (len(libs), cen['libraries_in_scope'])
    F = cen['facts']; l6f = [f for f in F['L6'] if f.get('main')]
    opt_libs = sorted({f['libs'][0] for t in ('L3', 'L8') for f in F[t]} & set(libs), key=int)
    if DEV:
        l6f = [{'libs': [lid], 'system': r['system'], 'main': o['main']} for lid, (r, P) in libs.items()
               if (o := M22.l6_v22(P, r['system'])) and o.get('main')]
        opt_libs = sorted(libs, key=int)
    out = {'scope_libraries': len(libs), 'S4mc3': {'synthetic': s4mc3_synth()}, 'L6_detector': {'synthetic': l6_synth(l6f)}}
    t1, t2 = s4mc3_real(libs, opt_libs); out['S4mc3']['transparent'] = t1; out['S4mc3']['replicate'] = t2
    out['L6_detector']['replicate'] = l6_real(libs, l6f)
    g3 = out['S4mc3']; g6 = out['L6_detector']
    g3['pass'] = g3['synthetic']['pass'] and t1['pass'] and t2['status'] != 'fail'
    g6['pass'] = g6['synthetic']['pass'] and g6['replicate']['status'] != 'fail'
    out['types_dropped'] = (['L3', 'L8'] if not g3['pass'] else []) + (['L6'] if not g6['pass'] else [])
    if DEV: print(json.dumps(out, indent=1, default=float)); return
    json.dump(out, open(os.path.join(CM.HERE, 'MV2_READERS.json'), 'w'), indent=1, default=float)
    L = ['# MV2 readers (readers_mv2.py; HTEM_MC2_RULES_v22.md, prompt MV2)', '',
         f'Scope: {len(libs)} non-dev (e) libraries. S4mc6 v2, S4hx and S4hf stay frozen.', '',
         '| Reader | Gate | Result | Pass |', '|---|---|---|---|',
         f"| S4mc3 | synthetic, fresh base {B3}, |dA| <= 0.01 on >= 90 % | {g3['synthetic']['within_0.01']:.3f} | {g3['synthetic']['pass']} |",
         f"| S4mc3 | transparent region within 2 sigma_A on >= 90 % (max T <= 1.05) | {t1['within_band']} of {t1['positions']} (all positions: {t1['all_within_band']} of {t1['all_positions']}) | {t1['pass']} |",
         f"| S4mc3 | replicate A(E) within 2 sqrt2 sigma_A on >= 90 % | {t2['agree']} of {t2['pairs']} pairs | {t2['status']} |",
         f"| L6 detector | synthetic, fresh base {B6}: recovery >= 0.9, false <= 0.05 | recovery {g6['synthetic']['recovery']}, false {g6['synthetic']['false_flags']}, by band {g6['synthetic']['by_band']} | {g6['synthetic']['pass']} |",
         f"| L6 detector | replicate call agreement >= 90 % | {g6['replicate']['agree']} of {g6['replicate']['pairs']} pairs | {g6['replicate']['status']} |",
         '', f"**Types dropped:** {out['types_dropped'] or 'none'}."]
    open(os.path.join(CM.HERE, 'MV2_READERS.md'), 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))


if __name__ == '__main__':
    main()
