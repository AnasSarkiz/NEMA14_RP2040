"""Prune obsolete copper leaves at physical same-net junctions, not by labels.
Only shorten dangling first/last trace tails; never add a bridging segment.
Independent connectivity and DRC/CAM must pass after this operation.
"""
import verify_supplier_connectivity as g
import json,hashlib
from shapely.geometry import Polygon,Point,LineString
from shapely.ops import unary_union
j=g.j;changes=[]
def other(trace,layer):
 shapes=[];net=g.key(trace)
 for e in j:
  if e is trace or g.key(e)!=net:continue
  t=e['type']
  if t in ['pcb_smtpad','pcb_plated_hole']and layer in e.get('layers',[e.get('layer')]):shapes.append(g.geometry(e))
  elif t=='pcb_via'and layer in e['layers']:shapes.append(Point(e['x'],e['y']).buffer(e['outer_diameter']/2))
  elif t=='pcb_copper_pour'and e['layer']==layer:
   b=e['brep_shape'];coords=lambda r:[(p['x'],p['y'])for p in r['vertices']];shapes.append(Polygon(coords(b['outer_ring']),[coords(r)for r in b.get('inner_rings',[])]))
  elif t=='pcb_trace':
   for a,b in zip(e['route'],e['route'][1:]):
    if a['route_type']==b['route_type']=='wire'and a['layer']==b['layer']==layer:shapes.append(LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2))
 return unary_union(shapes)
for e in j.copy():
 if e['type']!='pcb_trace':continue
 before=json.loads(json.dumps(e['route']))
 for reverse in [False,True]:
  r=list(reversed(e['route']))if reverse else e['route'][:]
  if len(r)<2 or r[0]['route_type']!='wire':continue
  layer=r[0]['layer'];shape=other(e,layer)
  if Point(r[0]['x'],r[0]['y']).distance(shape)<r[0]['width']/2-.002:continue
  found=None
  for i,(a,b)in enumerate(zip(r,r[1:])):
   if a['route_type']!=b['route_type']or a['route_type']!='wire'or a['layer']!=b['layer']:break
   line=LineString([(a['x'],a['y']),(b['x'],b['y'])]);hit=line.intersection(shape.buffer(min(a['width'],b['width'])/2-.005))
   if hit.is_empty:continue
   pieces=list(hit.geoms)if hasattr(hit,'geoms')else[hit];points=[]
   for p in pieces:
    if p.geom_type=='Point':points.append(p)
    elif hasattr(p,'coords'):points.extend(Point(c)for c in p.coords)
   if not points:continue
   cut=min(line.project(p)for p in points);cut=min(line.length,cut+.01);p=line.interpolate(cut);first={**a,'x':p.x,'y':p.y};first.pop('start_pcb_port_id',None);first.pop('end_pcb_port_id',None);found=[first]+r[i+1:];break
  if found:e['route']=list(reversed(found))if reverse else found
 if e['route']!=before:
  changes.append({'trace':e['pcb_trace_id'],'net':g.nets.get(g.key(e)),'before':before,'after':e['route']});e['pcb_port_ids']=[]
# Remove only physically unanchored traces/vias, never a component/pad.
dropped=[]
for net in {g.key(e)for e in j if e['type']in['pcb_trace','pcb_via']}:
 es,roots=g.groups(net);anchored={r for e,r in zip(es,roots)if e.get('pcb_port_id')}
 for e,r in zip(es,roots):
  if r not in anchored and e['type']in['pcb_trace','pcb_via']:dropped.append(e.get(e['type']+'_id'))
j=[e for e in j if e.get(e['type']+'_id')not in dropped];g.path.write_text(json.dumps(j,indent=2)+'\n');(g.ROOT/'artifacts/validation/service-stub-prune.json').write_text(json.dumps({'method':'Only dangling endpoint tails shortened to an interior physical junction; no new copper segments; terminal-free trace/via groups removed.','trimmed':changes,'orphan_copper_removed':dropped,'boardSha256':hashlib.sha256(g.path.read_bytes()).hexdigest()},indent=2)+'\n');print('Pruned',len(changes),'traces;',len(dropped),'orphan records')
