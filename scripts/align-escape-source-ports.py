"""Bind each explicit pin escape to that pin's native source trace declaration."""
import verify_supplier_connectivity as g
import json
changes={}
for e in g.j:
 if e['type']!='pcb_trace'or not e['pcb_trace_id'].startswith(('inside_','outer_'))or len(e.get('pcb_port_ids',[]))!=1:continue
 p=g.ports[e['pcb_port_ids'][0]];st=next(e for e in g.j if e['type']=='source_trace'and p['source_port_id']in e['connected_source_port_ids']and g.key(e)==g.sp[p['source_port_id']]['subcircuit_connectivity_map_key']);e['source_trace_id']=st['source_trace_id'];changes[e['pcb_trace_id']]=st['source_trace_id']
for e in g.j:
 if e['type']=='pcb_via'and e.get('pcb_trace_id')in changes:e['source_trace_id']=changes[e['pcb_trace_id']]
g.path.write_text(json.dumps(g.j,indent=2)+'\n');print(json.dumps(changes,indent=2))
