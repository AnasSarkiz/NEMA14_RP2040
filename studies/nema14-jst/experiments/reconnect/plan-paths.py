"""Explicit native paths against actual full-board copper, including conservative keepout bounds.
This offline deterministic geometry search is not a native autorouter result.
"""
from pathlib import Path
import json,math,heapq,sys
from model import *
from routing_geometry import resolve_copper_nets
from shapely.ops import unary_union
from shapely import intersects_xy
import numpy as np
j=resolve_copper_nets(read(sys.argv[1]));nm,cs,pn,sps,pps,ps,cts=index(j);obstacles=[];routes=[]
for e in j:
 typ=e['type']
 if typ in ['pcb_smtpad','pcb_plated_hole']:
  source=sps[pps[e['pcb_port_id']]['source_port_id']];obstacles.append((g.pad_shape(e),source.get('subcircuit_connectivity_map_key'),e.get('layers',[e.get('layer')]),e['pcb_port_id']))
 elif typ=='pcb_via':obstacles.append((g.pad_shape(e),e['subcircuit_connectivity_map_key'],e['layers'],None))
 elif typ=='pcb_trace':
  for a,z in zip(e['route'],e['route'][1:]):
   if a['route_type']==z['route_type']=='wire' and a['layer']==z['layer']:obstacles.append((LineString([(a['x'],a['y']),(z['x'],z['y'])]).buffer(max(a['width'],z['width'])/2,quad_segs=128),e['subcircuit_connectivity_map_key'],[a['layer']],None))
def resolve(ref):
 owner,pinname=ref.split('.')
 if owner.startswith('V_BUZ_'):
  wanted=next(v for v in read('experiments/reconnect/vias.json') if v['name']==owner);via=next(v for v in j if v['type']=='pcb_via' and math.dist([v['x'],v['y']],[wanted['x'],wanted['y']])<1e-9);port=next(p for p in j if p['type']=='pcb_port' and p['pcb_port_id'] in via['pcb_port_ids'] and pinname in p['layers']);return (owner,pinname),port
 matches=[(k,e) for k,e in ps.items() if k[0]==owner and pinname in sps[e['source_port_id']].get('port_hints',[k[1]])];assert len(matches)==1,(ref,matches);return matches[0]
def net(port):
 return next((v['subcircuit_connectivity_map_key'] for v in j if v['type']=='pcb_via' and port['pcb_port_id'] in v.get('pcb_port_ids',[])),sps[port['source_port_id']].get('subcircuit_connectivity_map_key'))
