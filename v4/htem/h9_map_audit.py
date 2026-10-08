# h9_map_audit.py (Track H, H9): audit of the H8 map items (v4_host/htem/items_H8 items as committed at c211c3f7, old white labels).
# Ideal colour-bar reader on the exported JPEG (q95) of each map item: locates square A and the colour bar via probe renders
# (same figure geometry), samples square A away from the label, inverts through the colour bar column. Reports |err|/span vs tol 0.02.
import io, json, math, os, sys
import numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from PIL import Image
sys.path.insert(0, os.path.expanduser('~/Documents/harbor_htem/v4/htem'))
import generate_htem as G, render as RD, htem_api as API
def fig_png(xy, v, vmin, vmax, cmap, annot, label, colors=None):
    with plt.rc_context(RD.RC):
        fig, ax = plt.subplots(figsize=(3.8, 1.9)); xy = np.asarray(xy, float)
        kw = dict(c=v, cmap=cmap, vmin=vmin, vmax=vmax) if colors is None else dict(c=colors)
        sc = ax.scatter(xy[:, 0], xy[:, 1], s=70, marker='s', edgecolors='k', linewidths=0.3, **kw)
        if colors is not None: sc = matplotlib.cm.ScalarMappable(norm=matplotlib.colors.Normalize(vmin, vmax), cmap=cmap)
        for (a, b), t in zip(xy, annot):
            if t: ax.text(a, b, t, ha='center', va='center', fontsize=6, color='w', fontweight='bold')
        ax.set_xlabel('x (mm)'); ax.set_ylabel('y (mm)'); ax.set_aspect('equal'); cb = fig.colorbar(sc, ax=ax, shrink=0.85); cb.set_label(label, fontsize=7)
        buf = io.BytesIO(); fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.04); plt.close(fig)
    return np.asarray(Image.open(buf).convert('RGB')).astype(int)
def jpg(a):
    b = io.BytesIO(); Image.fromarray(a.astype(np.uint8)).save(b, format='JPEG', quality=95); return np.asarray(Image.open(b).convert('RGB')).astype(int)
out = []
for role in ('P1', 'P2'):
    IC = G.CFG['items'][role]; pl = json.load(open(os.path.join(API.HOST, 'census', 'PILOT_LIBS.json')))[role]
    cells = [json.loads(l) for l in open(os.path.join(API.HOST, 'matrix', role, 'cells.jsonl'))]
    import subprocess
    for l in subprocess.run(['git', '-C', os.path.dirname(os.path.abspath(__file__)), 'show', f'c211c3f7:v4/htem/items/{role}/items.jsonl'], capture_output=True, text=True, check=True).stdout.splitlines():
        it = json.loads(l); ds = it['provenance'].get('design', {}); q = ds.get('quantity')
        if q not in ('Rs', 'fraction'): continue
        lib, pos = it['provenance']['fact'].split('|')[-1].split(':'); lib = int(lib) if lib.isdigit() else lib; pos = int(pos)
        cs = sorted([c for c in cells if str(c['library']) == str(lib)], key=lambda c: c['position'])
        xy = [c['xyz_mm'][:2] if c.get('xyz_mm') else None for c in cs]
        if q == 'Rs':
            vals = [c['derived'].get('Rs_ohm_sq') if (c['derived'].get('Rs_r2') or 0) > 0.99 else None for c in cs]
            ok = [i for i, (a, b) in enumerate(zip(xy, vals)) if a is not None and b and b > 0]; v = [math.log10(vals[i]) for i in ok]; cmap = 'magma'
            label = 'log10 sheet resistance (ohm/sq)'; key = math.log10(it['expected']['value'])
        else:
            vals = [(c['M'].get('cation_frac') or {}).get(IC['cation']) for c in cs]
            ok = [i for i, (a, b) in enumerate(zip(xy, vals)) if a is not None and b is not None]; v = [vals[i] for i in ok]; cmap = 'viridis'
            label = f"{IC['cation']} / ({IC['cation']} + {IC['partner']})"; key = it['expected']['value']
        lo, hi = ds['axis']; ia = [k for k, i in enumerate(ok) if cs[i]['position'] == pos][0]
        annot = ['A' if k == ia else '' for k in range(len(ok))]; P = [xy[i] for i in ok]
        real = jpg(fig_png(P, v, lo, hi, cmap, annot, label))
        # probe 1: A square red, others white -> mask of A; probe 2: colour bar pure green cmap
        cols = [(1, 0, 0) if k == ia else (1, 1, 1) for k in range(len(ok))]
        p1 = fig_png(P, v, lo, hi, ListedColormap([(1, 1, 1)]), [''] * len(ok), label, colors=cols)
        p2 = fig_png(P, v, lo, hi, ListedColormap([(0, 1, 0)]), [''] * len(ok), label, colors=[(1, 1, 1)] * len(ok))
        assert p1.shape == real.shape == p2.shape, (p1.shape, real.shape)
        ma = (p1[..., 0] > 200) & (p1[..., 1] < 60) & (p1[..., 2] < 60)
        yy, xx = np.nonzero(ma); cy, cx = yy.mean(), xx.mean(); r = np.hypot(yy - cy, xx - cx)
        ring = r > 0.45 * r.max()   # away from the label glyph
        a_rgb = np.median(real[yy[ring], xx[ring]], axis=0)
        mg = (p2[..., 1] > 200) & (p2[..., 0] < 60) & (p2[..., 2] < 60); gy, gx = np.nonzero(mg)
        col = int(np.median(gx)); rows = np.arange(gy.min() + 1, gy.max())
        bar = real[rows, col]; vals_bar = hi - (rows - gy.min()) / (gy.max() - gy.min()) * (hi - lo)
        read = vals_bar[np.argmin(((bar - a_rgb) ** 2).sum(1))]
        clipped = not (lo <= key <= hi)
        e = abs(read - key) / (hi - lo); out.append({'id': it['id'], 'q': q, 'err_span': e, 'clipped': clipped, 'pass': e <= 0.02, 'pass05': e <= 0.05, 'npix': int(ring.sum())})
        print(it['id'], q, 'key %.3f read %.3f err/span %.3f' % (key, read, e), 'CLIPPED' if clipped else '', 'ok' if e <= 0.02 else '')
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'H9_MAP_AUDIT.json'), 'w'), indent=0, default=lambda o: o.item())
for q in ('Rs', 'fraction'):
    s = [o for o in out if o['q'] == q and not o['clipped']]
    print(q, 'n', len(s), 'pass@0.02', sum(o['pass'] for o in s), 'pass@0.05', sum(o['pass05'] for o in s), 'median err/span %.3f' % np.median([o['err_span'] for o in s]))
