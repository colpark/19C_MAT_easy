#!/usr/bin/env python3
"""validate_readers.py: synthetic gates for the three readers on fresh seeds (skill M2, I7). Gates come from config.json gates and are
frozen with the readers (labels H4x, H4o, H4f). Writes $HTEM_HOST/validation/synthetic.json.

  XRD:     on peaks with SNR >= 10, |center error| <= xrd_pos_deg for >= xrd_pos_frac of peaks, |FWHM error| <= xrd_fwhm_rel for the median.
           Amorphous patterns: >= xrd_amorphous_frac must return no peak above 2 * min_snr.
  Optical: eg_seeds fresh seeds with Eg inside the measured range: >= eg_seeds_pass within eg_ev after removing the median bias,
           and the bias SD across seeds <= eg_bias_sd_ev (a constant bias is allowed and reported). Censoring: a gap above the range is flagged.
  FPM:     |Rs error| <= rs_rel on every seed.
  XRD broad (FWHM 0.8 to 2.0 deg): center within xrd_broad_pos_deg for >= xrd_broad_pos_frac, median FWHM error <= xrd_broad_fwhm_rel.
Fresh seeds start at config fresh_seed_base. Draw a new base at freeze time and record it with the freeze, so the gate seeds were never
seen while tuning. Dev seeds: 0 to 99.
usage: validate_readers.py [--seeds dev|fresh] [--fresh-base N]
"""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import synth as SY
from readers import xrd as RX, optical as RO, fpm as RF

CFG = json.load(open(os.path.join(HERE, 'config.json')))
G = CFG['gates']


def xrd_gate(seeds, broad=False):
    errs, fw, amorph_ok = [], [], 0
    for s in seeds:
        x, y, truth = SY.xrd_pattern(s, broad=broad)
        got = RX.read(x, y, CFG['readers']['xrd'])['peaks']
        for t in truth:
            snr_t = t['height'] / max(1.0, np.sqrt(t['height']))
            if snr_t < 10:
                continue
            if not got:
                errs.append(np.inf)
                continue
            p = min(got, key=lambda q: abs(q['center'] - t['center']))
            errs.append(abs(p['center'] - t['center']) if abs(p['center'] - t['center']) < 0.5 else np.inf)
            if abs(p['center'] - t['center']) < 0.5:
                fw.append(abs(p['fwhm'] - t['fwhm']) / t['fwhm'])
        xa, ya, _ = SY.xrd_pattern(s, amorphous=True)
        ga = RX.read(xa, ya, CFG['readers']['xrd'])['peaks']
        amorph_ok += not any(p['snr'] > 2 * CFG['readers']['xrd']['min_snr'] for p in ga)
    errs = np.array(errs)
    if broad:
        frac = float(np.mean(errs <= G['xrd_broad_pos_deg'])) if errs.size else 0.0
        med_fw = float(np.median(fw)) if fw else None
        return {'peaks': int(errs.size), 'pos_within_frac': round(frac, 4), 'median_fwhm_rel_err': None if med_fw is None else round(med_fw, 4),
                'pass': bool(frac >= G['xrd_broad_pos_frac'] and med_fw is not None and med_fw <= G['xrd_broad_fwhm_rel'])}
    frac = float(np.mean(errs <= G['xrd_pos_deg'])) if errs.size else 0.0
    med_fw = float(np.median(fw)) if fw else None
    return {'peaks': int(errs.size), 'pos_within_frac': round(frac, 4), 'median_fwhm_rel_err': None if med_fw is None else round(med_fw, 4),
            'amorphous_clean': f'{amorph_ok}/{len(seeds)}',
            'pass': bool(frac >= G['xrd_pos_frac'] and med_fw is not None and med_fw <= G['xrd_fwhm_rel']
                         and amorph_ok >= G.get('xrd_amorphous_frac', 0.95) * len(seeds))}


def optical_gate(seeds):
    rows = []
    for s in seeds:
        op, truth = SY.optical_spectra(s)
        r = RO.read(op, truth['thickness_um'], CFG['readers']['optical'])
        rows.append({'seed': s, 'Eg_true': truth['Eg'], 'Eg': r.get('Eg'), 'censored': r.get('censored')})
    ok = [r for r in rows if r['Eg'] is not None and not r['censored']]
    err = np.array([r['Eg'] - r['Eg_true'] for r in ok])
    bias = float(np.median(err)) if err.size else None
    within = int(np.sum(np.abs(err - bias) <= G['eg_ev'])) if err.size else 0
    sd = float(np.std(err)) if err.size else None
    op, truth = SY.optical_spectra(seeds[0] + 5000, eg=4.6)
    cens = RO.read(op, truth['thickness_um'], CFG['readers']['optical'])
    return {'rows': rows, 'bias_ev': bias, 'bias_sd_ev': sd, 'within': f'{within}/{len(seeds)}',
            'censor_flagged_above_range': bool(cens.get('censored') or cens.get('Eg') is None),
            'pass': bool(within >= G['eg_seeds_pass'] and sd is not None and sd <= G['eg_bias_sd_ev']
                         and (cens.get('censored') or cens.get('Eg') is None))}


def fpm_gate(seeds):
    errs = []
    for s in seeds:
        fp, truth = SY.iv_points(s, gf=CFG['readers']['fpm']['geometry_factor'])
        r = RF.read(fp, None, CFG['readers']['fpm'])
        errs.append(abs(r['Rs_ohm_sq'] - truth['Rs']) / truth['Rs'])
    return {'max_rel_err': float(max(errs)), 'pass': bool(max(errs) <= G['rs_rel'])}


def main(argv):
    fresh = '--seeds' not in argv or argv[argv.index('--seeds') + 1] == 'fresh'
    base = int(argv[argv.index('--fresh-base') + 1]) if '--fresh-base' in argv else CFG['fresh_seed_base']
    seeds = list(range(base, base + G['eg_seeds'])) if fresh else list(range(0, 100))
    out = {'seeds': 'fresh' if fresh else 'dev', 'seed_list': [seeds[0], seeds[-1]], 'xrd': xrd_gate(seeds),
           'xrd_broad': xrd_gate(seeds, broad=True), 'optical': optical_gate(seeds), 'fpm': fpm_gate(seeds)}
    out['all_pass'] = all(out[k]['pass'] for k in ('xrd', 'xrd_broad', 'optical', 'fpm'))
    host = os.environ.get('HTEM_HOST')
    if host:
        os.makedirs(os.path.join(host, 'validation'), exist_ok=True)
        json.dump(out, open(os.path.join(host, 'validation', f"synthetic_{out['seeds']}.json"), 'w'), indent=1)
    print(json.dumps({k: (v if k != 'optical' else {kk: vv for kk, vv in v.items() if kk != 'rows'}) for k, v in out.items()}, indent=1))
    return 0 if out['all_pass'] else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
