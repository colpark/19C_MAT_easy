"""Validate panel detections and match each panel to the text that defines and uses it.

Stages 1-4 and 6 are regex + geometry only (CPU). Stage 5 (OCR) runs on flagged figures when
pytesseract is available; otherwise those panels carry ocr_letter=null and reason codes are kept.

Usage:
  python match_panels.py --root ~/Documents/causalmat/matmech --out-dir ~/panels/match_out \
      [--sample 200] [--workers 16] [--no-write] [--ocr]
"""
import argparse
import json
import os
import random
import re
import sys
import time
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

RUN_VERSION = "match/v4+r1-NAT+r1-OCR+r1-AND+r1-BARE"
LETTERS = "abcdefghijklmnopqrst"

# --- Stage 1/2 regexes (versioned with RUN_VERSION) ---------------------------------------------
SEP = r"(?:\s*(?:,|and|&|–|—|-|to)\s*)"
LBL = r"[a-tA-T][0-9]?"
# (a) (a, b) (a–c) (a and b) (a1) (a1–a3) — a non-letter must precede the opening paren
PAREN = re.compile(rf"(?<![A-Za-z])\((\s*{LBL}(?:{SEP}{LBL})*\s*)\)")
# a) b) at a clause start
BARE = re.compile(rf"(?:^|[\s;:.])({LBL})\)")
BARE2 = re.compile(rf"(?:^|[\s;:.])({LBL}(?:{SEP}{LBL})*)\)")   # r1-BARE: label groups "B-D)", "E, F)", "J and K)"
ITEM = re.compile(LBL)
# r1-NAT Nature-style caption labels: lowercase label group at the caption-body start or after . or ; then a space
NAT = re.compile(r"(?:^\s*(?:Fig(?:ure)?s?\.?|FIG\.?)\s*\d+\s*[.|:]?\s*[^.]*?\.\s*|(?<=[.;])\s*)([a-t](?:\s*(?:,|and|&|–|—|-|to)\s*[a-t])*)(?:\s*,)?\s+(?=\S)")
FIGNUM = re.compile(r"^\s*(?:Fig(?:ure)?s?\.?|FIG\.?)\s*(\d+)", re.I)
# a letter counts as a panel reference only inside parentheses, or glued to the number ("Fig. 4a"),
# and never when another letter follows it ("Fig. 3 shows" is not panel s)
REF = re.compile(rf"(?:Fig(?:ure)?s?\.?|FIG\.?)\s*(\d+)\s*(?:\(\s*({LBL}(?:{SEP}{LBL})*)\s*\)|({LBL}(?:{SEP}{LBL})*)(?![A-Za-z]))", re.I)
SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(])")


def expand(body):
    """Labels named in one group, ranges expanded. Returns (labels, two_level)."""
    parts = ITEM.findall(re.sub(r"\b(?:and|to)\b", " ", body, flags=re.I))   # r1-AND: letters of 'and'/'to' are not labels
    two = any(len(p) > 1 for p in parts)
    if re.search(r"(–|—|-|to)", body) and len(parts) == 2 and not two:
        a, b = parts[0].lower(), parts[1].lower()
        if a in LETTERS and b in LETTERS and LETTERS.index(a) <= LETTERS.index(b):
            return list(LETTERS[LETTERS.index(a):LETTERS.index(b) + 1]), False
    return [p.lower() for p in parts], two


def segment_caption(caption):
    """Stage 1: preamble + one span per label, empty slots recorded."""
    text = " ".join((caption or "").split())
    marks = []
    for m in PAREN.finditer(text):
        labs, two = expand(m.group(1))
        marks.append((m.start(), m.end(), labs, two))
    bare = BARE2 if not marks else BARE   # r1-BARE groups only in captions without (a)-style labels
    for m in bare.finditer(text):
        if not any(s <= m.start(1) < e for s, e, _, _ in marks):
            labs, two = expand(m.group(1))
            marks.append((m.start(1), m.end(), labs, two))
    nat_marks = []   # r1-NAT Nature-style labels
    for m in NAT.finditer(text):
        labs, two = expand(m.group(1))
        nat_marks.append((m.start(1), m.end(1), labs, two))
    nat = [l for _, _, labs, _ in nat_marks for l in labs]
    old = [l for _, _, labs, _ in marks for l in labs]
    if nat and nat[0] == "a" and len(set(nat)) >= 2 and (not old or (len(set(nat)) > len(set(old)) and sorted(set(old)) != list(LETTERS[:len(set(old))]))):
        marks = nat_marks   # guard: starts at a, >= 2 letters; replaces (a)/a) labels only when those are not a clean a.. run and NAT names more
    marks.sort()
    cases = {("upper" if m.group(1).strip()[0].isupper() else "lower")
             for m in PAREN.finditer(text)} | {("upper" if m.group(1)[0].isupper() else "lower")
                                               for m in BARE.finditer(text)}
    spans, empties, letters, two_level = {}, [], [], len(cases) > 1
    preamble = text[:marks[0][0]].strip(" :;,.-") if marks else text
    for i, (s, e, labs, two) in enumerate(marks):
        nxt = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        span = text[e:nxt].strip().strip(";:,. -")
        two_level = two_level or two
        for lab in labs:
            if len(lab) == 1:
                if lab not in letters:
                    letters.append(lab)
                if len(span) >= 3:
                    spans[lab] = (spans.get(lab, "") + " " + span).strip()
                else:
                    spans.setdefault(lab, "")
    for lab in letters:
        if len(spans.get(lab, "")) < 3:
            empties.append(lab)
    return {"preamble": preamble, "spans": spans, "letters": letters,
            "empty_slots": empties, "two_level": two_level, "text": text}


