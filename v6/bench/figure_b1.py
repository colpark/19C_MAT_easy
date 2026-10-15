"""B1 V6-11 figure: the Sonnet FM gap per compound (fm minus noprior pair resolution over k = 1..4), sorted, coloured by stratum (K: the
heuristic panel fails the pair; E: it resolves it), FM status marked under each bar.
  python v6/bench/figure_b1.py ANALYSIS.json OUT.png"""
import json, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

a = json.load(open(sys.argv[1]))['models']['sonnet']
pc = sorted(a['per_compound'].values(), key=lambda r: (r['gap'], r['stratum']))
col = {'K': '#c0392b', 'E': '#2471a3'}; mark = {'right': '', 'in band': 'b', 'wrong': 'w'}
fig, ax = plt.subplots(figsize=(11, 4.2))
xs = range(len(pc))
ax.bar(xs, [r['gap'] for r in pc], color=[col[r['stratum']] for r in pc])
ax.axhline(0, color='k', lw=0.8)
ax.set_xticks(list(xs)); ax.set_xticklabels([f"{r['formula']}{' (' + mark[r['fm_status']] + ')' if mark[r['fm_status']] else ''}" for r in pc], rotation=75, fontsize=7)
ax.set_ylabel('FM gap (pair resolution, fm - noprior)'); ax.set_ylim(-1.05, 1.05)
ax.set_title(f"B1: Sonnet FM gap per compound (overall {a['gap_overall']:+.2f}, 95 % CI {a['ci95'][0]:+.2f} to {a['ci95'][1]:+.2f}; "
             f"K {a['gap_K']:+.2f}, E {a['gap_E']:+.2f})", fontsize=9)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=col['K'], label='K: panel fails'), Patch(color=col['E'], label='E: panel resolves')], fontsize=8, loc='upper left')
ax.text(0.99, 0.02, '(b) FM in band, (w) FM wrong', transform=ax.transAxes, ha='right', fontsize=7)
fig.tight_layout(); fig.savefig(sys.argv[2], dpi=150)
print('saved', sys.argv[2])
