"""v8 adapters on the family I server (mcenv/server8.py). Same pattern as adapters_mcenv.py: each adapter returns
dict(outputs, cost_min, calls) and reaches the world only through the server's tools with an episode token. No physics of our own.

Tokens: every executor run opens a fresh episode (budget, measurements and noise are per episode: the noise stream is seeded by
world id, k and scan number, so a rerun of the same task sees the same data). The first adapter call of a run mints the token with
`server8.py admin new` as a local subprocess (episodes are never created over HTTP; the state directory is passed in V8_SERVER8_STATE).

  simulator (S1a, S1d)  the server's `simulate` (free; it models the plan from the free scan m0 only). Plan grid of one AFM scan plus
                        one lattice scan, tried in order of cost (the cost formulas are the status tool's); the cheapest plan whose
                        predicted_D reaches TARGET_FACTOR x D_accept within the budget left; if none does, the most separating one
                        that fits. S1d plans again with the budget left.
  instrument (S1b, S1e) afm_scan / lattice_scan for every plan item
  fit (S1c, S1f)        `fit` on m0 and the measurements (S1f: both rounds); phase, angle relative to the lattice, SE, D as returned
  fm S2a                `structure` (protein FM) on the repeat unit read from the sample text
  fm S2b                `registry_energy` (materials FM) on S2a's structure
  rule S3               mcenv/rule_I.py (executors pass rules=RULES_I)

Ceiling set (CEILING): the server's tools only. Nothing in this graph needs a reference value served free (the stage's ceiling
serves the same adapters); the set is named so a selection or gold run says what it used.
"""
import json, os, re, subprocess, sys, time, urllib.request, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'mcenv'))
import graphexec as G  # noqa: E402
from rule_I import rule_I_registry_match  # noqa: E402

RULES_I = {'I_registry_match': rule_I_registry_match}
SERVER_PY = os.path.join(ROOT, 'mcenv', 'server8.py')
TARGET_FACTOR = 2.0            # plan for 2 x D_accept (simulate over-predicts D somewhat: TRACK3_LOG)

# plan grid (server limits: afm size 100-2000, px 128-1024, sec 0.5-8; lattice size 4-60, px 128-512, sec 0.5-8)
AFM_GRID = [dict(kind='afm_scan', size_nm=s, px=px, sec_per_line=sec) for s in (500, 1000, 1500) for px in (256, 512) for sec in (1.0, 2.0, 4.0)]
LAT_GRID = [dict(kind='lattice_scan', size_nm=20, px=px, sec_per_line=sec) for px in (128, 256, 384, 512) for sec in (1.0, 2.0, 4.0)]


def _cost(p):
    """the status tool's stated cost formulas"""
    return p['px'] * p['sec_per_line'] / 60.0 + 5.0 if p['kind'] == 'afm_scan' else p['px'] * p['sec_per_line'] * 1.5 / 60.0 + 5.0


class Env:
    """one v8 server: HTTP for tools, a local `server8.py admin new` for tokens."""

    def __init__(self, url, state_dir, py=None, batch='v8-gold', model='gold'):
        self.url, self.state_dir, self.py, self.batch, self.model = url, state_dir, py or sys.executable, batch, model
        self.tokens = []

    def new_token(self, world, arm, k):
        env = dict(os.environ, V8_SERVER8_STATE=self.state_dir)
        r = subprocess.run([self.py, SERVER_PY, 'admin', 'new', '--world', world, '--arm', arm, '--k', str(k), '--model', self.model,
                            '--batch', self.batch], capture_output=True, text=True, timeout=120, env=env)
        out = r.stdout.strip().splitlines()
        tok = out[-1].strip() if out else ''
        if not re.fullmatch(r'[0-9a-f]{32}', tok): raise RuntimeError(f'token minting failed: {r.stderr[-300:]}')
        self.tokens.append(dict(world=world, arm=arm, k=k, token_sha256=__import__('hashlib').sha256(tok.encode()).hexdigest()[:16]))
        return tok

    def call(self, token, tool, args):
        body = json.dumps(dict(token=token, tool=tool, args=args, rid=uuid.uuid4().hex)).encode()
        req = urllib.request.Request(self.url, data=body, headers={'Content-Type': 'application/json'})
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=300) as r: out = json.loads(r.read()); break
            except Exception:
                if attempt == 3: raise
                time.sleep(2 * (attempt + 1))
        if not out.get('ok'): raise RuntimeError(f'{tool}: {out.get("error")}')
        return out['result']


def _token(task, ctx):
    if getattr(ctx, 'token', None) is None:
        ctx.token = task['env'].new_token(task['world'], task['arm'], task['k'])
        ctx.call_n = 0
    return ctx.token


def _call(task, ctx, tool, args):
    tok = _token(task, ctx); res = task['env'].call(tok, tool, args)
    ctx.call_n += 1
    return res, dict(call_id=f'c{ctx.call_n}', tool=tool, args=args)


def _try(task, ctx, tool, args):
    """a tool refusal (arm switched the tool off, budget) is data, not a crash: returns (None, record with the error)"""
    try: return _call(task, ctx, tool, args)
    except RuntimeError as e: return None, dict(call_id=None, tool=tool, args=args, error=str(e)[:200])


def _status(task, ctx, calls):
    st, rec = _call(task, ctx, 'status', {})
    calls.append(dict(rec, result=dict(budget_left_min=st['budget_left_min'])))
    return st


