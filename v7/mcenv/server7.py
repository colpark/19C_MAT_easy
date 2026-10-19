"""v7 environment server (V7-1): server6 (B1 instrument, nuisances, count scale, simulator, FM tools, structured answers, call log) plus the
v7 families T and H (mcenv/family7.py). No DFT tool in any v7 arm. Runs on its own port and state; server6.py is imported, not changed:
its arm table, ceiling set and tool tables are extended at import.
  T worlds: two samples, pre and post (TEpisode). Each sample has its own free survey scan (ids pre_m0, post_m0; the episode's
     measurement ids carry the sample: pre_m1, post_m2, ...), its own hidden nuisances, the scenario's count scale and its own noise key
     f'{seed_scen}|{sample}'. measure and fit name the sample; fit refuses ids of another sample. The budget is the scenario's (the T budget
     rule, V7-2), shared by the two samples; the Si standard's preparation is charged once per sample.
  H worlds: one sample, as B1, budget 180.
Arms: v7t-noprior, v7t-fm (T agents), v7h-noprior, v7h-fm (H agents), v7-gold (FM path for the executor), v7-ceiling (energy and hull
serve DFT values, free; selection rows only).
  MCENV_STATE=... MCENV_PORT=... python -m mcenv.server7"""
import json, os, sys, threading
import numpy as np
from . import server as S
from . import scenarios as SC
from . import tools_common as TC
from . import separation as SP
from . import server6 as S6
from . import server4 as S4
from . import family7 as F7

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F7.install()
LAB = {'status', 'measure', 'simulate', 'peaks', 'fit', 'run_python', 'answer'}
FMT = {'energy', 'hull'}
ARMS7 = {'v7t-noprior': LAB, 'v7t-fm': LAB | FMT, 'v7h-noprior': LAB, 'v7h-fm': LAB | FMT, 'v7-gold': LAB | FMT, 'v7-ceiling': LAB | FMT,
         'v7t-fm-planner': LAB | FMT | {'predict_separation'}, 'v7h-fm-planner': LAB | FMT | {'predict_separation'}}      # V7-X8
BUDGET_ARMS = {f'v7-{kind}-b{b}': b for kind in ('ceiling', 'gold') for b in (180, 240, 300)}     # V7-2 budget rule: the budget in the arm name
ARMS7.update({a: LAB | FMT for a in BUDGET_ARMS})
S.ARM_TOOLS.update({a: set(t) for a, t in ARMS7.items()})
S6.ARMS6.update(ARMS7)                                  # call log with call ids; v6 energy and hull handlers
S6.CEILING.update({'v7-ceiling'} | {a for a in BUDGET_ARMS if 'ceiling' in a})
S4.MODEL_OF.update({'v7t-fm': 'fm', 'v7h-fm': 'fm', 'v7-gold': 'fm', 'v7-ceiling': 'dft', 'v7t-fm-planner': 'fm', 'v7h-fm-planner': 'fm'})
S4.MODEL_OF.update({a: 'dft' if 'ceiling' in a else 'fm' for a in BUDGET_ARMS})
ANSWER_T = json.load(open(os.path.join(ROOT, 'spec', 'answer_schema_T.json')))
STATED = json.load(open(os.path.join(ROOT, 'STATED7.json'))) if os.path.exists(os.path.join(ROOT, 'STATED7.json')) else {}


def _merge_tables():
    for fam in ('T', 'H'):
        p = os.path.join(ROOT, fam, f'TOOL_TABLES_{fam}.json')
        if not os.path.exists(p): continue
        t = json.load(open(p))
        S6._tb.setdefault('scenarios', []); S6._tb['scenarios'] += [x for x in t['scenarios'] if x not in S6._tb['scenarios']]
        for model in ('dft', 'fm'):
            S6._tb.setdefault(model, {}).update(t.get(model, {}))


_merge_tables()


def is_T(scen): return SC.SCEN.get(scen, {}).get('kind') == 'T'


def budget_of(ep):
    if ep.rec['arm'] in BUDGET_ARMS: return float(BUDGET_ARMS[ep.rec['arm']])
    return SC.SCEN[ep.tr['scen']].get('budget', S.BUDGET)


_Orig = S.Episode


