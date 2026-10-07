#!/usr/bin/env python3
"""C2 reconciliation, second routes, frozen tolerances and materials.jsonl (skill C2; prompt C2.2-C2.6).

  reconcile.py liion  C2DIR OUTDIR    -> RECONCILE_liion.md, materials_liion.jsonl, tolerances (merged)
  reconcile.py jarvis C2DIR OUTDIR    -> RECONCILE_jarvis.md, materials_jarvis.jsonl, tolerances (merged)

Tolerance rules (fixed here, before the numbers are computed; I4):
  * Li-ion D route agreement: tau_D = max(0.10 dex, 2 x 1.4826 x MAD of log10(ours / reference)) over every pair of
    (our D, a reference D at the same material and temperature), references being the deposited SAMOS D (Li7NbO6)
    and the printed FPMD sigma of Tables 2-3 converted by the same Nernst-Einstein law (level A, marked).
    A D is keyable when a reference exists and agrees within tau_D, and D_se / D <= 0.15 ("both routes agree").
  * JARVIS Tc route agreement: tau_Tc(Tc) = max(0.10 K, 2 x 1.4826 x MAD(Tc_ours - Tc_dep), 0.05 x Tc_dep);
    lambda agreement: |lambda_ours / lambda_dep - 1| <= max(0.02, 2 x 1.4826 x MAD of the relative difference).
    A JARVIS record is keyable for Tc when both agree and alpha2F has no negative-frequency weight inside the
    integration (n_negative_w == 0 or lambda finite).
Mismatch classes: rounding, rule ambiguity, missing records, paper inconsistency (never edits a card, I7).
"""
import json, os, sys, hashlib
import numpy as np
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nernst_einstein as ne, arrhenius, paper_tables as PT

D_SE_MAX = 0.15


def rmad(x):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return float(1.4826 * np.median(np.abs(x - np.median(x)))) if len(x) else float('nan')


def neutral_id(prefix, key):
    return f'{prefix}-{hashlib.sha256(key.encode()).hexdigest()[:8]}'


def tol_path(outdir):
    return os.path.join(outdir, 'TOLERANCES_trackC.json')


def merge_tol(outdir, part):
    p = tol_path(outdir)
    t = json.load(open(p)) if os.path.exists(p) else {}
    t.update(part)
    json.dump(t, open(p, 'w'), indent=1, sort_keys=True)


