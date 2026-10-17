"""Clear only foreign legacy copper obstructing the explicit reviewed USB escapes."""
import json
import verify_supplier_connectivity as g
from shapely.geometry import LineString,Point
seed=[]
for e in g.j:
 if e['type']=='pcb_trace' and e['pcb_trace_id'].startswith('usb_'):
  for a,b in zip(e['route'],e['route'][1:]):
   if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']:seed.append((g.key(e),[a['layer']],LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2)))
 elif e['type']=='pcb_via' and e['pcb_via_id'].startswith('usb_'):seed.append((g.key(e),e['layers'],Point(e['x'],e['y']).buffer(e['outer_diameter']/2)))
from shapely.strtree import STRtree
layers=['top','inner1','inner2','bottom'];bylayer={l:[(net,shape) for net,ls,shape in seed if l in ls] for l in layers};trees={l:STRtree([q[1] for q in bylayer[l]]) for l in layers}
def conflict(shape,ls,net):
 for l in ls:
  for i in trees[l].query(shape.buffer(.153),predicate='intersects'):
   owner,other=bylayer[l][int(i)]
   if owner!=net and shape.distance(other)<.153:return True
 return False
removed=[];kept=[]
for e in g.j:
 id=e.get(e['type']+'_id','');hit=False
 if e['type']=='pcb_trace' and not id.startswith('usb_'):
  hit=any(a['route_type']==b['route_type']=='wire' and a['layer']==b['layer'] and conflict(LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2),[a['layer']],g.key(e)) for a,b in zip(e['route'],e['route'][1:]))
 elif e['type']=='pcb_via' and not id.startswith('usb_'):hit=conflict(Point(e['x'],e['y']).buffer(e['outer_diameter']/2),e['layers'],g.key(e))
 if hit:
  assert not id.startswith('oscillator_'),'USB construction obstructs protected oscillator copper';removed.append(id)
 else:kept.append(e)
g.path.write_text(json.dumps(kept,indent=2)+'\n');print('Cleared obstructing legacy copper',len(removed),removed)
