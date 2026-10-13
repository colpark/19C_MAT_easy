"""v6 adapters on the mcenv environment server (V6_SPEC 2). Each adapter returns dict(outputs, cost_min, calls) and reaches the
world only through the server's tools with an episode token; nothing here reads truth.

Tokens: every executor run opens a fresh episode (budget, measurements and noise are per episode). The first adapter call of a run
mints the token server-side (admin new over ssh; episodes are never created over HTTP) and keeps it on the run's Context.

  simulator (S1a)  agent-side model from what status and the free-scan fit show (library structures, the manual's count statement,
                   the fitted displacement, zero offset, size and background of the best-fitting polymorph) and the lab's forward
                   model (mcenv physics, the code behind `simulate`); the cheapest plan on the stage 1 plan grid (singles and pairs)
                   whose predicted D, free scan plus plan, reaches D_accept under every polymorph hypothesis against every other
                   polymorph, planned for PLAN_FACTOR x D_accept (V6-X3); the free scan alone if it already does; if no plan reaches
                   the target within the budget, the plan with the largest minimum predicted D that reaches D_accept
  instrument (S1b) measure
  fit (S1c)        fit of every library polymorph on all measurements (free scan included); phase = best fit; D = chi2 of the best
                   other polymorph minus chi2 of the best
  fm (S2)          energy of every library polymorph of the claim's formula (R) or hull of the identified phase (H)
  dft (S2x)        the priced DFT tool (energy_dft), every polymorph (R) or the identified phase (H), as far as the budget allows"""
import json, math, os, re, subprocess, sys, time, urllib.request, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import graphexec as G  # noqa: E402


class Env:
    """one environment server: HTTP for tools, ssh for minting tokens (admin new on the server host)."""

    def __init__(self, url, ssh_host, code_dir, state_dir, stage_env, py='~/v5env/bin/python', batch='v6-gold', model='gold'):
        self.url, self.ssh_host, self.code_dir, self.state_dir = url, ssh_host, code_dir, state_dir
        self.stage_env, self.py, self.batch, self.model = stage_env, py, batch, model
        self.tokens = []

    def new_token(self, world, arm, k):
        cmd = (f'cd {self.code_dir} && MCENV_STATE={self.state_dir} {self.stage_env} {self.py} -m mcenv.admin new --world {world} '
               f'--arm {arm} --k {k} --model {self.model} --batch {self.batch} 2>/dev/null')
        out = subprocess.run(['ssh', '-n', self.ssh_host, cmd], capture_output=True, text=True, timeout=120).stdout.strip().splitlines()
        tok = out[-1].strip()
        if not re.fullmatch(r'[0-9a-f]{32}', tok): raise RuntimeError(f'token minting failed: {out[-3:]}')
        self.tokens.append(dict(token=tok, world=world, arm=arm, k=k))
        return tok

    def call(self, token, tool, args):
        body = json.dumps(dict(token=token, tool=tool, args=args, rid=uuid.uuid4().hex)).encode()
        req = urllib.request.Request(self.url, data=body, headers={'Content-Type': 'application/json'})
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=300) as r: out = json.loads(r.read()); break
            except Exception:
                if attempt == 3: raise
                time.sleep(5 * (attempt + 1))
        if not out.get('ok'): raise RuntimeError(f'{tool}: {out.get("error")}')
        return out['result']


def _token(task, ctx):
    if getattr(ctx, 'token', None) is None:
        ctx.token = task['env'].new_token(task['world'], task['arm'], task['k'])
        ctx.call_n = 0; ctx.call_log = []
    return ctx.token


def _call(task, ctx, tool, args):
    tok = _token(task, ctx); res = task['env'].call(tok, tool, args)
    ctx.call_n += 1; cid = f'c{ctx.call_n}'
    rec = dict(call_id=cid, tool=tool, args=args); ctx.call_log.append(rec)
    return res, rec


def _digest(counts):
    import hashlib
    return hashlib.sha256(json.dumps([int(x) for x in counts]).encode()).hexdigest()[:16]


