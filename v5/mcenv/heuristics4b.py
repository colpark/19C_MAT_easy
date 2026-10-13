"""Stage 4b chemistry helpers and the heuristic panel (V5_SPEC J.5, J.6). Code only: DFT data files and pymatgen rules, no learned model.
  proto_key(st)                    anonymous formula, space group (symprec 0.1), sorted Wyckoff letters of symmetry-distinct sites
  oxi_assignment(formula)          most probable charge-balanced assignment (common oxidation states; one element may split between two)
  charge_ok(formula), magnetic_3d(formula), mixed_valence(formula), intermetallic(formula)
  Panel(data).verdicts(claim_type, library, sample)  -> {rule: True/False/None}, panel verdict (J.6)"""
import functools, gzip, itertools, json, os, zipfile
from collections import Counter, defaultdict
import numpy as np
from pymatgen.core import Composition, Element, Species, Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA4 = os.path.join(ROOT, 'data', 'stage4')
ANIONS = {'O', 'S', 'Se', 'Te', 'N', 'F', 'Cl', 'Br', 'I', 'P', 'As', 'Sb'}
STRICT_ANIONS = {'O', 'S', 'Se', 'Te', 'N', 'F', 'Cl', 'Br', 'I'}          # rule v2's anion set (charge balance applies)
MAG3D = ('V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni')
EXCL = {'H', 'He', 'Ne', 'Ar', 'Kr', 'Xe', 'Rn'} | {e.symbol for e in Element if e.is_actinoid or (e.is_lanthanoid and e.symbol != 'La')}


def proto_key(st):
    try:
        ds = SpacegroupAnalyzer(st, symprec=0.1).get_symmetry_dataset()
        wy = sorted({(int(e), w) for e, w in zip(ds.equivalent_atoms, ds.wyckoffs)})
        return f'{st.composition.anonymized_formula}|{int(ds.number)}|' + ''.join(sorted(w for _, w in wy))
    except Exception:
        return None


# ---------------------------------------------------------------- oxidation states
def _common(el):
    e = Element(el); return sorted(set(e.common_oxidation_states) | ({0} if e.is_metal or e.is_metalloid else set()))


@functools.lru_cache(None)
def oxi_assignment(formula):
    """the most probable charge-balanced assignment with common oxidation states for compounds with an anion of rule v2: pymatgen's
    oxi_state_guesses first; if none, one element may split between two of its common states (amounts integral in the reduced formula
    times up to 4). Returns {element: [(state, amount), ...]} or None. Intermetallics (no rule v2 anion): every element at 0."""
    c = Composition(formula).reduced_composition
    els = [e.symbol for e in c.elements]
    if not set(els) & STRICT_ANIONS:
        return {e: [(0, c[e])] for e in els}
    try:
        g = c.oxi_state_guesses(all_oxi_states=False)
    except Exception:
        g = []
    if g:
        best = g[0]
        if all(abs(v - round(v)) < 1e-6 for v in best.values()):
            return {e: [(int(round(best[e])), c[e])] for e in els}
    # fallback (mixed valence, V5-E27): the most electronegative element takes its negative common states, every other element its
    # positive ones; one element may split between two common states of the same sign
    anion = max(els, key=lambda e: Element(e).X)
    opts = {e: [s for s in Element(e).common_oxidation_states if (s < 0 if e == anion else s > 0)] for e in els}
    if any(not v for v in opts.values()): return None
    for mult in (1, 2, 3, 4):
        amt = {e: c[e] * mult for e in els}
        if any(abs(a - round(a)) > 1e-6 for a in amt.values()): continue
        amt = {e: int(round(amt[e])) for e in els}
        for split in els:
            others = [e for e in els if e != split]
            for combo in itertools.product(*[opts[e] for e in others]):
                rest = sum(s * amt[e] for s, e in zip(combo, others))
                for s1, s2 in itertools.combinations(sorted(opts[split]), 2):
                    for n1 in range(1, amt[split]):
                        if s1 * n1 + s2 * (amt[split] - n1) + rest == 0:
                            out = {e: [(s, amt[e] / mult)] for s, e in zip(combo, others)}
                            out[split] = [(s1, n1 / mult), (s2, (amt[split] - n1) / mult)]
                            return out
    return None


def intermetallic(formula): return not {e.symbol for e in Composition(formula).elements} & STRICT_ANIONS


def charge_ok(formula):
    """rule v2 extended (J.5 pool): compounds with a rule v2 anion need a charge-balanced assignment (mixed valence allowed)."""
    return oxi_assignment(formula) is not None


def mixed_valence(formula):
    a = oxi_assignment(formula)
    return bool(a) and any(len(v) > 1 for v in a.values())


