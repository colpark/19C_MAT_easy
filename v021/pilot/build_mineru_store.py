#!/usr/bin/env python3
"""build_mineru_store.py: a MatMech-layout panel-store input built from MinerU output only (PanelBench v0.21 pilot).

For each pilot paper writes store/<journal>/<key>/data.json + images/, the input format of
causalmat/scripts/panels/{detect,ocr,match}_panels.py:
  image_info = [{image_path, image_caption: [caption], image_description: [body passages citing the figure],
                 microscopic_image: false, caption_source}]
Rules (no model; regex + reading order only):
  R1 Figure images: MinerU `image` blocks at least 120 x 120 px (smaller ones are logos, icons, equation bits).
  R2 Caption: the block's own image_caption when it starts 'Fig. N' / 'Figure N'.
  R3 Reattach: a caption-like text block ('Fig. N' / 'Figure N' + more than 8 words) not attached by MinerU goes to
     the nearest uncaptioned image on the same page, in content_list order.
  R4 Remaining captions and uncaptioned images are paired in reading order only if their counts are equal
     (manuscripts that list captions apart from the figures).
  R5 One image per figure number (first in reading order); uncaptioned images left over are dropped.
  R6 image_description: body text blocks (not captions) that cite the figure number ('Fig. 3', 'Figure 3b', 'Figs. 2 and 3').
Prints counts only.
"""
import collections, json, os, re, shutil, sys
from PIL import Image

FIG = re.compile(r'^\s*(?:Fig\.?|Figure)\s*(\d+)', re.I)
def cites(n):
    return re.compile(rf'\bFig(?:ure)?s?\.?\s*(?:\d+[a-z]?\s*(?:,|and|&|–|-)\s*)*{n}(?![0-9])', re.I)

def build(key, info, mineru_dir, out_root):
    safe = info['safe']; auto = os.path.join(mineru_dir, safe, 'auto')
    B = json.load(open(os.path.join(auto, safe + '_content_list.json')))
    out = os.path.join(out_root, info['journal'], key); os.makedirs(os.path.join(out, 'images'), exist_ok=True)
    imgs = []
    for i, b in enumerate(B):
        if b['type'] != 'image' or not b.get('img_path'): continue
        p = os.path.join(auto, b['img_path'])
        try: w, h = Image.open(p).size
        except Exception: continue
        if w < 120 or h < 120: continue                                        # R1
        cap = ' '.join(b.get('image_caption') or [])
        imgs.append({'i': i, 'page': b.get('page_idx'), 'path': p, 'cap': cap if FIG.match(cap) else '',
                     'src': 'mineru' if FIG.match(cap) else ''})               # R2
    used = {x['cap'] for x in imgs if x['cap']}
    loose = [(i, b.get('page_idx'), b['text']) for i, b in enumerate(B)
             if b['type'] == 'text' and FIG.match(b.get('text') or '') and len(b['text'].split()) > 8 and b['text'] not in used]
    rest = []
    for i, pg, t in loose:                                                       # R3
        cand = [x for x in imgs if not x['cap'] and x['page'] == pg]
        if cand:
            x = min(cand, key=lambda x: abs(x['i'] - i)); x['cap'] = t; x['src'] = 'same_page'
        else: rest.append((i, pg, t))
    free = [x for x in imgs if not x['cap']]
    if rest and len(rest) == len(free):                                          # R4
        for x, (_, _, t) in zip(free, rest): x['cap'] = t; x['src'] = 'order'
    body = [b['text'] for b in B if b['type'] == 'text' and b.get('text') and not FIG.match(b['text'])]
    info_out, seen = [], set()
    for x in imgs:
        if not x['cap']: continue
        n = int(FIG.match(x['cap']).group(1))
        if n in seen: continue                                                   # R5
        seen.add(n)
        name = os.path.basename(x['path']); shutil.copy(x['path'], os.path.join(out, 'images', name))
        info_out.append({'image_path': 'images/' + name, 'image_caption': [x['cap']],
                         'image_description': [t for t in body if cites(n).search(t)],     # R6
                         'microscopic_image': False, 'caption_source': x['src']})
    json.dump({'doi': 'https://doi.org/' + info['doi'], 'title': '', 'image_info': info_out},
              open(os.path.join(out, 'data.json'), 'w'), ensure_ascii=False)
    return collections.Counter({'images_kept': len(imgs), 'figures': len(info_out),
                                **{'caption_' + x['caption_source']: 1 for x in info_out if False}}), \
           collections.Counter(x['caption_source'] for x in info_out)

if __name__ == '__main__':
    keys_file, mineru_dir, out_root, pilot = sys.argv[1:5]
    K = json.load(open(keys_file)); P = json.load(open(pilot))
    tot, src = collections.Counter(), collections.Counter()
    for k in P:
        a, b = build(k, K[k], mineru_dir, out_root); tot.update(a); src.update(b)
    print('store built:', len(P), 'papers |', dict(tot), '| caption source:', dict(src))
