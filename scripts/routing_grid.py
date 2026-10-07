"""Finish explicitly selected connections on saved copper.
A collision-aware grid assists the selected manual repairs; unchanged routes are retained.
All results must pass the independent tscircuit DRC and Gerber short checks.
"""
import json,math,pathlib,heapq,time
import numpy as np
from PIL import Image,ImageDraw
ROOT=pathlib.Path(__file__).resolve().parents[1];path=ROOT/'artifacts/board.circuit.json';j=json.loads(path.read_text())
STEP=.025;LOW=-17.5;N=1401
src={e['source_component_id']:e for e in j if e['type']=='source_component'}
sp={e['source_port_id']:e for e in j if e['type']=='source_port'}
ports={e['pcb_port_id']:e for e in j if e['type']=='pcb_port'}
comp={e['pcb_component_id']:e for e in j if e['type']=='pcb_component'}
nets={e['subcircuit_connectivity_map_key']:e for e in j if e['type']=='source_net'}
traces={e['subcircuit_connectivity_map_key']:e['source_trace_id'] for e in j if e['type']=='source_trace'}
pads=[e for e in j if e['type'] in ['pcb_smtpad','pcb_plated_hole']]
def xy(x,y):return (round((x-LOW)/STEP),round((y-LOW)/STEP))
def world(p):return (LOW+p[0]*STEP,LOW+p[1]*STEP)
def key(e):
 if e['type'] in ['pcb_smtpad','pcb_plated_hole']:
  p=ports.get(e.get('pcb_port_id'),{});return sp.get(p.get('source_port_id'),{}).get('subcircuit_connectivity_map_key')
 return e.get('subcircuit_connectivity_map_key')
def findport(cname,pname):
 return next(p for p in ports.values() if src[comp[p['pcb_component_id']]['source_component_id']]['name']==cname and sp[p['source_port_id']]['name']==pname)
def drawrect(draw,x,y,w,h,r=0):draw.rectangle([xy(x-w/2-r,y-h/2-r),xy(x+w/2+r,y+h/2+r)],fill=1)
def circle(draw,x,y,r):draw.ellipse([xy(x-r,y-r),xy(x+r,y+r)],fill=1)
def obstacle(net,width,via=False):
 imgs=[Image.new('L',(N,N)) for _ in range(2)];ds=[ImageDraw.Draw(i) for i in imgs]
 margin=.15+(.25 if via else width/2)+(.01 if via else .005)
 for e in j:
  typ=e['type']
  if typ in ['pcb_smtpad','pcb_plated_hole']:
   if key(e)==net and not via:continue
   w=e.get('width',e.get('outer_width',e.get('outer_diameter',e.get('radius',0)*2)));h=e.get('height',e.get('outer_height',e.get('outer_diameter',e.get('radius',0)*2)))
   if abs(e.get('ccw_rotation',0)%180-90)<.01:w,h=h,w
   ls=[0 if l=='top' else 1 for l in e.get('layers',[e.get('layer','top')])]
   for l in ls:
    if e.get('shape')=='circle':circle(ds[l],e['x'],e['y'],w/2+margin)
    else:drawrect(ds[l],e['x'],e['y'],w,h,margin)
  elif typ=='pcb_trace' and key(e)!=net:
   rr=e['route']
   for a,b in zip(rr,rr[1:]):
    if a['route_type']!='wire' or b['route_type']!='wire' or a['layer']!=b['layer']:continue
    r=margin+max(a['width'],b['width'])/2;d=ds[0 if a['layer']=='top' else 1]
    d.line([xy(a['x'],a['y']),xy(b['x'],b['y'])],fill=1,width=math.ceil(2*r/STEP))
    circle(d,a['x'],a['y'],r);circle(d,b['x'],b['y'],r)
  elif typ=='pcb_via':
   if key(e)==net and not via:continue
   r=e['outer_diameter']/2+.25+.15+.015 if via else e['outer_diameter']/2+margin
   for d in ds:circle(d,e['x'],e['y'],r)
  elif typ=='pcb_keepout':
   c=e['center']
   for d in ds:drawrect(d,c['x'],c['y'],e.get('width',e.get('radius',0)*2),e.get('height',e.get('radius',0)*2),.15+(.25 if via else width/2)+.018)
  elif typ=='pcb_hole':
   for d in ds:circle(d,e['x'],e['y'],e['hole_diameter']/2+.2+(.25 if via else width/2)+.018)
 border=.3+(.25 if via else width/2)
 for d in ds:
  b=math.ceil(border/STEP);d.rectangle([0,0,N-1,b],fill=1);d.rectangle([0,N-1-b,N-1,N-1],fill=1);d.rectangle([0,0,b,N-1],fill=1);d.rectangle([N-1-b,0,N-1,N-1],fill=1)
 return [np.asarray(im,dtype=np.bool_) for im in imgs]
from shapely.geometry import box, Point, LineString, Polygon
from shapely.strtree import STRtree
from shapely.ops import unary_union

def groups(net):
 elems=[e for e in j if e['type'] in ['pcb_smtpad','pcb_plated_hole','pcb_trace','pcb_via','pcb_copper_pour'] and key(e)==net]
 parent=list(range(len(elems)))
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 def union(a,b):
  a,b=root(a),root(b)
  if a!=b:parent[b]=a
 stack=['top','inner1','inner2','bottom'];layerindex={l:i for i,l in enumerate(stack)}
 layers=[[] for _ in stack];owners=[[] for _ in stack]
 def add(i,l,g):layers[l].append(g);owners[l].append(i)
 for i,e in enumerate(elems):
  typ=e['type']
  if typ in ['pcb_smtpad','pcb_plated_hole']:
   w=e.get('width',e.get('outer_width',e.get('outer_diameter',e.get('radius',0)*2)));h=e.get('height',e.get('outer_height',e.get('outer_diameter',e.get('radius',0)*2)))
   if abs(e.get('ccw_rotation',0)%180-90)<.01:w,h=h,w
   g=Point(e['x'],e['y']).buffer(w/2) if e.get('shape')=='circle' else box(e['x']-w/2,e['y']-h/2,e['x']+w/2,e['y']+h/2)
   for l in e.get('layers',[e.get('layer','top')]):add(i,layerindex[l],g)
  elif typ=='pcb_via':
   for l in e['layers']:add(i,layerindex[l],Point(e['x'],e['y']).buffer(e['outer_diameter']/2))
  elif typ=='pcb_copper_pour':
   b=e['brep_shape'];points=lambda ring:[(v['x'],v['y']) for v in ring['vertices']];add(i,layerindex[e['layer']],Polygon(points(b['outer_ring']),[points(r) for r in b.get('inner_rings',[])]))
  else:
   rr=e['route']
   for a,b in zip(rr,rr[1:]):
    if a['route_type']=='wire' and b['route_type']=='wire' and a['layer']==b['layer']:
     add(i,layerindex[a['layer']],LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2))
 for l in range(len(stack)):
  tree=STRtree(layers[l])
  for i,g in enumerate(layers[l]):
   for h in tree.query(g,predicate='intersects'):union(owners[l][i],owners[l][h])
 return elems,[root(i) for i in range(len(elems))]
