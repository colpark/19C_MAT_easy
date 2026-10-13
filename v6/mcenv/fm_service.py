"""Stage 2 FM service (V5_SPEC B.3): MACE-MP-0 medium (2023-12-03-mace-128-L1_epoch-199) on a node 2 GPU.
POST /relax {"structure": pymatgen Structure dict} -> {"structure": dict, "energy_per_atom": eV, "steps": n, "converged": bool}
FIRE on FrechetCellFilter with FixSymmetry, fmax 0.02 eV/A, at most 500 steps. Ordered sites only (MACE needs atoms; mixed sites are
relaxed as the ordered prototype the builder supplies). Run with the MACE venv: ~/Documents/fmllm/.venv/bin/python -m mcenv.fm_service"""
import json, os, threading, time, traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MODEL = os.path.expanduser(os.environ.get('V5_MACE_MODEL', '~/.cache/mace/20231203mace128L1_epoch199model'))
_lock = threading.Lock()
_calc = None


def calc():
    global _calc
    if _calc is None:
        from mace.calculators import mace_mp
        _calc = mace_mp(model=MODEL, device=os.environ.get('V5_FM_DEVICE', 'cuda'), default_dtype='float64')
    return _calc


def relax(sd, fmax=0.02, steps=500):
    from pymatgen.core import Structure
    from pymatgen.io.ase import AseAtomsAdaptor
    from ase.constraints import FixSymmetry
    from ase.filters import FrechetCellFilter
    from ase.optimize import FIRE
    s = Structure.from_dict(sd)
    if not s.is_ordered: raise ValueError('relax needs an ordered structure')
    at = AseAtomsAdaptor.get_atoms(s); at.calc = calc()
    at.set_constraint(FixSymmetry(at, symprec=1e-3))
    opt = FIRE(FrechetCellFilter(at), logfile=None)
    conv = opt.run(fmax=fmax, steps=steps)
    e = float(at.get_potential_energy()) / len(at)
    at.set_constraint()
    out = AseAtomsAdaptor.get_structure(at)
    return dict(structure=out.as_dict(), energy_per_atom=round(e, 6), steps=int(opt.nsteps), converged=bool(conv))


class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_POST(self):
        if self.path != '/relax': self.send_error(404); return
        n = int(self.headers.get('Content-Length', 0))
        try:
            req = json.loads(self.rfile.read(n))
            with _lock:          # one GPU relaxation at a time
                t0 = time.time(); out = relax(req['structure']); out['sec'] = round(time.time() - t0, 2)
            body = dict(ok=True, result=out)
        except Exception as e:
            body = dict(ok=False, error=f'{type(e).__name__}: {e}', trace=traceback.format_exc()[-1500:])
        b = json.dumps(body).encode()
        self.send_response(200); self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(b)))
        self.end_headers(); self.wfile.write(b)


if __name__ == '__main__':
    calc()
    srv = ThreadingHTTPServer((os.environ.get('V5_FM_BIND', '192.168.100.11'), int(os.environ.get('V5_FM_PORT', '8770'))), H)
    print('fm service up', MODEL, flush=True)
    srv.serve_forever()
