#!/usr/bin/env python3
"""make_match_r1nat.py: matcher revision r1-NAT (owner request 2026-10-01: "fix the 47 papers"), applied to a copy of
causalmat/scripts/panels/match_panels.py (the original is not edited).

Nature-family captions label panels without parentheses: 'Fig. 1 Title. a SEM image of ... b-d XRD ... e, f ...'. The matcher's caption
parser knows only '(a)' and 'a)', so these figures got no caption letters and fell to tier C (C3/C1/C6), and their lettered text
references never resolved. Change, nothing else:
  r1-NAT segment_caption(): a lowercase label group at the start of the caption body or
         after '.' or ';' ('a', 'b-d', 'b–d', 'c, d', 'e and f') followed by an optional comma and a space is a panel label. They are used when PAREN/BARE find nothing, or when the PAREN/BARE
         letters are not a clean run from 'a' and the Nature-style parse names more letters (stray 'h)' from math or parentheses). Guard: the NAT labels
         must start with 'a' and name at least two letters (rejects an article 'a' or math fragments after ';'). Sentence starts in captions are
         capitalised, so a lowercase single letter there is a label, not the article 'a'.
  r1-OCR do_folder(): a figure that is not tier A (and not a single-panel B3 figure) becomes tier A, reason A2_ocr_confirmed, when the
         image proves its labels: >= 2 detected panels, each with an OCR letter that agrees with the detector label, unique letters that
         run a, b, c, ... without gaps, and every letter cited in the text among them. If the caption letters differ from the detected
         letters, caption spans are not trusted: the panel definition comes from the citing text, else the whole caption.
  r1-AND expand(): the words 'and' / 'to' between labels were read as letters ('A and B' -> a, a, n, d, b; 'b to d' -> b, t, o, d),
         so text letters held a phantom 'n' (or 't', 'o') and figures fell to B4_text_only / C. The words are removed before collecting labels.
  r1-BARE the clause-start 'a)' pattern takes a label group ('B-D)', 'E, F)', 'J and K)'), as the parenthesised pattern already did, but only in captions
         without '(a)'-style labels (a unit like '1 g)' in an (a)-style caption was read as a label in the first try);
         before, only the last letter of the group was found (Bioactive Materials captions).
usage: make_match_r1nat.py <match_panels.py> <out file>"""
import hashlib, sys
src, out = sys.argv[1:3]; s = open(src).read()
print('source sha', hashlib.sha256(s.encode()).hexdigest()[:16])
def sub(t, old, new):
    assert t.count(old) == 1, old[:50]; return t.replace(old, new)
s = sub(s, 'ITEM = re.compile(LBL)\n', 'ITEM = re.compile(LBL)\n'
        '# r1-NAT Nature-style caption labels: lowercase label group at the caption-body start or after . or ; then a space\n'
        'NAT = re.compile(r"(?:^\\s*(?:Fig(?:ure)?s?\\.?|FIG\\.?)\\s*\\d+\\s*[.|:]?\\s*[^.]*?\\.\\s*|(?<=[.;])\\s*)([a-t](?:\\s*(?:,|and|&|–|—|-|to)\\s*[a-t])*)(?:\\s*,)?\\s+(?=\\S)")\n')
s = sub(s, '    marks.sort()\n    cases =', '    nat_marks = []   # r1-NAT Nature-style labels\n'
        '    for m in NAT.finditer(text):\n'
        '        labs, two = expand(m.group(1))\n'
        '        nat_marks.append((m.start(1), m.end(1), labs, two))\n'
        '    nat = [l for _, _, labs, _ in nat_marks for l in labs]\n'
        '    old = [l for _, _, labs, _ in marks for l in labs]\n'
        '    if nat and nat[0] == "a" and len(set(nat)) >= 2 and (not old or (len(set(nat)) > len(set(old)) and sorted(set(old)) != list(LETTERS[:len(set(old))]))):\n'
        '        marks = nat_marks   # guard: starts at a, >= 2 letters; replaces (a)/a) labels only when those are not a clean a.. run and NAT names more\n'
        '    marks.sort()\n    cases =')
s = sub(s, """        panels = []
        if tier != "C":""", """        ocr_ok = False   # r1-OCR: the image itself proves the panel letters
        if tier != "A" and reason != "B3_single" and not (cap["two_level"] or d.get("two_level")) and len(dets) >= 2:
            lab_of = [ocr_map.get(x.get("crop")) for x in dets]
            Ls = [x["label"].lower() for x in dets]
            if all(o is not None and o[1] and o[0] == l for o, l in zip(lab_of, Ls)) and len(set(Ls)) == len(Ls) and sorted(Ls) == list(LETTERS[:len(Ls)]) and set(T) <= set(Ls):
                tier, reason, ocr_ok = "A", "A2_ocr_confirmed", True
        panels = []
        if tier != "C":""")
s = sub(s, """                    defin = cap["spans"].get(lab, "")
                    src = "caption\"""", """                    defin = cap["spans"].get(lab, "") if not (ocr_ok and set(C) != set(D)) else ""   # r1-OCR: caption parse disagrees -> no caption span
                    src = "caption\"""")
s = sub(s, """                        else:
                            defin, src, missing = "", "caption_empty", True""", """                        elif ocr_ok:
                            defin, src = cap["text"], "caption_whole"   # r1-OCR
                        else:
                            defin, src, missing = "", "caption_empty", True""")
s = sub(s, """    figs_det = {f["file"]: f for f in det_run.get("figures", [])}""", """    figs_det = {f["file"]: f for f in det_run.get("figures", [])}
    ocr_map = {}   # r1-OCR: crop -> (OCR letter, agrees with detector)
    try:
        for c in json.load(open(folder / "panels" / "ocr.json")).get("crops", []):
            ocr_map[c["crop"]] = ((c.get("letter") or "").lower(), bool(c.get("letter_agrees")))
    except Exception:
        pass""")
s = sub(s, """    parts = ITEM.findall(body)
""", """    parts = ITEM.findall(re.sub(r"\\b(?:and|to)\\b", " ", body, flags=re.I))   # r1-AND: letters of 'and'/'to' are not labels
""")
s = sub(s, 'BARE = re.compile(rf"(?:^|[\\s;:.])({LBL})\\)")', 'BARE = re.compile(rf"(?:^|[\\s;:.])({LBL})\\)")\nBARE2 = re.compile(rf"(?:^|[\\s;:.])({LBL}(?:{SEP}{LBL})*)\\)")   # r1-BARE: label groups "B-D)", "E, F)", "J and K)"')
s = sub(s, """    for m in BARE.finditer(text):
        if not any""", """    bare = BARE2 if not marks else BARE   # r1-BARE groups only in captions without (a)-style labels
    for m in bare.finditer(text):
        if not any""")
s = s.replace('RUN_VERSION = "match/v4"', 'RUN_VERSION = "match/v4+r1-NAT+r1-OCR+r1-AND+r1-BARE"')
open(out, 'w').write(s); print('r1-NAT written', hashlib.sha256(s.encode()).hexdigest()[:16])
