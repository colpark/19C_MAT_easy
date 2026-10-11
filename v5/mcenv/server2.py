"""Stage 2 environment server (V5_SPEC Appendix B). Extends the stage 1 server without changing it: adds build and relax, per-episode
structure registries, and the arms placebo, fm, ceiling, blindfm. The relax interface and description are the same in every arm;
only the method behind it differs (placebo volume table, MACE-MP-0, true DFT structure).
  MCENV_STATE=... MCENV_PORT=8767 V5_FM_URL=http://192.168.100.11:8770/relax python -m mcenv.server2"""
import json, os, urllib.request
import numpy as np
from pymatgen.core import Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from . import server as S
from . import scenarios as SC
from . import stage2 as S2
from . import tools_common as TC
from . import physics as P

S2.install()
FM_URL = os.environ.get('V5_FM_URL', 'http://192.168.100.11:8770/relax')
FULL = {'status', 'measure', 'simulate', 'peaks', 'fit', 'run_python', 'build', 'relax', 'answer'}
S.ARM_TOOLS.update({'placebo': FULL, 'fm': FULL, 'ceiling': FULL, 'blindfm': {'build', 'relax', 'answer'}, 'planner': FULL})
RELAX_OF_ARM = {'placebo': 'placebo', 'fm': 'fm', 'ceiling': 'ceiling', 'blindfm': 'fm'}


def _structs(ep):
    st = ep.state.setdefault('structures', {})
    for sid, rec in st.items():                                 # re-register after a restart
        if rec['phase'] not in P.PHASES: S2.register_structure(rec['phase'], Structure.from_dict(rec['structure']))
    return st


def _add(ep, st, origin, extra=None):
    reg = _structs(ep); sid = f's{len(reg) + 1}'
    name = f'ep:{ep.token[:10]}:{sid}'
    S2.register_structure(name, st)
    reg[sid] = dict(phase=name, structure=st.as_dict(), origin=origin, **(extra or {}))
    ep.save()
    return sid


def _summary(sid, st, extra=None):
    try: sg = SpacegroupAnalyzer(st, symprec=1e-3).get_space_group_symbol()
    except Exception: sg = None
    out = dict(structure_id=sid, formula=st.composition.reduced_formula, space_group=sg, lattice=dict(zip('abc', np.round(st.lattice.abc, 5).tolist())),
               angles=np.round(st.lattice.angles, 3).tolist(), volume=round(st.volume, 4), n_sites=len(st),
               sites=[dict(species={e.symbol: round(f, 4) for e, f in s.species.items()}, frac=np.round(s.frac_coords, 5).tolist()) for s in st][:40])
    out.update(extra or {})
    return out


def resolver_for(ep):
    reg = _structs(ep)
    def r(sid):
        if sid not in reg: raise TC.ToolError(f'unknown structure_id {sid!r}; known: {sorted(reg)}')
        return reg[sid]['phase']
    return r


def t_status(ep, a):
    out = S.t_status(ep, a)
    d = SC.SCEN[ep.tr['scen']]
    out['library'] = dict(prototypes={k: dict(roles=v['roles'], params=v['params']) for k, v in S2.PROTOTYPES.items()},
                          note='build a hypothesis with build(prototype, sites, params); relax it with relax(structure_id); use structure ids in simulate and fit')
    els = sorted({e.symbol for e in __import__('pymatgen.core', fromlist=['Composition']).Composition(d['composition']).elements})
    out['volume_table'] = {e: round(S2.vol_atom(e), 3) for e in els}
    out['volume_table_note'] = 'elemental-solid volume per atom (A^3); build uses it when no lattice parameter is given'
    out['structures'] = [dict(structure_id=k, origin=v['origin']) for k, v in _structs(ep).items()]
    return out


