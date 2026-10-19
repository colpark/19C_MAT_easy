"""v7 FM check, after each family's world freeze (V7-2 step 5, V7-3 step 7). The FM is MACE-MP-0 (the B1 protocol:
exemplar/fastpath/fm_relax.py on node A2); FM values as B1 (energy4.fm_values: MACE energy per atom plus the entry's MP2020 correction, then
formation energy and hull against the fixed DFT hull). Adds the fm table to v7/FAM/TOOL_TABLES_FAM.json and writes v7/FAM/fm/fm_check.json.
  H  per twin: the FM hull distance of the twin's polymorph against 0.050 with the band 0.02: right (same side as DFT, outside the band),
     in band, wrong (other side, outside the band); per compound: right if both twins are right, wrong if either is wrong, else in band
  T  per compound: the FM energy difference E(H) - E(L) between the quad's two polymorphs against the band 0.045: right (L lower, outside
     the band), in band, wrong (H lower, outside the band); the change cells decide on it
  python v7/fm_check7.py H|T FM_RELAXED.json [SCEN_FILTER]"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)


def main():
    from mcenv import energy4 as E
    fam, fmp = sys.argv[1], sys.argv[2]
    fm = json.load(open(fmp))
    W = json.load(open(os.path.join(HERE, fam, f'WORLDS_{fam}.json')))['worlds']
    tp = os.path.join(HERE, fam, f'TOOL_TABLES_{fam}.json'); T = json.load(open(tp)); T.setdefault('fm', {})
    rows = []
    for w in W:
        ids = list(w['names_by_id']); nm = w['names_by_id']
        if fam == 'T' and str(w['scen']) in T['fm'] and w['set'] == 'paired':
            vals = None                                         # paired set: B1's MACE values (V6-9), already in the table
        else:
            if not all(i in fm for i in ids): continue
            fv = E.fm_values(ids, fm); vals = {nm[i]: fv[i] for i in ids}; T['fm'][str(w['scen'])] = vals
        tab = T['fm'][str(w['scen'])]
        if fam == 'H':
            tw = {}
            for k, i in (('A', w['a']), ('B', w['b'])):
                h = tab[nm[i]]['e_hull']; d = w['dft'][nm[i]]['e_hull']; m = h - 0.050
                st = 'in band' if abs(m) < 0.02 else ('right' if (h <= 0.050) == (d <= 0.050) else 'wrong')
                tw[k] = dict(fm_hull=round(h, 5), dft_hull=round(d, 5), margin=round(m, 5), status=st)
            joint = 'wrong' if 'wrong' in (tw['A']['status'], tw['B']['status']) else ('right' if tw['A']['status'] == tw['B']['status'] == 'right' else 'in band')
            rows.append(dict(scen=w['scen'], formula=w['formula'], type=w['type'], panel=w['panel'], twins=tw, fm_status=joint))
        else:
            dE = tab[nm[w['H']]]['e_form'] - tab[nm[w['L']]]['e_form']
            st = 'in band' if abs(dE) < 0.045 else ('right' if dE > 0 else 'wrong')
            rows.append(dict(scen=w['scen'], formula=w['formula'], set=w['set'], stratum=w['stratum'], slot=w.get('slot', 'take'),
                             fm_gap_H_minus_L=round(dE, 5), dft_gap=round(w['dft'][nm[w['H']]]['e_form'] - w['dft'][nm[w['L']]]['e_form'], 5), fm_status=st,
                             fm_source='B1 MACE (V6-9)' if w['set'] == 'paired' else 'MACE, computed after the T freeze'))
    json.dump(T, open(tp, 'w'), indent=1, sort_keys=True)
    os.makedirs(os.path.join(HERE, fam, 'fm'), exist_ok=True)
    json.dump(dict(family=fam, rows=rows), open(os.path.join(HERE, fam, 'fm', 'fm_check.json'), 'w'), indent=1)
    from collections import Counter
    key = (lambda r: (r['type'], r['fm_status'])) if fam == 'H' else (lambda r: (r['set'], r['fm_status']))
    print(len(rows), Counter(map(key, rows)))


if __name__ == '__main__':
    main()
