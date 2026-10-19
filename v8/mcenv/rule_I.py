"""Decide rule of graph I (kit D rule signature). Pure function, no truth.

SUPPORTED  measured angle relative to the lattice equals theta_match (within angle_tol_deg, modulo the lattice period)
           and the FM margin is outside the band.
REFUTED    it equals the other registry (theta_match + registry_offset_deg) and the margin is outside the band.
CANNOT_TELL otherwise: no decisive lattice-referenced angle (S1f or S1c not accepted, which includes D too small and no
           lattice scan), FM not accepted (margin inside the band), or the angle matches neither registry.
theta_match is read from the registry angle of the lowest registry, so an intervention on the FM's ranking moves it.
"""


def fold_dist(a, b, period):
    d = (a - b) % period
    return min(d, period - d)


def rule_I_registry_match(inp, ctx, params):
    pri = params.get('prior', 'S2b')
    c = ctx.const
    ang = None
    for e in params.get('identify', ['S1f:angle_rel_deg', 'S1c:angle_rel_deg']):
        node, _, name = e.partition(':')
        name = 'angle_rel_deg2' if node == 'S1f' else 'angle_rel_deg'
        if ctx.ran.get(node) and ctx.accepted.get(node) and inp.get(name) is not None:
            ang = inp[name]
            break
    if ang is None:
        return {'verdict': 'CANNOT_TELL', 'reason': 'no decisive angle relative to the lattice', 'margin_used': None}
    low, regs, margin = inp.get('lowest'), inp.get('registry_angles'), inp.get('margin')
    if not ctx.ran.get(pri) or low is None or not regs or low not in regs or margin is None:
        return {'verdict': 'CANNOT_TELL', 'reason': 'no registry ranking', 'margin_used': None}
    if not ctx.accepted.get(pri):
        return {'verdict': 'CANNOT_TELL', 'reason': f'FM margin {margin} inside the band {c["band"]}', 'margin_used': margin}
    per, tol, off = c['lattice_period_deg'], c['angle_tol_deg'], c['registry_offset_deg']
    th = regs[low]
    dm, do = fold_dist(ang, th, per), fold_dist(ang, th + off, per)
    if dm <= tol and dm < do:
        return {'verdict': 'SUPPORTED', 'reason': f'angle {round(ang, 2)} deg matches theta_match {round(th, 2)} deg, margin {margin} against the band {c["band"]}', 'margin_used': margin}
    if do <= tol and do < dm:
        return {'verdict': 'REFUTED', 'reason': f'angle {round(ang, 2)} deg matches the other registry {round(th + off, 2)} deg, margin {margin} against the band {c["band"]}', 'margin_used': margin}
    return {'verdict': 'CANNOT_TELL', 'reason': f'angle {round(ang, 2)} deg matches neither registry', 'margin_used': margin}
