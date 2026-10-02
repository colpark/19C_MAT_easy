#!/usr/bin/env python3
"""merge_sets.py: merge the two v0.24 paper sets (first 100 = S001-S100, oa2 = T001-T069, item ids W*-501+) into one items / r2 flags /
citations input for build_v024.py. Writes open_items_all.json, r2_flags_all.json, citations_all.json."""
import json
I1 = json.load(open('open_items_mineru_r1.json')); I2 = json.load(open('oa2/open_items_mineru_r1.json'))
ids1 = {i['id'] for i in I1['items']}; ids2 = {i['id'] for i in I2['items']}; assert not ids1 & ids2, 'id clash'
json.dump({'rules': I1['rules'], 'items': I1['items'] + I2['items']}, open('open_items_all.json', 'w'), indent=1, ensure_ascii=False)
F = json.load(open('r2_flags_v024.json')); F.update(json.load(open('oa2/r2_flags_oa2.json'))); json.dump(F, open('r2_flags_all.json', 'w'), indent=1, ensure_ascii=False)
C = json.load(open('citations_crossref.json')); C2 = json.load(open('oa2/citations_crossref.json')); assert not set(C) & set(C2); C.update(C2)
json.dump(C, open('citations_all.json', 'w'), indent=1, ensure_ascii=False)
print('items', len(I1['items']) + len(I2['items']), '| flags', len(F), '| papers', len(C))
