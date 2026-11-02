"""Install the checked top-only oscillator paths and reserve their reference."""
import hashlib
import json
from pathlib import Path
from shapely.geometry import LineString, Point
import verify_supplier_connectivity as g

plan=json.loads((g.ROOT/'artifacts/v2/routing/plans/oscillator-top.circuit.json').read_text())
names={e['subcircuit_connectivity_map_key']:e['name'] for e in g.j if e['type']=='source_net'}
clock={k for k,v in names.items() if v in ['XIN','XOUT','XTAL_OUT']}
new=[e for e in plan if e['type']=='pcb_trace' and g.key(e) in clock]
assert len(new)==5
assert all(q['route_type']=='wire' and q['layer']=='top' for e in new for q in e['route'])
def pieces(e):
    if e['type']=='pcb_via':return [(l,Point(e['x'],e['y']).buffer(e['outer_diameter']/2)) for l in e['layers']]
    return [(a['layer'],LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2)) for a,b in zip(e['route'],e['route'][1:]) if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']]
shapes=[(l,p) for e in new for l,p in pieces(e)]
rip=set()
for e in g.j:
    if e['type'] not in ['pcb_trace','pcb_via'] or g.key(e) in clock:continue
    if any(l==m and p.distance(q)<.15-1e-6 for l,p in shapes for m,q in pieces(e)):
        assert not e.get(e['type']+'_id','').startswith(('v2_escape_','v2_thermal_')),'Clock would cross a protected escape'
        rip.add(e[e['type']+'_id'])
dead=[e for e in g.j if e['type']=='pcb_via' and e['pcb_via_id'] in rip]
for e in g.j:
    if e['type']=='pcb_trace' and any(any(abs(q['x']-v['x'])<1e-6 and abs(q['y']-v['y'])<1e-6 for q in e['route']) for v in dead):
        assert not e['pcb_trace_id'].startswith('v2_escape_')
        rip.add(e['pcb_trace_id'])
g.j[:]=[e for e in g.j if not (e['type'] in ['pcb_trace','pcb_via'] and (g.key(e) in clock or e[e['type']+'_id'] in rip))]
routes=[];used=set()
for i,e in enumerate(new):
    name=names[g.key(e)];e['pcb_trace_id']=f'oscillator_v2_{name}_{i}'
    points=[(q['x'],q['y']) for q in e['route']]
    label='oscillator_'+name if name not in used else 'oscillator_load_'+name
    used.add(name)
    routes.append({'trace':label,'pcb_trace_id':e['pcb_trace_id'],'net':name,'points':points,'length_mm':LineString(points).length})
g.j.extend(new)
g.path.write_text(json.dumps(g.j,indent=2)+'\n')
record={'source_sha256':hashlib.sha256(g.path.read_bytes()).hexdigest(),'routes':routes,'guard_buffer_mm':.25,'layers_reserved':['top','inner1'],'MCU_pin_local_exemption_radius_mm':.55,'removed_obstructing_copper':sorted(rip),'top_only':True,'oscillator_vias':0}
(g.ROOT/'artifacts/v2/routing/oscillator-plan.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'clock_paths':len(new),'removed_copper':len(rip),'top_only':True}))
