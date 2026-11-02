"""Retain routing after a placement refinement; remove stale local connections."""
import hashlib
import json
from pathlib import Path
from shapely.geometry import Point, LineString
import verify_supplier_connectivity as g

fresh_path=g.ROOT/'artifacts/v2/source.circuit.json'
fresh=json.loads(fresh_path.read_text())
old_source={e['source_port_id']:(e['source_component_id'],e['pin_number'],e.get('subcircuit_connectivity_map_key')) for e in g.j if e['type']=='source_port'}
new_source={e['source_port_id']:(e['source_component_id'],e['pin_number'],e.get('subcircuit_connectivity_map_key')) for e in fresh if e['type']=='source_port'}
assert old_source==new_source,'Source pin/net identities changed'
old_ports=g.ports
new_ports={e['pcb_port_id']:e for e in fresh if e['type']=='pcb_port'}
moved={p for p in old_ports if (old_ports[p]['x'],old_ports[p]['y'])!=(new_ports[p]['x'],new_ports[p]['y'])}
new_pads=[e for e in fresh if e['type'] in ['pcb_smtpad','pcb_plated_hole'] and e.get('pcb_port_id') in moved]
def pieces(e):
    if e['type']=='pcb_via':return [(l,Point(e['x'],e['y']).buffer(e['outer_diameter']/2)) for l in e['layers']]
    return [(a['layer'],LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2)) for a,b in zip(e['route'],e['route'][1:]) if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']]
rip=set()
for e in g.j:
    if e['type'] not in ['pcb_trace','pcb_via']:continue
    if e['type']=='pcb_trace' and (set(e.get('pcb_port_ids',[]))|{q.get(k) for q in e['route'] for k in ['start_pcb_port_id','end_pcb_port_id']})&moved:
        rip.add(e['pcb_trace_id']);continue
    for p in new_pads:
        shape=g.geometry(p)
        if e['type']=='pcb_via' and any(s.intersection(shape).area>1e-8 for l,s in pieces(e)):
            rip.add(e['pcb_via_id']);break
        if g.key(e)!=g.key(p) and any(l in p.get('layers',[p.get('layer','top')]) and s.distance(shape)<.15-1e-6 for l,s in pieces(e)):
            rip.add(e[e['type']+'_id']);break
dead=[e for e in g.j if e['type']=='pcb_via' and e['pcb_via_id'] in rip]
for e in g.j:
    if e['type']=='pcb_trace' and any(any(abs(q['x']-v['x'])<1e-6 and abs(q['y']-v['y'])<1e-6 for q in e['route']) for v in dead):rip.add(e['pcb_trace_id'])
fresh.extend(e for e in g.j if e['type'] in ['pcb_trace','pcb_via'] and e[e['type']+'_id'] not in rip)
for e in fresh:
    if e['type']=='pcb_board':e['is_via_in_pad_allowed']=True
g.path.write_text(json.dumps(fresh,indent=2)+'\n')
report={'placement_source_sha256':hashlib.sha256(fresh_path.read_bytes()).hexdigest(),'moved_ports':sorted(moved),'removed_stale_copper':sorted(rip),'routed_source_sha256':hashlib.sha256(g.path.read_bytes()).hexdigest()}
(g.ROOT/'artifacts/v2/routing/source-graft.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'moved_ports':len(moved),'removed_stale_copper':len(rip)}))
