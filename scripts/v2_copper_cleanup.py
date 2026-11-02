"""Remove whole routed records that touch no physical terminal on any layer."""
from collections import defaultdict
import json

def prune_floating(g):
    remove=set()
    for net in g.nets:
        elements,roots=g.groups(net)
        attached={r for e,r in zip(elements,roots) if e.get('pcb_port_id')}
        records=defaultdict(list)
        for e,r in zip(elements,roots):
            if e['type'] in ['pcb_trace','pcb_via']:
                records[e[e['type']+'_id']].append(r in attached)
        remove.update(uid for uid,live in records.items() if not any(live))
    # Only islands with no supplier terminal are removed. No connection between
    # any pair of physical terminals can be lost by removing these islands.
    if remove:
        g.j[:]=[e for e in g.j if e.get(e['type']+'_id') not in remove]
        g.path.write_text(json.dumps(g.j,indent=2)+'\n')
        if g.path.resolve()==(g.ROOT/'artifacts/v2/routing/freerouted.circuit.json').resolve():
            path=g.ROOT/'artifacts/v2/routing/floating-copper-cleanup.json'
            history=json.loads(path.read_text()) if path.exists() else []
            history.append({'removed_ids':sorted(remove),'supplier_terminals_removed':0})
            path.write_text(json.dumps(history,indent=2)+'\n')
    return sorted(remove)
