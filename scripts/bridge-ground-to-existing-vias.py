"""Join isolated ground lands to existing return barrels without ripping foreign copper."""
import json,math
from shapely.geometry import Point,LineString,box
from shapely.strtree import STRtree
import verify_supplier_connectivity as g
key=next(k for k,v in g.nets.items() if v=='GND');net=next(e for e in g.j if e['type']=='source_net' and e['name']=='GND');records=[]
for attempt in range(40):
 es,rs=g.groups(key);lands={}
 for e,r in zip(es,rs):
  if e.get('pcb_port_id'):lands.setdefault(r,[]).append(e)
 if len(lands)<2:break
 main=max(lands,key=lambda r:len(lands[r]));vias=[e for e,r in zip(es,rs) if r==main and e['type']=='pcb_via'];found=None
 for root in sorted((r for r in lands if r!=main),key=lambda r:len(lands[r])):
  for land in lands[root]:
   p=g.ports[land['pcb_port_id']];a=(p['x'],p['y']);layer=land.get('layer','top')
   for v in sorted(vias,key=lambda v:math.dist(a,(v['x'],v['y']))):
    b=(v['x'],v['y'])
    if math.dist(a,b)>5:continue
    for pts in [[a,b],[a,(b[0],a[1]),b],[a,(a[0],b[1]),b]]:
     if LineString(pts).length>6:continue
     shape=LineString(pts).buffer(.08);bad=False
     if not box(-17.15,-17.15,17.15,17.15).covers(shape):continue
     for e in g.j:
      if g.key(e)==key:continue
      typ=e['type'];shapes=[];limit=.153
      if typ in ['pcb_smtpad','pcb_plated_hole'] and layer in e.get('layers',[e.get('layer','top')]):shapes=[g.geometry(e)];limit=.253 if typ=='pcb_plated_hole' else .153
      elif typ=='pcb_via':shapes=[Point(e['x'],e['y']).buffer(e['outer_diameter']/2)]
      elif typ=='pcb_trace':shapes=[LineString([(aa['x'],aa['y']),(bb['x'],bb['y'])]).buffer(max(aa['width'],bb['width'])/2) for aa,bb in zip(e['route'],e['route'][1:]) if aa['route_type']==bb['route_type']=='wire' and aa['layer']==bb['layer']==layer]
      elif typ=='pcb_keepout':shapes=[Point(e['center']['x'],e['center']['y']).buffer(e['radius'],quad_segs=128)]
      elif typ=='pcb_hole':shapes=[Point(e['x'],e['y']).buffer(e['hole_diameter']/2)];limit=.253
      if any(shape.distance(s)<limit for s in shapes):bad=True;break
     if not bad:found=(p,pts,layer,v);break
    if found:break
   if found:break
  if found:break
 if not found:break
 p,pts,layer,v=found;uid='reviewed_local_ground_bridge_'+p['pcb_port_id']
 while any(e.get('pcb_trace_id')==uid for e in g.j):uid+='_next'
 source=next(e['source_trace_id'] for e in g.j if e['type']=='source_trace' and e.get('subcircuit_connectivity_map_key')==key and p['source_port_id'] in e.get('connected_source_port_ids',[]));route=[dict(route_type='wire',x=x,y=y,layer=layer,width=.16) for x,y in pts];route[0]['start_pcb_port_id']=p['pcb_port_id']
 g.j.append(dict(type='pcb_trace',pcb_trace_id=uid,route=route,pcb_port_ids=[p['pcb_port_id']],source_net_id=net['source_net_id'],source_trace_id=source,subcircuit_connectivity_map_key=key,subcircuit_id='subcircuit_source_group_0'));records.append({'trace':uid,'points_mm':pts,'layer':layer,'existing_return_via':v['pcb_via_id']});print(records[-1],flush=True)
g.path.write_text(json.dumps(g.j,indent=2)+'\n');(g.ROOT/'artifacts/opposite-edge/ground-existing-return-bridges.json').write_text(json.dumps(records,indent=2)+'\n');print('Ground pad groups remaining',len(lands))
