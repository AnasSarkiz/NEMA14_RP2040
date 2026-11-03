"""Refill grounded, masked copper with a verified >=0.15 mm clearance."""
import json,math,sys
from pathlib import Path
from v2_route_io import g
g.nets={e["subcircuit_connectivity_map_key"]:e for e in g.j if e["type"]=="source_net"}
from shapely.geometry import box,Point,LineString,Polygon
from shapely.ops import unary_union
from shapely.geometry.polygon import orient
net=next(k for k,v in g.nets.items() if v['name']=='GND');netid=g.nets[net]['source_net_id']
g.j[:]=[e for e in g.j if e['type']!='pcb_copper_pour']
records=[]
clearance=float(next((q.split('=',1)[1] for q in sys.argv if q.startswith('--clearance-mm=')),.16))
assert .16<=clearance<=.20,'Plane construction retains at least 0.01 mm margin over the board clearance'
layers=['top','bottom'] if next(e for e in g.j if e['type']=='pcb_board')['num_layers']==2 else ['top','inner1','inner2','bottom']
for layer in layers:
 cuts=[];terminals=[]
 for e in g.j:
  typ=e['type']
  if typ in ['pcb_smtpad','pcb_plated_hole'] and layer in e.get('layers',[e.get('layer','top')]):
   geom=g.geometry(e)
   if g.key(e)==net:terminals.append(geom)
   else:cuts.append(geom.buffer(clearance,quad_segs=16))
  elif typ=='pcb_via':
   geom=Point(e['x'],e['y']).buffer(e['outer_diameter']/2,quad_segs=16)
   if g.key(e)==net:terminals.append(geom)
   else:cuts.append(geom.buffer(clearance,quad_segs=16))
  elif typ=='pcb_trace' and g.key(e)!=net:
   for a,b in zip(e['route'],e['route'][1:]):
    if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']==layer:cuts.append(LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2+clearance,quad_segs=16))
  elif typ=='pcb_hole':
   if e['hole_shape']=='circle':hole=Point(e['x'],e['y']).buffer(e['hole_diameter']/2+.26,quad_segs=64)
   else:
    from shapely.affinity import rotate
    w,h=e['hole_width'],e['hole_height'];dx,dy=((w-h)/2,0) if w>=h else (0,(h-w)/2)
    hole=rotate(LineString([(e['x']-dx,e['y']-dy),(e['x']+dx,e['y']+dy)]).buffer(min(w,h)/2+.26,quad_segs=64),e.get('ccw_rotation',0),origin=(e['x'],e['y']))
   cuts.append(hole)
  elif typ=='pcb_keepout' and layer in e['layers']:
   c=e['center']
   if e['shape']=='circle':cuts.append(Point(c['x'],c['y']).buffer(e['radius']+.20,quad_segs=64))
   else:cuts.append(box(c['x']-e['width']/2-.20,c['y']-e['height']/2-.20,c['x']+e['width']/2+.20,c['y']+e['height']/2+.20))
 region=box(-16.9,-16.9,16.9,16.9).difference(unary_union(cuts)).simplify(.001,preserve_topology=True);polys=[region] if region.geom_type=='Polygon' else list(region.geoms)
 for i,p in enumerate(polys):
  if p.area<.02 or not any(p.intersects(t) for t in terminals):continue
  vertices=lambda ring:[{'x':round(x,6),'y':round(y,6)} for x,y in list(ring.coords)[:-1]]
  rounded=lambda ring:[(v['x'],v['y']) for v in vertices(ring)]
  exact=Polygon(rounded(p.exterior),[rounded(r) for r in p.interiors]).buffer(0)
  pieces=[exact] if exact.geom_type=='Polygon' else list(exact.geoms)
  # A pinched neck can split after source precision rounding. Separate BReps
  # prevent a disconnected island from sharing a connected record's identity.
  for piece_index,piece in enumerate(pieces):
   if piece.area<.02 or not any(piece.intersects(t) for t in terminals):continue
   piece=orient(piece,sign=-1)
   record={'type':'pcb_copper_pour','pcb_copper_pour_id':f'ground_{layer}_{i}_{piece_index}','source_net_id':netid,'subcircuit_connectivity_map_key':net,'subcircuit_id':'subcircuit_source_group_0','layer':layer,'shape':'brep','covered_with_solder_mask':True,'brep_shape':{'outer_ring':{'vertices':vertices(piece.exterior)},'inner_rings':[{'vertices':vertices(r)} for r in piece.interiors]}}
   g.j.append(record);records.append({'layer':layer,'areaMm2':piece.area,'holes':len(piece.interiors)})
  continue
g.path.write_text(json.dumps(g.j,indent=2)+'\n')
report=Path(next((q.split('=',1)[1] for q in sys.argv if q.startswith('--report=')),g.ROOT/'artifacts/v2/routing/ground-planes.json'))
report.write_text(json.dumps({'clearanceMm':clearance,'edgeMarginMm':.35,'regions':records},indent=2)+'\n')
print('Filled',len(records),'ground regions')
