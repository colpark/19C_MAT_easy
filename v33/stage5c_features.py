#!/usr/bin/env python3
"""stage5c_features.py (Stage 5C, user instruction 2): per-paper feature specs - which features of which panels the laws, T1 and the T4
audits need, which validated replica style each panel maps to, and whether it may be read in 5D.
status:
  ready              crop usable (tier A/B accepted, or tier-C fallback 'verified' by verify_crops.py) and every listed feature type
                     passes the replica gate on the mapped style (replicas/feature_check.json)
  no crop            panel absent from inputs.json (not segmented) or its tier-C crop was dropped / unverified
  no validated style the panel style (or one of its feature types) has no passing replica style: never read for a key
  annotation         value printed in the image (HRTEM d-spacing, FTIR band label): annotation entry (OCR + blind Sol read), see stage5c_annotations.py
  not read           no reader by design (SAED ring radii, histograms of A sizes, micrographs)
Roles: a law id (T3/T7/T4 recompute input or target), 'T1' (cell values of an M panel), 'audit object' (an A value read only as the object
of a T4 recompute audit). Series colours, legend entries and feature arguments (x positions, peak windows) are 5D inputs, each with evidence
and a blind Sol check (rule 3). Writes papers/<k>/features.json and replicas/FEATURE_SPECS.md."""
import sys as _pb_s, os as _pb_o
_pb_d = _pb_o.path.dirname(_pb_o.path.abspath(__file__))
while not _pb_o.path.exists(_pb_o.path.join(_pb_d, 'pbroot.py')) and _pb_o.path.dirname(_pb_d) != _pb_d: _pb_d = _pb_o.path.dirname(_pb_d)
_pb_s.path.insert(0, _pb_d)
from pbroot import ROOT, HOST
import json, os
V32 = f'{ROOT}'
G = {(r['style'], r['feature']): r['pass'] for r in json.load(open(f'{V32}/replicas/feature_check.json'))}
# (panel, node, roles, style, feature types, note)  - style None = see note / status override
SPEC = {
 's039': [
  ('F2', 'xrd', ['bragg_xrd_hrtem', 'T1'], 't042_spectrum', ['peak_x'], '6 stacked subplots: crop per subplot, x ticks declared from the bottom axis'),
  ('F5c', 'edx', ['T1'], 't042_spectrum', ['peak_x'], ''),
  ('F6', 'uvvis', ['T1'], 't042_curve', ['y_at_x', 'x_at_extremum'], ''),
  ('F11a', 'ftir', ['T1'], 't042_dip', ['peak_x'], 'transmittance dips: peak_x kind=min'),
  ('F11b', 'ftir_fp', ['recompute_force_const', 'recompute_debye', 'T1'], 'annotation', [], 'band positions printed on the panel (nu1, nu2 per x)'),
  ('F14', 'xps_survey', ['T1'], 't042_spectrum', ['peak_x'], ''),
  ('F16', 'mh', ['T1'], 't042_loop', ['crossing'], '6 stacked subplots, one loop each: crop per subplot'),
  ('F4g', 'hrtem', ['bragg_xrd_hrtem'], 'annotation', [], 'd(400) label'), ('F4h', 'hrtem', ['bragg_xrd_hrtem'], 'annotation', [], 'd label'),
  ('F4i', 'hrtem', ['bragg_xrd_hrtem'], None, [], 'not segmented'),
  ('F4j', 'saed', ['bragg_xrd_saed'], 'not read', [], 'ring radii: no reader (indices only printed)'), ('F4k', 'saed', ['bragg_xrd_saed'], 'not read', [], 'ring radii: no reader'),
  ('F8', 'Eg_dir/E_U', ['audit object'], 's048_curve', ['y_at_x'], 'A values on a scatter vs x: read only as T4 audit objects'),
  ('F12', 'F_const/theta_D', ['audit object'], 's048_curve', ['y_at_x'], 'A values vs x'),
  ('F19a', 'eta_B', ['audit object'], None, [], 'law of approach fits (A); eta_B values printed in the caption/text: text_recoverable'),
 ],
 's098': [
  ('F4a', 'xrd', ['T1'], 't042_spectrum', ['peak_x'], ''), ('F4b', 'xrd_002', ['T1'], 't042_spectrum', ['peak_x'], 'labelled stacked traces'),
  ('F4c', 'ftir', ['T1'], 't042_dip', ['peak_x'], ''),
  ('F4d', 'tga_pure/tga_comp', ['mix_tga_residue', 'T1'], 's098_tga', ['plateau', 'y_at_x'], 'residue at 800 C'),
  ('F4e', 'dtg', ['T1'], 's098_curve', ['x_at_extremum'], 'DTG peak temperature'),
  ('F5b', 'folding', ['T1'], 's098_bar', ['bar_top'], ''), ('F5c', 'stress_strain', ['T1'], 's098_ss', ['x_end', 'y_at_extremum'], 'break strain, strength'),
  ('F6a', 'sigma', ['thinfilm_SE_rank', 'T1'], 's098_bar', ['bar_top'], 'error-bar caps are black, not the bar colour'),
  ('F6b', 'R_bend', ['T1'], 't051_htd', ['y_at_x'], 'single marker series'),
  ('F7a', 'SE_T', ['thinfilm_SE_rank', 'recompute_SE_eff', 'recompute_SSE_t', 'T1'], 's098_curve', ['y_at_x'], ''),
  ('F7b', 'SE_A', ['T1'], 's098_curve', ['y_at_x'], ''), ('F7c', 'SE_R', ['T1'], 's098_curve', ['y_at_x'], ''),
  ('F7h', 'SE_layers', ['T1'], 's098_bar', ['bar_top'], 'grouped bars, 3 colours'),
  ('F7f', 'SE_eff', ['audit object'], None, [], 'crop dropped (E05)'), ('F7e', 'SSE_t', ['audit object'], 's098_bar', ['bar_top'], ''),
 ],
 't042': [
  ('F1a', 'density', ['T1'], 't042_curve', ['y_at_x'], ''),
  ('F2b', 'xrd_peaks', ['bragg_xrd_hrtem', 'vegard_rank', 'T1'], None, [], 'not segmented'), ('F2c', 'xrd_peaks', ['bragg_xrd_hrtem', 'vegard_rank', 'T1'], None, [], 'crop dropped (shows F2e)'),
  ('F3a', 'd_hrtem', ['bragg_xrd_hrtem'], 'annotation', [], '0.113 nm (222)'), ('F3b', 'd_hrtem', ['bragg_xrd_hrtem'], 'annotation', [], '0.134 nm (220)'),
  ('F3g', 'eds', ['T1'], 't042_spectrum', ['peak_x'], ''), ('F3h', 'eds', ['T1'], 't042_spectrum', ['peak_x'], ''),
  ('F4a', 'xps_survey', ['T1'], 't042_spectrum', ['peak_x'], ''), ('F4b', 'xps_survey', ['T1'], 't042_spectrum', ['peak_x'], ''),
  ('F4c', 'xps_hr', ['T1'], 't042_spectrum', ['peak_x'], ''), ('F4d', 'xps_hr', ['T1'], 't042_spectrum', ['peak_x'], ''), ('F4e', 'xps_hr', ['T1'], 't042_spectrum', ['peak_x'], ''),
  ('F4f', 'xps_hr', ['T1'], 't042_spectrum', ['peak_x'], ''), ('F4h', 'xps_hr', ['T1'], 't042_spectrum', ['peak_x'], ''),
  ('F5a', 'raman', ['T1'], 't042_spectrum', ['peak_x'], ''), ('F5b', 'ftir', ['recompute_k', 'T1'], 't042_dip', ['peak_x'], 'B-O band positions'),
  ('F6a', 'eps_T', ['T1'], 't042_curve', ['y_at_x', 'x_at_extremum', 'y_at_extremum'], 'Tm, eps_max'), ('F6b', 'eps_T', ['T1'], 't042_curve', ['y_at_x', 'x_at_extremum', 'y_at_extremum'], ''),
  ('F6c', 'eps_T', ['T1'], 't042_curve', ['y_at_x', 'x_at_extremum', 'y_at_extremum'], ''), ('F6d', 'eps_T', ['T1'], 't042_curve', ['y_at_x', 'x_at_extremum', 'y_at_extremum'], ''),
  ('F7a', 'pe', ['electrostriction_SP2', 'T1'], 't042_loop', ['crossing', 'y_at_x'], 'Pr, Ec, P at E'), ('F7b', 'pe', ['electrostriction_SP2', 'T1'], 't042_loop', ['crossing', 'y_at_x'], ''),
  ('F7c', 'pe', ['electrostriction_SP2', 'T1'], 't042_loop', ['crossing', 'y_at_x'], ''), ('F7d', 'pe', ['electrostriction_SP2', 'T1'], 't042_loop', ['crossing', 'y_at_x'], ''),
  ('F8a', 'se_bip', ['electrostriction_SP2', 'T1'], 't042_butterfly', ['y_at_x'], 'S at E, both branches'), ('F8b', 'se_bip', ['electrostriction_SP2', 'T1'], 't042_butterfly', ['y_at_x'], ''),
  ('F8c', 'se_bip', ['electrostriction_SP2', 'T1'], 't042_butterfly', ['y_at_x'], ''), ('F8d', 'se_bip', ['electrostriction_SP2', 'T1'], 't042_butterfly', ['y_at_x'], ''),
  ('F8e', 'se_uni', ['T1'], 't042_curve', ['y_at_extremum'], 'Smax of unipolar loops'),
  ('F8f', 'd33s/Smax', ['audit object'], 's098_bar', ['bar_top'], ''), ('F6e', 'Ts_Tm/dT', ['audit object'], 's048_curve', ['y_at_x'], ''), ('F5c', 'k_force', ['audit object'], 's048_curve', ['y_at_x'], ''),
  ('F7e', 'pmax_pr', ['audit object'], None, [], 'crop dropped (E05)'), ('F7f', 'dP', ['audit object'], None, [], 'crop dropped (E05)'),
 ],
 't051': [
  ('F1a', 'pe_rt', ['Pr_PE_vs_HTD', 'recompute_w', 'T1'], 't051_loop', ['crossing'], 'graded overlapping loops'),
  ('F1b', 'leak', ['T1'], None, [], 'log-scale scatter: no validated style'),
  ('F1c', 'htd', ['Pr_PE_vs_HTD', 'T1'], 't051_htd', ['plateau'], 'released polarization'),
  ('F3a', 'pe_T_x0_x20', ['recompute_PrT', 'T1'], 't051_loop_sep', ['crossing'], ''), ('F3b', 'pe_T_x0_x20', ['recompute_PrT', 'T1'], 't051_loop_sep', ['crossing'], ''),
  ('F1e', 'diel_T', ['T1'], None, [], 'dual-axis scatter with open/filled markers: no validated style'),
  ('F1f', 'hydro', ['T1'], 't051_htd', ['y_at_x'], ''),
  ('F2c', 'raman_rt', ['T1'], 't051_spectrum', ['peak_x'], ''), ('F3e', 'raman_T', ['T1'], 't051_spectrum', ['peak_x'], ''), ('F4a', 'epr', ['T1'], 't042_spectrum', ['peak_x'], ''),
  ('F6b', 'mlcc_pe_E', ['mlcc_Pr_PE_vs_shock', 'T1'], 't051_mlcc', ['crossing'], ''),
  ('F6d', 'mlcc_depol', ['T1'], 't051_htd', ['plateau'], 'two sub-panels d1/d2: crop'), ('F6e', 'mlcc_shock_I', ['T1'], 's048_curve', ['x_at_extremum', 'y_at_extremum'], ''),
  ('F6f', 'mlcc_diel', ['Td_mlcc_diel_vs_PE', 'T1'], None, [], 'dual-axis scatter: no validated style'),
  ('F7a', 'raman_P', ['T1'], 't051_spectrum', ['peak_x'], ''), ('F7b', 'raman_P', ['T1'], 't051_spectrum', ['peak_x'], ''), ('F7d', 'raman_P', ['T1'], 't051_spectrum', ['peak_x'], ''),
  ('F7e', 'raman_P', ['T1'], 't051_spectrum', ['peak_x'], ''), ('F7f', 'raman_P', ['T1'], 't051_spectrum', ['peak_x'], ''),
  ('F1d', 'Pr_T', ['audit object'], 's048_curve', ['y_at_x'], ''), ('F1h', 'lit_w', ['audit object'], 's048_curve', ['y_at_x'], ''),
 ],
 's048': [
  ('F2', 'xrd_raw', ['T1'], 'mono_spectrum', ['peak_x'], ''), ('F3', 'xrd_gpc', ['T1'], 't042_spectrum', ['peak_x'], 'labelled stacked traces'),
  ('F5', 'ftir', ['T1'], None, [], 'not segmented (sub-panels F5a-c dropped/unverified)'),
  ('F6a', 'stress_strain', ['archard_ucs', 'T1'], 's048_curve', ['y_at_extremum', 'x_at_extremum'], 'UCS = peak stress'),
  ('F8', 'tga_0/tga_ti', ['tga_mass_balance', 'T1'], 's048_tga_right', ['plateau'], '3x2 grid: crop per subplot; TGA on the right axis'),
  ('F10m', 'cof_trace', ['recompute_cof', 'T1'], None, [], 'not segmented (only the full figure exists)'),
  ('F11', 'wear_profile', ['recompute_wear', 'T1'], 's048_wear', ['y_at_extremum'], ''),
  ('F6b', 'ucs_bar', ['audit object'], 's098_bar', ['bar_top'], ''), ('F9', 'cof_bar/wear_rate', ['audit object'], 's098_bar', ['bar_top'], ''),
 ],
}

