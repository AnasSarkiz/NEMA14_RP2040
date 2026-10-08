"""Refill grounded, masked copper from saved final copper with 0.20 mm clearance."""
import json,math
import verify_supplier_connectivity as g
g.nets={e["subcircuit_connectivity_map_key"]:e for e in g.j if e["type"]=="source_net"}
from shapely.geometry import box,Point,LineString,Polygon
from shapely.ops import unary_union
from shapely.geometry.polygon import orient
net=next(k for k,v in g.nets.items() if v['name']=='GND');netid=g.nets[net]['source_net_id']
g.j[:]=[e for e in g.j if e['type']!='pcb_copper_pour' or g.key(e)!=net]
# A standalone source-net label on a via does not establish a grounded barrel.
# Require an existing copper island containing a mapped physical GND terminal.
elements,roots=g.groups(net)
anchored_roots={r for e,r in zip(elements,roots) if e.get('pcb_port_id')}
anchored_vias={e['pcb_via_id'] for e,r in zip(elements,roots) if e['type']=='pcb_via' and r in anchored_roots}
records=[];discarded=[]
layers=['top','bottom'] if next(e for e in g.j if e['type']=='pcb_board')['num_layers']==2 else ['top','inner1','inner2','bottom']
for layer in layers:
 cuts=[];terminals=[]
 for e in g.j:
  typ=e['type']
  if typ in ['pcb_smtpad','pcb_plated_hole'] and layer in e.get('layers',[e.get('layer','top')]):
   geom=g.geometry(e)
   if g.key(e)==net:terminals.append(geom)
   else:cuts.append(geom.buffer(.20,quad_segs=16))
  elif typ=='pcb_via':
   geom=Point(e['x'],e['y']).buffer(e['outer_diameter']/2,quad_segs=16)
   if g.key(e)==net:
    if e['pcb_via_id'] in anchored_vias:terminals.append(geom)
   else:cuts.append(geom.buffer(.20,quad_segs=16))
  elif typ=='pcb_trace' and g.key(e)!=net:
   for a,b in zip(e['route'],e['route'][1:]):
    if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']==layer:cuts.append(LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2+.20,quad_segs=16))
  elif typ=='pcb_copper_pour' and e['layer']==layer and g.key(e)!=net:
   b=e['brep_shape'];pts=lambda r:[(p['x'],p['y']) for p in r['vertices']];cuts.append(Polygon(pts(b['outer_ring']),[pts(r) for r in b.get('inner_rings',[])]).buffer(.20,quad_segs=16))
  elif typ=='pcb_hole':cuts.append(Point(e['x'],e['y']).buffer(e['hole_diameter']/2+.25,quad_segs=16))
  elif typ=='pcb_keepout':
   cuts.append(g.keepout_geometry(e).buffer(.20))
 region=box(-17.15,-17.15,17.15,17.15).difference(unary_union(cuts))
 # Remove bridges narrower than 0.15mm before checking each physical polygon.
 # Intersect with the original region so rounding never reduces foreign clearance.
 region=region.buffer(-.075,quad_segs=16).buffer(.075,quad_segs=16).intersection(region)
 polys=[region] if region.geom_type=='Polygon' else list(region.geoms)
 for i,p in enumerate(polys):
  if p.area<.02 or not any(p.intersects(t) for t in terminals):
   discarded.append({'layer':layer,'areaMm2':p.area,'bounds':list(p.bounds),'reason':'belowMinimumAreaOrNoMappedGroundPadOrAnchoredBarrel'});continue
  p=orient(p,sign=-1);vertices=lambda ring:[{'x':round(x,6),'y':round(y,6)} for x,y in list(ring.coords)[:-1]]
  e={'type':'pcb_copper_pour','pcb_copper_pour_id':f'ground_{layer}_{i}','source_net_id':netid,'subcircuit_connectivity_map_key':net,'subcircuit_id':'subcircuit_source_group_0','layer':layer,'shape':'brep','covered_with_solder_mask':True,'brep_shape':{'outer_ring':{'vertices':vertices(p.exterior)},'inner_rings':[{'vertices':vertices(r)} for r in p.interiors]}}
  g.j.append(e);records.append({'layer':layer,'areaMm2':p.area,'holes':len(p.interiors)})
# Emit ground first and separately isolated, hole-free heat copper last.
# This is canonical record order only; native land patterns stay unchanged.
ordinary=[e for e in g.j if e['type']!='pcb_copper_pour']
ground_pours=[e for e in g.j if e['type']=='pcb_copper_pour' and g.key(e)==net]
foreign_pours=[e for e in g.j if e['type']=='pcb_copper_pour' and g.key(e)!=net]
g.j[:]=ordinary+ground_pours+foreign_pours
g.path.write_text(json.dumps(g.j,indent=2)+'\n');(g.ROOT/'artifacts/ground-planes.json').write_text(json.dumps({'clearanceMm':.20,'edgeMarginMm':.35,'minimumPourNeckMm':.15,'requiresMappedGroundPadOrAnchoredBarrel':True,'regions':records,'discardedPolygons':discarded},indent=2)+'\n');print('Filled',len(records),'ground regions')