# ------------------------------------------------------------------ Li-ion
def liion(c2, outdir):
    traj = [json.loads(l) for l in open(os.path.join(c2, 'liion_traj.jsonl'))]
    cl = json.load(open(os.path.join(c2, 'liion_cells.json')))
    cells = {c['uuid']: c for c in cl['cells']}
    tabs = PT.by_formula()
    samos = {s['T']: s for s in cl['samos_li7nbo6'] if s['D_cm2_s'] is not None}
    # per material per temperature: prefer the run tagged final, then the longest
    runs = defaultdict(lambda: defaultdict(list))
    for r in traj:
        runs[r['unitcell_uuid']][r['T_label']].append(r)
    mats = []
    pairs = []
    for uid, c in sorted(cells.items(), key=lambda x: x[1]['reduced']):
        tab = tabs.get(c['reduced'])
        per_T = {}
        for T, rs in sorted(runs.get(uid, {}).items(), reverse=True):
            rs = sorted(rs, key=lambda r: (bool(r.get('final_trajectory')), r['t_total_ps']), reverse=True)
            r = rs[0]
            per_T[T] = {'D': r['D_cm2_s'], 'D_se': r['D_se'], 'sigma_H1': r['sigma_mS_cm_H1'], 'traj_uuid': r['traj_uuid'],
                        'kind': r['kind'], 't_ps': r['t_total_ps'], 'n_li': r['n_li'], 'volume_A3': r['volume_A3'],
                        'n_alternative_runs': len(rs) - 1, 'T_label_src': r['T_label_src']}
            ref = None
            if c['reduced'] == 'Li7NbO6' and T in samos:
                ref = ('samos_deposited', samos[T]['D_cm2_s'], 'S')
            elif tab:
                key = {1000: 'sigma_fpmd_1000', 750: 'sigma_fpmd_750', 500: 'sigma_fpmd_500'}.get(T)
                if tab['table'] == 2 and 'Li2P2PdO7' in tab['printed']:
                    key = 'sigma_fpmd_1000' if T == 600 else None   # printed value is at 600 K (**)
                if key and key in tab:
                    Dref = ne.D_from_sigma(r['n_li'], r['volume_A3'], tab[key], T)
                    ref = (f'printed_table{tab["table"]}_{key}', Dref, 'A')
            if ref and r['D_cm2_s'] > 0:
                lr = float(np.log10(r['D_cm2_s'] / ref[1]))
                per_T[T]['ref'] = {'route': ref[0], 'D_ref': ref[1], 'level': ref[2], 'log10_ratio': lr}
                pairs.append(lr)
        mats.append({'uuid': uid, 'c': c, 'tab': tab, 'per_T': per_T})
    tau = max(0.10, 2 * rmad(pairs))
    merge_tol(outdir, {'liion_tau_D_dex': tau, 'liion_tau_D_pairs': len(pairs), 'liion_D_se_max_rel': D_SE_MAX,
                       'liion_tau_rule': 'max(0.10 dex, 2 x 1.4826 x MAD of log10(ours/ref))'})
    # keyability, S10 frozen reading, Arrhenius (ours) where >= 3 resolved temperatures
    out = []
    for m in mats:
        c, tab = m['c'], m['tab']
        for T, v in m['per_T'].items():
            rel = v['D_se'] / v['D'] if v['D'] > 0 else float('inf')
            v['resolved'] = bool(v['D'] > 0 and rel <= D_SE_MAX)
            v['route_agree'] = bool('ref' in v and abs(v['ref']['log10_ratio']) <= tau)
            v['keyable_D'] = v['resolved'] and v['route_agree']
        s10 = None
        if 1000 in m['per_T']:
            s10 = 'diffusive' if m['per_T'][1000]['D'] > 1e-9 else 'no_diffusion'
        # second-route Arrhenius (reconciliation only): every temperature with D > 0 and a finite SE, inverse-variance
        # weighted (arrhenius.py R3); the 0.15 resolvability gate stays on keys (T1) and T7 has its own g1-g4 gates.
        # Revision RC1 (VC-E21): the first draft reused the 0.15 gate here and left no fit at all.
        res = {T: v for T, v in m['per_T'].items() if v['D'] > 0 and np.isfinite(v['D_se']) and v['D_se'] > 0}
        arr = None
        if len(res) >= 3:
            Ts = sorted(res)
            f = arrhenius.fit(Ts, [res[T]['D'] for T in Ts], [res[T]['D_se'] for T in Ts], n_boot=1000)
            arr = {'T': Ts, 'Ea_eV': f['Ea_eV'], 'Ea_sd': f['Ea_sd'], 'Ea_printed': tab.get('Ea') if tab else None}
        mid = neutral_id('LI', m['uuid'])
        rec = {'material_id': mid, 'source': 'liion', 'unitcell_uuid': m['uuid'], 'formula': c['formula'],
               'reduced_formula': c['reduced'], 'input_origin': {'db': c['origin_db'], 'id': c['origin_id']},
               'input_level': 'A', 'release_eligible': False,
               'stages': {'S2_S8_flags': {'value': c['flags'], 'level': 'S', 'source_address': c['source_address']},
                          'S6_gap_eV': {'value': c['direct_bandgap_eV'], 'level': 'S', 'source_address': c['source_address']},
                          'S10_frozen_reading': s10,
                          'FPMD': {str(T): v for T, v in sorted(m['per_T'].items())}},
               'arrhenius_ours': arr,
               'paper_class_A': tab['class'] if tab else None, 'paper_table': tab['table'] if tab else None,
               'fate': {'deposited_through': 'S9 (FPMD candidate)', 'escalated_to_ladder': len(m['per_T']) >= 2 and 1000 in m['per_T'],
                        'eliminating_stage': None, 'keyable': False,
                        'note': 'no deposited reject before S10; S10 decision panels missing for Table 1 materials (VC-E18)'}}
        out.append(rec)
    with open(os.path.join(outdir, 'materials_liion.jsonl'), 'w') as f:
        for r in out:
            f.write(json.dumps(r, default=float) + '\n')
    report_liion(out, tau, pairs, cells, tabs, outdir)