class TEpisode(_Orig):
    def __init__(self, token, rec):
        self.token, self.rec = token, rec
        self.dir = os.path.join(S.EPIS, token); os.makedirs(self.dir, exist_ok=True); os.chmod(self.dir, 0o700)
        self.sbx = os.path.join(self.dir, 'data'); os.makedirs(self.sbx, exist_ok=True)
        sp = os.path.join(self.dir, 'state.json')
        self.state = json.load(open(sp)) if os.path.exists(sp) else dict(spent=0.0, measurements=[], std_prepared={'pre': False, 'post': False}, answer=None)
        self.tw = F7.T_SCEN[rec['world']]
        self.trs = {sm: SP.world_truth(self.tw[sm]) for sm in ('pre', 'post')}
        self.tr = self.trs['pre']                       # scenario and count scale (shared by the samples); simulate uses it
        if not self.state['measurements']:
            for sm in ('pre', 'post'): self._acquire(SP.DEFAULT, sm, charge=False, default=True)

    def _acquire(self, m, sample='pre', charge=True, default=False):
        idx = sum(1 for r in self.state['measurements'] if r['sample'] == sample)
        mu = SP.mu_truth(self.trs[sample], m)
        counts = S.noise_rng(f"{SC.SCEN[self.tr['scen']].get('seed_scen', self.tr['scen'])}|{sample}", self.rec['k'], idx).poisson(mu).astype(int)
        mid = f'{sample}_m{idx}'
        prep = m.si_standard and not self.state['std_prepared'][sample]
        cost = 0.0 if not charge else m.cost + (S.STD_PREP if prep else 0.0)
        if m.si_standard: self.state['std_prepared'][sample] = True
        self.state['spent'] += cost
        rec = dict(id=mid, sample=sample, spec=m.key(), cost=round(cost, 3), default=default)
        self.state['measurements'].append(rec)
        np.save(os.path.join(self.dir, mid + '.npy'), counts)
        TC.write_sandbox_measurement(self.sbx, mid, m, counts)
        self.save()
        return rec, counts

    def sample_of(self, mid):
        for r in self.state['measurements']:
            if r['id'] == mid: return r['sample']
        raise TC.ToolError(f'unknown measurement id {mid!r}; known: ' + ', '.join(r['id'] for r in self.state['measurements']))


def Episode(token, rec):
    return TEpisode(token, rec) if rec['world'] in F7.T_SCEN else _Orig(token, rec)


S.Episode = Episode


def _sample(a):
    s = str(a.get('sample', '')).strip().lower()
    if s not in ('pre', 'post'): raise TC.ToolError("sample must be 'pre' or 'post'")
    return s


# ---------------------------------------------------------------- manual
def energy_text(arm, kind='T'):
    if arm in ('v7t-noprior', 'v7h-noprior'): return '- No energy tools are available in this session.'
    if arm == 'v7-ceiling' or (arm in BUDGET_ARMS and 'ceiling' in arm):
        return ('- **energy(structure_name):** DFT formation energy per atom (eV/atom) of a library structure, on the scale above. Free. Exact.\n'
                '- **hull(structure_name):** DFT energy above the convex hull (eV/atom) and the decomposition products. Free. Exact.')
    st = STATED
    return '\n'.join([
        f"- **energy(structure_name):** formation energy per atom (eV/atom) of a library structure from the lab's energy model, on the scale above. Free. Stated error: mean absolute error {st.get('fm_mae', 0):.3f} eV/atom; polymorph energy differences {st.get('polymorph_gap_mae', 0):.3f} eV/atom.",
        f"- **hull(structure_name):** energy above the convex hull (eV/atom) and the decomposition products, from the energy model's formation energy of that structure against the fixed reference hull (DFT, the same in every session). Free. Stated error: mean absolute error {st.get('hull_mae', 0):.3f} eV/atom.",
        "- Each call returns the value and the stated error. Reliability of the model on held-out structures (sign error rate against the absolute predicted margin to the claim's threshold):",
        st.get('reliability_text_' + kind, '')] + ([
        "- **predict_separation(plan" + (", sample" if kind == 'T' else "") + "):** for a proposed plan (a list of measure arguments" + (" for one sample" if kind == 'T' else "") + "), the expected Δχ² between each library polymorph taken as the truth and the best other polymorph, for your measurements so far" + (" of that sample" if kind == 'T' else "") + " plus the plan, at the least favourable crystallite size, displacement and zero offset, with the count scale from simulate and the background from your own data, and the plan's cost. Free. It uses only the library and your measurements."] if arm.endswith('-planner') else []))


def manual_text7(scen, arm):
    t = TC.manual_text(scen, arm)
    rep = {'{ENERGY_TOOLS}': energy_text(arm, SC.SCEN[scen]['kind']), '{BAND}': STATED.get('band_text_' + SC.SCEN[scen]['kind'], ''), '{COUNTS}': F7.COUNT_TEXT,
           '{BUDGET}': f"{SC.SCEN[scen].get('budget', S.BUDGET):.0f}"}
    for k, v in rep.items(): t = t.replace(k, v)
    return t


