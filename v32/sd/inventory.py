#!/usr/bin/env python3
"""sd/inventory.py (Source Data build, step 1): per paper, every Source Data sheet with its figure/panel label, header rows and numeric
column count, and the published figure files. Writes sd/<paper>/inventory.json. No values are interpreted here."""
import glob, json, os, re, hashlib
import openpyxl
EXT = '/home/aid1/Documents/harbor/v32_host/fidelity/ext'; OUT = '/home/aid1/Documents/harbor/v32/sd'
P = {'P2': 's41467-024-48346-6', 'P3': 's41467-025-60705-5', 'P4': 's41467-026-77120-z', 'P5': 's41467-025-65917-3', 'P6': 's41467-024-46801-y'}
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
for k, aid in P.items():
    os.makedirs(f'{OUT}/{k}', exist_ok=True); inv = {'article': aid, 'doi': '10.1038/' + aid, 'files': {}, 'sheets': [], 'figures': {}}
    for f in sorted(glob.glob(f'{EXT}/{aid}/*')):
        inv['files'][os.path.basename(f)] = {'sha256': sha(f), 'bytes': os.path.getsize(f)}
    for x in sorted(glob.glob(f'{EXT}/{aid}/*.xlsx')):
        wb = openpyxl.load_workbook(x, read_only=True, data_only=True)
        for s in wb.sheetnames:
            rows = [list(r) for _, r in zip(range(400), wb[s].iter_rows(values_only=True))]
            hdr = [[str(c) for c in r if c is not None][:30] for r in rows[:4]]
            nnum = sum(isinstance(c, (int, float)) for r in rows for c in r)
            m = re.search(r'(S(?:upplementary)?\.?\s*Fig|Fig|FIG)\D*?(\d+)\s*([a-z][a-z,\-\s&]*)?', s, re.I)
            supp = bool(re.search(r'^\s*(S\b|S\.|Supp|FigS|Fig\s*S)', s, re.I))
            inv['sheets'].append({'file': os.path.basename(x), 'sheet': s, 'figure': (('S' if supp else '') + m.group(2)) if m else None,
                                  'panels': (m.group(3) or '').strip() if m else '', 'header': hdr, 'numeric_cells_first400rows': nnum})
    json.dump(inv, open(f'{OUT}/{k}/inventory.json', 'w'), indent=1, ensure_ascii=False)
    main = [s for s in inv['sheets'] if s['figure'] and not s['figure'].startswith('S')]
    print(k, aid, '| sheets', len(inv['sheets']), '| main-text sheets', len(main), '| figures', sorted({s['figure'] for s in main}, key=lambda v: int(v)))