def _d_count(el, state):
    e = Element(el); return e.group - state if e.block == 'd' else None


def magnetic_3d(formula):
    """a 3d metal of MAG3D with 1 to 9 d electrons under the most probable assignment (0 for intermetallics), high spin."""
    a = oxi_assignment(formula)
    if not a: return False
    for el in MAG3D:
        for s, _ in a.get(el, []):
            d = _d_count(el, s)
            if d is not None and 1 <= d <= 9: return True
    return False


def closed_shell(formula):
    """G rule 4: every cation d0 or d10 (s/p cations closed by their common states) under the most probable assignment; None for
    intermetallics or without an assignment."""
    if intermetallic(formula): return None
    a = oxi_assignment(formula)
    if not a: return None
    for el, lst in a.items():
        for s, _ in lst:
            if s <= 0: continue
            d = _d_count(el, s)
            if d is not None and d not in (0, 10): return False
    return True


def chem_classes(formula, pbe_u):
    n = len(Composition(formula).elements); out = []
    if n <= 3: out.append('ternary_or_less')
    if n >= 4: out.append('quaternary')
    if pbe_u: out.append('pbe_u')
    if magnetic_3d(formula) or mixed_valence(formula): out.append('magnetic_or_mixed_valence')
    return out


def pool_ok(formula):
    els = [e.symbol for e in Composition(formula).elements]
    return 3 <= len(els) <= 4 and not set(els) & EXCL and charge_ok(formula)


# ---------------------------------------------------------------- substitution (element level)
@functools.lru_cache(None)
def substitutes():
    """element -> list of (other element, probability), the maximum species-pair probability of pymatgen's substitution table."""
    from pymatgen.analysis.structure_prediction.substitution_probability import SubstitutionProbability
    sp = SubstitutionProbability(); best = defaultdict(dict)
    for s1 in sp.species:
        for s2 in sp.species:
            e1, e2 = s1.element.symbol, s2.element.symbol
            if e1 == e2: continue
            p = sp.prob(s1, s2)
            if p > best[e1].get(e2, 0.0): best[e1][e2] = p
    return {e: sorted(d.items(), key=lambda kv: -kv[1]) for e, d in best.items()}


def analog_formulas(formula):
    """J.6 rule 3: replace one element at a time by its most probable substitute not in the formula; ordered by probability."""
    c = Composition(formula).reduced_composition; els = {e.symbol for e in c.elements}; out = []
    for el in els:
        for sub, p in substitutes().get(el, []):
            if sub in els: continue
            d = {(sub if e.symbol == el else e.symbol): v for e, v in c.items()}
            out.append((p, Composition(d).reduced_formula)); break
    return [f for p, f in sorted(out, key=lambda t: -t[0])]