DIGEST_CODE = ("import hashlib, json\nprint(hashlib.sha256(json.dumps([int(x) for x in meas['m0']['counts']]).encode()).hexdigest()[:16])")


def m0_digest(task, ctx):
    """V6-X4: the sha256 of the free scan's counts, read through run_python (an agent's own channel), once per run."""
    if getattr(ctx, 'm0_digest', None) is None:
        r, rec = _call(task, ctx, 'run_python', dict(code=DIGEST_CODE))
        ctx.m0_digest = (r.get('stdout') or '').strip(); ctx.m0_rec = dict(rec, args=dict(code='sha256 of m0 counts'), result_digest=ctx.m0_digest)
    return ctx.m0_rec


def polymorphs(task):
    f = task['formula']
    return [x['name'] for x in task['library'] if x['formula'] == f]


# ---------------------------------------------------------------- S1a simulator: an agent-side model, no truth
def _structure(entry):
    from pymatgen.core import Lattice, Structure
    l = entry['lattice']
    lat = Lattice.from_parameters(l['a'], l['b'], l['c'], l['alpha'], l['beta'], l['gamma'])
    return Structure(lat, [s[0] for s in entry['sites']], [s[1:4] for s in entry['sites']])


def _counts_N(manual):
    m = re.search(r'free default scan gives about (\d+(?:\.\d+)?) counts', manual)
    return float(m.group(1)) if m else 1000.0


AGENT_SCEN = 990
PLAN_FACTOR = 3.0


def agent_model(task, nuis):
    """register the library polymorphs and a hypothetical scenario: world 9900 + i holds polymorph i; its other side is every other
    polymorph; nuisances are the agent's estimates (free-scan fit), not the truth."""
    from mcenv import scenarios as SC
    from mcenv import stage2 as S2
    names = polymorphs(task); entries = {x['name']: x for x in task['library']}
    reg = {n: S2.register_structure(f'v6agent {n}', _structure(entries[n])) for n in names}
    br = {n: SC.fixed([(reg[n], {}, 1.0)], label=n) for n in names}
    worlds = {9900 + i: dict(holds=(i == 0), phases=[[(reg[n], {}, 1.0)]], other_branches=[br[o] for o in names if o != n],
                             disp_mm=nuis['displacement_mm'], zero_deg=nuis['zero_deg']) for i, n in enumerate(names)}
    SC.SCEN[AGENT_SCEN] = dict(name='v6 agent model', kind='agent', claim='', description='', library=list(reg.values()), worlds=worlds,
                               claim_side=[br[names[0]]], other_side=[br[names[1]]])
    SC.TUNE[AGENT_SCEN] = dict(L=nuis['size_nm'], N=task['N_stated'], bg=max(1.0, nuis['background_cps']), Nn=1000.0, bgn=50.0)
    SC.WORLD_SCEN.update({w: AGENT_SCEN for w in worlds})
    return {9900 + i: n for i, n in enumerate(names)}


def _pool_init(task, nuis):
    agent_model(task, nuis)


