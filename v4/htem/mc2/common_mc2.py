"""common_mc2.py (v4.5 MC v2): cache-only position records for the MC v2 census (HTEM_MC2_RULES.md section 1). Frozen at MV1."""
import csv, json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'mc'))
import htem_api as API, sample_io as SIO
from readers import optical as RO, xrd as RX
import mc_keys as K
HC = 1239.84198
C = API.Client()
ROWS = [r for r in csv.DictReader(open(os.path.join(API.HOST, 'census', 'libraries.csv'))) if r.get('multi') == '1']
SPL = json.load(open(os.path.join(HERE, 'MC_SPLITS.json')))['libraries']
NOISE = json.load(open(os.path.join(HERE, 'MC_CENSUS.json')))['noise']


def sig_A(system):
    return NOISE['sigma_A_rep'].get(system, NOISE['sigma_A_median'])


def sig_logrs(system):
    return NOISE['sigma_logRs_rep'].get(system, NOISE['sigma_logRs_median'])


def fully_cached(lid):
    lib = C.cached('library', lid); ids = (lib or {}).get('sample_ids') or []
    return bool(ids) and all(C.cached('sample', s) for s in ids)


def positions(lid):
    """Position records in sample_ids order; None unless every sample is cached (VM-E03)."""
    lib = C.cached('library', lid)
    if not lib or not fully_cached(lid): return None
    out = []
    for sid in lib.get('sample_ids') or []:
        s = C.cached('sample', sid); fp = SIO.fpm(s)
        P = {'sid': sid, 'xy': SIO.xyz(s), 'comp': SIO.composition(s), 'an': SIO.anion_fraction(s), 'd': SIO.thickness_um(s),
             'iv': K.iv_fit(fp['current_A'], fp['voltage_V']) if fp else None, 'opt': None, '_s': s}
        op = SIO.optical(s); pr = RO._pair(op) if op else None
        if pr is not None:
            w, t, r = pr; e = HC / w; o = np.argsort(e); e, t, r = e[o], t[o], r[o]
            ok = (t >= 0.01) & np.isfinite(t) & np.isfinite(r); bad = np.flatnonzero(~ok); n = bad[0] if bad.size else ok.size
            if n >= 20: P['opt'] = (e[:n], t[:n], r[:n])
        out.append(P)
    return out


_PK = {}


def peaks(P, i):
    key = P[i]['sid']
    if key not in _PK:
        x = SIO.xrd(P[i]['_s']); _PK[key] = RX.read(x['two_theta'], x['intensity'], API.CFG['readers']['xrd'])['peaks'] if x else None
    return _PK[key]