def t_build(ep, a):
    try:
        st = S2.build(str(a.get('prototype', '')), a.get('sites') or {}, a.get('params') or {})
    except (ValueError, KeyError, TypeError) as e:
        raise TC.ToolError(str(e))
    sid = _add(ep, st, f"build {a.get('prototype')}")
    return _summary(sid, st)


def _match_truth(ep, st):
    """ceiling: a scenario structure (claim or other side, at its reference parameters) with the same reduced formula, space group
    and number of sites."""
    d = SC.SCEN[ep.tr['scen']]
    try: sg = SpacegroupAnalyzer(st, symprec=1e-2).get_space_group_number()
    except Exception: return None
    for br in d['claim_side'] + d['other_side']:
        for u in (br.lo, br.hi) if br.dim else ([],):
            for g in br.groups(u):
                for name, p, w in g:
                    t = P.PHASES[name].structure(p)
                    try: tsg = SpacegroupAnalyzer(t, symprec=1e-2).get_space_group_number()
                    except Exception: continue
                    if t.composition.reduced_formula == st.composition.reduced_formula and tsg == sg and len(t) == len(st):
                        return t
    return None


def _fm(st):
    if not st.is_ordered: raise TC.ToolError('relax needs ordered sites (mixed sites cannot be relaxed); relax ordered end members instead')
    req = urllib.request.Request(FM_URL, data=json.dumps(dict(structure=st.as_dict())).encode(), headers={'Content-Type': 'application/json'})
    out = json.loads(urllib.request.urlopen(req, timeout=900).read())
    if not out.get('ok'): raise TC.ToolError('relaxation failed: ' + str(out.get('error'))[:300])
    r = out['result']
    return Structure.from_dict(r['structure']), r['energy_per_atom']


def t_relax(ep, a):
    reg = _structs(ep); sid = str(a.get('structure_id', ''))
    if sid not in reg: raise TC.ToolError(f'unknown structure_id {sid!r}; known: {sorted(reg)}')
    st = Structure.from_dict(reg[sid]['structure'])
    how = RELAX_OF_ARM.get(ep.rec['arm'], 'fm')
    if how == 'placebo':
        if not st.is_ordered: raise TC.ToolError('relax needs ordered sites (mixed sites cannot be relaxed); relax ordered end members instead')
        out, e = S2.placebo_relax(st)
    elif how == 'ceiling':
        if not st.is_ordered: raise TC.ToolError('relax needs ordered sites (mixed sites cannot be relaxed); relax ordered end members instead')
        t = _match_truth(ep, st)
        if t is not None: out, e = t, None
        else: out, e = _fm(st)
        if e is None: e = _fm(out)[1] if out.is_ordered else None
    else:
        out, e = _fm(st)
    nid = _add(ep, out, f'relax {sid}', dict(energy_per_atom=e))
    return _summary(nid, out, dict(energy_per_atom_eV=e, relaxed_from=sid))


def t_simulate(ep, a): return TC.simulate(ep.tr, a, resolver_for(ep))


def t_fit(ep, a):
    ids = a.get('measurement_ids') or a.get('measurement_id')
    ids = [ids] if isinstance(ids, str) else list(ids or [])
    if not ids: raise TC.ToolError('give measurement_id or measurement_ids')
    ms = [ep.meas(i) for i in ids]; ys = [ep.counts(i) for i in ids]
    return TC.fit(ep.tr['scen'], ms, ys, a.get('spec') or {}, resolver_for(ep))


S.TOOLS.update(status=t_status, simulate=t_simulate, fit=t_fit, build=t_build, relax=t_relax)

_orig_init = S.Episode.__init__


def _init(self, token, rec):
    """blind plus FM gets no free default scan (stage 1 skips m0 only for 'blind')."""
    if rec['arm'] == 'blindfm':
        _orig_init(self, token, dict(rec, arm='blind')); self.rec = rec
    else:
        _orig_init(self, token, rec)


S.Episode.__init__ = _init

if __name__ == '__main__':
    S.main()
