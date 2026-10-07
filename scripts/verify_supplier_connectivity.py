"""Independent geometry check of every physical supplier pad and copper layer."""
import json,pathlib,hashlib
from shapely.geometry import Point,Polygon,LineString,box
from shapely.affinity import rotate
from shapely.strtree import STRtree
ROOT=pathlib.Path(__file__).resolve().parents[1];path=ROOT/'artifacts/board.circuit.json';j=json.loads(path.read_text());src={e['source_component_id']:e['name'] for e in j if e['type']=='source_component'};sp={e['source_port_id']:e for e in j if e['type']=='source_port'};ports={e['pcb_port_id']:e for e in j if e['type']=='pcb_port'};comp={e['pcb_component_id']:e for e in j if e['type']=='pcb_component'};nets={e['subcircuit_connectivity_map_key']:e['name'] for e in j if e['type']=='source_net'}
for p in sp.values():
 k=p.get('subcircuit_connectivity_map_key')
 if k and k not in nets:nets[k]='DIRECT_'+k.rsplit('_',1)[-1]
def key(e):
 if e['type'] in ['pcb_smtpad','pcb_plated_hole']:return sp.get(ports.get(e.get('pcb_port_id'),{}).get('source_port_id'),{}).get('subcircuit_connectivity_map_key')
 return e.get('subcircuit_connectivity_map_key')
def geometry(e):
 if e.get('shape')=='polygon':return Polygon([(p['x'],p['y']) for p in e['points']]).buffer(0)
 x,y=e['x'],e['y'];w=e.get('width',e.get('outer_width',e.get('outer_diameter',e.get('radius',0)*2)));h=e.get('height',e.get('outer_height',e.get('outer_diameter',e.get('radius',0)*2)))
 if e.get('shape')=='circle':g=Point(x,y).buffer(w/2)
 elif e.get('shape')=='pill':
  dx,dy=((w-h)/2,0) if w>=h else (0,(h-w)/2);g=LineString([(x-dx,y-dy),(x+dx,y+dy)]).buffer(min(w,h)/2)
 else:g=box(x-w/2,y-h/2,x+w/2,y+h/2)
 return rotate(g,e.get('ccw_rotation',0),origin=(x,y))
def groups(net):
 elems=[e for e in j if e['type'] in ['pcb_smtpad','pcb_plated_hole','pcb_trace','pcb_via','pcb_copper_pour'] and key(e)==net];parent=list(range(len(elems)));stack=['top','inner1','inner2','bottom'];layers={l:[] for l in stack};owners={l:[] for l in stack}
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 def add(i,l,g):layers[l].append(g);owners[l].append(i)
 for i,e in enumerate(elems):
  if e['type'] in ['pcb_smtpad','pcb_plated_hole']:
   g=geometry(e)
   for l in e.get('layers',[e.get('layer','top')]):add(i,l,g)
  elif e['type']=='pcb_via':
   for l in e['layers']:add(i,l,Point(e['x'],e['y']).buffer(e['outer_diameter']/2))
  elif e['type']=='pcb_copper_pour':
   b=e['brep_shape'];pts=lambda r:[(p['x'],p['y']) for p in r['vertices']];add(i,e['layer'],Polygon(pts(b['outer_ring']),[pts(r) for r in b.get('inner_rings',[])]))
  else:
   for a,b in zip(e['route'],e['route'][1:]):
    if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']:add(i,a['layer'],LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2))
 for l in stack:
  tree=STRtree(layers[l])
  for i,g in enumerate(layers[l]):
   for other in tree.query(g,predicate='intersects'):
    a,b=root(owners[l][i]),root(owners[l][other])
    if a!=b:parent[b]=a
 return elems,[root(i) for i in range(len(elems))]
def report():
 errors=[]
 for net,name in nets.items():
  elems,roots=groups(net);islands={}
  for e,r in zip(elems,roots):
   if e.get('pcb_port_id'):
    p=ports[e['pcb_port_id']];ref=src[comp[p['pcb_component_id']]['source_component_id']]+'.'+sp[p['source_port_id']]['name'];islands.setdefault(r,set()).add(ref)
  if len(islands)>1:errors.append({'net':name,'key':net,'islands':[sorted(v) for v in islands.values()]})
 r={'checkedNets':len(nets),'disconnectedNets':errors,'allCopperLayersChecked':True,'nativePolygonAndSlotGeometry':True,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()};(ROOT/'artifacts/physical-connectivity.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));return bool(errors)
if __name__=='__main__':raise SystemExit(report())
