"""Merge fresh native geometry, rerouting only copper affected by moved lands.

Courtyard space beneath component bodies is not an electrical copper obstacle.
Native pads, all source pins and original net identities remain authoritative.
"""
import json,sys
from shapely.geometry import Point,LineString
import verify_supplier_connectivity as g
fresh=json.load(open('artifacts/final-source.circuit.json'));names=set(sys.argv[1:]);assert not [e for e in fresh if e['type'].endswith('_error')],'Fresh source has errors'
fs={e['source_port_id']:e for e in fresh if e['type']=='source_port'}
assert fs.keys()==g.sp.keys()
for id,p in g.sp.items():
 for k in ['pin_number','name','source_component_id','subcircuit_connectivity_map_key']:assert p.get(k)==fs[id].get(k),(id,k)
def pads(data):
 ss={e['source_component_id']:e['name'] for e in data if e['type']=='source_component'};cc={e['pcb_component_id']:e for e in data if e['type']=='pcb_component'}
 return [e for e in data if e['type'] in ['pcb_smtpad','pcb_plated_hole'] and ss[cc[e['pcb_component_id']]['source_component_id']] in names]
old,new=pads(g.j),pads(fresh);changed_ports={e['pcb_port_id'] for e in old};kept=[];removed=[]
def layers(e):return e.get('layers',[e.get('layer','top')])
for e in g.j:
 typ=e['type']
 if typ not in ['pcb_trace','pcb_via']:continue
 hit=False
 if typ=='pcb_trace':
  if set(e.get('pcb_port_ids',[]))&changed_ports:hit=True
  for a,b in zip(e['route'],e['route'][1:]):
   if hit:break
   if a['route_type']!=b['route_type'] or a['route_type']!='wire' or a['layer']!=b['layer']:continue
   geom=LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2)
   if any(a['layer'] in layers(p) and g.key(e)==g.key(p) and geom.intersects(g.geometry(p)) for p in old):hit=True
   if any(a['layer'] in layers(p) and g.key(e)!=g.key(p) and geom.distance(g.geometry(p))<.153 for p in new):hit=True
 elif typ=='pcb_via':
  geom=Point(e['x'],e['y']).buffer(e['outer_diameter']/2)
  if any(geom.distance(g.geometry(p))<(.003 if g.key(e)==g.key(p) else .153) for p in new):hit=True
 if hit:removed.append({'id':e.get('pcb_trace_id',e.get('pcb_via_id')),'net':g.nets.get(g.key(e))})
 else:kept.append(e)
board=[{**e,'is_via_in_pad_allowed':True} if e['type']=='pcb_board' else e for e in fresh if e['type'] not in ['pcb_trace','pcb_via','pcb_copper_pour'] and not e['type'].endswith(('_error','_warning'))]+kept
g.path.write_text(json.dumps(board,indent=2)+'\n');out=g.ROOT/'artifacts/reference-feedback/selective-placement-merges.json';hist=json.loads(out.read_text()) if out.exists() else [];hist.append({'changed_components':sorted(names),'removed_actual_affected_copper':removed,'unaffected_copper_retained':len(kept),'source_pin_roles_preserved':True});out.write_text(json.dumps(hist,indent=2)+'\n');print('Selective native geometry merge',sorted(names),'rerouting',removed)
