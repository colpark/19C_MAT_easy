"""mineru_paras.py (converter revision r1-M6: body starts at the first paragraph over 40 words when a paper has no Introduction heading; see make_conv_r1m6.py): MinerU content_list.json -> <key>.paras.json, the exact input format of levels.py/open.py.

This file replaces ONLY segment.py (the pdfplumber segmenter of v0.1). Everything downstream (levels.py v3.2,
open.py, build_bench.py) runs unchanged. The rules below mirror segment.py's rules S5 to S10 one for one,
so that the only difference between v0.1 and v0.2 is the layout engine.

Input : MinerU 2.x output for one PDF, the file <name>_content_list.json (a list of blocks in reading order;
        MinerU already discards page headers, footers and page numbers).
Output: <key>.paras.json = {"key", "engine": "mineru", "mineru_version", "paras": [{i, section, page, text}]}

M1  Blocks are read in content_list order. type "text" blocks are candidates. type "image", "table",
    "equation" (display math), "code", "list" of figure text are skipped, as v0.1 dropped non-body text.
    If a block type is unknown, it is skipped and logged.
M2  Heading: a "text" block with text_level >= 1, or a short block (< 14 words, no final period) that
    matches the v0.1 heading pattern HEADRE. A heading sets the section label (v0.1 S7).
M3  Inline math $...$ becomes plain text: LaTeX commands (\\mathrm, \\mathbf, \\text, ...) are dropped with
    their argument kept, braces, _ and ^ are dropped, spaces inside the math span are removed, and a few
    symbols map to Unicode (\\mu -> μ, \\circ -> °, \\cdot -> ·, \\times -> ×, \\pm -> ±, \\sim -> ∼,
    \\alpha..\\omega -> Greek letters, \\% -> %). So $\\mathrm{Co}_{3}\\mathrm{O}_{4}$ -> Co3O4.
M4  Continuation (v0.1 S5c): a body block is appended to the previous paragraph when the previous one does
    not end a sentence (END regex of v0.1: . ? ! : optionally followed by a citation). Otherwise it starts a
    new paragraph. A heading always closes the paragraph.
M4b A block that starts with KEYWORDS or ABSTRACT never absorbs the next block (added after the synthetic
    self-test: the unpunctuated keyword line swallowed the first Nano Letters body paragraph).
M5  Hyphen join at the junction (v0.1 S6): 'anneal-' + 'ing' -> 'annealing' when the next word is lowercase.
M6  Body start and stop (v0.1 S8): start at the heading containing 'Introduction'; for Nano Letters (Xu17),
    which has no numbered headings, start at the first body block after the block containing 'KEYWORDS',
    or after the abstract if no KEYWORDS block exists. Stop at the same STOP headings as v0.1.
M7  Nano Letters run-in headings: when MinerU emits 'Results and Discussion(s)', 'Conclusions',
    'Experimental Section' as a separate heading block, its text is prefixed to the next paragraph
    ('Results and Discussions. ...'), because levels.py C1 finds the Nano Letters results by that prefix.
M8  v0.1 S10 text fixes: drop caps rejoined, 'F igure' -> 'Figure', 'Figure 4 a' -> 'Figure 4a'.
M9  page = MinerU page_idx + 1. Paragraphs shorter than 5 words are dropped (v0.1 rule).
"""
import json, re, sys, os

HEADRE = re.compile(r'^(\d+(\.\d+)*\.\s+[A-Z][a-z][^.]{2,80}|(Introduction|Results( and [Dd]iscussions?)?|Discussion|Conclusions?|Experimental( [Ss]ection| details)?|Methods|Materials and [Mm]ethods|References|Acknowledg\w*))$')
STOP = re.compile(r'^(\d+\.?\s+)?(The Supporting Information|References|REFERENCES|Acknowledg|ACKNOWLEDG|Appendix|Supplementary|Declaration|Conflict|■?\s*ASSOCIATED CONTENT|Supporting Information|Notes)')
END = re.compile(r'[.?!:]\s*(\[\s*[\d,\s–−-]+\]|[\d,–−-]+)?\s*$')
FRONT = re.compile(r'^(KEYWORDS|Keywords|KEY WORDS|ABSTRACT|Abstract)\b')   # M4b
RUNIN = re.compile(r'^(Results and Discussions?|Conclusions?|Experimental Section)\.?$')
GREEK = {'alpha': 'α', 'beta': 'β', 'gamma': 'γ', 'delta': 'δ', 'Delta': 'Δ', 'epsilon': 'ε', 'varepsilon': 'ε', 'eta': 'η',
         'theta': 'θ', 'kappa': 'κ', 'lambda': 'λ', 'mu': 'μ', 'nu': 'ν', 'pi': 'π', 'rho': 'ρ', 'sigma': 'σ', 'tau': 'τ',
         'phi': 'φ', 'chi': 'χ', 'psi': 'ψ', 'omega': 'ω', 'Omega': 'Ω'}
