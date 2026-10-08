#!/usr/bin/env python3
"""pilot_table.py (stage H5): turn matrix cells into the CSV that v4/trackS/separability_s.py reads (condition, unit, value, order).

Conditions are composition bins of one cation (bin width --bin, frozen before the run) inside ONE temperature level (--temp, required):
a series never crosses temperatures. Rows without a temperature are skipped.
Units:
  --unit library    one unit per library and bin (replicate libraries give real replicates; preferred when they exist)
  --unit position   one unit per film position (spatial units: pass --unit-type field to separability_s.py, which flags the result as
                    optimistic)
Observables: Eg (eV, non-censored only), peak (strongest XRD peak center inside --peak-window lo hi, deg), logRs (log10 ohm/sq).
usage: pilot_table.py --tag <name> --obs Eg|peak|logRs|E04|EU (--cation Zn | --frac cation|anion --element El) --bin 0.05 --temp 230 [--unit library|position] [--peak-window 30 36]
"""
import argparse, csv, json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import htem_api as API


def value(r, obs, win):
    d = r['derived']
    if obs == 'Eg':
        return None if d['Eg_eV'] is None or d['Eg_censored'] else d['Eg_eV']
    if obs == 'logRs':
        return math.log10(d['Rs_ohm_sq']) if d['Rs_ohm_sq'] and d['Rs_ohm_sq'] > 0 else None
    if obs == 'peak':
        ps = [p for p in (d['xrd_peaks'] or []) if win[0] <= p['center'] <= win[1]]
        return max(ps, key=lambda p: p['height'])['center'] if ps else None
    if obs == 'E04':   # round 2 (S4ho2): uncensored only
        return d.get('E04_eV')
    if obs == 'EU':    # round 2 (S4hu)
        return d.get('E_U_eV')
    raise ValueError(obs)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--tag', required=True)
    ap.add_argument('--obs', required=True, choices=['Eg', 'peak', 'logRs', 'E04', 'EU'])
    ap.add_argument('--cation', help='round-1 alias for --frac cation --element <El>')
    ap.add_argument('--frac', choices=['cation', 'anion'], default='cation', help='round 2: bin on cation_frac or anion_frac')
    ap.add_argument('--element')
    ap.add_argument('--bin', type=float, required=True)
    ap.add_argument('--temp', type=int, required=True, help='rounded substrate temperature (census temp_round_c)')
    ap.add_argument('--unit', default='library', choices=['library', 'position'])
    ap.add_argument('--peak-window', nargs=2, type=float, default=[19.0, 52.0])
    a = ap.parse_args(argv)
    if a.cation and not a.element:
        a.element = a.cation
    if not a.element:
        ap.error('--element (or --cation) is required')
    fk = 'cation_frac' if a.frac == 'cation' else 'anion_frac'
    src = os.path.join(API.HOST, 'matrix', a.tag, 'cells.jsonl')
    out = os.path.join(API.HOST, 'matrix', a.tag, (f'pilot_{a.obs}_{a.element}_T{a.temp}_{a.unit}.csv' if a.frac == 'cation' else f'pilot_{a.obs}_anion{a.element}_T{a.temp}_{a.unit}.csv'))
    rows = []
    for line in open(src):
        r = json.loads(line)
        if r['D']['temp_c'] != a.temp:
            continue
        cf = (r['M'].get(fk) or {}).get(a.element)
        v = value(r, a.obs, a.peak_window)
        if cf is None or v is None:
            continue
        b = math.floor(cf / a.bin + 1e-9)
        cond = f"T{a.temp}_x{b * a.bin:.3f}"
        unit = str(r['library']) if a.unit == 'library' else r['entity']
        rows.append({'condition': cond, 'unit': unit, 'value': v, 'order': round((b + 0.5) * a.bin, 6), 'sub': r['entity']})
    if not rows:
        temps = sorted({json.loads(l)['D']['temp_c'] for l in open(src)} - {None})
        print(f'no rows at --temp {a.temp}; temperature levels present (rounded): {temps}')
        return 3
    with open(out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['condition', 'unit', 'value', 'order', 'sub'])
        w.writeheader()
        w.writerows(rows)
    print(json.dumps({'rows': len(rows), 'conditions': len({r['condition'] for r in rows}), 'out': out}, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