def simulator(node, inp, task, ctx):
    from mcenv import separation as SP
    from mcenv import plangrid as PG
    calls = [m0_digest(task, ctx)]
    fits = {}
    for n in polymorphs(task):
        r, rec = _call(task, ctx, 'fit', dict(measurement_ids=['m0'], spec=dict(phases=[dict(name=n, weight=1.0)], size_nm=100)))
        fits[n] = r; calls.append(dict(rec, result=dict(chi2=r['chi2'])))
    best = min(fits, key=lambda n: fits[n]['chi2']); f = fits[best]['fitted']
    nuis = dict(displacement_mm=f['displacement_mm'], zero_deg=f['zero_deg'], size_nm=f['size_nm'], background_cps=f['xray']['background_cps'])
    wm = agent_model(task, nuis); worlds = sorted(wm)
    # m0 alone
    d0 = [SP.separation(w, [SP.DEFAULT]) for w in worlds]
    calls.append(dict(call_id=None, tool='simulate (local forward model)', args=dict(hypotheses=[wm[w] for w in worlds], plan='m0'),
                      result=dict(predicted_D_m0=[round(x, 3) for x in d0])))
    target = PLAN_FACTOR * ctx.const['D_accept']          # V6-X3: plan for twice D_accept (noise and nuisance-estimate error)
    if min(d0) >= target:
        return dict(outputs=dict(window=None, plan=[], predicted_D=round(min(d0), 3), predicted_cost_min=0.0), cost_min=0.0, calls=calls)
    from multiprocessing import get_context
    with get_context('spawn').Pool(int(os.environ.get('V6_PROCS', '12')), initializer=_pool_init, initargs=(task, nuis)) as pool:
        cands = []
        for w in worlds:
            rows = PG.scan_world(w, pairs=True, max_cost=ctx.const['budget_min'], pool=pool)
            cands += [r[2] for r in rows if r[1] >= ctx.const['D_accept']]
            rows2 = PG.scan_world(w, pairs=True, max_cost=ctx.const['budget_min'], thr=target, pool=pool)
            cands += [r[2] for r in rows2 if r[1] >= target]
        uniq = {json.dumps([m.key() for m in p]): p for p in cands}
        ev = pool.starmap(PG.d_plan, [(w, p) for p in uniq.values() for w in worlds], chunksize=2)
    best_plan, i = None, 0
    for key, p in uniq.items():
        ds = ev[i:i + len(worlds)]; i += len(worlds)
        if min(ds) >= target:
            c = PG.plan_cost(p)
            if best_plan is None or (c, sum(m.n for m in p)) < (best_plan[0], sum(m.n for m in best_plan[2])): best_plan = (c, min(ds), p)
    if best_plan is None:                                   # nothing reaches the target: the most separating plan that reaches D_accept
        i = 0
        for key, p in uniq.items():
            ds = ev[i:i + len(worlds)]; i += len(worlds)
            if min(ds) >= ctx.const['D_accept'] and (best_plan is None or min(ds) > best_plan[1]): best_plan = (PG.plan_cost(p), min(ds), p)
    if best_plan is None:
        return dict(outputs=dict(window=None, plan=[], predicted_D=None, predicted_cost_min=0.0), cost_min=0.0, calls=calls)
    c, d, p = best_plan
    plan = [dict(radiation=m.radiation, start=m.start, stop=round(m.start + m.step * (m.n - 1), 4), step=m.step, time_per_step=m.t,
                 optics=m.optics, si_standard=m.si_standard) for m in p]
    win = [min(x['start'] for x in plan), max(x['stop'] for x in plan)]
    calls.append(dict(call_id=None, tool='plan search (local forward model)', args=dict(n_candidates=len(uniq)),
                      result=dict(plan=plan, predicted_D=round(d, 3), cost_min=round(c, 3))))
    return dict(outputs=dict(window=win, plan=plan, predicted_D=round(d, 3), predicted_cost_min=round(c, 3)), cost_min=0.0, calls=calls)


# ---------------------------------------------------------------- S1b, S1c, S2, S2x through the server's tools
def instrument(node, inp, task, ctx):
    ids, calls, cost = [], [], 0.0
    for p in inp['plan'] or []:
        if p.get('radiation') == 'neutron': args = dict(radiation='neutron')
        else: args = dict(start=p['start'], stop=p['stop'], step=p['step'], time_per_step=p['time_per_step'], optics=p.get('optics', 'standard'),
                          si_standard=p.get('si_standard', False))
        r, rec = _call(task, ctx, 'measure', args)
        ids.append(r['id']); cost += r['cost_minutes']
        calls.append(dict(rec, result=dict(id=r['id'], cost_minutes=r['cost_minutes']), result_digest=_digest(r['counts'])))
    return dict(outputs=dict(measurements=ids, cost_min=round(cost, 3)), cost_min=cost, calls=calls)


