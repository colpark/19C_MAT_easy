#!/usr/bin/env python3
"""sd/bundle.py (v3.3 A2): adapter from Source Data cells to the bundle interface the family generators use.
A condition is (series, x): series = the plotted sample/curve label, x = the plotted x value (None for bars). Where the condition series
sits on the x axis itself (P3: filler fraction f) the single series carries the conditions on x.
Definition 1 (v3.3): u = half the frozen panel tolerance (sd/<P>/tol.json), so one band (2u) equals the tolerance. Log panels: u in decades.
Levels come from the audited sd/<P>/nodes.json (one node per keyed panel), never from spec comments.
B.cell(panel, series, x) -> {'value', 'u', 'lv' (log10 value on log panels), 'level', ...} or None."""
import importlib.util, json, math, os, sys
import numpy as np
import sys as _pb_s, os as _pb_o
_pb_d = _pb_o.path.dirname(_pb_o.path.abspath(__file__))
while not _pb_o.path.exists(_pb_o.path.join(_pb_d, 'pbroot.py')) and _pb_o.path.dirname(_pb_d) != _pb_d: _pb_d = _pb_o.path.dirname(_pb_d)
_pb_s.path.insert(0, _pb_d)
from pbroot import ROOT, HOST

def _load(path, name):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

class SDBundle:
    def __init__(self, P, root=None, cells=None, tol=None, nodes=None, spec=None, physics=None):
        self.P = P; self.dir = f'{root or ROOT}/sd/{P}'
        self.spec = spec or _load(f'{self.dir}/spec.py', f'spec_{P}')
        self.physics = physics if physics is not None else (_load(f'{self.dir}/physics.py', f'physics_{P}') if os.path.exists(f'{self.dir}/physics.py') else None)
        self.tol = tol or json.load(open(f'{self.dir}/tol.json'))
        if tol is None and os.path.exists(f'{self.dir}/tol_add33.json'): self.tol = dict(self.tol, **json.load(open(f'{self.dir}/tol_add33.json')))   # v3.3 appended panels
        raw = cells if cells is not None else [json.loads(l) for l in open(f'{self.dir}/cells.jsonl')]
        nl = nodes if nodes is not None else (json.load(open(f'{self.dir}/nodes.json')) if os.path.exists(f'{self.dir}/nodes.json') else [])
        self.nodes = {n['panel']: n for n in nl}
        self.PN = {p['id']: p for p in self.spec.PANELS}
        self.excluded = set(getattr(self.spec, 'EXCLUDED_PANELS', {}).keys())
        self.cells = {}
        for c in raw:
            if c['panel'] in self.excluded: continue
            t = self.tol.get(c['panel'])
            if not t: continue
            c = dict(c); c['u'] = t['tol'] / 2.0; c['log'] = bool(t.get('log'))
            c['lv'] = math.log10(c['value']) if c['log'] and c['value'] > 0 else c['value']
            c['level'] = self.level(c['panel'])
            self.cells[(c['panel'], c['series'], None if c['x'] is None else round(float(c['x']), 9))] = c
        # dense curves: cells linearly interpolated at the panel's declared x values (t1_at), as build.items does for T1/T4 (v3.3 A4)
        for p in self.spec.PANELS:
            if not p.get('t1_at') or p['id'] in self.excluded or p['id'] not in self.tol: continue
            for ser in self.series_of(p['id']):
                cv = self.curve(p['id'], ser)
                for x0 in p['t1_at']:
                    if cv[0][0] <= x0 <= cv[-1][0] and self.cell(p['id'], ser, x0) is None:
                        v = float(np.interp(x0, [a for a, _ in cv], [b for _, b in cv])); t = self.tol[p['id']]
                        self.cells[(p['id'], ser, round(float(x0), 9))] = {'id': f"{p['id']}:{ser}:{x0:g}", 'panel': p['id'], 'series': ser, 'x': x0, 'value': v,
                            'unit': p['unit'], 'u': t['tol'] / 2.0, 'log': bool(t.get('log')), 'lv': math.log10(v) if t.get('log') and v > 0 else v,
                            'level': self.level(p['id']), 'source': 'source data (linear interpolation of the plotted curve)', 'addr': f"{p['sheet']} ({ser} curve)"}

    def level(self, panel):
        """level of a panel's plotted quantity: the audited node; a panel without a node is treated as A (restrictive)."""
        n = self.nodes.get(panel); return n['level'] if n else 'A'

    def cell(self, panel, series, x=None):
        return self.cells.get((panel, series, None if x is None else round(float(x), 9)))

    def series_of(self, panel):
        return list(dict.fromkeys(k[1] for k in self.cells if k[0] == panel))

    def xs_of(self, panel, series):
        return sorted(k[2] for k in self.cells if k[0] == panel and k[1] == series and k[2] is not None)

    def curve(self, panel, series):
        return sorted((k[2], c['value']) for k, c in self.cells.items() if k[0] == panel and k[1] == series and k[2] is not None)

    def label(self, panel, series):
        f = self.PN[panel].get('series_label'); return f(series) if f else series

    def desc(self, panel): return self.PN[panel]['desc']
