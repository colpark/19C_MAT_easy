"""V6-14: choose the second energy model on the v5 stage 4b dev split (v5/stage4b/dev/dev4b_v2.json, 637 entries, removed from candidacy),
by the rule pre-registered in fm2/PREREG.md, applied once. Host A (DFT truth and the MP2020 corrections via mcenv.energy4).
  energy convention per candidate: (a) raw energy per atom plus the entry's MP2020 correction (energy4.fm_values, the MACE convention,
      X49) or (b) the output as given; the one with the lower formation-energy MAE against DFT
  pairs: every pair of relaxed entries of a formula (v5 dev4b.py); polymorph-gap error = (FM gap) - (DFT gap)
  R1 relaxes >= 98 % of entries (no error); R2 polymorph-gap MAE within 15 % of the best candidate's and <= 0.064 eV/atom;
  R3 lowest Pearson correlation with MACE in signed polymorph-gap error on the same pairs (tie: lower MAE)
  winner: the J.4 reliability table (v5 dev4b.py bins and m* rule) for claim R and H, m*_2, stated errors -> fm2/STATED2.json
  baseline: MACE on the dev pairs with a DFT gap >= 0.075 eV/atom (outside its band 0.045 or inside; wrong or tie), then per candidate
      AGREE / SPLIT / SOFT, the catch rate and the false-alarm rate; Gate A0
  python v6/fm2/dev_second_fm.py OUT_DIR"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..'))
import numpy as np
from mcenv import energy4 as E

DEV = os.path.expanduser('~/Documents/harbor/v5/v5/stage4b/dev')
CANDS = ('chgnet', 'sevennet', 'm3gnet')
BAND1 = 0.045
BINS = [0, .01, .02, .04, .06, .08, .1, .15, .2, 9]
GRID = np.round(np.arange(0, 0.5001, 0.005), 3)


def mstar_table(items):
    a = np.array([abs(x['pred']) for x in items]); wrong = np.array([(x['pred'] > 0) != (x['true'] > 0) for x in items])
    table = [dict(lo=BINS[i], hi=BINS[i + 1], n=int(((a >= BINS[i]) & (a < BINS[i + 1])).sum()),
                  sign_error_rate=round(float(wrong[(a >= BINS[i]) & (a < BINS[i + 1])].mean()), 3) if ((a >= BINS[i]) & (a < BINS[i + 1])).any() else None)
             for i in range(len(BINS) - 1)]
    ms = None
    for t in GRID:
        sel = a >= t
        if sel.sum() >= 20 and wrong[sel].mean() < 0.10: ms = float(t); break
    return dict(n_items=len(items), overall_sign_error=round(float(wrong.mean()), 4), table=table, m_star=ms)


def values(ids, raw, conv):
    from pymatgen.core import Structure
    if conv == 'corrected': return E.fm_values(ids, raw)
    out = {}
    for mid in ids:
        st = Structure.from_dict(raw[mid]['structure']); comp = st.composition
        out[mid] = E.form_hull(comp, raw[mid]['energy_per_atom'] * comp.num_atoms)
    return out


def main():
    od = sys.argv[1]; os.makedirs(od, exist_ok=True)
    rows = json.load(open(os.path.join(DEV, 'dev4b_v2.json'))); byid = {r['id']: r for r in rows}
    mace = {r['id']: r for r in json.load(open(os.path.join(DEV, 'errors4b_v2_entries.json')))}      # fm_e_form, fm_e_hull (MACE, X49)
    raws = {}
    for c in CANDS:
        p = os.path.join(od, f'relax_{c}.json')
        raws[c] = json.load(open(p)) if os.path.exists(p) else {}
    res = {}; e2 = {}
    for c in CANDS:
        raw = raws[c]; ok = [r['id'] for r in rows if r['id'] in raw and 'error' not in raw[r['id']]]
        conv_mae = {}
        for conv in ('corrected', 'as_given'):
            v = values(ok, raw, conv); conv_mae[conv] = (float(np.mean([abs(v[i]['e_form'] - byid[i]['e_form']) for i in ok])), v)
        conv = min(conv_mae, key=lambda k: conv_mae[k][0]); v = conv_mae[conv][1]
        e2[c] = {i: v[i] for i in ok}
        res[c] = dict(n_relaxed=len(ok), relaxed_frac=round(len(ok) / len(rows), 4),
                      n_converged=sum(1 for i in ok if raw[i].get('converged')), convention=conv,
                      e_form_mae={k: round(m, 4) for k, (m, _) in conv_mae.items()},
                      hull_mae=round(float(np.mean([abs(v[i]['e_hull'] - byid[i]['e_hull']) for i in ok])), 4))
    # pairs relaxed by MACE and every candidate (MACE relaxed all 637)
    byf = {}
    for r in rows: byf.setdefault(r['formula'], []).append(r['id'])
    pairs = []
    for f, ids in byf.items():
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a, b = ids[i], ids[j]
                pairs.append(dict(formula=f, a=a, b=b, dft=byid[a]['e_form'] - byid[b]['e_form'], mace=mace[a]['fm_e_form'] - mace[b]['fm_e_form']))
    for c in CANDS:
        ps = [p for p in pairs if p['a'] in e2[c] and p['b'] in e2[c]]
        for p in ps: p[c] = e2[c][p['a']]['e_form'] - e2[c][p['b']]['e_form']
        err = np.array([p[c] - p['dft'] for p in ps]); errm = np.array([p['mace'] - p['dft'] for p in ps])
        res[c].update(n_pairs=len(ps), polymorph_gap_mae=round(float(np.mean(np.abs(err))), 4),
                      pearson_vs_mace=round(float(np.corrcoef(err, errm)[0, 1]), 4) if len(ps) > 2 else None)
    mace_pg = round(float(np.mean([abs(p['mace'] - p['dft']) for p in pairs])), 4)
    best = min(res[c]['polymorph_gap_mae'] for c in CANDS if res[c]['n_pairs'])
    for c in CANDS:
        r = res[c]
        r['R1'] = r['relaxed_frac'] >= 0.98
        r['R2'] = r['polymorph_gap_mae'] <= 1.15 * best and r['polymorph_gap_mae'] <= 0.064
    elig = [c for c in CANDS if res[c]['R1'] and res[c]['R2']]
    win = min(elig, key=lambda c: (res[c]['pearson_vs_mace'], res[c]['polymorph_gap_mae'])) if elig else None
    out = dict(rule='fm2/PREREG.md V6-14', n_dev_entries=len(rows), n_pairs_all=len(pairs), mace_polymorph_gap_mae=mace_pg,
               best_polymorph_gap_mae=best, R2_cap=round(min(1.15 * best, 0.064), 4), candidates=res, eligible=elig, winner=win)
    # winner: reliability tables and stated errors
    if win:
        ids_by_f = {f: [i for i in ids if i in e2[win]] for f, ids in byf.items()}
        itR, itH = [], []
        for f, ids in ids_by_f.items():
            for i in ids:
                itH.append(dict(pred=0.050 - e2[win][i]['e_hull'], true=0.050 - byid[i]['e_hull']))
                if len(ids) >= 2:
                    o = [x for x in ids if x != i]
                    itR.append(dict(pred=min(e2[win][x]['e_form'] for x in o) - e2[win][i]['e_form'], true=min(byid[x]['e_form'] for x in o) - byid[i]['e_form']))
        relR, relH = mstar_table(itR), mstar_table(itH)
        out['winner_reliability'] = dict(R=relR, H=relH)
        fmt = lambda rel, lab, thr: (f"  - {lab}, absolute predicted margin in eV/atom: " + ' | '.join(
            f"{t['lo']}–{'∞' if t['hi'] >= 9 else t['hi']}: {round(100 * t['sign_error_rate']) if t['sign_error_rate'] is not None else '-'} % (n {t['n']})" for t in rel['table'])
            + f". m* = {rel['m_star']} eV/atom.")
        mstar2 = relR['m_star']
        stated = dict(fm_mae=res[win]['e_form_mae'][res[win]['convention']], polymorph_gap_mae=res[win]['polymorph_gap_mae'], hull_mae=res[win]['hull_mae'],
                      band_R=mstar2, band_H=relH['m_star'], dft_price_min=60.0,
                      reliability_text=fmt(relR, 'relative stability (predicted energy gap to the nearest other polymorph, threshold 0)', 0) + '\n'
                                       + fmt(relH, 'hull stability (predicted hull distance minus 0.050 eV/atom)', 0.05),
                      model=win, convention=res[win]['convention'], source='v6 fm2 V6-14 on the v5 stage 4b dev split (dev4b_v2.json)')
        json.dump(stated, open(os.path.join(HERE, 'STATED2.json'), 'w'), indent=1)
        out['m_star_2'] = mstar2
    # baseline on pairs with DFT gap >= 0.075 and the joint classes
    big = [p for p in pairs if abs(p['dft']) >= 0.075]
    def side(x, band): return 'out' if abs(x) >= band else 'in'
    def right(x, d): return None if x == 0 else ((x > 0) == (d > 0))
    base = dict(n=len(big), outside=sum(side(p['mace'], BAND1) == 'out' for p in big),
                outside_wrong=sum(side(p['mace'], BAND1) == 'out' and right(p['mace'], p['dft']) is False for p in big),
                inside=sum(side(p['mace'], BAND1) == 'in' for p in big),
                inside_wrong=sum(side(p['mace'], BAND1) == 'in' and right(p['mace'], p['dft']) is False for p in big),
                inside_tie=sum(side(p['mace'], BAND1) == 'in' and p['mace'] == 0 for p in big))
    out['mace_baseline_162'] = base
    cls = {}
    for c in CANDS:
        b2 = (out['m_star_2'] if c == win else None)
        if b2 is None:                                           # the candidate's own band from its own reliability table
            itR = []
            for f, ids in byf.items():
                ids = [i for i in ids if i in e2[c]]
                for i in ids:
                    if len(ids) >= 2:
                        o = [x for x in ids if x != i]
                        itR.append(dict(pred=min(e2[c][x]['e_form'] for x in o) - e2[c][i]['e_form'], true=min(byid[x]['e_form'] for x in o) - byid[i]['e_form']))
            b2 = mstar_table(itR)['m_star']
        rows_c = []
        for p in big:
            if c not in p: continue
            s1, s2 = side(p['mace'], BAND1), side(p[c], b2 if b2 is not None else 9)
            k = 'SOFT' if 'in' in (s1, s2) else ('AGREE' if (p['mace'] > 0) == (p[c] > 0) else 'SPLIT')
            rows_c.append(dict(pair=[p['a'], p['b']], formula=p['formula'], cls=k, mace_out=s1 == 'out', mace_right=right(p['mace'], p['dft']),
                               c_right=right(p[c], p['dft'])))
        mw = [r for r in rows_c if r['mace_out'] and r['mace_right'] is False]; mr = [r for r in rows_c if r['mace_out'] and r['mace_right']]
        mr_all = [r for r in rows_c if r['mace_right']]
        cls[c] = dict(band=b2, n=len(rows_c), AGREE=sum(r['cls'] == 'AGREE' for r in rows_c), SPLIT=sum(r['cls'] == 'SPLIT' for r in rows_c),
                      SOFT=sum(r['cls'] == 'SOFT' for r in rows_c),
                      AGREE_wrong=sum(r['cls'] == 'AGREE' and r['mace_right'] is False for r in rows_c),
                      catch_rate=dict(caught=sum(r['cls'] in ('SPLIT', 'SOFT') for r in mw), of=len(mw)),
                      false_alarm_outside_correct=dict(flagged=sum(r['cls'] in ('SPLIT', 'SOFT') for r in mr), of=len(mr)),
                      false_alarm_all_correct=dict(flagged=sum(r['cls'] in ('SPLIT', 'SOFT') for r in mr_all), of=len(mr_all)),
                      split_pairs=[r for r in rows_c if r['cls'] == 'SPLIT'])
    out['classes_162'] = cls
    if win:
        n_split = cls[win]['SPLIT']; rate = n_split / max(1, cls[win]['n'])
        out['gate_A0'] = dict(winner=win, split_pairs=n_split, passes=n_split >= 5, split_rate=round(rate, 4),
                              expected_split_in_60_compounds=round(60 * rate, 1))
    json.dump(out, open(os.path.join(od, 'dev_second_fm.json'), 'w'), indent=1)
    print(json.dumps({k: out[k] for k in ('mace_polymorph_gap_mae', 'best_polymorph_gap_mae', 'R2_cap', 'eligible', 'winner', 'm_star_2', 'mace_baseline_162', 'gate_A0') if k in out}, indent=1))
    for c in CANDS: print(c, {k: v for k, v in res[c].items()}, {k: v for k, v in cls[c].items() if k != 'split_pairs'})


if __name__ == '__main__':
    main()
