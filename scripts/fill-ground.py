"""Refill grounded, masked copper from saved final copper with 0.20 mm clearance."""
import json,math
import routing_grid as g
from shapely.geometry import box,Point,LineString,Polygon
from shapely.ops import unary_union
from shapely.geometry.polygon import orient
net=next(k for k,v in g.nets.items() if v['name']=='GND');netid=g.nets[net]['source_net_id']
g.j[:]=[e for e in g.j if e['type']!='pcb_copper_pour']
# Legal, ordinary through-vias tie the perimeter of the two ground planes.
for sx,sy in [(-16.5,-16.5),(-16.5,16.5),(16.5,-16.5),(16.5,16.5),(-16.5,0),(16.5,0),(0,-16.9),(0,16.5)]:
 if any(e['type']=='pcb_via' and math.hypot(e['x']-sx,e['y']-sy)<.01 for e in g.j):continue
 vb=g.obstacle(net,.16,True);ix,iy=g.xy(sx,sy)
 if vb[0][iy,ix] or vb[1][iy,ix]:continue
 g.j.append({'type':'pcb_via','pcb_via_id':f'ground_stitch_{sx}_{sy}','x':sx,'y':sy,'layers':['top','inner1','inner2','bottom'],'hole_diameter':.25,'outer_diameter':.5,'source_net_id':netid,'subcircuit_connectivity_map_key':net,'subcircuit_id':'subcircuit_source_group_0'})

def pad(e):
 w=e.get('width',e.get('outer_width',e.get('outer_diameter',e.get('radius',0)*2)));h=e.get('height',e.get('outer_height',e.get('outer_diameter',e.get('radius',0)*2)))
 if abs(e.get('ccw_rotation',0)%180-90)<.01:w,h=h,w
 if e.get('shape')=='circle':return Point(e['x'],e['y']).buffer(w/2,quad_segs=16)
 return box(e['x']-w/2,e['y']-h/2,e['x']+w/2,e['y']+h/2)
records=[]
for layer in ['top','inner1','inner2','bottom']:
 cuts=[];terminals=[]
 for e in g.j:
  typ=e['type']
  if typ in ['pcb_smtpad','pcb_plated_hole'] and layer in e.get('layers',[e.get('layer','top')]):
   geom=pad(e)
   if g.key(e)==net:terminals.append(geom)
   else:cuts.append(geom.buffer(.20,quad_segs=16))
  elif typ=='pcb_via':
   geom=Point(e['x'],e['y']).buffer(e['outer_diameter']/2,quad_segs=16)
   if g.key(e)==net:terminals.append(geom)
   else:cuts.append(geom.buffer(.20,quad_segs=16))
  elif typ=='pcb_trace' and g.key(e)!=net:
   for a,b in zip(e['route'],e['route'][1:]):
    if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']==layer:cuts.append(LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2+.20,quad_segs=16))
  elif typ=='pcb_hole':cuts.append(Point(e['x'],e['y']).buffer(e['hole_diameter']/2+.25,quad_segs=16))
  elif typ=='pcb_keepout':
   c=e['center'];cuts.append(box(c['x']-e['width']/2-.20,c['y']-e['height']/2-.20,c['x']+e['width']/2+.20,c['y']+e['height']/2+.20))
 region=box(-17.15,-17.15,17.15,17.15).difference(unary_union(cuts));polys=[region] if region.geom_type=='Polygon' else list(region.geoms)
 for i,p in enumerate(polys):
  if p.area<.02 or not any(p.intersects(t) for t in terminals):continue
  p=orient(p,sign=-1);vertices=lambda ring:[{'x':round(x,6),'y':round(y,6)} for x,y in list(ring.coords)[:-1]]
  e={'type':'pcb_copper_pour','pcb_copper_pour_id':f'ground_{layer}_{i}','source_net_id':netid,'subcircuit_connectivity_map_key':net,'subcircuit_id':'subcircuit_source_group_0','layer':layer,'shape':'brep','covered_with_solder_mask':True,'brep_shape':{'outer_ring':{'vertices':vertices(p.exterior)},'inner_rings':[{'vertices':vertices(r)} for r in p.interiors]}}
  g.j.append(e);records.append({'layer':layer,'areaMm2':p.area,'holes':len(p.interiors)})
g.path.write_text(json.dumps(g.j,indent=2)+'\n');(g.ROOT/'artifacts/ground-planes.json').write_text(json.dumps({'clearanceMm':.20,'edgeMarginMm':.35,'regions':records},indent=2)+'\n');print('Filled',len(records),'ground regions')
