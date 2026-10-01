#!/usr/bin/env python3
"""quality_v022.py: quality measures for PanelBench v0.22 (94 published Acta Materialia papers). Script only;
prints markdown tables, no extracted text.

Q1 run: MinerU success per paper.
Q2 extraction: MinerU words vs kept paragraph words, paragraph sizes, Introduction heading, skipped block types.
Q3 sentence integrity vs publisher text: sentences (>= 10 words) from MatMech `image_description` (publisher full-text
   passages citing each figure). Test identical to quote_integrity.py: normalised head and tail 30-char anchors in ONE
   paragraph = one; either anchor somewhere = across; neither = missing.
Q4 figure capture: MatMech figures vs MinerU figures (captioned, caption source).
Q5 panel stores: tiers, accepted panels, OCR letter agreement, for the MatMech and the MinerU store.
Q6 items per store: counts per level, papers with items, overlap, L1 key visible elsewhere in the question (leak),
   and source check: share of items whose source sentence is found in the publisher text (head+tail anchors).
"""
import collections, glob, json, os, re, statistics, sys, unicodedata
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
K = json.load(open('paper_keys.json'))
LIG = {'ﬁ': 'fi', 'ﬂ': 'fl', 'ﬀ': 'ff', 'ﬃ': 'ffi', 'ﬄ': 'ffl'}
GREEK = {'α':'alpha','β':'beta','γ':'gamma','μ':'mu','σ':'sigma','κ':'kappa','ρ':'rho','θ':'theta','λ':'lambda','Δ':'delta','δ':'delta','Ω':'omega','ω':'omega','π':'pi','τ':'tau','χ':'chi','ν':'nu','η':'eta','ε':'epsilon'}
def norm(s):   # identical to v02/work/quote_integrity.py
    for a, b in LIG.items(): s = s.replace(a, b)
    s = re.sub(r'\\(text|mathrm|mathbf|mathit|rm)\s*', ' ', s); s = re.sub(r'\\rightarrow|\\to', '', s)
    s = re.sub(r'\\(alpha|beta|gamma|mu|sigma|kappa|rho|theta|lambda|delta|Delta|omega|Omega|pi|tau|chi|nu|eta|epsilon)', lambda m: m.group(1).lower(), s)
    s = re.sub(r'\\(bar|equiv|sim|le|ge|pm)\b', '', s).replace('\\%', '')
    for a, b in GREEK.items(): s = s.replace(a, b)
    s = unicodedata.normalize('NFKD', s)
    return re.sub(r'[^a-z0-9]', '', s.lower())
SPLIT = re.compile(r'(?<=[.?!])\s+(?=[A-Z(])')
FIG = re.compile(r'^\s*(?:Fig\.?|Figure)\s*(\d+)', re.I)
def paras(k): p = f'work/{k}.paras.json'; return json.load(open(p))['paras'] if os.path.exists(p) else None
def cl(k):
    p = f"mineru_out/{K[k]['safe']}/auto/{K[k]['safe']}_content_list.json"; return json.load(open(p)) if os.path.exists(p) else None
def pubsents(k):
    d = json.load(open(K[k]['matmech_folder'] + '/data.json')); out = []
    for im in d.get('image_info') or []:
        for psg in im.get('image_description') or []:
            out += [s for s in SPLIT.split(' '.join(psg.split())) if len(s.split()) >= 10]
    return list(dict.fromkeys(out))
pct = lambda a, b: f'{100 * a / b:.1f}%' if b else '-'
out = ['# PanelBench v0.22 quality report (94 published Acta Materialia papers)\n']

# Q1, Q2
ok = [k for k in K if cl(k) is not None]
out += ['## Q1 MinerU run\n', f'- PDFs: {len(K)}, pages {sum(v["pages"] for v in K.values())}; MinerU content_list produced: **{len(ok)} / {len(K)}**\n']
win = wkeep = 0; npar = []; plen = []; intro = 0; low = 0; skipped = collections.Counter(); per = []
for k in ok:
    B = cl(k); P = paras(k) or []
    a = sum(len((b.get('text') or '').split()) for b in B if b['type'] == 'text'); b_ = sum(len(p['text'].split()) for p in P)
    win += a; wkeep += b_; npar.append(len(P)); plen += [len(p['text'].split()) for p in P]
    intro += any((b.get('text_level') or 0) >= 1 and 'Introduction' in (b.get('text') or '') for b in B)
    low += b_ < 0.2 * a; per.append(b_ / a if a else 0)
    for x in B:
        if x['type'] != 'text': skipped[x['type']] += 1
