"""Second-FM service (fm2, V6-14): the MACE protocol of mcenv/fm_service.py (FIRE on FrechetCellFilter with FixSymmetry symprec 1e-3,
fmax 0.02 eV/A, at most 500 steps, ordered structures only) with the calculator of one candidate model:
  chgnet   CHGNet 0.3.0 (chgnet 0.4.2; MPtrj), CUDA                                   venv ~/v6fm2/.venv
  sevennet SevenNet-0 11Jul2024, '7net-0' (sevenn 0.13.0; MPtrj), CUDA                 venv ~/v6fm2/.venv
  m3gnet   M3GNet-MP-2021.2.8-PES (matgl 1.1.3 with DGL 2.1.0; MP relaxations 2021.2.8),  venv ~/v6fm2/.venv_m3g (CPU: torch 2.2.1 has no
           aarch64 CUDA build; matgl 4.x no longer ships this model, so the weights come from the matgl v1.1.3 tag, ~/v6fm2/models/)
Returned energy: the calculator's total energy per atom as given (the energy convention is fixed afterwards on the dev split, V6-14).
  batch:   python -m mcenv.fm2_service batch MODEL IN.json OUT.json [SHARD NSHARD]     IN: {id: Structure dict} or the dev list
  service: python -m mcenv.fm2_service serve MODEL PORT                               POST /relax {"structure": dict}"""
import json, os, sys, threading, time, traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

M3G_PATH = os.path.expanduser(os.environ.get('V6_M3G_PATH', '~/v6fm2/models/M3GNet-MP-2021.2.8-PES'))
_calc = {}
_lock = threading.Lock()


def calc(model):
    if model not in _calc:
        if model == 'chgnet':
            from chgnet.model import CHGNet, CHGNetCalculator
            _calc[model] = CHGNetCalculator(CHGNet.load(model_name='0.3.0', verbose=False), use_device=os.environ.get('V6_FM2_DEVICE', 'cuda'))
        elif model == 'sevennet':
            from sevenn.calculator import SevenNetCalculator
            _calc[model] = SevenNetCalculator('7net-0', device=os.environ.get('V6_FM2_DEVICE', 'cuda'))
        elif model == 'm3gnet':
            import matgl
            from matgl.ext.ase import PESCalculator
            _calc[model] = PESCalculator(matgl.load_model(M3G_PATH))
        else:
            raise ValueError(f'unknown model {model}')
    return _calc[model]


def relax(sd, model, fmax=0.02, steps=500):
    from pymatgen.core import Structure
    from pymatgen.io.ase import AseAtomsAdaptor
    from ase.constraints import FixSymmetry
    from ase.filters import FrechetCellFilter
    from ase.optimize import FIRE
    s = Structure.from_dict(sd)
    if not s.is_ordered: raise ValueError('relax needs an ordered structure')
    at = AseAtomsAdaptor.get_atoms(s); at.calc = calc(model)
    at.set_constraint(FixSymmetry(at, symprec=1e-3))
    opt = FIRE(FrechetCellFilter(at), logfile=None)
    conv = opt.run(fmax=fmax, steps=steps)
    e = float(at.get_potential_energy()) / len(at)
    at.set_constraint()
    out = AseAtomsAdaptor.get_structure(at)
    return dict(structure=out.as_dict(), energy_per_atom=round(e, 6), steps=int(opt.nsteps), converged=bool(conv))


def batch(model, inp, out, shard=0, nshard=1):
    rows = json.load(open(inp))
    items = list(rows.items()) if isinstance(rows, dict) else [(r['id'], r['structure']) for r in rows]
    res = json.load(open(out)) if os.path.exists(out) else {}
    for i, (mid, sd) in enumerate(items):
        if i % nshard != shard or mid in res: continue
        t0 = time.time()
        try: res[mid] = relax(sd, model)
        except Exception as e: res[mid] = dict(error=f'{type(e).__name__}: {str(e)[:200]}')
        res[mid]['sec'] = round(time.time() - t0, 2)
        if len(res) % 10 == 0: json.dump(res, open(out, "w"), default=float); print(len(res), flush=True)
    json.dump(res, open(out, "w"), default=float); print("done", len(res), flush=True)


def serve(model, port):
    calc(model)

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a): pass

        def do_POST(self):
            if self.path != '/relax': self.send_error(404); return
            n = int(self.headers.get('Content-Length', 0))
            try:
                req = json.loads(self.rfile.read(n))
                with _lock:
                    t0 = time.time(); r = relax(req['structure'], model); r['sec'] = round(time.time() - t0, 2)
                body = dict(ok=True, result=r)
            except Exception as e:
                body = dict(ok=False, error=f'{type(e).__name__}: {e}', trace=traceback.format_exc()[-1500:])
            b = json.dumps(body, default=float).encode()
            self.send_response(200); self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(b)))
            self.end_headers(); self.wfile.write(b)

    srv = ThreadingHTTPServer((os.environ.get('V6_FM2_BIND', '192.168.100.11'), int(port)), H)
    print('fm2 service up', model, port, flush=True); srv.serve_forever()


if __name__ == '__main__':
    if sys.argv[1] == 'batch': batch(sys.argv[2], sys.argv[3], sys.argv[4], *(int(x) for x in sys.argv[5:7]))
    else: serve(sys.argv[2], sys.argv[3])
