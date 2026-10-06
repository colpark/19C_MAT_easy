#!/usr/bin/env python3
"""provenance.py (v3.2, frozen): the provenance ladder, quantity nodes, the law classifier and the key-eligibility check.

Levels
  D design record   sample identity, nominal composition, processing, test conditions
  M measurement     instrument output per sample and condition, including quantities a standard instrument equation computes from
                    readings that are not matrix quantities (n_H = 1/(e R_H), kappa = D Cp d)
  A author derived  computed by the authors from >= 1 other matrix quantity, by a fitted model, or as a statistic over their own images;
                    literature compilations and fitted curves
  S schematic       illustration or simulation only
  I interpretation  stated mechanisms and conclusions
A key may never come from A or I (hard rule 2). Key sources (hard rule 1): D cells, M cells (within reading uncertainty), two-method image
orderings, laws of the library (by class and family), signatures of the signature table.

Node: {id, quantity, panel, level, computed_from [node ids], formula, instrument, evidence {kind: 'span'|'default', text}, params}.
When Methods says nothing, DEFAULT_LEVEL applies and evidence.kind = 'default'. The same quantity from two instruments = two nodes.

Law classes (code, from the node graph)
  definition   target is A and its computed_from set lies within the law inputs and their ancestors, or the target is an ancestor of an
               input                                                                            -> T4 recompute audits
  fit          a parameter comes from a fit on cells that include the target or its ancestors, by the authors or by us  -> T7 (disjoint
               fit and test cells)
  independent  the M ancestors of target and inputs are disjoint, and every parameter is an external constant with a source or a fit
               on disjoint cells                                                                -> T3 (ranking only if spread > 20%)
  agreement    two instruments measure the same physical quantity (declared by the law) on disjoint M ancestors -> T3 and T4
  dependent    none of the above (shared M ancestors without a definitional relation): not usable
"""
LEVELS = ('D', 'M', 'A', 'S', 'I')
DEFAULT_LEVEL = {   # quantity -> (level, rule text); applies only when Methods says nothing
    'PF': ('A', 'default: power factor is computed from S and rho'),
    'ZT': ('A', 'default: ZT is computed from S, rho, kappa and T'),
    'kappa_e': ('A', 'default: electronic thermal conductivity is computed (Wiedemann-Franz)'),
    'kappa_L': ('A', 'default: lattice thermal conductivity is computed'),
    'kappa_Lb': ('A', 'default: kappa_L + kappa_b is computed as kappa - kappa_e'),
    'mu_H': ('A', 'default: Hall mobility mu_H = R_H / rho (A unless Methods states a separate Hall resistivity)'),
    'n_H': ('M', 'default: n_H = 1/(e R_H) is a standard instrument equation on the Hall voltage'),
    'kappa': ('M', 'default: laser-flash kappa = D Cp d is a standard instrument equation'),
}
FAMILY_LAW_CLASSES = {'t3': {'independent', 'agreement'}, 't4_recompute': {'definition', 'agreement'}, 't7': {'fit'}}

# ---------------------------------------------------------------- v3.3 definitions (frozen F9)
SD_U_FRACTION = 0.5            # definition 1: u = 0.5 x frozen panel tolerance, so one band (2u) = the tolerance
SD_CLAIM = {'consistent_within_bands': 0.5, 'contradicted_one_cell_bands': 5.0, 'contradicted_two_cells_bands': 3.0, 'comparison_margin_bands': 3.0}
LEVEL_DEFAULTS_V33 = {          # definition 2: used when Methods says nothing; the evidence is marked 'default'
    'M': ['mean over repeated specimens reported directly by the test (tensile strength, elongation at break, nanoindentation hardness and modulus, '
          'density, thermal conductivity) when the plotted value does not come from a curve shown in the matrix for the same specimen',
          'iR-corrected current density', 'ICP-MS ratios'],
    'A': ['slope fits (modulus from a stress-strain window)', 'integrals (toughness, fracture energy)', 'normalisations by another matrix quantity '
          '(specific load, specific MOR, specific K values)', 'Tafel slopes', 'overpotentials', 'mass activities', 'orientation factors', 'EXAFS coordination numbers'],
    'S': ['DFT results', 'simulations']}
