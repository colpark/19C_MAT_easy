"""Stage 2s DIFFICULTY.md and CONSTRAINTS.md from the final tune2s output (V5_SPEC E.3, E.4).
  python -m mcenv.difficulty2s CONSTRAINTS.json stage2s/DIFFICULTY.md stage2s/validation/CONSTRAINTS.md"""
import json, sys


def fm(m):
    if m['radiation'] == 'neutron': return 'neutron pattern'
    hi = m['start'] + m['step'] * (m['n'] - 1)
    return f"{m['start']:.2f}-{hi:.2f} deg at {m['step']} deg, {m['t']:.2f} s, {m['optics'].replace('_', ' ')}{', Si standard' if m['si_standard'] else ''}"


def main():
    C = json.load(open(sys.argv[1]))['scen']
    L = ['# Stage 2s difficulty (V5_SPEC E.3, E.4)\n', 'Costs in minutes with the stage 2s cost model (10-min overhead per measurement, neutron 125 min). '
         'c_dec: cheapest plan with planning D >= 40 in both worlds (alternatives\' lattices free within +-1 %). c_loc: cheapest 60-degree survey '
         'with 2 sigma(lattice_scale) <= 1 % (Cramer-Rao, every nuisance free). c_loc|dec: cheapest further plan after that survey. c_pla: the plan a '
         'placebo-quality hypothesis chooses within B, with its key D on each true world. Slack = B - c_dec.\n',
         '| scenario | N | B | c_dec | c_dec plan | D_key of c_dec plan (worlds) | c_loc (survey) | default survey: cost, 2 sigma, D_key | c_loc + c_loc|dec | c_pla, D_key on true worlds | slack |',
         '|---|---|---|---|---|---|---|---|---|---|---|']
    K = ['\n# Stage 2s constraints (V5_SPEC E.4)\n', '| scenario | T1 (1.2 c_dec <= B <= 1.3 c_dec) | T2 (c_loc + c_dec > B) | T2\' (c_loc + c_loc|dec > B) | T3 (placebo plan D < 9) | control C1s |', '|---|---|---|---|---|---|']
    for s, r in sorted(C.items(), key=lambda kv: int(kv[0])):
        cd = r['c_dec']; cl = r.get('c_loc'); ld = r.get('c_loc_dec'); cp = r.get('c_pla'); ds = r['default_survey']
        L.append(f"| {s} | {r['tune']['N']:g} | {r['budget']:g} | {cd and cd['cost']} | {cd and '; '.join(fm(m) for m in cd['plan'])} | "
                 f"{cd and cd.get('D_key_per_world')} | {cl and cl['cost']} ({cl and fm(cl['meas'])}) | {ds['cost']}, {ds['two_sigma']}, {ds.get('D_key_per_world')} | "
                 f"{(cl['cost'] + ld['cost']) if (cl and ld) else ('no further plan' if cl and 'c_loc_dec' in r else None)} | "
                 f"{(cp['cost'], cp['D_key_true']) if cp else 'none within B (spends nothing, D = 0)'} | {cd and round(r['budget'] - cd['cost'], 2)} |")
        ch = r['checks']
        K.append(f"| {s} | {ch.get('T1', '-')} | {ch.get('T2', '-')} | {ch.get('T2p', '-')} | {ch.get('T3', '-')} | {ch.get('C1s', '-')} |")
    open(sys.argv[2], 'w').write('\n'.join(L) + '\n')
    open(sys.argv[3], 'w').write('\n'.join(K) + '\n')
    print('\n'.join(L + K))


if __name__ == '__main__':
    main()
