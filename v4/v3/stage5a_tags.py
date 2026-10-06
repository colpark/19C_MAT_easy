#!/usr/bin/env python3
"""stage5a_tags.py (Stage 5A, step 3): a paper's node graph (papers/<key>/nodes.json) from its provisional graph
(selection/graphs/<KEY>.json), every span re-verified by code against the extracted text (MinerU md, pdftotext raw; whitespace and
LaTeX markup normalised), plus the inputs of the Sol tag audit (Methods text and figure captions in v32_host/papers/<key>/text/).
A span that is not found turns the node's evidence into 'default' only when a default rule names the quantity; otherwise the node is
listed as unverified (the Sol tag audit then decides, restrictively).
Rietveld convention (graph agent, recorded): lattice parameters from a Rietveld refinement are A, computed_from the XRD pattern; the
refinement is a model, not a law parameter. usage: stage5a_tags.py <KEY> ..."""
import sys as _pb_s, os as _pb_o
_pb_d = _pb_o.path.dirname(_pb_o.path.abspath(__file__))
while not _pb_o.path.exists(_pb_o.path.join(_pb_d, 'pbroot.py')) and _pb_o.path.dirname(_pb_d) != _pb_d: _pb_d = _pb_o.path.dirname(_pb_d)
_pb_s.path.insert(0, _pb_d)
from pbroot import ROOT, HOST
import json, re, sys
V32 = f'{ROOT}'; sys.path.insert(0, V32)
import provenance as P

def norm(s):
    s = re.sub(r'\$|\\mathrm|\\mathbf|\\bf|\\mathcal|\\left|\\right|[{}^_~\\]', ' ', s or '')
    return re.sub(r'[^a-z0-9.%]+', ' ', s.lower()).strip()

def methods_section(md):
    lines = md.splitlines(); start = end = None
    for i, l in enumerate(lines):
        h = l.strip('# ').lower()
        if start is None and l.startswith('#') and re.search(r'method|experimental|materials and|characteri[sz]ation|synthesis', h): start = i
        elif start is not None and l.startswith('#') and re.search(r'^(\d+\.?\s*)?(results|discussion|conclusion)', h): end = i; break
    return '\n'.join(lines[start:end]) if start is not None else ''

def run(key):
    k = key.lower(); PD = f'{V32}/papers/{k}'; H = f'{HOST}/papers/{k}'
    gj = json.load(open(f'{V32}/selection/graphs/{key}.json')); inp = json.load(open(f'{PD}/inputs.json'))
    md = open(f'{H}/text/{key}.md').read(); raw = open(f'{H}/text/{key}_raw.txt').read(); hay = norm(md) + ' ' + norm(raw)
    nodes, unver = [], []
    for n in gj['nodes']:
        nd = {kk: n.get(kk) for kk in ('id', 'quantity', 'panel', 'level', 'computed_from', 'instrument', 'formula', 'conditions_shown', 'chart_type', 'scale_bar', 'params', 'fit_model')}
        nd['computed_from'] = nd['computed_from'] or []; nd['params'] = nd['params'] or []
        ev = n.get('evidence') or {}
        if ev.get('kind') == 'span':
            if norm(ev['text']) and norm(ev['text']) in hay: nd['evidence'] = {'kind': 'span', 'text': ev['text'], 'verified': True}
            else:
                q = n.get('quantity'); dflt = P.DEFAULT_LEVEL.get(q)
                nd['evidence'] = {'kind': 'default', 'text': dflt[1]} if dflt else {'kind': 'span', 'text': ev['text'], 'verified': False}
                unver.append(n['id'])
        else: nd['evidence'] = {'kind': 'default', 'text': ev.get('text') or 'default rule'}
        if nd['level'] == 'A' and not nd['computed_from'] and not nd['params']: nd['params'] = [{'name': nd.get('fit_model') or 'model', 'kind': 'fit', 'by': 'authors', 'fit_on': []}]
        nodes.append(nd)
    P.Graph([dict(x, evidence={'kind': x['evidence']['kind'], 'text': x['evidence']['text']}) for x in nodes])   # validates
    json.dump(nodes, open(f'{PD}/nodes.json', 'w'), indent=1, ensure_ascii=False)
    open(f'{H}/text/methods.txt', 'w').write(methods_section(md))
    store = json.load(open([f for f in (f'/home/aid1/Documents/harbor/v024/store/SEM2026/{key}/panels/match.json', f'/home/aid1/Documents/harbor/v024/oa2/store/OA2/{key}/panels/match.json') if __import__('os').path.exists(f)][0]))
    caps = {f'F{f["figure_number"]}': f.get('caption_preamble', '') for f in store['figures'] if f.get('figure_number')}
    json.dump(caps, open(f'{H}/text/captions.json', 'w'), indent=1, ensure_ascii=False)
    print(f"{key}: {len(nodes)} nodes ({sum(x['evidence']['kind'] == 'span' and x['evidence'].get('verified') for x in nodes)} spans verified, "
          f"{sum(x['evidence']['kind'] == 'default' for x in nodes)} default, unverified {unver}); Methods {len(methods_section(md).split())} words; captions {len(caps)}")

if __name__ == '__main__':
    for k in sys.argv[1:]: run(k)
