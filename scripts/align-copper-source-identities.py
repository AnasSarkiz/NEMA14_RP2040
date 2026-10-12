"""Associate each actual copper island with source traces for its real lands.

This changes source-trace references only. Coordinates, widths, vias, net IDs
and connectivity keys are unchanged; physical open nets remain mandatory errors.
"""
import hashlib,json
import verify_supplier_connectivity as g
traces=[e for e in g.j if e['type']=='source_trace'];changes=[]
for net in g.nets:
 elems,roots=g.groups(net);lands={}
 for e,r in zip(elems,roots):
  if e.get('pcb_port_id'):lands.setdefault(r,set()).add(g.ports[e['pcb_port_id']]['source_port_id'])
 for e,r in zip(elems,roots):
  if e['type'] not in ['pcb_trace','pcb_via'] or r not in lands:continue
  actual=set()
  for pid in e.get('pcb_port_ids',[]):
   if pid in g.ports:actual.add(g.ports[pid]['source_port_id'])
  options=[t for t in traces if t.get('subcircuit_connectivity_map_key')==net and set(t.get('connected_source_port_ids',[])) & (actual or lands[r])]
  if not options:continue
  chosen=options[0]['source_trace_id']
  if e.get('source_trace_id')!=chosen:changes.append({'element':e.get('pcb_trace_id',e.get('pcb_via_id')),'old_source_trace':e.get('source_trace_id'),'new_source_trace':chosen});e['source_trace_id']=chosen

g.path.write_text(json.dumps(g.j,indent=2)+'\n');(g.ROOT/'artifacts/reference-feedback/copper-source-identities.json').write_text(json.dumps({'geometry_and_net_keys_unchanged':True,'changes':changes,'board_sha256':hashlib.sha256(g.path.read_bytes()).hexdigest()},indent=2)+'\n');print('Aligned',len(changes),'copper source identities with their actual physical lands')
