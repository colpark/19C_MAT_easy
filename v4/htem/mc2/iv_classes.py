"""iv_classes.py (v4.5 MC v2.1; HTEM_MC2_RULES_v21.md section 3): S4mc6 v2 reading classes on raw I-V points.
valid uses the frozen S4mc6 criteria (mc_keys.iv_fit) with an optional r2 threshold for the robustness rule; classes are checked in
order valid, fault (degenerate, < 4 points, zero sweep, reversed polarity), beyond range (0 < max|I| < I_FLOOR), non-ohmic (quadratic
r2 >= 0.999 and V strictly monotonic in I), fault (erratic). I_FLOOR is the dev-derived noise floor frozen at MV1c."""
import math
import numpy as np

I_FLOOR = 5e-8
CLASSES = ('valid', 'beyond range', 'non-ohmic', 'fault')


def classify(I, V, r2min=0.999):
    I, V = np.asarray(I, float), np.asarray(V, float); m = np.isfinite(I) & np.isfinite(V); I, V = I[m], V[m]
    out = {'n': int(I.size), 'imax': float(np.max(np.abs(I))) if I.size else 0.0, 'R': None, 'R_err': None, 'r2': None}
    if I.size < 2 or np.ptp(I) == 0:
        return {**out, 'cls': 'fault', 'why': 'degenerate', 'valid': False}
    A = np.vstack([I, np.ones(I.size)]).T; (R, V0), *_ = np.linalg.lstsq(A, V, rcond=None); res = V - A @ np.array([R, V0])
    ss = float(np.sum((V - V.mean()) ** 2)); r2 = 1 - float(np.sum(res ** 2)) / ss if ss > 0 else 0.0
    dof = max(I.size - 2, 1); se = math.sqrt(float(np.sum(res ** 2)) / dof / max(float(np.sum((I - I.mean()) ** 2)), 1e-300))
    rms = math.sqrt(float(np.mean(res ** 2))); vmax = float(np.max(np.abs(V))) or 1e-300
    out.update(R=float(R), R_err=float(se), r2=float(r2), rms_frac=rms / vmax)
    lin_ok = r2 >= r2min and rms <= 0.02 * vmax
    if I.size >= 4 and out['imax'] >= I_FLOOR and R > 0 and lin_ok:
        return {**out, 'cls': 'valid', 'why': None, 'valid': True}
    if I.size < 4: return {**out, 'cls': 'fault', 'why': 'points<4', 'valid': False}
    if out['imax'] == 0: return {**out, 'cls': 'fault', 'why': 'zero sweep', 'valid': False}
    if R <= 0: return {**out, 'cls': 'fault', 'why': 'polarity', 'valid': False}
    if out['imax'] < I_FLOOR: return {**out, 'cls': 'beyond range', 'why': 'below I_floor', 'valid': False}
    o = np.argsort(I); Is, Vs = I[o], V[o]
    if np.all(np.diff(Is) > 0):
        q = np.polyfit(I, V, 2); rq = V - np.polyval(q, I); r2q = 1 - float(np.sum(rq ** 2)) / ss if ss > 0 else 0.0
        if r2q >= 0.999 and np.all(np.diff(Vs) > 0):
            return {**out, 'cls': 'non-ohmic', 'why': f'quadratic r2 {r2q:.4f}', 'valid': False}
    return {**out, 'cls': 'fault', 'why': 'erratic', 'valid': False}
