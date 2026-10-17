import json
import verify_supplier_connectivity as g
from shapely.geometry import Point,LineString
holes=[Point(e['x'],e['y']).buffer(e['hole_diameter']/2+.205,quad_segs=128) for e in g.j if e['type']=='pcb_hole'];removed=[];keep=[]
for e in g.j:
 hit=False
 if e['type']=='pcb_trace':hit=any(a['route_type']==b['route_type']=='wire' and a['layer']==b['layer'] and any(LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2).intersects(h) for h in holes) for a,b in zip(e['route'],e['route'][1:]))
 if e['type']=='pcb_via':hit=any(Point(e['x'],e['y']).buffer(e['outer_diameter']/2).intersects(h) for h in holes)
 if hit:removed.append(e.get(e['type']+'_id'))
 else:keep.append(e)
g.path.write_text(json.dumps(keep,indent=2)+'\n');print('Removed copper conflicting with actual new holes',removed)
