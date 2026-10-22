"""V7-G4 figures from analyzeG.py's output: (1) fresh T, every arm on the 30 fresh quads at k = 1, per quad and per world (evidence key,
registered key hatched); (2) offline against online, per family: Sonnet fm (online) against each S-llm program and the mean of 5, round G
(corrected) and round F3 (compromised by V7-E4), evidence key, k = 1 on Sonnet fm's compounds.
  python v7/figG.py ANALYSIS_G.json OUTDIR"""
import json, os, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
A = json.load(open(sys.argv[1])); OUT = sys.argv[2]
F = A['fresh_T']; arms = ['sonnet-fm', 'fm-hint', 's-broad', 's-neutron', 's-plan', 'gold-oracle (ceiling, k 1)']
fig, axs = plt.subplots(1, 2, figsize=(10, 3.6), sharey=True)
for ax, (key, title) in zip(axs, (('per_quad', 'per quad'), ('per_world', 'per world'))):
    xs = [a for a in arms if (F[key].get(a) or {}).get('evidence') is not None]
    ev = [F[key][a]['evidence'] for a in xs]; rg = [F[key][a]['registered'] for a in xs]
    ax.bar([i - 0.2 for i in range(len(xs))], ev, 0.4, color='#3b6ea5', label='evidence key')
    ax.bar([i + 0.2 for i in range(len(xs))], rg, 0.4, color='#c0c0c0', label='registered key')
    ax.set_xticks(range(len(xs))); ax.set_xticklabels([x.replace(' (ceiling, k 1)', '\n(ceiling)') for x in xs], fontsize=8, rotation=20)
    ax.set_ylim(0, 1); ax.set_title(f'fresh T (30 quads, k = 1): {title}', fontsize=10)
axs[0].set_ylabel('resolution rate'); axs[1].legend(fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(OUT, 'fig_G_fresh_T.png'), dpi=140); plt.close(fig)
O = A['offline_vs_online']
fig, axs = plt.subplots(1, 3, figsize=(10.5, 3.6), sharey=True)
for ax, fam in zip(axs, ('B1', 'H', 'T')):
    o = O[fam]
    for x, (rnd, col) in enumerate((('G (corrected)', '#3b6ea5'), ('F3 (compromised by V7-E4)', '#b0b0b0'))):
        if rnd not in o: continue
        v = [p['evidence'] for p in o[rnd]['programs'].values()]
        ax.scatter([x + 1 + 0.06 * (j - 2) for j in range(len(v))], v, color=col, s=28, zorder=3)
        ax.hlines(sum(v) / len(v), x + 0.75, x + 1.25, color='k', lw=2, zorder=4)
    ax.bar([0], [o['sonnet-fm']['evidence']], 0.5, color='#d98c3f')
    ax.set_xticks([0, 1, 2]); ax.set_xticklabels(['Sonnet fm\n(online)', 'S-llm G\n(corrected)', 'S-llm F3\n(V7-E4)'], fontsize=8)
    ax.set_ylim(0, 1); ax.set_title(f"{fam} ({o['compounds']} compounds, k = 1)", fontsize=10)
axs[0].set_ylabel('resolution rate, evidence key\n(dots: programs; bar: mean of 5)')
fig.tight_layout(); fig.savefig(os.path.join(OUT, 'fig_G_offline_online.png'), dpi=140); plt.close(fig)
print('figures written')
