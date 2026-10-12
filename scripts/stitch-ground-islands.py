"""Join actual ground islands with through vias only in independently clear copper.

All ground lands remain subject to final native DRC, physical connectivity,
independent Gerber comparison and the strict three-site via-in-pad policy.
"""
import hashlib,json,math
import verify_supplier_connectivity as g
from shapely.geometry import Point,Polygon,LineString,box
from shapely.ops import unary_union
board=next(e for e in g.j if e['type']=='pcb_board');layers=['top','bottom'] if board['num_layers']==2 else ['top','inner1','inner2','bottom'];net=next(k for k,v in g.nets.items() if v=='GND');sid=next(e['source_net_id'] for e in g.j if e['type']=='source_net' and e['name']=='GND');trace=next(e['source_trace_id'] for e in g.j if e['type']=='source_trace' and e.get('subcircuit_connectivity_map_key')==net)
diameter=board['min_via_pad_diameter'];hole=board['min_via_hole_diameter'];rad=diameter/2
obstacles=[]
for e in g.j:
 typ=e['type']
 if typ in ['pcb_smtpad','pcb_plated_hole']:
  obstacles.append(g.geometry(e).buffer(rad+(.003 if g.key(e)==net else .153)))
 elif typ=='pcb_via':obstacles.append(Point(e['x'],e['y']).buffer(rad+e['outer_diameter']/2+.003 if g.key(e)==net else rad+e['outer_diameter']/2+.153))
 elif typ=='pcb_trace' and g.key(e)!=net:
  for a,b in zip(e['route'],e['route'][1:]):
   if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']:obstacles.append(LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2+rad+.153))
 elif typ=='pcb_keepout':
  c=e['center'];r=e['radius'];obstacles.append(box(c['x']-r,c['y']-r,c['x']+r,c['y']+r).buffer(rad+.153))
 elif typ=='pcb_hole':obstacles.append(Point(e['x'],e['y']).buffer(e['hole_diameter']/2+rad+.253))
allowed=box(-17.15+rad,-17.15+rad,17.15-rad,17.15-rad).difference(unary_union(obstacles));stitches=[]
def shapes(e):
 typ=e['type']
 if typ in ['pcb_smtpad','pcb_plated_hole']:
  for l in e.get('layers',[e.get('layer','top')]):yield l,g.geometry(e)
 elif typ=='pcb_via':
  for l in e['layers']:yield l,Point(e['x'],e['y']).buffer(e['outer_diameter']/2)
 elif typ=='pcb_copper_pour':
  b=e['brep_shape'];pts=lambda r:[(p['x'],p['y']) for p in r['vertices']];yield e['layer'],Polygon(pts(b['outer_ring']),[pts(r) for r in b.get('inner_rings',[])])
 elif typ=='pcb_trace':
  for a,b in zip(e['route'],e['route'][1:]):
   if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']:yield a['layer'],LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2)
for attempt in range(120):
 elems,roots=g.groups(net);lands={};regions={}
 for e,r in zip(elems,roots):
  if e.get('pcb_port_id'):lands.setdefault(r,set()).add(e['pcb_port_id'])
  for l,poly in shapes(e):regions.setdefault(r,{}).setdefault(l,[]).append(poly)
 if len(lands)<=1:break
 main=max(lands,key=lambda r:len(lands[r]));geom={r:{l:unary_union(ps) for l,ps in ls.items()} for r,ls in regions.items()};found=None
 for r in sorted((r for r in lands if r!=main),key=lambda r:len(lands[r])):
  for la,a in geom[r].items():
   for lb,b in geom[main].items():
    if la==lb:continue
    area=a.intersection(b).intersection(allowed).buffer(-.005)
    if area.is_empty:continue
    p=area.representative_point();x,y=round(p.x,6),round(p.y,6)
    if not area.covers(Point(x,y)):continue
    found=(r,x,y,la,lb);break
   if found:break
  if found:break
 if not found:break
 r,x,y,la,lb=found;uid='feedback_ground_stitch_'+str(attempt)
 while any(e.get('pcb_via_id')==uid for e in g.j):uid+='_next'
 g.j.append({'type':'pcb_via','pcb_via_id':uid,'x':x,'y':y,'outer_diameter':diameter,'hole_diameter':hole,'layers':layers,'from_layer':'top','to_layer':'bottom','source_net_id':sid,'source_trace_id':trace,'subcircuit_connectivity_map_key':net,'subcircuit_id':'subcircuit_source_group_0','tented_on_top':True,'tented_on_bottom':True})
 allowed=allowed.difference(Point(x,y).buffer(diameter+.003));stitches.append({'via':uid,'xy_mm':[x,y],'isolated_ports':sorted(lands[r]),'joins_layers':[la,lb]});print(stitches[-1],flush=True)
g.path.write_text(json.dumps(g.j,indent=2)+'\n');out=g.ROOT/'artifacts/reference-feedback/ground-stitching.json';out.write_text(json.dumps({'stitches':stitches,'remaining_ground_roots':len(lands),'strict_no_additional_via_in_pad':True,'all_layer_clearance_mm':.15,'board_sha256':hashlib.sha256(g.path.read_bytes()).hexdigest()},indent=2)+'\n');print('Ground roots remaining:',len(lands))
