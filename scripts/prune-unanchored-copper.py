"""Remove only physical-net copper islands with no native source pad contact."""
import verify_supplier_connectivity as g
import json,hashlib
removed=[]
for net in g.nets:
 elems,roots=g.groups(net);anchors={r for e,r in zip(elems,roots) if e['type'] in ['pcb_smtpad','pcb_plated_hole'] and e.get('pcb_port_id')}
 removed.extend(e for e,r in zip(elems,roots) if r not in anchors and e['type'] in ['pcb_trace','pcb_via','pcb_copper_pour'])
g.j[:]=[e for e in g.j if e not in removed];g.path.write_text(json.dumps(g.j,indent=2)+'\n');(g.ROOT/'artifacts/unanchored-copper-removal.json').write_text(json.dumps({'removed':removed,'nativePadRecordsChanged':False,'reason':'Island has no same-net physical contact with any native source pad; all conductive layers/barrels included in independent graph.','savedSHA256':hashlib.sha256(g.path.read_bytes()).hexdigest()},indent=2)+'\n');print('Removed',len(removed),'unanchored copper records')