def report_liion(out, tau, pairs, cells, tabs, outdir):
    n = len(out)
    cls = Counter(r['paper_class_A'] for r in out)
    ic = Counter((r['paper_class_A'], r['stages']['S2_S8_flags']['value']['ionic_conductor_1000K']) for r in out)
    have1000 = sum(1 for r in out if '1000' in r['stages']['FPMD'])
    ladder = sum(1 for r in out if r['fate']['escalated_to_ladder'])
    no_traj = [r['reduced_formula'] for r in out if not r['stages']['FPMD']]
    only600 = [r['reduced_formula'] for r in out if set(r['stages']['FPMD']) == {'600'}]
    poly = Counter(r['reduced_formula'] for r in out)
    keyD = sum(v['keyable_D'] for r in out for v in r['stages']['FPMD'].values())
    allD = sum(len(r['stages']['FPMD']) for r in out)
    gaps = [(r['stages']['S6_gap_eV']['value'], r['paper_table'] and tabs[r['reduced_formula']].get('gap'), r['reduced_formula'])
            for r in out if r['paper_table'] in (2, 3)]
    gd = [a - b for a, b, _ in gaps if a is not None and b is not None]
    ea = [(r['reduced_formula'], r['arrhenius_ours']['Ea_eV'], r['arrhenius_ours']['Ea_sd'], r['arrhenius_ours']['Ea_printed'],
           r['arrhenius_ours']['T']) for r in out if r['arrhenius_ours']]
    L = ['# RECONCILE_liion (C2)', '',
         'Card: CARD_liion.json (C1). Deposit: xm-46 (fpmd_structures, fpmd_trajectories, fpmd_screening_Li7NbO6). '
         'Our counts never edit the card (I7). Paper tables are level A (author outputs) and serve as targets only.', '',
         '## Stage counts', '', '| Stage | Stated | Ours | Class |', '|---|---|---|---|',
         '| S0-S5 sources to distance | 30,229 / 22,842 / 12,198 / 5,239 / 1,550 / 1,499 | not recountable | missing records (input CIFs not deposited; ICSD/MPDS licensed) |',
         '| S6 electronic (> 1 eV) | 982 | 55/55 deposited cells electronic_insulator True | missing records (rejects not deposited) |',
         '| S7 pinball self-consistency | 914 | 55/55 pinball_parameters_converged True | missing records |',
         '| S7d drift | 851 | not recountable | missing records |',
         '| S8 pinball sigma >= 1 mS/cm | 132 | 55/55 ionic_conductor True | missing records; paper inconsistency PI3 (Fig. 5 sums) |',
         f'| S9 novelty (exclude known) | 55 | {n} deposited unit cells ({len(poly)} reduced formulas) | reconciles (55); KNOWN_77 list gap 6 (B2) |',
         f'| S10 FPMD 1000 K no diffusion | 18 (Table 1) | 1000 K runs deposited for {have1000} materials, all diffusive by the frozen reading; '
         f'{len(only600)} Table 1 materials deposited only at ~600 K, {len(no_traj)} without any trajectory | missing records + deposit/paper inconsistency (VC-E18) |',
         f'| S11 ladder | 34 (9 + 25) | {ladder} materials with a 1000 K run and >= 1 lower temperature | see per-class table |',
         f'| S12 classes | 18 / 25 / 9 (52 of 55) | table membership by reduced formula: {dict(cls)} | rule gap (no criterion); PI1 (52 of 55) |', '',
         '## ionic_conductor_1000K extras (deposited flag) by paper class', '',
         '| paper class (A) | flag True | flag False | flag missing |', '|---|---|---|---|']
    for k in sorted({a for a, _ in ic}, key=str):
        L.append(f'| {k} | {ic.get((k, True), 0)} | {ic.get((k, False), 0)} | {ic.get((k, None), 0)} |')
    L += ['', 'Reading: the flag is not documented; it is reported, never keyed.', '',
          '## Unit cells without trajectories or only at ~600 K', '', f'- no trajectory: {", ".join(sorted(no_traj)) or "none"}',
          f'- only ~600 K (SIRIUS runs): {", ".join(sorted(only600)) or "none"}',
          f'- formulas with several cells (polymorphs): {", ".join(k for k, v in poly.items() if v > 1) or "none"}', '',
          '## Second route: D (ours, msd.py C2proc) against references at the same material and temperature', '',
          f'- pairs: {len(pairs)}; median log10(ours/ref) = {np.median(pairs):+.3f}; robust SD = {rmad(pairs):.3f} dex',
          f'- frozen tau_D = {tau:.3f} dex (rule in the module docstring); keyable D (resolved and agreeing): {keyD} of {allD} runs', '',
          '| material | T (K) | D ours | D_se/D | reference route | D ref | log10 ratio | agree |', '|---|---|---|---|---|---|---|---|']
    for r in out:
        for T, v in sorted(r['stages']['FPMD'].items(), key=lambda x: -int(x[0])):
            if 'ref' in v:
                rr = v['ref']
                L.append(f"| {r['reduced_formula']} | {T} | {v['D']:.2e} | {v['D_se'] / v['D'] if v['D'] > 0 else float('nan'):.2f} | "
                         f"{rr['route']} ({rr['level']}) | {rr['D_ref']:.2e} | {rr['log10_ratio']:+.2f} | {'yes' if v['route_agree'] else 'no'} |")
    L += ['', '## Arrhenius barrier: ours (>= 3 temperatures with D > 0, inverse-variance weighted) against printed (Table 3, A)', '',
          '| material | temperatures | Ea ours (eV) | sd | Ea printed |', '|---|---|---|---|---|']
    for f, e, sd, p, Ts in ea:
        L.append(f'| {f} | {Ts} | {e:.3f} | {sd:.3f} | {p if p is not None else "-"} |')
    if gd:
        L += ['', f'## Band gap: deposited direct_bandgap (S) against printed Table 2-3 gap (A)', '',
              f'- n = {len(gd)}, median difference {np.median(gd):+.3f} eV, max |diff| {np.max(np.abs(gd)):.3f} eV']
    L += ['', '## Engine route (pinball, PET-MAD, FPMD)', '',
          '- pinball D/sigma deposited only for Li7NbO6 (provenance archive); PET-MAD trajectories (1c-13) cover 11+ materials '
          'outside the 55 FPMD set (LiGaBr3 is in KNOWN_77). Overlap FPMD x PET-MAD = 0 materials: no engine comparison table '
          'can be built from the deposits (reported, not imputed).', '']
    open(os.path.join(outdir, 'RECONCILE_liion.md'), 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L[:40]))