REPRESENTATIVE_CURVE_RULE = 'definition 3: no recompute audit from a single representative curve for an A value that averages several specimens'
T4_BALANCE = (0.28, 0.38)      # definition 9
T2_MIN_CLASSES = 3             # definition 5
T7_MAX_PARAMS = 2; T7_EXTRA_CELLS = 3; T7_PER_HOLDOUT = 2   # definition 8
T3_RANKING_MARGIN = 3.0        # definition 6: combined tolerances
RANKING_SPREAD = 0.20

class ProvenanceError(Exception):
    pass

class Graph:
    def __init__(self, nodes):
        self.n = {}
        for nd in nodes:
            if nd['level'] not in LEVELS: raise ProvenanceError(f"node {nd['id']}: level {nd['level']!r} not in {LEVELS}")
            ev = nd.get('evidence') or {}
            if ev.get('kind') not in ('span', 'default'): raise ProvenanceError(f"node {nd['id']}: evidence must be a Methods span or a named default")
            if nd['level'] == 'A' and not nd.get('computed_from') and not nd.get('params'):
                raise ProvenanceError(f"node {nd['id']}: an A node needs computed_from or fitted params")
            self.n[nd['id']] = dict(nd, computed_from=list(nd.get('computed_from') or []), params=list(nd.get('params') or []))
        for nd in self.n.values():
            for c in nd['computed_from']:
                if c not in self.n: raise ProvenanceError(f"node {nd['id']}: computed_from {c!r} unknown")

    def ancestors(self, nid, _seen=None):
        """all nodes nid is computed from, recursively (excluding nid)."""
        seen = set() if _seen is None else _seen
        for c in self.n[nid]['computed_from']:
            if c not in seen: seen.add(c); self.ancestors(c, seen)
        return seen

    def m_roots(self, nid):
        """M (and D) nodes nid rests on: itself if M, plus every M ancestor."""
        s = {a for a in self.ancestors(nid) if self.n[a]['level'] in ('M', 'D')}
        if self.n[nid]['level'] in ('M', 'D'): s.add(nid)
        return s

    def level(self, nid): return self.n[nid]['level']

def default_node(nid, quantity, panel, instrument=None, methods_span=None, computed_from=None, formula=None, separate_hall_rho=False):
    """node from a Methods span when given, else from DEFAULT_LEVEL (evidence 'default'). A quantity without a default and without a
    span is M only if an instrument is named."""
    if methods_span:
        raise ProvenanceError('default_node is for quantities Methods says nothing about; build span nodes explicitly')
    if quantity == 'mu_H' and separate_hall_rho:
        return {'id': nid, 'quantity': quantity, 'panel': panel, 'level': 'M', 'computed_from': computed_from or [], 'formula': formula,
                'instrument': instrument, 'evidence': {'kind': 'default', 'text': 'default: mu_H from R_H and a separate Hall resistivity'}}
    if quantity in DEFAULT_LEVEL:
        lv, txt = DEFAULT_LEVEL[quantity]
    elif instrument:
        lv, txt = 'M', f'default: instrument output ({instrument})'
    else:
        raise ProvenanceError(f'{nid}: no Methods span, no default and no instrument')
    return {'id': nid, 'quantity': quantity, 'panel': panel, 'level': lv, 'computed_from': computed_from or [], 'formula': formula,
            'instrument': instrument, 'evidence': {'kind': 'default', 'text': txt}}