n = len(ok)
out += ['## Q2 Extraction\n', '| Measure | Value |', '|---|---|',
        f'| MinerU text words per paper (mean) | {win / n:.0f} |', f'| Kept body words per paper (mean) | {wkeep / n:.0f} |',
        f'| Kept share (all words) | {pct(wkeep, win)} |', f'| Kept share per paper (median) | {100 * statistics.median(per):.0f}% |',
        f'| Papers keeping under 20% of words | {low} |', f'| Papers with an "Introduction" heading | {intro} / {n} |',
        f'| Paragraphs per paper (median) | {statistics.median(npar):.0f} |',
        f'| Paragraph length, words (median / p95 / max) | {statistics.median(plen):.0f} / {sorted(plen)[int(.95 * len(plen))]} / {max(plen)} |',
        f'| Paragraphs of 500+ words | {sum(1 for x in plen if x >= 500)} |',
        '| Non-text blocks skipped | ' + ', '.join(f'{t} {c}' for t, c in skipped.most_common()) + ' |', '']

# Q3
T = collections.Counter(); perpaper = []
for k in ok:
    P = [norm(p['text']) for p in paras(k) or []]; allp = ''.join(P); c = collections.Counter()
    for s in pubsents(k):
        q = norm(s); h, t = q[:30], q[-30:]
        if any(h in p and t in p for p in P): c['one'] += 1
        elif h in allp and t in allp: c['split'] += 1
        elif h in allp or t in allp: c['one_anchor'] += 1
        else: c['missing'] += 1
    T.update(c); tot = sum(c.values())
    if tot: perpaper.append(c['one'] / tot)
tt = sum(T.values())
out += ['## Q3 Sentence integrity against publisher text\n',
        'Reference: publisher sentences (10+ words) from MatMech `image_description` (body passages citing each figure). Same test as `quote_integrity.py` (v0.1: 188/203 = 92.6%; v0.2 MinerU: 198/203 = 97.5%, six papers, hand-verified quotes).\n',
        '| | Sentences | Share |', '|---|---|---|', f"| whole in one paragraph | {T['one']} | **{pct(T['one'], tt)}** |",
        f"| split across paragraphs (both anchors found, different paragraphs) | {T['split']} | {pct(T['split'], tt)} |",
        f"| one anchor only (PDF wording differs from publisher HTML) | {T['one_anchor']} | {pct(T['one_anchor'], tt)} |", f"| missing (neither anchor found) | {T['missing']} | {pct(T['missing'], tt)} |",
        f"| **paragraph integrity: whole / (whole + split)** | {T['one']} / {T['one'] + T['split']} | **{pct(T['one'], T['one'] + T['split'])}** |",
        f'| total reference sentences | {tt} | |', '',
        f'Per paper, share whole in one paragraph: median {100 * statistics.median(perpaper):.0f}%, papers under 80%: {sum(1 for x in perpaper if x < .8)} of {len(perpaper)}.\n']

# Q4
mm = mi = cap = 0; src = collections.Counter()
for k in ok:
    mm += len(json.load(open(K[k]['matmech_folder'] + '/data.json')).get('image_info') or [])
    p = f'store/Acta_Materialia/{k}/data.json'
    if os.path.exists(p):
        info = json.load(open(p))['image_info']; mi += len(info); src.update(x['caption_source'] for x in info)
out += ['## Q4 Figure capture\n', '| | Figures |', '|---|---|', f'| MatMech (publisher) figures | {mm} |', f'| MinerU figures with a "Fig. N" caption | {mi} ({pct(mi, mm)}) |',
        '| caption source | ' + ', '.join(f'{s} {c}' for s, c in src.most_common()) + ' |', '']

