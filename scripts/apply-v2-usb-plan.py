"""Prioritize the four USB nets; reroute displaced lower-priority escapes."""
import hashlib
import json
from pathlib import Path
from shapely.geometry import LineString, Point
import verify_supplier_connectivity as g

plan=json.loads((g.ROOT/'artifacts/v2/routing/plans/usb.circuit.json').read_text())
names={e['subcircuit_connectivity_map_key']:e['name'] for e in g.j if e['type']=='source_net'}
usb={k for k,v in names.items() if v in ['USB_DP','USB_DM','MCU_DP','MCU_DM']}
new=[e for e in plan if e['type'] in ['pcb_trace','pcb_via'] and g.key(e) in usb]
assert len([e for e in new if e['type']=='pcb_trace'])>=10
def pieces(e):
    if e['type']=='pcb_via':return [(l,Point(e['x'],e['y']).buffer(e['outer_diameter']/2)) for l in e['layers']]
    return [(a['layer'],LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2)) for a,b in zip(e['route'],e['route'][1:]) if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']]
shapes=[(l,p) for e in new for l,p in pieces(e)]
rip=set()
for e in g.j:
    if e['type'] not in ['pcb_trace','pcb_via'] or g.key(e) in usb:continue
    if any(l==m and p.distance(q)<.15-1e-6 for l,p in shapes for m,q in pieces(e)):
        assert not e.get(e['type']+'_id','').startswith(('oscillator_v2_','v2_thermal_'))
        rip.add(e[e['type']+'_id'])
dead=[e for e in g.j if e['type']=='pcb_via' and e['pcb_via_id'] in rip]
for e in g.j:
    if e['type']=='pcb_trace' and any(any(abs(q['x']-v['x'])<1e-6 and abs(q['y']-v['y'])<1e-6 for q in e['route']) for v in dead):
        assert not e['pcb_trace_id'].startswith('oscillator_v2_')
        rip.add(e['pcb_trace_id'])
g.j[:]=[e for e in g.j if not (e['type'] in ['pcb_trace','pcb_via'] and (g.key(e) in usb or e[e['type']+'_id'] in rip))]
for i,e in enumerate(new):e[e['type']+'_id']='usb_v2_'+e['type']+'_'+str(i)
g.j.extend(new)
g.path.write_text(json.dumps(g.j,indent=2)+'\n')
(g.ROOT/'artifacts/v2/routing/usb-priority-plan.json').write_text(json.dumps({'routed_source_sha256':hashlib.sha256(g.path.read_bytes()).hexdigest(),'added_copper':[e[e['type']+'_id'] for e in new],'removed_obstructions':sorted(rip)},indent=2)+'\n')
print(json.dumps({'usb_records':len(new),'displaced_records':len(rip)}))