# ---------------------------------------------------------------- data for the panel
class Data:
    """MP and WBM lookups for the panel (DFT data only). Loads lazily; holds the candidate formula's own entries out of analog lookups."""

    def __init__(self):
        import pandas as pd
        self.W = pd.read_csv(os.path.join(DATA4, '2023-12-13-wbm-summary.csv.gz'))
        self.W['rf'] = [Composition(f).reduced_formula for f in self.W.formula]
        self.Wby = {rf: g for rf, g in self.W.groupby('rf')}
        d = json.load(gzip.open(os.path.join(DATA4, '2023-02-07-mp-computed-structure-entries.json.gz'), 'rt'))
        self.mp = {mid: d['entry'][k] for k, mid in d['material_id'].items()}
        self.MPby = defaultdict(list); self.MPanon = defaultdict(list)
        for mid, e in self.mp.items():
            c = Composition(e['composition']); self.MPby[c.reduced_formula].append(mid); self.MPanon[c.anonymized_formula].append(mid)
        self._zip = zipfile.ZipFile(os.path.join(ROOT, 'data', 'stage2', '2024-08-04-wbm-relaxed-atoms.extxyz.zip'))
        self._mpkeys = {}; self._wbmkey = {}
        kp = os.path.join(ROOT, 'data', 'stage4b', 'wbm_keys.json')          # precomputed J.6 keys of every WBM entry (V5-E29)
        if os.path.exists(kp): self._wbmkey = json.load(open(kp))
        self.W['anon'] = [Composition(f).anonymized_formula for f in self.W.formula]

    def wbm_structure(self, mid):
        from mcenv import stage2 as S2
        return S2.wbm(mid)

    def wbm_key(self, mid):
        if mid not in self._wbmkey: self._wbmkey[mid] = proto_key(self.wbm_structure(mid))
        return self._wbmkey[mid]

    def mp_key_counts(self, anon):
        if anon not in self._mpkeys:
            self._mpkeys[anon] = Counter(proto_key(Structure.from_dict(self.mp[m]['structure'])) for m in self.MPanon.get(anon, []))
        return self._mpkeys[anon]

    @functools.lru_cache(None)
    def ppd(self):
        import pickle
        return pickle.load(gzip.open(os.path.join(DATA4, '2023-02-07-ppd-mp.pkl.gz'), 'rb'))

    def analog_data(self, f, need):
        """for an analog formula: R -> ground-state prototype key; H -> lowest hull distance; G -> gap of the lowest-energy WBM entry."""
        from pymatgen.entries.computed_entries import ComputedStructureEntry
        w = self.Wby.get(f); m = self.MPby.get(f, [])
        if need == 'G':
            if w is None: return None
            r = w.sort_values('e_form_per_atom_mp2020_corrected').iloc[0]; return float(r.bandgap_pbe) > 0.5
        cands = []
        if w is not None:
            for r in w.itertuples(index=False): cands.append((float(r.e_form_per_atom_mp2020_corrected), float(r.e_above_hull_mp2020_corrected_ppd_mp), 'wbm', r.material_id))
        P = self.ppd() if m else None
        for mid in m:
            e = ComputedStructureEntry.from_dict(self.mp[mid])
            cands.append((float(P.get_form_energy_per_atom(e)), float(P.get_e_above_hull(e, allow_negative=True)), 'mp', mid))
        if not cands: return None
        gs = min(cands)
        if need == 'H': return min(c[1] for c in cands) <= 0.050
        if gs[2] == 'wbm': return self.wbm_key(gs[3])
        return proto_key(Structure.from_dict(self.mp[gs[3]]['structure']))

    def wbm_proto_gap_majority(self, key, exclude_formula):
        """G rule 2: share of WBM entries with this prototype key (other formulas) whose PBE gap exceeds 0.5 eV; scans by anonymous
        formula through the WBM wyckoff labels' anonymous part first, then keys the structures (cached)."""
        anon = key.split('|')[0]
        rows = self.W[(self.W.anon == anon) & (self.W.rf != exclude_formula)]
        hits = [float(g) > 0.5 for mid, g in zip(rows.material_id, rows.bandgap_pbe) if self._wbmkey.get(mid) == key]
        return None if not hits else (sum(hits) / len(hits) > 0.5)


# ---------------------------------------------------------------- the panel
def _vpa(st): return st.volume / len(st)


def panel(D, claim, formula, library, sample):
    """library: {name: Structure} of the formula's polymorphs; sample: name. Returns dict(rules, verdict) with True = claim holds."""
    st = library[sample]; vpa = {n: _vpa(s) for n, s in library.items()}
    keys = {n: proto_key(s) for n, s in library.items()}
    anon = st.composition.anonymized_formula
    rules = {}
    # 1 density
    if claim in ('R', 'H'): rules['density'] = vpa[sample] == min(vpa.values())
    else: rules['density'] = vpa[sample] >= float(np.median(list(vpa.values())))
    # 2 prototype frequency
    if claim in ('R', 'H'):
        cnt = D.mp_key_counts(anon); c = {n: cnt.get(k, 0) for n, k in keys.items()}
        rules['prototype'] = c[sample] == max(c.values())
    else:
        rules['prototype'] = D.wbm_proto_gap_majority(keys[sample], formula)
    # 3 nearest analog
    rules['analog'] = None
    for af in analog_formulas(formula):
        if af == formula: continue
        v = D.analog_data(af, claim)
        if v is None: continue
        rules['analog'] = (v == keys[sample]) if claim == 'R' else bool(v); rules['analog_formula'] = af
        break
    # 4 oxidation state / electron counting
    from pymatgen.analysis.bond_valence import BVAnalyzer
    def bv(s):
        try: BVAnalyzer().get_valences(s); return True
        except Exception: return False
    if claim == 'R':
        ok = {n: bv(s) for n, s in library.items()}
        if all(ok.values()) or not any(ok.values()): rules['oxidation'] = None
        else: rules['oxidation'] = ok[sample] and not any(ok[n] for n in library if n != sample and vpa[n] < vpa[sample])
    elif claim == 'H': rules['oxidation'] = bv(st)
    else: rules['oxidation'] = closed_shell(formula)
    votes = [rules[r] for r in ('density', 'prototype', 'analog', 'oxidation') if rules[r] is not None]
    yes, no = sum(votes), len(votes) - sum(votes)
    if yes != no: verdict = yes > no
    elif rules['analog'] is not None: verdict = rules['analog']
    else: verdict = False
    return dict(rules={k: v for k, v in rules.items()}, verdict=bool(verdict), keys=keys)