# ---------------------------------------------------------------- S1a, S1d
def simulator(node, inp, task, ctx):
    calls = []
    left = float(_status(task, ctx, calls)['budget_left_min'])
    target = TARGET_FACTOR * ctx.const['D_accept']
    cands = sorted(((_cost(a) + _cost(l), a, l) for a in AFM_GRID for l in LAT_GRID if _cost(a) + _cost(l) <= left + 1e-9), key=lambda t: (t[0], t[1]['px'] * t[1]['sec_per_line']))
    best, tried = None, 0
    for c, a, l in cands:
        r, rec = _call(task, ctx, 'simulate', dict(plan=[a, l])); tried += 1
        if best is None or r['predicted_D'] > best[0]['predicted_D']: best = (r, rec, [a, l])
        if r['predicted_D'] >= target: best = (r, rec, [a, l]); break
    calls.append(dict(tool='simulate (plan search over the grid, cheapest first)', args=dict(n_tried=tried, n_grid=len(cands), target=target, budget_left_min=left)))
    if best is None:
        return dict(outputs=dict(window=None, plan=[], predicted_D=None, predicted_cost_min=0.0), cost_min=0.0, calls=calls)
    r, rec, plan = best
    calls.append(dict(rec, result=dict(predicted_D=r['predicted_D'], predicted_cost_min=r['predicted_cost_min'], within_budget=r['within_budget'])))
    sizes = [p['size_nm'] for p in plan if p['kind'] == 'afm_scan']
    return dict(outputs=dict(window=[0.0, float(max(sizes))], plan=plan, predicted_D=r['predicted_D'], predicted_cost_min=r['predicted_cost_min']),
                cost_min=0.0, calls=calls)


# ---------------------------------------------------------------- S1b, S1e
def instrument(node, inp, task, ctx):
    ids, calls, cost = [], [], 0.0
    for p in inp['plan'] or []:
        r, rec = _try(task, ctx, p['kind'], {k: v for k, v in p.items() if k != 'kind'})
        if r is None: calls.append(rec); continue
        ids.append(r['measurement_id']); cost += r['cost_min']
        calls.append(dict(rec, result=dict(measurement_id=r['measurement_id'], cost_min=r['cost_min'], budget_left_min=r['budget_left_min'],
                                           n_rods=r['summary'].get('n_rods'))))
    return dict(outputs=dict(measurements=ids, cost_min=round(cost, 3)), cost_min=cost, calls=calls)


# ---------------------------------------------------------------- S1c, S1f
def fit(node, inp, task, ctx):
    ids = ['m0'] + list(inp.get('measurements') or []) + list(inp.get('measurements2') or [])
    r, rec = _call(task, ctx, 'fit', dict(measurement_ids=ids))
    keys = ('phase', 'angle_rel_deg', 'angle_se_deg', 'runner_up', 'D')
    return dict(outputs={k: r.get(k) for k in keys}, cost_min=0.0,
                calls=[dict(rec, result={k: r.get(k) for k in keys + ('n_rods', 'n_lattice_scans')})])


# ---------------------------------------------------------------- S2a, S2b
def _sequence(text):
    m = re.search(r'One repeat reads ([A-Za-z]+)', text or '')
    return m.group(1).upper() if m else None


def fm(node, inp, task, ctx):
    nid = node['id']
    if nid == 'S2a':
        seq = _sequence(task.get('sample_text'))
        r, rec = _try(task, ctx, 'structure', dict(sequence=seq) if seq else {})
        if r is None: return dict(outputs=dict(carboxylate_geometry=None, n_carboxylate=None, stated_error=None), cost_min=0.0, calls=[rec])
        return dict(outputs=dict(carboxylate_geometry=r, n_carboxylate=float(r['n_carboxylate']), stated_error=r.get('stated_error_A')),
                    cost_min=0.0, calls=[dict(rec, result=dict(structure_id=r['structure_id'], n_carboxylate=r['n_carboxylate'], stated_error_A=r.get('stated_error_A')))])
    sid = (inp.get('carboxylate_geometry') or {}).get('structure_id')
    r, rec = _try(task, ctx, 'registry_energy', dict(structure_id=sid))
    if r is None: return dict(outputs=dict(G_NULL), cost_min=0.0, calls=[rec])
    out = dict(energies=r['energies'], registry_angles=r['registry_angles'], theta_match=r['theta_match'], lowest=r['lowest'],
               margin=r['margin'], stated_error=r.get('stated_error'))
    return dict(outputs=out, cost_min=0.0, calls=[dict(rec, result=out)])


G_NULL = dict(energies=None, registry_angles=None, theta_match=None, lowest=None, margin=None, stated_error=None)

CEILING = dict(simulator=simulator, instrument=instrument, fit=fit, fm=fm)
ADAPTERS = CEILING


def executor(graph, source='gold', constants=None, adapters=None):
    import graphexec_d as D
    return D.executor(graph, adapters or ADAPTERS, rules=RULES_I, constants=constants, source=source)


def make_task(env, world, arm, k, key=None, extra=None):
    """the task an agent sees: claim and sample text from `status` of a fresh episode (that episode only reads status)."""
    tok = env.new_token(world, arm, k)
    st = env.call(tok, 'status', {})
    t = dict(task_id=f'{world}-{arm}-k{k}', world=world, arm=arm, k=k, claim=st['claim'], sample_text=st['sample_text'], m0='m0', env=env)
    if key: t['key'] = key
    t.update(extra or {})
    return t