# Q5
def store_stats(fold):
    c = collections.Counter()
    for k in ok:
        mp = fold(k) + '/panels/match.json'
        if not os.path.exists(mp): c['no_match_json'] += 1; continue
        for f in json.load(open(mp))['figures']:
            c['figures'] += 1; c['tier_' + f['tier']] += 1
            for p in f['panels']:
                c['panels'] += 1; c['tierA_panels'] += f['tier'] == 'A'; c['def'] += bool(p.get('definition')); c['use'] += bool(p.get('use'))
        op = fold(k) + '/panels/ocr.json'
        if os.path.exists(op):
            for x in json.load(open(op)).get('crops', []):
                c['ocr_crops'] += 1; c['ocr_letter'] += bool(x.get('letter')); c['ocr_agree'] += bool(x.get('letter_agrees'))
    return c
A = store_stats(lambda k: K[k]['matmech_folder']); Bm = store_stats(lambda k: f'store/Acta_Materialia/{k}')
rows = [('figures', 'figures'), ('tier A', 'tier_A'), ('tier B', 'tier_B'), ('tier C', 'tier_C'), ('accepted panels', 'panels'),
        ('panels in tier-A figures', 'tierA_panels'), ('panels with caption span', 'def'), ('panels cited in text', 'use'),
        ('crops OCR-read', 'ocr_crops'), ('crops with a letter read', 'ocr_letter'), ('letter agrees with detector', 'ocr_agree')]
out += ['## Q5 Panel stores\n', '| | MatMech store | MinerU store |', '|---|---|---|'] + [f'| {a} | {A[b]} | {Bm[b]} |' for a, b in rows] + ['']

# Q6
SUFFIX = os.environ.get('ITEMS_SUFFIX', '')
def load(which):
    p = f'open_items_{which}{SUFFIX}.json'; return json.load(open(p))['items'] if os.path.exists(p) else []
out += [f"## Q6 Items ({'rules revision r1' if SUFFIX else 'frozen v0.1 rules'}; all unreviewed)\n", '| | MatMech store | MinerU store |', '|---|---|---|']
I = {w: load(w) for w in ('matmech', 'mineru')}
pub = {k: [norm(s) for s in pubsents(k)] for k in ok}; pubjoin = {k: ''.join(v) for k, v in pub.items()}
import difflib
def src_sim(it):
    txt = it.get('key') if it['level'] == 3 else it.get('source')
    ss = [x for x in SPLIT.split(' '.join((txt or '').split())) if len(x.split()) >= 6]
    if not ss: return None
    sims = []
    for x in ss:
        q = norm(x); sims.append(max((difflib.SequenceMatcher(None, q, p, autojunk=False).ratio() for p in pub[it['paper']]
                                      if abs(len(p) - len(q)) < 0.5 * len(q) + 20), default=0))
    return min(sims)
def leak(it):
    if it['level'] != 1 or it.get('type') != 'number' or not it.get('key'): return False
    q = (it.get('question') or ''); return norm(it['key']) and norm(it['key']) in norm(q.replace('____', ''))
sig = lambda it: (it['paper'], it['level'], it.get('question'), it.get('key'))
st = {}
for w, its in I.items():
    lv = collections.Counter(i['level'] for i in its)
    st[w] = {'L1 / L2 / L3': f'{lv[1]} / {lv[2]} / {lv[3]}', 'items total': len(its), 'L1 number items': sum(1 for i in its if i.get('type') == 'number'),
             'papers with >= 1 item': len({i['paper'] for i in its}),
             **{f'L{L} source vs publisher: similarity >= 0.90': (lambda v: f"{sum(1 for x in v if x >= .9)} / {len(v)} ({pct(sum(1 for x in v if x >= .9), len(v))})")([x for x in (src_sim(i) for i in its if i['level'] == L) if x is not None]) for L in (1, 2, 3)},
             'L1 key visible elsewhere in question (leak)': sum(leak(i) for i in its)}
same = len({sig(i) for i in I['matmech']} & {sig(i) for i in I['mineru']})
for r in st['matmech']: out.append(f"| {r} | {st['matmech'][r]} | {st['mineru'][r]} |")
out += [f'| items identical in both stores | {same} | {same} |', '',
        'Source check: each item sentence (L1/L2 `source`, L3 `key`) is compared with the most similar publisher sentence from MatMech (difflib ratio on normalised text; the item counts as matching when its least similar sentence reaches 0.90). MatMech passages only cover sentences that cite a figure, so a low score can also mean the sentence is missing from MatMech rather than garbled.\n']
open(f'QUALITY{SUFFIX}.md', 'w').write('\n'.join(out)); print('\n'.join(out))