# ------------------------------------------------------------------ JARVIS
def jarvis(c2, outdir):
    rows = [json.loads(l) for l in open(os.path.join(c2, 'jarvis_c2.jsonl'))]
    par = json.load(open(os.path.join(c2, 'jarvis_c2_parent.json')))['summary']
    ok = [r for r in rows if r.get('ours_meV') and r['dep_Tc'] is not None and np.isfinite(r['ours_meV']['Tc_K'])]
    dT = np.array([r['ours_meV']['Tc_K'] - r['dep_Tc'] for r in ok])
    dl = np.array([r['ours_meV']['lambda'] / r['dep_lamb'] - 1 for r in ok if r['dep_lamb']])
    tau_abs = max(0.10, 2 * rmad(dT))
    tau_l = max(0.02, 2 * rmad(dl))
    merge_tol(outdir, {'jarvis_tau_Tc_abs_K': tau_abs, 'jarvis_tau_Tc_rel': 0.05, 'jarvis_tau_lambda_rel': tau_l,
                       'jarvis_tau_rule': 'Tc: max(0.10 K, 2 x 1.4826 x MAD, 0.05 Tc); lambda: max(0.02, 2 x 1.4826 x MAD rel)',
                       'jarvis_freq_unit': 'meV'})
    out = []
    for r in rows:
        o = r.get('ours_meV') or {}
        agree = bool(o and r['dep_Tc'] is not None and np.isfinite(o.get('Tc_K', np.nan))
                     and abs(o['Tc_K'] - r['dep_Tc']) <= max(tau_abs, 0.05 * r['dep_Tc'])
                     and r['dep_lamb'] and abs(o['lambda'] / r['dep_lamb'] - 1) <= tau_l)
        tc, st = r['dep_Tc'], r['stability']
        j5 = tc >= 5.0
        j6 = st == 'stable'
        fails = (not j5) + (not j6)
        elim = None if fails == 0 else ('J5_tc' if not j5 and j6 else 'J6_stability' if j5 and not j6 else 'J5|J6 (order-dependent)')
        near5 = abs(tc - 5.0) <= max(tau_abs, 0.05 * 5.0)
        out.append({'material_id': neutral_id('JV', r['jid']), 'source': 'jarvis', 'jid': r['jid'], 'formula': r['formula'],
                    'n_atoms': r['n_atoms'], 'parent_version': r.get('parent_version'),
                    'input_origin': {'icsd': (r.get('parent') or {}).get('icsd')}, 'release_eligible': False,
                    'stages': {'J1_theta_D_ours': (r.get('parent') or {}).get('theta_D_K'),
                               'J4': {'lambda_dep': r['dep_lamb'], 'wlog_dep_K': r['dep_wlog'], 'lambda_ours': o.get('lambda'),
                                      'wlog_ours_K': o.get('omega_log_K'), 'level': 'S'},
                               'J5': {'Tc_dep': tc, 'Tc_ours': o.get('Tc_K'), 'pass': j5, 'near_threshold': near5},
                               'J6': {'stability': st, 'pass': j6}},
                    'route_agree_Tc': agree,
                    'fate': {'eliminating_stage': elim, 'survived': fails == 0,
                             'keyable': bool(agree and elim in ('J5_tc', 'J6_stability') and not near5),
                             'note': 'Fate family not opened: keyable reject stages J5, J6 only (< 3; VC-E19)'},
                    'source_address': r['source_address']})
    with open(os.path.join(outdir, 'materials_jarvis.jsonl'), 'w') as f:
        for r in out:
            f.write(json.dumps(r, default=float) + '\n')
    st = Counter(r['stages']['J6']['stability'] for r in out)
    j5 = sum(r['stages']['J5']['pass'] for r in out)
    both = sum(r['stages']['J5']['pass'] and r['stages']['J6']['pass'] for r in out)
    nag = sum(r['route_agree_Tc'] for r in out)
    el = Counter(r['fate']['eliminating_stage'] for r in out)
    th = [r['stages']['J1_theta_D_ours'] for r in out if r['stages']['J1_theta_D_ours'] is not None]
    L = ['# RECONCILE_jarvis (C2)', '',
         'Card: CARD_jarvis.json (C1). Deposit: figshare 21370572 (1,058 records). Parent: jarvis-tools dft_3d_2021 '
         f'({par["parent_n"]} entries; {par["n_in_2021_parent"]} of 1,058 jids present, the rest from the 2025 dft_3d for B1 and atoms only).', '',
         '## Stage counts', '', '| Stage | Stated | Ours | Class |', '|---|---|---|---|',
         f'| J0 entries with DOS | 55,723 | dft_3d_2021 holds {par["parent_n"]} entries | rounding / versioning (11 fewer) |',
         f'| (elastic tensors) | 17,419 | {par["parent_with_elastic"]} with a usable elastic tensor | rounding / versioning (+{par["parent_with_elastic"] - 17419}) |',
         f'| J1 theta_D > 300 K | 5,618 | {par["parent_theta_gt_300"]} (jarvis-tools ElasticTensor.debye_temperature, VRH) | rule ambiguity: +{par["parent_theta_gt_300"] - 5618} ({(par["parent_theta_gt_300"] / 5618 - 1) * 100:.0f} %); J1 not keyable |',
         '| J2 N(0) > 1 states/eV/Nelect | 1,736 | not recountable (no DOS-at-E_F field) | missing records |',
         f'| J3 n_atoms <= 5 | 1,058 | {sum(r["n_atoms"] <= 5 for r in out)} of the 1,058 have <= 5 atoms as deposited | rule ambiguity (cell basis) + "as of now" subset |',
         f'| J4 EPC computed | 1,058 | {len(out)} | reconciles |',
         f'| J5 Tc >= 5 K | 283 (Fig. 1) | {j5} | reconciles |',
         f'| J6 dynamically stable | 626 of 1,058 (text); 105 after J5 (Fig. 1) | stable {st.get("stable", 0)}; stable and Tc >= 5 K: {both} | reconciles |', '',
         f'Our theta_D on the 1,058 survivors: {sum(t > 300 for t in th)} of {len(th)} above 300 K (the authors\' own J1 survivors).', '',
         '## Second route: lambda, omega_log, Tc recomputed from alpha2F (meV axis; eq. 6-8, mu* = 0.09, no f1 f2)', '',
         f'- records with a finite recomputation: {len(ok)} of {len(rows)}',
         f'- Tc ours - deposited: median {np.median(dT):+.3f} K, robust SD {rmad(dT):.3f} K, p95 |diff| {np.percentile(np.abs(dT), 95):.2f} K, max {np.max(np.abs(dT)):.2f} K',
         f'- lambda relative: median {np.median(dl):+.4f}, robust SD {rmad(dl):.4f}',
         f'- frozen tau_Tc = max({tau_abs:.3f} K, 0.05 Tc); tau_lambda = {tau_l:.3f}; records where both routes agree: {nag} of {len(rows)}', '',
         '## Eliminating stage (frozen readings: Tc >= 5 K; a double failure is order-dependent and never keyed)', '',
         '| eliminating stage | n | keyable (routes agree, not near 5 K) |', '|---|---|---|']
    for k, v in sorted(el.items(), key=lambda x: str(x[0])):
        L.append(f'| {k or "survived"} | {v} | {sum(r["fate"]["keyable"] for r in out if r["fate"]["eliminating_stage"] == k)} |')
    L += ['', 'Fate needs keyable rejects on at least 3 stages (skill C0). JARVIS keys rejects at J5 and J6 only (J1 fails '
          'reconciliation, J2 has no field, J3 is ambiguous): the Fate and Route families are not built (VC-E19, I5).', '']
    open(os.path.join(outdir, 'RECONCILE_jarvis.md'), 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    {'liion': liion, 'jarvis': jarvis}[sys.argv[1]](sys.argv[2], sys.argv[3])
