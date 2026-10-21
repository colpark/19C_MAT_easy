"""V7-F6 figures: one per family, the baseline ladder (unit resolution per arm, evidence key and registered key, k = 1 where the arm
has only k = 1, all k otherwise), from analyzeF.py's output.
  python v7/figF.py ANALYSIS.json OUTDIR"""
import json, os, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
A = json.load(open(sys.argv[1])); OUT = sys.argv[2]
ORDER = ['blind-FM (floor)', 'qwen3-8b-noprior', 'qwen3-8b-fm', 'haiku-noprior', 'haiku-fm', 'sonnet-noprior', 'opus-noprior', 'sonnet-fm',
         'opus-fm', 'sonnet-fm-planner', 'fm-hint', 'sllm-mean', 's-broad', 's-neutron', 's-plan', 'gold-oracle (ceiling, k 1)']
NAME = {'B1': 'B1 (claim R): pair resolution', 'H': 'H (hull): pair resolution', 'T': 'T (transformation): quad resolution'}
for fam in ('B1', 'H', 'T'):
    L = dict(A[fam]['ladder_matched_k1']['arms']); nC = len(A[fam]['ladder_matched_k1']['compounds'])
    sl = [a for a in L if a.startswith('sllm-')]
    if sl:
        L['sllm-mean'] = dict(evidence=sum(L[a]['evidence'] for a in sl) / len(sl), registered=sum(L[a]['registered'] for a in sl) / len(sl))
    arms = [a for a in ORDER if a in L] + sorted(sl)
    ev = [L[a]['evidence'] or 0 for a in arms]; rg = [L[a]['registered'] or 0 for a in arms]
    fig, ax = plt.subplots(figsize=(7.5, 0.32 * len(arms) + 1.4))
    y = range(len(arms))
    ax.barh([i + 0.2 for i in y], ev, 0.4, label='evidence key', color='#3b6ea5')
    ax.barh([i - 0.2 for i in y], rg, 0.4, label='registered key', color='#c0c0c0')
    ax.set_yticks(list(y)); ax.set_yticklabels(arms, fontsize=8); ax.invert_yaxis(); ax.set_xlim(0, 1)
    ax.set_xlabel('resolution rate (mean over compounds)', fontsize=8); ax.set_title(f"{NAME[fam]}, k = 1, Sonnet fm's {nC} compounds", fontsize=10)
    ax.legend(fontsize=8, loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f'fig_F_{fam}.png'), dpi=140); plt.close(fig)
    print('wrote', fam)
