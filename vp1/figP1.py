"""vP.1 figures from analyzeP1.py's output. Every mark is a contrast with its 95 % bootstrap interval; the dashed line is zero.
  1. fig_P1_offline_online.png: rows Sonnet, Haiku, Qwen3-8B; columns B1, H, T. Offline minus the same model online for the cross-fitted
     program, the mean of five and the post hoc best (chosen inside every replicate). Evidence key filled, registered key hollow.
  2. fig_P1_manipulations.png: fm-late, fit-once and fm-flip minus Sonnet fm (k 1), for B1, H and the family-weighted pool.
Colors: the first slots of the dataviz reference categorical palette, in fixed order (the validator script needs node, which host A
lacks; the slots are the palette's validated default). Key is encoded by fill as well as by legend, so it never rests on color alone.
  python vp1/figP1.py ANALYSIS.json OUTDIR"""
import json, os, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

A = json.load(open(sys.argv[1])); OUT = sys.argv[2]
COL = ['#2a78d6', '#eb6834', '#1baf7a']
INK, MUTED, SURF = '#0b0b0b', '#52514e', '#fcfcfb'
plt.rcParams.update({'font.size': 8, 'axes.edgecolor': MUTED, 'axes.labelcolor': INK, 'xtick.color': MUTED, 'ytick.color': MUTED,
                     'figure.facecolor': SURF, 'axes.facecolor': SURF})


def point(ax, x, c, color, filled):
    if not c: return
    lo, hi = c['ci95']
    ax.plot([x, x], [lo, hi], color=color, lw=2, solid_capstyle='round', zorder=2)
    ax.scatter([x], [c['gap']], s=40, color=color if filled else SURF, edgecolors=color, linewidths=2, zorder=3)


def style(ax):
    ax.axhline(0, color=MUTED, lw=1, ls='--', zorder=1)
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
    ax.set_xlim(-0.5, 2.5)
    ax.grid(axis='y', color='#e6e5e1', lw=0.6); ax.set_axisbelow(True)


# ---------------------------------------------------------------- 1. offline against online
O = A['offline_vs_online']; models = [('sonnet', 'Sonnet'), ('haiku', 'Haiku'), ('qwen', 'Qwen3-8B')]
kinds = ['cross-fitted minus online', 'mean of five minus online', 'post hoc best minus online']
fig, axs = plt.subplots(3, 3, figsize=(9, 7.2), sharey=True)
for i, (m, mname) in enumerate(models):
    for j, fam in enumerate(('B1', 'H', 'T')):
        ax = axs[i][j]; style(ax); f = O.get(m, {}).get(fam, {})
        for x, kd in enumerate(kinds):
            point(ax, x - 0.12, (f.get('ev') or {}).get(kd), COL[x], True)
            point(ax, x + 0.12, (f.get('reg') or {}).get(kd), COL[x], False)
        ax.set_xticks(range(3)); ax.set_xticklabels(['cross-fitted', 'mean of 5', 'post hoc best'] if i == 2 else ['', '', ''])
        r = (f.get('rates') or {}).get('ev') or {}
        ax.set_title(f'{mname}, {fam}' + (f"   online {r['online']:.2f}" if r.get('online') is not None else '   (missing)'), fontsize=8, color=INK)
        if j == 0: ax.set_ylabel('offline minus online\n(unit resolution)')
h = [axs[0][0].scatter([], [], color=MUTED, s=40), axs[0][0].scatter([], [], color=SURF, edgecolors=MUTED, linewidths=2, s=40)]
fig.legend(h, ['evidence key', 'registered key'], loc='lower center', ncol=2, fontsize=7, frameon=False)
fig.suptitle('The same model offline (a program it wrote) minus online (acting in the loop); 95 % bootstrap intervals', fontsize=9, color=INK)
fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(os.path.join(OUT, 'fig_P1_offline_online.png'), dpi=150); plt.close(fig)

# ---------------------------------------------------------------- 2. manipulations
M = A['manipulations']; arms = ['fm-late', 'fit-once', 'fm-flip']
fig, axs = plt.subplots(1, 3, figsize=(9, 3.2), sharey=True)
for ax, (fam, title) in zip(axs, (('B1', 'B1'), ('H', 'H'), ('pooled (family-weighted)', 'B1 and H, family-weighted'))):
    style(ax)
    for x, a in enumerate(arms):
        d = M.get(a, {}).get(fam) or {}
        ev = d.get('ev') if fam.startswith('pooled') else (d.get('ev') or {}).get('contrast')
        rg = d.get('reg') if fam.startswith('pooled') else (d.get('reg') or {}).get('contrast')
        point(ax, x - 0.12, ev, COL[x], True); point(ax, x + 0.12, rg, COL[x], False)
    ax.set_xticks(range(3)); ax.set_xticklabels(arms); ax.set_title(title, fontsize=8, color=INK)
axs[0].set_ylabel('manipulated minus Sonnet fm\n(unit resolution, k 1)')
h = [axs[0].scatter([], [], color=MUTED, s=40), axs[0].scatter([], [], color=SURF, edgecolors=MUTED, linewidths=2, s=40)]
fig.legend(h, ['evidence key', 'registered key'], loc='lower center', ncol=2, fontsize=7, frameon=False)
fig.tight_layout(rect=(0, 0.07, 1, 1)); fig.savefig(os.path.join(OUT, 'fig_P1_manipulations.png'), dpi=150); plt.close(fig)
print('figures written to', OUT)