def crop_status(k, pid):
    inp = json.load(open(f'{V32}/papers/{k}/inputs.json'))['panels']
    if pid not in inp: return 'no crop', 'not in inputs.json (not segmented)'
    v = inp[pid]
    if v['tier'] != 'C fallback': return 'ok', f"tier {v['tier']} {v.get('status', '')}".strip()
    rows = {r['crop']: r for r in json.load(open(f'{V32}/papers/{k}/audit/crop_verification.json'))['rows']}
    r = rows.get(pid, {}); return ('ok', 'tier C, verified') if r.get('verdict') == 'verified' else ('no crop', f"tier C, {r.get('verdict', 'not verified')}")

if __name__ == '__main__':
    md = ['# Stage 5C feature specs (v3.2)', '', 'status per needed panel; generated by stage5c_features.py from inputs.json, crop_verification.json and replicas/feature_check.json.', '']
    totals = {}
    for k, rows in SPEC.items():
        out = []
        for pid, node, roles, style, feats, note in rows:
            cs, cwhy = crop_status(k, pid)
            if style == 'annotation': st = 'no validated reader' if cs == 'ok' else 'no crop'   # OCR fails the annotation replica gate (E10)
            elif style == 'not read': st = 'not read'
            elif cs != 'ok': st = 'no crop'
            elif style is None: st = 'no validated style' if 'no validated style' in note else ('not read' if 'text_recoverable' in note else 'no crop')
            else:
                bad = [f for f in feats if not G.get((style, f), False)]; st = 'ready' if not bad else 'no validated style'
                if bad: note = (note + '; ' if note else '') + f"replica gate FAIL on {style}: {', '.join(bad)}"
            out.append({'panel': pid, 'node': node, 'roles': roles, 'style': style, 'features': feats, 'crop': cwhy, 'status': st, 'note': note})
        json.dump(out, open(f'{V32}/papers/{k}/features.json', 'w'), indent=1)
        from collections import Counter
        c = Counter(r['status'] for r in out); totals[k] = c
        md += [f'## {k}', '', '| panel | node | roles | style | features | crop | status | note |', '|---|---|---|---|---|---|---|---|']
        md += [f"| {r['panel']} | {r['node']} | {', '.join(r['roles'])} | {r['style'] or ''} | {', '.join(r['features'])} | {r['crop']} | **{r['status']}** | {r['note']} |" for r in out]
        md += ['', 'counts: ' + ', '.join(f'{a} {b}' for a, b in sorted(c.items())), '']
        print(k, dict(c))
    open(f'{V32}/replicas/FEATURE_SPECS.md', 'w').write('\n'.join(md) + '\n')