def fit(node, inp, task, ctx):
    ids = ['m0'] + list(inp.get('measurements') or [])
    chi, calls = {}, [m0_digest(task, ctx)]
    for n in polymorphs(task):
        r, rec = _call(task, ctx, 'fit', dict(measurement_ids=ids, spec=dict(phases=[dict(name=n, weight=1.0)], size_nm=100)))
        chi[n] = r['chi2']; calls.append(dict(rec, result=dict(chi2=r['chi2'], n_points=r.get('n_points'))))
    order = sorted(chi, key=chi.get)
    return dict(outputs=dict(phase=order[0], runner_up=order[1], D=round(chi[order[1]] - chi[order[0]], 3)), cost_min=0.0, calls=calls)


def fm(node, inp, task, ctx):
    calls = []
    if task['claim_type'] == 'R':
        e = {}
        for n in polymorphs(task):
            r, rec = _call(task, ctx, 'energy', dict(structure_name=n)); e[n] = r['formation_energy_eV_per_atom']
            calls.append(dict(rec, result=dict(formation_energy_eV_per_atom=e[n])))
        out = dict(dict(energies=e, stated_error=task.get('stated_error')), **G.summarize_R(e))
        return dict(outputs=out, cost_min=0.0, calls=calls)
    ph = inp.get('phase')
    r, rec = _call(task, ctx, 'hull', dict(structure_name=ph)); h = r['energy_above_hull_eV_per_atom']
    calls.append(dict(rec, result=dict(energy_above_hull_eV_per_atom=h)))
    thr = ctx.const['threshold']
    return dict(outputs=dict(hull_distance=h, decomposition=r.get('decomposition'), stated_error=task.get('stated_error'),
                             margin=round(abs(h - thr), 6)), cost_min=0.0, calls=calls)


def dft(node, inp, task, ctx):
    calls, cost = [], 0.0
    names = polymorphs(task) if task['claim_type'] == 'R' else [inp.get('phase')]
    vals = {}
    for n in names:
        try: r, rec = _call(task, ctx, task.get('dft_tool', 'energy_dft'), dict(structure_name=n))
        except RuntimeError as e:
            calls.append(dict(call_id=None, tool=task.get('dft_tool', 'energy_dft'), args=dict(structure_name=n), error=str(e)[:200])); break
        vals[n] = r; cost += float(r.get('cost_minutes', 0.0)); calls.append(dict(rec, result={k: v for k, v in r.items() if k != 'decomposition'}))
    if task['claim_type'] == 'R':
        if len(vals) < len(names):
            return dict(outputs=dict(energies_dft=None, lowest_dft=None, cost_min=round(cost, 3)), cost_min=cost, calls=calls)
        e = {n: v['formation_energy_eV_per_atom'] for n, v in vals.items()}
        return dict(outputs=dict(energies_dft=e, lowest_dft=min(e, key=e.get), cost_min=round(cost, 3)), cost_min=cost, calls=calls)
    h = vals[names[0]]['energy_above_hull_eV_per_atom'] if vals else None
    return dict(outputs=dict(hull_distance_dft=h, cost_min=round(cost, 3)), cost_min=cost, calls=calls)


ADAPTERS = dict(simulator=simulator, instrument=instrument, fit=fit, fm=fm, dft=dft)


def make_task(env, world, arm, k, claim_type, key=None, extra=None):
    """the task an agent sees: claim, library (with structures), the manual's stated count rate and stated error, from status on a
    fresh episode of the same world (that episode only reads status)."""
    tok = env.new_token(world, arm, k)
    st = env.call(tok, 'status', {})
    f = st['claim'].split(' of ')[-1].rstrip('.') if claim_type == 'R' else None
    if claim_type == 'H':
        f = re.search(r'^(\S+) powder', st['description']).group(1)
    m = re.search(r'typical error is (\d+\.\d+) eV/atom', st['manual']) or re.search(r'mean absolute error (\d+\.\d+) eV/atom', st['manual'])
    t = dict(task_id=f'w{world}-{arm}-k{k}', world=world, arm=arm, k=k, claim=st['claim'], claim_type=claim_type, formula=f,
             library=st['library'], m0='m0', N_stated=_counts_N(st['manual']), stated_error=float(m.group(1)) if m else None, env=env,
             status_token=tok)
    if key: t['key'] = key
    t.update(extra or {})
    return t
