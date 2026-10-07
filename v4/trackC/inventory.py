#!/usr/bin/env python3
"""C0.5 archive inventory (skill discoveryqa C0, CR1-CR4). Reports structure, never outcome values.

For one imported .aiida archive (identified by the import group the importer creates) it reports:
  node counts by node_type; groups and their sizes; for array/trajectory nodes the array names and shapes;
  for Dict nodes the key sets (keys only); process labels with process_state and exit_status counts
  (failed calculations are reject coverage); for each StructureData the reduced formula and whether it has
  descendants of each process type (provenance depth per structure).
Numeric outputs (band gaps, D, sigma, MSD values) are never printed, so the inventory can run before C1 freezes.

usage: AIIDA_PATH=... inventory.py --profile trackC --group LABEL --out inventory_X.json
       inventory.py --profile trackC --list-groups
"""
import argparse, json, sys
from collections import Counter, defaultdict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--profile', default='trackC')
    ap.add_argument('--group')
    ap.add_argument('--out')
    ap.add_argument('--list-groups', action='store_true')
    ap.add_argument('--max-struct', type=int, default=100000)
    a = ap.parse_args()
    from aiida import load_profile, orm
    load_profile(a.profile)
    if a.list_groups:
        qb = orm.QueryBuilder().append(orm.Group, project=['label', 'type_string', 'id'])
        for lab, ts, gid in qb.all():
            n = orm.QueryBuilder().append(orm.Group, filters={'id': gid}, tag='g').append(
                orm.Node, with_group='g').count()
            print(f'{gid}\t{ts}\t{n}\t{lab}')
        return
    g = orm.load_group(a.group)
    nodes = list(g.nodes)
    rep = {'group': a.group, 'n_nodes': len(nodes)}
    rep['node_types'] = dict(Counter(n.node_type for n in nodes).most_common())
    # sub-groups created by the authors (archives carry their own groups)
    qb = orm.QueryBuilder().append(orm.Node, filters={'id': {'in': [n.pk for n in nodes]}}, tag='n').append(
        orm.Group, with_node='n', project=['label'])
    rep['member_groups'] = dict(Counter(lab for (lab,) in qb.all()).most_common())
    arrays = Counter()
    dict_keys = Counter()
    procs = defaultdict(Counter)
    attrs_struct = []
    for n in nodes:
        if isinstance(n, orm.ArrayData):
            try:
                names = [f'{k}[{len(n.get_shape(k))}d]' for k in n.get_arraynames()]
            except Exception as e:  # noqa
                names = ['error:' + repr(e)[:60]]
            arrays[(n.node_type.split('.')[-2], tuple(sorted(names)))] += 1
        elif isinstance(n, orm.Dict):
            dict_keys[tuple(sorted(n.keys()))[:40]] += 1
        elif isinstance(n, orm.ProcessNode):
            lab = n.process_label or n.node_type
            procs[lab][f'{n.process_state.value if n.process_state else None}:{n.exit_status}'] += 1
        elif isinstance(n, orm.StructureData) and len(attrs_struct) < a.max_struct:
            attrs_struct.append(n)
    rep['arrays'] = [{'type': t, 'names': list(k), 'count': c} for (t, k), c in arrays.most_common(60)]
    rep['dict_keysets'] = [{'keys': list(k), 'count': c} for k, c in dict_keys.most_common(40)]
    rep['processes'] = {k: dict(v) for k, v in sorted(procs.items(), key=lambda x: -sum(x[1].values()))}
    # provenance depth per structure: which process labels consume it (directly or via descendants)
    depth = Counter()
    per_struct = []
    for s in attrs_struct:
        qb = orm.QueryBuilder().append(orm.StructureData, filters={'id': s.pk}, tag='s').append(
            orm.ProcessNode, with_ancestors='s', project=['process_type'])
        labs = sorted({(pt or '').split(':')[-1].split('.')[-1] for (pt,) in qb.all()})
        depth[len(labs)] += 1
        per_struct.append({'uuid': s.uuid, 'formula': s.get_formula(mode='hill_compact'),
                           'n_sites': len(s.sites), 'n_descendant_process_types': len(labs),
                           'descendant_process_types': labs[:20],
                           'extras_keys': sorted(s.base.extras.keys())[:30],
                           'label': s.label[:80], 'has_description': bool(s.description)})
    rep['structures'] = {'count': len(attrs_struct), 'depth_hist': dict(sorted(depth.items()))}
    rep['structure_list'] = per_struct
    out = json.dumps(rep, indent=1, default=str)
    if a.out:
        open(a.out, 'w').write(out + '\n')
    s = dict(rep)
    s.pop('structure_list')
    print(json.dumps(s, indent=1, default=str)[:20000])


if __name__ == '__main__':
    main()
