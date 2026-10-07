#!/usr/bin/env python3
"""census.py (stage H1): library-level census of HTEM from the cached library list. One API call (the list) plus library records only
where the list lacks a field. Writes $HTEM_HOST/census/libraries.csv and systems.csv, and prints the stage A ranking.

Per library: id, system (sorted elements), anion class, has_* counters, quality, data_access, recipe fields, recipe key.
Per system (public libraries only when config census.public_only):
  n_libs, n_multi (xrd>0, opt>0, xrf>0), n_ele (ele>0), n_full (all four), replicate libraries among multi (recipe groups of 2 or more),
  temperature levels among multi (rounded to census.temp_round_c), recipe completeness among multi.

Recipe key: system, rounded substrate temperature, (target, power) pairs, (gas, flow) pairs, growth pressure, time, substrate.
usage: census.py [--fetch-missing]   (--fetch-missing pulls library records for multimodal libraries, which carry data_access)
"""
import collections, csv, json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import htem_api as API
import sample_io as SIO

OUT = os.path.join(API.HOST, 'census')
MODS = API.CFG['census']['modalities']


def _num(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def _list(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def _r(v, nd):
    return None if v is None else round(v, nd)


def _nullsafe(pair):
    """Sort key for (name, value) pairs whose value may be None (VH-E02: None vs float crashed the census)."""
    return (pair[0], pair[1] is None, pair[1] if pair[1] is not None else 0.0)


def recipe_key(r, round_c):
    """Deterministic recipe identity. Powers stay paired with their targets (deposition_compounds) and flows with their gases, so
    Zn 15 W / Sn 25 W never matches Zn 25 W / Sn 15 W. Without target names the power order is kept as recorded."""
    t = _num(r.get('deposition_initial_temp_c'))
    t = None if t is None else int(math.floor(t / round_c + 0.5) * round_c)
    tg = [str(x).strip() for x in _list(r.get('deposition_compounds'))]
    pw = [_num(p) for p in _list(r.get('deposition_power'))]
    if tg and len(tg) == len(pw):
        powers = tuple(sorted(((g, _r(p, 1)) for g, p in zip(tg, pw) if p), key=_nullsafe))
    else:
        powers = tuple(_r(p, 1) for p in pw if p)
    gs = [str(g).strip().lower() for g in _list(r.get('deposition_gases'))]
    fl = [_num(f) for f in _list(r.get('deposition_gas_flow_sccm'))]
    if len(gs) == len(fl):
        gases = tuple(sorted(((g, _r(f, 1)) for g, f in zip(gs, fl) if g and g != 'none'), key=_nullsafe))
    else:
        gases = tuple(sorted(g for g in gs if g and g != 'none')) + tuple(_r(f, 1) for f in fl if f is not None)
    return (SIO.system_key(r.get('elements')), t, powers, gases, _r(_num(r.get('deposition_growth_pressure_mtorr')), 1),
            _r(_num(r.get('deposition_sample_time_min')), 0), str(r.get('deposition_substrate_material') or '').strip().lower())


def library_rows(libs, round_c):
    rows = []
    for r in libs:
        h = {m: int(_num(r.get(f'has_{m}')) or 0) for m in MODS}
        rk = recipe_key(r, round_c)
        rows.append({'id': r.get('id'), 'system': SIO.system_key(r.get('elements')), 'anion': SIO.anion_class(r.get('elements')),
                     **{f'has_{m}': h[m] for m in MODS},
                     'multi': int(h['xrd'] > 0 and h['opt'] > 0 and h['xrf'] > 0), 'full': int(all(h[m] > 0 for m in MODS)),
                     'quality': r.get('quality'), 'data_access': r.get('data_access'),
                     'temp_c': rk[1], 'powers': json.dumps(rk[2]), 'gases': json.dumps(rk[3]),
                     'complete': int(rk[1] is not None and bool(rk[2])), 'recipe': json.dumps(rk), 'sample_date': r.get('sample_date')})
    return rows


def system_rows(rows, public_only=True):
    by = collections.defaultdict(list)
    for r in rows:
        if public_only and r['data_access'] not in (None, 'public'):
            continue
        by[r['system']].append(r)
    out = []
    for sysk, rs in by.items():
        multi = [r for r in rs if r['multi']]
        groups = collections.Counter(r['recipe'] for r in multi if r['complete'])
        reps = sum(n for n in groups.values() if n >= 2)
        temps = sorted({r['temp_c'] for r in multi if r['temp_c'] is not None})
        out.append({'system': sysk, 'anion': rs[0]['anion'], 'n_libs': len(rs), 'n_multi': len(multi),
                    'n_ele': sum(1 for r in rs if r['has_ele'] > 0), 'n_full': sum(r['full'] for r in rs),
                    'n_rep': reps, 'n_temps': len(temps), 'temps': ' '.join(map(str, temps)),
                    'complete_frac': round(sum(r['complete'] for r in multi) / len(multi), 3) if multi else 0.0,
                    'multi_ids': ' '.join(str(r['id']) for r in multi)})
    return sorted(out, key=lambda r: (-r['n_multi'], r['system']))


def write_csv(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not rows:
        open(path, 'w').close()
        return
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main(argv):
    c = API.Client()
    libs = c.libraries()
    rc = API.CFG['census']['temp_round_c']
    if '--fetch-missing' in argv:  # data_access sits on library records only; fetch them for the multimodal libraries that lack it
        merged = []
        for r in libs:
            if 'data_access' not in r and library_rows([r], rc)[0]['multi']:
                r = dict(r, **{k: v for k, v in c.library(r['id']).items() if k not in r})
            merged.append(r)
        libs = merged
    rows = library_rows(libs, rc)
    srows = system_rows(rows, API.CFG['census']['public_only'])
    write_csv(os.path.join(OUT, 'libraries.csv'), rows)
    write_csv(os.path.join(OUT, 'systems.csv'), srows)
    tot = {'libraries': len(rows), 'systems': len(srows), 'multi_libraries': sum(r['multi'] for r in rows),
           'full_libraries': sum(r['full'] for r in rows),
           'data_access': dict(collections.Counter(str(r['data_access']) for r in rows)),
           'quality': dict(collections.Counter(str(r['quality']) for r in rows)), 'requests': c.n_requests}
    json.dump(tot, open(os.path.join(OUT, 'census_totals.json'), 'w'), indent=1)
    print(json.dumps(tot, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