def figure_number(caption, order_idx):
    m = FIGNUM.match(" ".join((caption or "").split()))
    return int(m.group(1)) if m else order_idx


def body_refs(passages, fignum):
    """Stage 2: sentences referencing this figure with a letter, plus other-figure letters."""
    text = " ".join(" ".join(passages or []).split())
    spans, letters, other = {}, [], []
    sents = SENT.split(text)
    for sent in sents:
        for m in REF.finditer(sent):
            n = int(m.group(1))
            body = m.group(2) or m.group(3) or ""
            if m.group(3) and m.start(3) != m.end(1):  # bare form must be glued to the number
                continue
            labs, _ = expand(body)
            for lab in labs:
                if len(lab) != 1:
                    continue
                if n == fignum:
                    if lab not in letters:
                        letters.append(lab)
                    spans.setdefault(lab, [])
                    if sent not in spans[lab]:
                        spans[lab].append(sent.strip())
                elif lab not in other:
                    other.append(lab)
    return {"spans": spans, "letters": letters, "other_figure_letters": other}


def reading_order(dets):
    """Stage 3: row-major order and whether the labels run alphabetically in it."""
    boxes = [d for d in dets if len(d["label"]) == 1 and d["label"].lower() in LETTERS]
    if not boxes:
        return [], True
    hs = [d["bbox"][3] - d["bbox"][1] for d in boxes]
    med = sorted(hs)[len(hs) // 2]
    rows, cur = [], []
    for d in sorted(boxes, key=lambda d: (d["bbox"][1] + d["bbox"][3]) / 2):
        cy = (d["bbox"][1] + d["bbox"][3]) / 2
        if cur and cy - (cur[0]["bbox"][1] + cur[0]["bbox"][3]) / 2 > med / 2:
            rows.append(cur)
            cur = []
        cur.append(d)
    rows.append(cur)
    order = [d for row in rows for d in sorted(row, key=lambda d: d["bbox"][0])]
    seq = [d["label"].lower() for d in order]
    return seq, seq == sorted(seq)


def tier_for(C, T, D, cap, det, order_ok, in_errors, two_level, n_boxes, other_letters):
    """Stage 4: one tier and one reason code."""
    Cs, Ts, Ds = set(C), set(T), set(D)
    if two_level:
        return "C", "C4_two_level"
    if in_errors or (not cap["text"] and n_boxes >= 3):
        return "C", "C5_broken_record"
    # a figure with no caption labels and no letter boxes is one panel, not an empty exact match
    if not Cs and not Ds and not Ts:
        return "B", "B3_single"
    if Cs == Ds and Ts <= Cs:
        if cap["empty_slots"]:
            return "B", "B1_caption_empty"
        return "A", "A_exact"
    if not Cs and (not Ts) and (n_boxes <= 2 or any(d["label"] == "single" for d in det)):
        return "B", "B3_single"
    if Cs == Ds and Ts and not Ts <= Cs:
        return "B", "B4_text_only"
    if other_letters and set(other_letters) & Ds:
        return "C", "C3_caption_swap"
    if Ts and not (Ts & Cs) and not (Ts & Ds):
        return "C", "C3_caption_swap"
    if Cs and Cs == Ts and len(Cs ^ Ds) == 1:
        return "B", "B2_detector_off_by_one"
    if Cs and len(Cs ^ Ds) >= 2:
        return "C", "C1_count_mismatch"
    if not order_ok:
        return "C", "C2_order_violation"
    return "C", "C6_unresolved"


def do_folder(args):
    folder, root, errors, want_ocr = args
    folder = Path(folder)
    pj = folder / "panels" / "panels.json"
    if not pj.exists():
        return None
    try:
        det_run = json.load(open(pj))
        rec = json.load(open(folder / "data.json", encoding="utf-8"))
    except Exception:
        return None
    figs_det = {f["file"]: f for f in det_run.get("figures", [])}
    ocr_map = {}   # r1-OCR: crop -> (OCR letter, agrees with detector)
    try:
        for c in json.load(open(folder / "panels" / "ocr.json")).get("crops", []):
            ocr_map[c["crop"]] = ((c.get("letter") or "").lower(), bool(c.get("letter_agrees")))
    except Exception:
        pass
    info = rec.get("image_info") or []
    out_figs, rows = [], []
    for idx, im in enumerate(info, 1):
        rel = im.get("image_path")
        d = figs_det.get(rel)
        if not d:
            # figure skipped by the detector (broken record): still gets a tier, per Stage 4 C5
            fignum = figure_number(" ".join(im.get("image_caption") or []), idx)
            out_figs.append({"file": rel, "figure_number": fignum, "tier": "C", "reason": "C5_broken_record",
                             "letters": {"caption": [], "text": [], "detector": []}, "order_ok": True,
                             "reading_order": [], "caption_preamble": "", "caption_empty_slots": [],
                             "text_letters_other_figure": [], "panels": []})
            rows.append({"doi": folder.name, "journal": folder.parent.name, "figure_number": fignum,
                         "file": rel, "label": None, "tier": "C", "reason": "C5_broken_record",
                         "panel_status": "quarantined", "definition_missing": True, "has_use": False,
                         "crop": None, "microscopic": bool(im.get("microscopic_image"))})
            continue
        cap = segment_caption(" ".join(im.get("image_caption") or []))
        fignum = figure_number(" ".join(im.get("image_caption") or []), idx)
        ref = body_refs(im.get("image_description") or [], fignum)
        dets = [x for x in d["detections"] if len(x["label"]) == 1]
        seq, order_ok = reading_order(dets)
        D = sorted({x["label"].lower() for x in dets})
        C, T = cap["letters"], ref["letters"]
        tier, reason = tier_for(C, T, D, cap, d["detections"], order_ok,
                                (folder.name, rel) in errors, cap["two_level"] or d.get("two_level"),
                                len(d["detections"]), ref["other_figure_letters"])
        ocr_ok = False   # r1-OCR: the image itself proves the panel letters
        if tier != "A" and reason != "B3_single" and not (cap["two_level"] or d.get("two_level")) and len(dets) >= 2:
            lab_of = [ocr_map.get(x.get("crop")) for x in dets]
            Ls = [x["label"].lower() for x in dets]
            if all(o is not None and o[1] and o[0] == l for o, l in zip(lab_of, Ls)) and len(set(Ls)) == len(Ls) and sorted(Ls) == list(LETTERS[:len(Ls)]) and set(T) <= set(Ls):
                tier, reason, ocr_ok = "A", "A2_ocr_confirmed", True
        panels = []
        if tier != "C":
            if reason == "B3_single":
                panels.append({"label": "single", "crop": None, "bbox": None, "score": None, "ocr_letter": None,
                               "definition": cap["preamble"] or cap["text"], "definition_source": "caption_preamble",
                               "use": ref["spans"].get("", []) or [s for v in ref["spans"].values() for s in v],
                               "use_source": "text" if ref["spans"] else "none",
                               "panel_status": "accepted", "definition_missing": not bool(cap["text"])})
            else:
                for x in sorted(dets, key=lambda x: x["label"]):
                    lab = x["label"].lower()
                    defin = cap["spans"].get(lab, "") if not (ocr_ok and set(C) != set(D)) else ""   # r1-OCR: caption parse disagrees -> no caption span
                    src = "caption"
                    missing = False
                    if len(defin) < 3:
                        alt = " ".join(ref["spans"].get(lab, []))
                        if len(alt) >= 3:
                            defin, src = alt, "text_fallback"
                        elif ocr_ok:
                            defin, src = cap["text"], "caption_whole"   # r1-OCR
                        else:
                            defin, src, missing = "", "caption_empty", True
                    status = "accepted"
                    if reason == "B2_detector_off_by_one" and want_ocr:
                        status = "accepted"  # OCR stage refines; unresolved panels marked by --ocr pass
                    panels.append({"label": lab, "crop": x.get("crop"), "bbox": x["bbox"], "score": x["score"],
                                   "ocr_letter": None, "definition": defin, "definition_source": src,
                                   "use": ref["spans"].get(lab, []), "use_source": "text" if ref["spans"].get(lab) else "none",
                                   "panel_status": status, "definition_missing": missing})
        out_figs.append({"file": rel, "figure_number": fignum, "tier": tier, "reason": reason,
                         "letters": {"caption": C, "text": T, "detector": D},
                         "order_ok": order_ok, "reading_order": seq,
                         "caption_preamble": cap["preamble"], "caption_empty_slots": cap["empty_slots"],
                         "text_letters_other_figure": ref["other_figure_letters"], "panels": panels})
        for p in panels:
            rows.append({"doi": folder.name, "journal": folder.parent.name, "figure_number": fignum,
                         "file": rel, "label": p["label"], "tier": tier, "reason": reason,
                         "panel_status": p["panel_status"], "definition_missing": p["definition_missing"],
                         "has_use": bool(p["use"]), "crop": p["crop"],
                         "microscopic": bool(im.get("microscopic_image"))})
        if not panels:
            rows.append({"doi": folder.name, "journal": folder.parent.name, "figure_number": fignum,
                         "file": rel, "label": None, "tier": tier, "reason": reason, "panel_status": "quarantined",
                         "definition_missing": True, "has_use": False, "crop": None,
                         "microscopic": bool(im.get("microscopic_image"))})
    return {"doi": folder.name, "journal": folder.parent.name, "path": str(folder),
            "detector_run_version": det_run.get("run_version"), "figures": out_figs, "rows": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--no-write", action="store_true", help="do not write per-DOI match.json (sample checks)")
    ap.add_argument("--ocr", action="store_true")
    a = ap.parse_args()

    root, out = Path(a.root).expanduser(), Path(a.out_dir).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    errors = set()
    er = root / "panels_run" / "errors.jsonl"
    if er.exists():
        for line in open(er):
            e = json.loads(line)
            errors.add((e["doi"], e.get("file")))

    folders = sorted(p.parent for p in root.glob("*/*/data.json"))
    if a.sample:
        random.Random(1).shuffle(folders)
        folders = folders[:a.sample]
    print(f"{len(folders)} folders, {a.workers} workers, run_version={RUN_VERSION}", flush=True)

    t0 = time.time()
    tiers, reasons, n_fig, n_pan = Counter(), Counter(), 0, 0
    man = open(out / "manifest.jsonl", "w")
    qua = open(out / "quarantine.jsonl", "w")
    fetch = open(out / "fetch_captions.txt", "w")
    has_def = has_use = both = 0
    micro_tier = Counter()
    with Pool(a.workers) as pool:
        for i, res in enumerate(pool.imap_unordered(do_folder, ((str(f), str(root), errors, a.ocr) for f in folders), chunksize=32), 1):
            if not res:
                continue
            for f in res["figures"]:
                n_fig += 1
                tiers[f["tier"]] += 1
                reasons[f["reason"]] += 1
                if f["tier"] == "C":
                    qua.write(json.dumps({"doi": res["doi"], "file": f["file"], "figure_number": f["figure_number"],
                                          "reason": f["reason"], "letters": f["letters"]}) + "\n")
                if f["reason"] == "B1_caption_empty":
                    fetch.write(f"{res['doi']}\tfig{f['figure_number']}\t{','.join(f['caption_empty_slots'])}\n")
            for r in res["rows"]:
                man.write(json.dumps(r) + "\n")
                if r["label"]:
                    n_pan += 1
                    d = not r["definition_missing"]
                    has_def += d
                    has_use += r["has_use"]
                    both += d and r["has_use"]
                if r["microscopic"]:
                    micro_tier[r["tier"]] += 1
            if not a.no_write:
                p = Path(res["path"]) / "panels" / "match.json"
                json.dump({"run_version": RUN_VERSION, "detector_run_version": res["detector_run_version"],
                           "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "figures": res["figures"]},
                          open(p, "w"), ensure_ascii=False)
            if i % 5000 == 0:
                print(f"  {i}/{len(folders)} folders, {n_fig} figures, {time.time()-t0:.0f}s", flush=True)
    man.close(); qua.close(); fetch.close()
    summary = {"run_version": RUN_VERSION, "folders": len(folders), "figures": n_fig, "panels": n_pan,
               "tiers": dict(tiers), "reasons": dict(reasons.most_common()),
               "panels_with_definition": has_def, "panels_with_use": has_use, "panels_with_both": both,
               "fraction_definition": round(has_def / max(n_pan, 1), 4),
               "fraction_use": round(has_use / max(n_pan, 1), 4),
               "fraction_both": round(both / max(n_pan, 1), 4),
               "microscopy_figures_by_tier": dict(micro_tier),
               "seconds": round(time.time() - t0, 1)}
    json.dump(summary, open(out / "summary.json", "w"), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    sys.exit(main())
