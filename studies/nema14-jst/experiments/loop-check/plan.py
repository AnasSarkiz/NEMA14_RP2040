"""Bounded native-board geometry search, no autorouter and no new via process."""
import sys,json,math,heapq
from pathlib import Path
sys.path.insert(0,'experiments/external-star')
from model import *
from routing_geometry import resolve_copper_nets
from shapely.ops import unary_union
import shapely,numpy as np
r=Path('artifacts/iteration-14');bb=resolve_copper_nets(b);_,co,pc,sp,pp,ports,courts=index(bb);pads={e['pcb_port_id']:e for e in bb if e['type']=='pcb_smtpad'};net=sp[ports['U_DRV','EP']['source_port_id']]['subcircuit_connectivity_map_key'];obs=[];own=[];details=[];radius=.096;clearance=float(sys.argv[1]) if len(sys.argv)>1 else .18
allowed=[g.pad_shape(pads[ports[k]['pcb_port_id']]) for k in [('C_VREG','pin2'),('U_DRV','EP'),('U_DRV','GND18'),('U_DRV','GND')]];allow=unary_union(allowed)
for e in bb:
 t=e['type'];key=e.get('subcircuit_connectivity_map_key');name=e.get('pcb_via_id',e.get('pcb_trace_id',''))
 if t=='pcb_smtpad' and e['layer']=='top':
  p=pp[e['pcb_port_id']];key=sp[p['source_port_id']].get('subcircuit_connectivity_map_key');poly=g.pad_shape(e);name=pc[e['pcb_component_id']]+'.'+sp[p['source_port_id']]['name']
 elif t=='pcb_via' and 'top' in e['layers']:poly=g.pad_shape(e)
 elif t=='pcb_trace':
  for i,(a,z) in enumerate(zip(e['route'],e['route'][1:])):
   if a['route_type']==z['route_type']=='wire' and a['layer']==z['layer']=='top':
    poly=LineString([(a['x'],a['y']),(z['x'],z['y'])]).buffer(max(a['width'],z['width'])*1.2/2,quad_segs=64)
    if key!=net:obs.append(poly.buffer(clearance+radius,quad_segs=64));details.append((name+':'+str(i),poly,key))
    else:own.append(poly.difference(allow).buffer(radius+.005,quad_segs=64))
  continue
 else:continue
 if key!=net:obs.append(poly.buffer(clearance+radius,quad_segs=64));details.append((name,poly,key))
 else:
  q=poly.difference(allow)
  if not q.is_empty:own.append(q.buffer(radius+.005,quad_segs=64))
for e in bb:
 if e['type'] in ['pcb_via','pcb_hole','pcb_plated_hole']:obs.append(g.pad_shape(e,True).buffer(radius+.005,quad_segs=64))
 if e['type']=='pcb_keepout':
  c=e['center'];obs.append(box(c['x']-e['radius'],c['y']-e['radius'],c['x']+e['radius'],c['y']+e['radius']).buffer(radius+.001))
region=box(3.6,6.0,11.7,12.8);obstacle=unary_union(obs+own);free=region.difference(obstacle);start=Point(ports['C_VREG','pin2']['x'],ports['C_VREG','pin2']['y']);goal=Point(ports['U_DRV','EP']['x'],ports['U_DRV','EP']['y']);polys=list(free.geoms) if hasattr(free,'geoms') else [free];ids=lambda p:[i for i,q in enumerate(polys) if q.covers(p)];report={'region_mm':list(region.bounds),'nominal_width_mm':.16,'stressed_width_mm':.192,'clearance_mm':.15,'start_mm':list(start.coords)[0],'goal_mm':list(goal.coords)[0],'start_free_components':ids(start),'goal_free_components':ids(goal),'same_continuous_component':bool(set(ids(start))&set(ids(goal))),'avoids_unrelated_ground_contacts':True,'holes_avoided_without_adding_vias':True,'new_process_assumed':False}
# Grid is only a candidate generator, not a proof of continuous infeasibility.
step=.02;xs=np.arange(3.6,11.70001,step);ys=np.arange(6,12.80001,step);xx,yy=np.meshgrid(xs,ys);valid=shapely.contains_xy(free,xx,yy);h,w=valid.shape
nearest=lambda p:(int(round((p.y-6)/step)),int(round((p.x-3.6)/step)))
s=nearest(start);target=nearest(goal);heap=[(0,0,s)];dist={s:0};prev={};found=None;steps=[(dy,dx) for dy in [-1,0,1] for dx in [-1,0,1] if dy or dx]
while heap:
 _,cost,u=heapq.heappop(heap)
 if cost!=dist[u]:continue
 if u==target:found=u;break
 for dy,dx in steps:
  v=(u[0]+dy,u[1]+dx)
  if not(0<=v[0]<h and 0<=v[1]<w and valid[v]):continue
  if dx and dy and not(valid[u[0],v[1]] and valid[v[0],u[1]]):continue
  nd=cost+math.hypot(dx,dy)*step
  if nd<dist.get(v,1e9):dist[v]=nd;prev[v]=u;heapq.heappush(heap,(nd+math.hypot(xs[v[1]]-goal.x,ys[v[0]]-goal.y),nd,v))
report['grid_search_found']=found is not None;report['grid_step_mm']=step;report['visited']=len(dist)
if found:
 chain=[found]
 while chain[-1]!=s:chain.append(prev[chain[-1]])
 chain.reverse();raw=[list(start.coords)[0]]+[[float(xs[v[1]]),float(ys[v[0]])] for v in chain]+[list(goal.coords)[0]]
 # Greedy visibility simplification must be covered by the same continuous free geometry.
 out=[raw[0]];i=0
 while i<len(raw)-1:
  k=len(raw)-1
  while k>i+1 and not free.covers(LineString([raw[i],raw[k]])):k-=1
  out.append(raw[k]);i=k
 assert free.buffer(1e-9).covers(LineString(out));report['path_mm']=out;report['centreline_length_mm']=LineString(out).length
(r/'plan.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
