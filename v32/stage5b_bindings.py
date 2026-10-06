#!/usr/bin/env python3
"""stage5b_bindings.py (Stage 5B): law bindings of papers 2-6 (candidate law -> library entry, inputs/target node ids), classified by
provenance.classify_law on the audited node graphs (after the Sol tag overrides). Definitions become T4 recompute candidates, fits T7
candidates, independent/agreement T3 candidates; 'dependent' bindings are dropped. Writes papers/<k>/law_bindings.json.
Library map: candidate-law id -> library id ('definition' = the authors' own computation, recompute audit only)."""
import json, sys
V32 = '/home/aid1/Documents/harbor/v32'; sys.path.insert(0, V32)
import provenance as P, laws as L
MAP = {
 's039': {'bragg_xrd_hrtem': 'bragg', 'bragg_xrd_saed': 'bragg', 'scherrer_vs_tem': 'scherrer', 'scherrer_vs_sem': 'scherrer', 'tem_vs_sem_size': None,
          'recompute_tauc': 'definition', 'recompute_urbach': 'definition', 'recompute_force_const': 'definition', 'recompute_debye': 'definition', 'recompute_etaB': 'definition'},
 's098': {'mix_tga_residue': 'mixing_residue', 'thinfilm_SE_rank': 'colaneri_shacklette', 'recompute_SE_eff': 'definition', 'recompute_SSE_t': 'definition', 'layers_linear': None},
 't042': {'bragg_xrd_hrtem': 'bragg', 'vegard_rank': 'vegard', 'electrostriction_SP2': 'electrostriction', 'recompute_d33s': 'definition', 'recompute_dP': 'definition',
          'recompute_dT': 'definition', 'recompute_k': 'definition', 'modified_curie_weiss': None},
 't051': {'Pr_PE_vs_HTD': 'pr_agreement', 'Td_diel_vs_PrT': 'td_agreement', 'FE_RFE_IE_vs_XRD': None, 'mlcc_Pr_PE_vs_shock': 'pr_agreement', 'Td_mlcc_diel_vs_PE': 'td_agreement',
          'recompute_PrT': 'definition', 'recompute_w': 'definition'},
 's048': {'bragg_anatase_ref': 'bragg_reference', 'xrd_intensity_fraction': None, 'tga_mass_balance': 'mixing_residue', 'recompute_ucs': 'definition', 'recompute_cof': 'definition',
          'recompute_wear': 'definition', 'archard_ucs': 'archard_ucs'},
}
WHY_NONE = {'tem_vs_sem_size': 'both sizes are histogram statistics of the authors\' images (A): no M target', 'layers_linear': 'additivity of SE with layer count needs a layer-count series the panels do not give per sample',
            'modified_curie_weiss': 'needs a fitted diffuseness exponent per sample from the same curve (fit on the target): no disjoint test cells',
            'FE_RFE_IE_vs_XRD': 'presence/absence of a transition, not a value; 2 opportunities', 'xrd_intensity_fraction': 'intensity ratios need a reference intensity scale not on the panels (spread 50%)'}
if __name__ == '__main__':
    for k, mp in MAP.items():
        gj = json.load(open(f'{V32}/selection/graphs/{k.upper()}.json')); nodes = json.load(open(f'{V32}/papers/{k}/nodes.json'))
        g = P.Graph([dict(x, evidence={'kind': x['evidence']['kind'], 'text': x['evidence']['text']}) for x in nodes]); out = []
        for cl in gj['candidate_laws']:
            lib = mp.get(cl['id'])
            if lib is None: out.append({'id': cl['id'], 'law_class': 'not bound', 'reason': WHY_NONE.get(cl['id'], 'not in the library')}); continue
            params = cl.get('params', []) if lib == 'definition' else (L.LIBRARY[lib].get('params', []) + [p for p in cl.get('params', []) if p.get('kind') == 'fit'])
            params = [dict(p) for p in params]
            for p in params:
                if isinstance(p.get('fit_on'), str): p['fit_on'] = []   # library text ('end-member cells, disjoint from the target'): disjoint by construction
                if p.get('kind') == 'fit' and not p.get('fit_on'): p['fit_on'] = [cl['target']] if lib in ('electrostriction', 'archard_ucs') else []
            try:
                cls, mode, why = P.classify_law({'id': cl['id'], 'inputs': cl['inputs'], 'target': cl['target'], 'params': params,
                                                 'agreement': (L.LIBRARY[lib].get('agreement', False) if lib != 'definition' else False)}, g)
            except P.ProvenanceError as e: cls, mode, why = 'error', None, str(e)
            if lib != 'definition' and L.LIBRARY[lib].get('mode') == 'ranking': mode = 'ranking'
            if 'ranking' in (cl.get('family') or '').lower() and cls in ('independent', 'agreement'): mode = 'ranking'   # the candidate predicts a direction only
            out.append({'id': cl['id'], 'library': lib, 'inputs': cl['inputs'], 'target': cl['target'], 'params': params, 'law_class': cls, 'mode': mode, 'reason': why,
                        'family': cl.get('family'), 'opportunities': cl.get('opportunities'), 'reader': (L.LIBRARY[lib].get('reader') if lib != 'definition' else 'curve/bar'),
                        'methods_span': next((n['evidence']['text'] for n in nodes if n['id'] == cl['target'] and n['evidence']['kind'] == 'span'), None)})
        json.dump(out, open(f'{V32}/papers/{k}/law_bindings.json', 'w'), indent=1, ensure_ascii=False)
        print(k, ' | '.join(f"{b['id']}: {b['law_class']}{'/' + b['mode'] if b.get('mode') else ''}" for b in out))
