"""Refresh copper metadata from actual same-net pad intersections.
No coordinates, widths, net assignments or conductive geometry change.
Independent physical connectivity and native/CAM clearance are still mandatory.
"""
import json,hashlib
from shapely.geometry import LineString,Point
from shapely.strtree import STRtree
import verify_supplier_connectivity as g
pads=[e for e in g.j if e['type'] in ['pcb_smtpad','pcb_plated_hole']];geoms=[g.geometry(e) for e in pads];tree=STRtree(geoms);changes=[]
for t in g.j:
 if t['type']!='pcb_trace':continue
 key=g.key(t);attached=set()
 for a,b in zip(t['route'],t['route'][1:]):
  if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']:
   shape=LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2)
   for i in tree.query(shape,predicate='intersects'):
    p=pads[i]
    if g.key(p)==key and a['layer'] in p.get('layers',[p.get('layer','top')]):attached.add(p['pcb_port_id'])
 for q in t['route']:
  for f in ['start_pcb_port_id','end_pcb_port_id']:
   if f not in q:continue
   p=next((p for p in pads if p.get('pcb_port_id')==q[f] and g.key(p)==key and q.get('layer') in p.get('layers',[p.get('layer','top')]) and g.geometry(p).buffer(.00001).covers(Point(q['x'],q['y']))),None)
   if p is None:del q[f]
 old=t.get('pcb_port_ids',[])
 if set(old)!=attached:changes.append(dict(trace=t['pcb_trace_id'],old=old,new=sorted(attached)));t['pcb_port_ids']=sorted(attached)
g.path.write_text(json.dumps(g.j,indent=2)+'\n');(g.ROOT/'artifacts/upright-revision/physical-contact-metadata.json').write_text(json.dumps(dict(board_sha256=hashlib.sha256(g.path.read_bytes()).hexdigest(),geometry_and_net_assignments_unchanged=True,changes=changes),indent=2)+'\n');print('Refreshed',len(changes),'trace contact lists from actual pad geometry')