def route(name,fromref,toref,width,margin,region,step,through=[],layer='top'):
 (sn,spn),src=resolve(fromref);(tn,tpn),dst=resolve(toref);key=net(src);assert net(dst)==key;ends={src['pcb_port_id'],dst['pcb_port_id']};foreign=[p for p,k,ls,pid in obstacles if layer in ls and pid not in ends and (k!=key or pid is not None)];blocked_parts=[p.buffer(margin+width/2,quad_segs=64) for p in foreign]
 for k in [e for e in j if e['type']=='pcb_keepout']:
  x,y,r=k['center']['x'],k['center']['y'],k['radius'];blocked_parts.append(box(x-r,y-r,x+r,y+r).buffer(margin+width/2,join_style=2))
 blocked=unary_union(blocked_parts);x0,y0=src['x'],src['y'];xmin=math.floor((region[0]-x0)/step);xmax=math.ceil((region[2]-x0)/step);ymin=math.floor((region[1]-y0)/step);ymax=math.ceil((region[3]-y0)/step);xs,ys=np.meshgrid(np.arange(xmin,xmax+1)*step+x0,np.arange(ymin,ymax+1)*step+y0);mask=intersects_xy(blocked,xs,ys);safe=17.5-.25-width/2;mask|=(abs(xs)>safe)|(abs(ys)>safe)
 def pos(n):return [x0+n[0]*step,y0+n[1]*step]
 def legal(n):return xmin<=n[0]<=xmax and ymin<=n[1]<=ymax and not mask[n[1]-ymin,n[0]-xmin]
 def clear(a,z):return not LineString([a,z]).intersects(blocked)
 simple=[[x0,y0]];start=(0,0);visited=0
 targets=[]
 for target in through:
  node=(round((target[0]-x0)/step),round((target[1]-y0)/step));targets.append((pos(node),node))
 targets.append(([dst['x'],dst['y']],None))
 for target,goal in targets:
  assert legal(start),(name,'blocked source');assert not blocked.covers(Point(*target)),(name,'blocked target');pq=[(math.dist(pos(start),target),0,start)];cost={start:0};prev={};end=None
  while pq:
   _,d,n=heapq.heappop(pq)
   if d!=cost[n]:continue
   p=pos(n)
   if (n==goal if goal is not None else math.dist(p,target)<step*2.5 and clear(p,target)):end=n;break
   for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
    q=(n[0]+dx,n[1]+dy)
    if not legal(q) or not clear(p,pos(q)):continue
    nd=d+math.hypot(dx,dy)*step
    if nd>=cost.get(q,1e9):continue
    cost[q]=nd;prev[q]=n;heapq.heappush(pq,(nd+math.dist(pos(q),target),nd,q))
  assert end is not None,(name,'no bounded corridor',len(cost));visited+=len(cost);path=[];n=end
  while n!=start:path.append(pos(n));n=prev[n]
  path=[pos(start)]+list(reversed(path))
  if path[-1]!=target:path.append(target)
  i=0
  while i<len(path)-1:
   k=len(path)-1
   while k>i+1 and not clear(path[i],path[k]):k-=1
   simple.append(path[k]);i=k
  start=end
 c=cs.get(sn,{'center':{'x':src['x'],'y':src['y']},'rotation':0});angle=math.radians(-c['rotation']);local=[]
 for x,y in simple[1:-1]:
  dx,dy=x-c['center']['x'],y-c['center']['y'];local.append({'x':dx*math.cos(angle)-dy*math.sin(angle),'y':dx*math.sin(angle)+dy*math.cos(angle)})
 wire=LineString(simple).buffer(width/2,quad_segs=128);gap=min(wire.distance(p) for p in foreign);assert gap>=.15;record={'name':name,'from':'.'+sn+' > .'+spn,'to':'.'+tn+' > .'+tpn,'width_mm':width,'layer':layer,'world_points_mm':simple,'local_points':local or ['.'+sn+' > .'+spn],'minimum_other_copper_gap_mm':gap,'search_margin_mm':margin,'wire_length_mm':sum(math.dist(a,z) for a,z in zip(simple,simple[1:])),'actual_native_port_pair':[src['pcb_port_id'],dst['pcb_port_id']],'mandatory_world_waypoints_mm':through,'native_autorouter_run':False};routes.append(record);obstacles.append((wire,key,[layer],None));print(name,'length',record['wire_length_mm'],'gap',gap,'nodes',visited,flush=True);Path('.config/reconnect-progress.json').write_text(json.dumps(routes,indent=2)+'\n')
cached=read('experiments/reconnect/paths.json') if '--charge-pump-only' in sys.argv else []
route('AUTHORED_CP1_CORRIDOR','U_DRV.CP1','C_CP.pin1',.16,.152,[9.8,7.1,12.8,9.4],.01,[[11.45,8.1]])
route('AUTHORED_CP2_CORRIDOR','U_DRV.CP2','C_CP.pin2',.16,.152,[9.2,7.4,12.8,9.55],.01)
if cached:
 routes += [r for r in cached if not r['name'].startswith('AUTHORED_CP')]
 Path('experiments/reconnect/paths.json').write_text(json.dumps(routes,indent=2)+'\n')
 raise SystemExit(0)
region=[-10,-17.1,11.2,-5]
route('BUZ_SWITCH_SUPPLY__0','C_BUZZER.pin1','V_BUZ_SUPPLY_SOURCE.top',.45,.15,region,.025)
route('BUZ_SWITCH_SUPPLY__1','V_BUZ_SUPPLY_SOURCE.inner2','V_BUZ_SUPPLY_TARGET.inner2',.45,.25,region,.05,layer='inner2')
route('BUZ_SWITCH_SUPPLY__2','V_BUZ_SUPPLY_TARGET.top','BZ1._POS',.45,.25,region,.025)
for name,a,z,width in [
 ('BUZ_FLYBACK_SINK','BZ1._NEG','D_BUZZER.anode',.45),
 ('BUZ_FLYBACK_SUPPLY','D_BUZZER.cathode','BZ1._POS',.45),
 ('BUZ_SWITCH_RETURN','Q_BUZZER.S','C_BUZZER.pin2',.45),
 ('BUZ_SWITCH_DRAIN','BZ1._NEG','Q_BUZZER.D',.45),
 ('BUZ_GATE_SERIES','R_BUZZER_GATE.pin2','Q_BUZZER.G',.16),
 ('BUZ_GATE_PULLDOWN','R_BUZZER_PD.pin1','Q_BUZZER.G',.16)]:route(name,a,z,width,.25,region,.05)

Path('experiments/reconnect/paths.json').write_text(json.dumps(routes,indent=2)+'\n')