# ---------------------------------------------------------------- tools
def t_status(ep, a):
    scen = ep.tr['scen']; s = SC.SCEN[scen]
    if s.get('stage') not in ('7T', '7H'): return S6.t_status(ep, a)
    B = budget_of(ep)
    base = dict(claim=s['claim'], description=s['description'], manual=manual_text7(scen, ep.rec['arm']), library=S4.library4(scen),
                budget_minutes=B, budget_left_minutes=round(B - ep.state['spent'], 3), answered=ep.state['answer'] is not None)
    if is_T(scen):
        base['samples'] = {sm: dict(si_standard_prepared=ep.state['std_prepared'][sm],
                                    measurements=[dict(id=r['id'], spec=TC.public_spec(r['spec']), cost_minutes=r['cost']) for r in ep.state['measurements'] if r['sample'] == sm])
                           for sm in ('pre', 'post')}
    else:
        base.update(si_standard_prepared=ep.state['std_prepared'],
                    measurements=[dict(id=r['id'], spec=TC.public_spec(r['spec']), cost_minutes=r['cost']) for r in ep.state['measurements']])
    return base


def t_measure(ep, a):
    if not isinstance(ep, TEpisode): return S.TOOLS_BASE['measure'](ep, a)
    sm = _sample(a); m = TC.parse_measure(a); B = budget_of(ep)
    cost = m.cost + (S.STD_PREP if m.si_standard and not ep.state['std_prepared'][sm] else 0.0)
    left = B - ep.state['spent']
    if cost > left + 1e-9:
        raise TC.ToolError(f'over budget: this measurement costs {cost:.2f} min, {left:.2f} min left. Nothing was charged.')
    rec, counts = ep._acquire(m, sm)
    return dict(id=rec['id'], sample=sm, start=m.start, step=m.step, n=m.n, radiation=m.radiation, cost_minutes=rec['cost'],
                budget_left_minutes=round(B - ep.state['spent'], 3), counts=counts.tolist())


def t_fit(ep, a):
    if not isinstance(ep, TEpisode): return S.TOOLS_BASE['fit'](ep, a)
    sm = _sample(a)
    ids = a.get('measurement_ids') or a.get('measurement_id')
    ids = [ids] if isinstance(ids, str) else list(ids or [])
    if not ids: raise TC.ToolError('give measurement_ids')
    bad = [i for i in ids if ep.sample_of(i) != sm]
    if bad: raise TC.ToolError(f'measurement ids {bad} belong to the other sample; fit one sample at a time')
    return TC.fit(ep.tr['scen'], [ep.meas(i) for i in ids], [ep.counts(i) for i in ids], a.get('spec') or {})


def t_answer(ep, a):
    if not isinstance(ep, TEpisode): return S6.t_answer(ep, a)
    import jsonschema
    try: jsonschema.validate(a, ANSWER_T)
    except jsonschema.ValidationError as e:
        raise TC.ToolError(f'the answer does not follow the v7 T answer format: {e.message[:300]}. Nothing was recorded; call answer again.')
    a2 = dict(a, region=f"pre {a.get('region_pre', '')}; post {a.get('region_post', '')}")
    out = S.t_answer(ep, a2)
    ep.state['answer']['structured'] = {k: v for k, v in a.items() if k not in ('verdict', 'rationale')}; ep.save()
    return out


def t_predict_separation(ep, a):
    """V7-X8: the B1 planner tool (planner v3, V6-X18); for T it names the sample and uses only that sample's measurements."""
    if not isinstance(ep, TEpisode): return S6.t_predict_separation(ep, a)
    sm = _sample(a)
    class _View:                      # a one-sample view of the T episode for the B1 computation
        pass
    v = _View(); v.tr = ep.tr; v.rec = ep.rec
    ids = [r['id'] for r in ep.state['measurements'] if r['sample'] == sm]
    v.state = dict(measurements=[r for r in ep.state['measurements'] if r['sample'] == sm])
    v.meas, v.counts = ep.meas, ep.counts
    out = S6.t_predict_separation(v, {k: x for k, x in a.items() if k != 'sample'})
    return dict(out, sample=sm)


S.TOOLS_BASE = dict(S6._base)
S.TOOLS.update(status=t_status, measure=t_measure, fit=t_fit, answer=t_answer, predict_separation=t_predict_separation)

if __name__ == '__main__':
    S.main()
