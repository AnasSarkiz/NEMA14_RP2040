"""Explicit eight-path candidate on accepted all-top geometry; no gates waived."""
from pathlib import Path
import json,math,sys,heapq,itertools,importlib.util
import numpy as np,shapely
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
sys.path.insert(0,str(Path('scripts').resolve()));spec=importlib.util.spec_from_file_location('copper',Path('scripts/inspect-copper.py'));g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
b=json.load(open('artifacts/final-source.circuit.json'));sc={e['source_component_id']:e['name'] for e in b if e['type']=='source_component'};sp={e['source_port_id']:e for e in b if e['type']=='source_port'};pcs={sc[e['source_component_id']]:e for e in b if e['type']=='pcb_component'};pp={(sc[sp[e['source_port_id']]['source_component_id']],sp[e['source_port_id']]['name']):e for e in b if e['type']=='pcb_port'};pads={e['pcb_port_id']:e for e in b if e['type']=='pcb_smtpad'};padrows=[(e,g.pad_shape(e)) for e in b if e['type'] in ['pcb_smtpad','pcb_plated_hole']];holes=[g.pad_shape(e,True) for e in b if e['type'] in ['pcb_hole','pcb_plated_hole']];keep=unary_union([box(e['center']['x']-e['radius'],e['center']['y']-e['radius'],e['center']['x']+e['radius'],e['center']['y']+e['radius']) for e in b if e['type']=='pcb_keepout']);alllayers=['top','inner1','inner2','bottom'];placed=[];violations=[];step=.08;size=427;lo=-17.04;axis=lo+step*np.arange(size);xx,yy=np.meshgrid(axis,axis)
def xy(port):return [port['x'],port['y']]
def via_ok(v,own):
 p=Point(*v);disk=p.buffer(.225,quad_segs=128);drill=p.buffer(.15,quad_segs=128);bad=[]
 if not box(-17.25,-17.25,17.25,17.25).covers(disk) or disk.distance(keep)<.15-1e-6:bad.append('edge/keepout')
 for e,shape in padrows:
  if drill.intersection(shape).area>1e-9:bad.append('via-in-pad:'+e.get('pcb_port_id',''))
  if e.get('pcb_port_id')!=own and disk.distance(shape)<.15-1e-6:bad.append('via-pad:'+e.get('pcb_port_id',''))
 for h in holes:
  if drill.distance(h)<.45-1e-6:bad.append('drill-hole')
 return bad

reserved=[[9.1,10.6262697],[14.02488,7.477096],[9.65,8.95],[9.740253,6.798],[9.4,13.68851],[8.739493,6.798],[8.8464949,12.6],[13.25,-4.79987],[6.05,12.8475],[13.25,-2.79962]]
def obstacles(layer,width,ignore=None,endpoints=None):
 items=[shape.buffer(width/2+.15,quad_segs=16) for e,shape in padrows if layer in e.get('layers',[e.get('layer','top')]) and e.get('pcb_port_id')!=ignore];items+=[h.buffer(width/2+.2,quad_segs=16) for h in holes];items+=[keep.buffer(width/2+.15,quad_segs=32)]
 for old in placed:
  for ls,p in old['copper']:
   if layer in ls:items.append(p.buffer(width/2+.15,quad_segs=16))
 if endpoints is not None and layer=='top':
  items += [Point(*v).buffer(.08+width/2+.15,quad_segs=32) for v in [[8.5,10.43],[14.674866,6.8],[8.5,10.82],[14.02488,7.477096],[7.481256,14.4],[2.777096,10.675134],[7.481256,13.68851],[2.777096,11.32512]] if all(math.dist(v,q)>1e-6 for q in endpoints)]
 if endpoints is not None:
  items += [Point(*v).buffer(.225+width/2+.15,quad_segs=32) for v in reserved if all(math.dist(v,q)>1e-6 for q in endpoints)]
 return unary_union(items)
def plan(a,z,layer,width):
 obs=obstacles(layer,width,endpoints=[a,z]);blocked=shapely.contains_xy(obs,xx,yy);ix=lambda p:(round((p[0]-lo)/step),round((p[1]-lo)/step));s,t=ix(a),ix(z);free=lambda p:0<=p[0]<size and 0<=p[1]<size and not blocked[p[1],p[0]]
 # Exact off-grid endpoints connect only across screened straight segments.
 candidates=lambda p:[(i,j) for i in range(ix(p)[0]-2,ix(p)[0]+3) for j in range(ix(p)[1]-2,ix(p)[1]+3) if free((i,j)) and not LineString([p,(axis[i],axis[j])]).intersects(obs)]
 starts,ends=candidates(a),set(candidates(z));assert starts and ends,('grid endpoint blocked',a,z,layer)
 q=[];dist={};previous={};counter=itertools.count()
 for p in starts:dist[p]=math.dist(a,(axis[p[0]],axis[p[1]]));heapq.heappush(q,(dist[p]+math.dist((axis[p[0]],axis[p[1]]),z),next(counter),p));previous[p]=None
 end=None
 while q:
  _,_,p=heapq.heappop(q)
  if p in ends:end=p;break
  for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
   r=(p[0]+dx,p[1]+dy)
   if not free(r) or (dx and dy and (not free((p[0]+dx,p[1])) or not free((p[0],p[1]+dy)))):continue
   d=dist[p]+step*math.hypot(dx,dy)
   if d<dist.get(r,math.inf)-1e-9:dist[r]=d;previous[r]=p;heapq.heappush(q,(d+math.dist((axis[r[0]],axis[r[1]]),z),next(counter),r))
 assert end is not None,('No path',a,z,layer);nodes=[]
 while end is not None:nodes.append([float(axis[end[0]]),float(axis[end[1]])]);end=previous[end]
 nodes=[a]+nodes[::-1]+[z];simple=[nodes[0]];i=0
 while i<len(nodes)-1:
  k=len(nodes)-1
  while k>i+1 and LineString([nodes[i],nodes[k]]).intersects(obs):k-=1
  simple.append(nodes[k]);i=k
 return simple