def classify_law(law, g):
    """law: {id, inputs [node ids], target node id, params [{name, kind: 'external'|'fit', source, fit_on [node ids], by, spread}],
    agreement: bool (two instruments, same physical quantity)}. Returns (class, mode, reason); mode 'value' or 'ranking'."""
    t, ins = law['target'], list(law['inputs'])
    for x in [t] + ins:
        if x not in g.n: raise ProvenanceError(f"law {law['id']}: node {x!r} unknown")
    anc_in = set(ins)
    for i in ins: anc_in |= g.ancestors(i)
    tn = g.n[t]
    # definition
    if tn['level'] == 'A' and tn['computed_from'] and set(tn['computed_from']) <= anc_in:
        return 'definition', 'value', f"target {t} is A, computed_from {tn['computed_from']} lies within the inputs and their ancestors"
    if any(t in g.ancestors(i) for i in ins):
        return 'definition', 'value', f'target {t} is an ancestor of an input'
    # fit
    t_roots = g.m_roots(t) | {t} | g.ancestors(t)
    for p in law.get('params', []):
        if p.get('kind') == 'fit':
            fo = set(p.get('fit_on') or [])
            if fo & t_roots:
                return 'fit', 'value', f"parameter {p['name']} fitted ({p.get('by', '?')}) on {sorted(fo)}, which include the target or its ancestors"
    for x in [t] + ins:   # an A node with a fitted parameter makes any law on it a fit
        for p in g.n[x]['params']:
            if p.get('kind') == 'fit' and (set(p.get('fit_on') or []) & t_roots):
                return 'fit', 'value', f"node {x} carries parameter {p['name']} fitted on cells of the target"
    # independent / agreement: disjoint M roots
    r_in = set()
    for i in ins: r_in |= g.m_roots(i)
    if g.m_roots(t) & r_in:
        return 'dependent', None, f'target and inputs share M ancestors {sorted(g.m_roots(t) & r_in)}'
    for p in law.get('params', []):
        if p.get('kind') == 'external' and not p.get('source'):
            return 'dependent', None, f"external parameter {p['name']} has no source"
        if p.get('kind') == 'fit' and (set(p.get('fit_on') or []) & (t_roots | r_in)):
            return 'fit', 'value', f"parameter {p['name']} fitted on cells shared with the law"
    spread = max([p.get('spread') or 0 for p in law.get('params', [])] + [law.get('spread') or 0])
    mode = 'ranking' if spread > RANKING_SPREAD else 'value'
    if law.get('agreement'):
        return 'agreement', mode, 'two instruments measure the same physical quantity on disjoint M ancestors'
    return 'independent', mode, f'disjoint M ancestors; parameters external with sources (max spread {spread:.0%})'

def check_key_sources(family, sources, g=None):
    """hard rules 1-2: raise ProvenanceError unless every key source is allowed. sources: list of dicts with kind in
    'cell' (node or level), 'verbatim', 'law' (class), 'image_ordering', 'signature'. A cells and I/S never enter a key, except the A
    cell that is the *object* of a T4 recompute audit (kind 'audited_cell')."""
    for s in sources:
        k = s['kind']
        if k == 'cell':
            lv = s.get('level') or (g.level(s['node']) if g is not None else None)
            if lv not in ('D', 'M'): raise ProvenanceError(f'{family}: key uses a {lv} cell ({s})')
        elif k == 'audited_cell':
            if family not in ('t4',): raise ProvenanceError(f'{family}: an audited A cell may appear only in a T4 audit')
        elif k == 'law':
            allowed = FAMILY_LAW_CLASSES.get({'t4': 't4_recompute'}.get(family, family))
            if allowed is not None and s['class'] not in allowed:
                raise ProvenanceError(f"{family}: law class {s['class']} not allowed (allowed {sorted(allowed)})")
            if s['class'] == 'dependent': raise ProvenanceError(f'{family}: dependent law')
        elif k in ('verbatim', 'image_ordering', 'signature', 'design'):
            pass
        elif k == 'derived':   # v3.3 definition 7: an observable our code computes from an M curve with a library procedure
            import laws as _L
            if s.get('procedure') not in _L.DERIVED: raise ProvenanceError(f"{family}: derived observable without a library procedure ({s})")
            if s.get('from_level') not in ('D', 'M'): raise ProvenanceError(f"{family}: derived observable from a {s.get('from_level')} curve")
        else:
            raise ProvenanceError(f'{family}: unknown key source kind {k!r}')
    return True
