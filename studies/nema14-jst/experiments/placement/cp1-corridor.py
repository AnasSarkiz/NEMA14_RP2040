"""Find a deterministic explicit local CP1 corridor against true native copper, without autorouting."""
from pathlib import Path
import json,math,heapq
from model import *
from routing_geometry import resolve_copper_nets
from shapely.ops import unary_union
from shapely import intersects_xy
j=resolve_copper_nets(read(sys.argv[1] if len(sys.argv)>1 else 'artifacts/iteration-6/current-board.circuit.json'));src=ports['U_DRV','CP1'];dst=ports['C_CP','pin1'];key=sp[src['source_port_id']]['subcircuit_connectivity_map_key'];obstacles=[]
for e in j:
 typ=e['type']
 if typ in ['pcb_smtpad','pcb_plated_hole']:
  k=sp[pp[e['pcb_port_id']]['source_port_id']].get('subcircuit_connectivity_map_key')
  if k!=key and 'top' in e.get('layers',[e.get('layer')]):obstacles.append(g.pad_shape(e))
 elif typ=='pcb_via' and e['subcircuit_connectivity_map_key']!=key:obstacles.append(g.pad_shape(e))
 elif typ=='pcb_trace' and e['subcircuit_connectivity_map_key']!=key:
  for a,z in zip(e['route'],e['route'][1:]):
   if a['route_type']==z['route_type']=='wire' and a['layer']==z['layer']=='top':obstacles.append(LineString([(a['x'],a['y']),(z['x'],z['y'])]).buffer(max(a['width'],z['width'])/2,quad_segs=128))
# This region is wholly inside the mechanical safe region, far from all four screws.
margin=float(next((a.split('=')[1] for a in sys.argv if a.startswith('--margin=')),'.152'));blocked=unary_union([p.buffer(margin+.08,quad_segs=128) for p in obstacles]);step=.025;x0=src['x'];y0=src['y'];xmin,xmax,ymin,ymax=-8,110,-35,100
import numpy as np
xs,ys=np.meshgrid(np.arange(xmin,xmax+1)*step+x0,np.arange(ymin,ymax+1)*step+y0);mask=intersects_xy(blocked,xs,ys)
def pos(n):return [x0+n[0]*step,y0+n[1]*step]
def legal(n):return xmin<=n[0]<=xmax and ymin<=n[1]<=ymax and not mask[n[1]-ymin,n[0]-xmin]
def clear(a,z):return not LineString([a,z]).intersects(blocked)
start=(0,0);target=[dst['x'],dst['y']];assert legal(start),'Blocked source endpoint';pq=[(0,0,start)];cost={start:0};prev={};end=None
while pq:
 _,d,n=heapq.heappop(pq)
 if d!=cost[n]:continue
 p=pos(n)
 if math.dist(p,target)<.08 and clear(p,target):end=n;break
 for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
  z=(n[0]+dx,n[1]+dy)
  if not legal(z) or not clear(p,pos(z)):continue
  nd=d+math.hypot(dx,dy)*step
  if nd>=cost.get(z,1e9):continue
  cost[z]=nd;prev[z]=n;heapq.heappush(pq,(nd+math.dist(pos(z),target),nd,z))
assert end is not None,'No corridor in the bounded actual-copper region';path=[];n=end
while n!=start:path.append(pos(n));n=prev[n]
path=list(reversed([*path,[src['x'],src['y']]])) if False else [[src['x'],src['y']]]+list(reversed(path))+[target]
# Visibility simplification keeps every retained line independently clear.
simple=[path[0]];i=0
while i<len(path)-1:
 k=len(path)-1
 while k>i+1 and not clear(path[i],path[k]):k-=1
 simple.append(path[k]);i=k
c=co['U_DRV'];angle=math.radians(-c['rotation']);local=[]
for x,y in simple[1:-1]:
 dx,dy=x-c['center']['x'],y-c['center']['y'];local.append({'x':dx*math.cos(angle)-dy*math.sin(angle),'y':dx*math.sin(angle)+dy*math.cos(angle)})
wire=LineString(simple).buffer(.08,quad_segs=128);gap=min(wire.distance(p) for p in obstacles);assert gap>=.15
record={'enabled':True,'width_mm':.16,'layer':'top','from':'U_DRV.CP1','to':'C_CP.pin1','world_points_mm':simple,'local_points':local,'minimum_foreign_copper_clearance_mm':gap,'design_rule_mm':.15,'corridor_search_margin_mm':margin,'wire_length_mm':sum(math.dist(a,z) for a,z in zip(simple,simple[1:])),'bounded_search_visited_nodes':len(cost),'native_autorouter_run':False};Path('experiments/placement/cp1-path.json').write_text(json.dumps(record,indent=2)+'\n');print(record)