SYM = {'circ': '°', 'cdot': '·', 'times': '×', 'pm': '±', 'sim': '∼', 'approx': '≈', 'le': '≤', 'leq': '≤', 'ge': '≥', 'geq': '≥',
       'rightarrow': '→', 'to': '→', 'AA': 'Å', 'degree': '°', 'prime': '′'}

def math_to_text(m):
    t = m.group(1)
    t = t.replace('\\%', '%').replace('\\,', '').replace('\\;', '').replace('\\!', '').replace('~', '')
    t = re.sub(r'\\(mathrm|mathbf|mathit|mathsf|mathtt|text|textrm|rm|bf|operatorname|mathcal|boldsymbol)\s*', '', t)
    t = re.sub(r'\\(left|right|big|Big|bigg|Bigg)\b', '', t)
    t = re.sub(r'\\([A-Za-z]+)', lambda x: GREEK.get(x.group(1), SYM.get(x.group(1), '')), t)
    t = re.sub(r'[{}_^\s]', '', t)
    t = t.replace('--', '−')
    return t

def clean_text(t):
    t = re.sub(r'\$([^$]+)\$', math_to_text, t or '')
    return ' '.join(t.split())

def ended(t):
    return bool(END.search(t))

def join(a, b):
    if re.search(r'[A-Za-z]-$', a) and re.match(r'[a-z]', b):
        return a[:-1] + b
    return a + ' ' + b

def fixes(t):   # M8 = v0.1 S10
    t = re.sub(r'^([A-Z]) ([a-z])', r'\1\2', t)
    t = re.sub(r'\bF igure', 'Figure', t)
    t = re.sub(r'\b(Fig(?:ure|s)?\.?\s*\d+)\s+([a-h])(?=\s*[,)\s.;]|$)', r'\1\2', t)
    return t

def run(key, content_list_path, out_path, mineru_version='unknown'):
    blocks = json.load(open(content_list_path))
    items, skipped = [], {}
    for b in blocks:
        ty = b.get('type')
        if ty != 'text':
            skipped[ty] = skipped.get(ty, 0) + 1
            continue
        txt = clean_text(b.get('text', ''))
        if not txt:
            continue
        page = int(b.get('page_idx', 0)) + 1
        lvl = b.get('text_level') or 0
        is_head = lvl >= 1 or (len(txt.split()) < 14 and not txt.endswith('.') and HEADRE.match(txt))
        items.append({'head' if is_head else 'text': txt, 'page': page})
    # M4, M5, M7
    paras, pending_prefix = [], None
    for it in items:
        if 'head' in it:
            if key == 'Xu17' and RUNIN.match(it['head']):
                pending_prefix = it['head'].rstrip('.') + '.'
                continue
            paras.append({'head': it['head'], 'page': it['page']})
            continue
        t = it['text']
        if pending_prefix:
            t = pending_prefix + ' ' + t
            pending_prefix = None
            paras.append({'text': t, 'page': it['page']})
            continue
        last = paras[-1] if paras else None
        if last and 'text' in last and not ended(last['text']) and not FRONT.match(last['text']):
            last['text'] = join(last['text'], t)
        else:
            paras.append({'text': t, 'page': it['page']})
    # M6, M9 (identical to segment.py S8)
    out, section, started = [], None, False
    has_intro = any('head' in x and re.search(r'ntroduction|INTRODUCTION', x['head']) for x in paras)   # r1-M6
    for k, it in enumerate(paras):
        if 'head' in it:
            t = it['head']
            if STOP.match(t) and started:
                break
            if re.search(r'ntroduction|INTRODUCTION', t):
                started = True
            section = t
            continue
        t = fixes(' '.join(it['text'].split()))
        if STOP.match(t) and started:
            break
        if key == 'Xu17' and not started:
            prev = ' '.join(x.get('text', x.get('head', '')) for x in paras[:k])
            if ('KEYWORDS' in prev or 'ABSTRACT' in prev.upper()) and len(t.split()) > 40:
                started = True
        if not started and key != 'Xu17' and not has_intro and len(t.split()) > 40:   # r1-M6 no Introduction heading
            started = True
        if started and len(t.split()) >= 5:
            out.append({'i': len(out), 'section': section, 'page': it['page'], 'text': t})
    json.dump({'key': key, 'engine': 'mineru', 'mineru_version': mineru_version, 'skipped_block_types': skipped, 'paras': out},
              open(out_path, 'w'), indent=1, ensure_ascii=False)
    return out, skipped

if __name__ == '__main__':
    key, cl, outp = sys.argv[1], sys.argv[2], sys.argv[3]
    ver = sys.argv[4] if len(sys.argv) > 4 else 'unknown'
    out, sk = run(key, cl, outp, ver)
    print(key, 'paras', len(out), 'words', sum(len(p['text'].split()) for p in out), 'skipped', sk)
