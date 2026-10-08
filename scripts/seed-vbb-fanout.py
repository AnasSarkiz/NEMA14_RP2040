"""Shorten VBB1 bypass with two explicitly checked ordinary vias.

Native capacitor and driver land patterns remain unchanged. Run after motor
escapes, before freeze-escape-routes and local top routing. Exact saved geometry
and final real CAM independently verify these routed segments.
"""
import json,math,heapq
import numpy as np
from PIL import Image,ImageDraw
import verify_supplier_connectivity as g
j=json.loads((g.ROOT/'artifacts/final-source.circuit.json').read_text());seeds=json.loads((g.ROOT/'artifacts/supplier-seeds.circuit.json').read_text());j.extend(seeds);g.j=j
g.sp={e['source_port_id']:e for e in j if e['type']=='source_port'};g.ports={e['pcb_port_id']:e for e in j if e['type']=='pcb_port'};g.comp={e['pcb_component_id']:e for e in j if e['type']=='pcb_component'};g.src={e['source_component_id']:e['name'] for e in j if e['type']=='source_component'}
def port(ref,pin):return next(p for p in g.ports.values() if g.src[g.comp[p['pcb_component_id']]['source_component_id']]==ref and g.sp[p['source_port_id']]['name']==pin)
p,q=port('U_DRV','VBB1'),port('C_VM2','pin1');key=g.sp[p['source_port_id']]['subcircuit_connectivity_map_key'];net=next(e for e in j if e['type']=='source_net' and e['subcircuit_connectivity_map_key']==key);trace=next(e for e in j if e['type']=='source_trace' and e['subcircuit_connectivity_map_key']==key)
width=.30;vias=[(1.05,-7.8),(q['x'],-9.35)];toplines=[[(p['x'],p['y']),vias[0]],[vias[1],(q['x'],q['y'])]]
for v,linepts in zip(vias,toplines):
 circ=g.Point(*v).buffer(.25);line=g.LineString(linepts).buffer(width/2)
 for e in j:
  typ=e['type']
  if typ in ['pcb_smtpad','pcb_plated_hole']:
   shape=g.geometry(e);assert circ.distance(shape)>=.15,(v,'via-to-native-pad',g.key(e),circ.distance(shape))
   if g.key(e)!=key:assert line.distance(shape)>=.15,(v,'top-to-native-pad',g.key(e),line.distance(shape))
  elif typ=='pcb_via' and g.key(e)!=key:
   shape=g.Point(e['x'],e['y']).buffer(e['outer_diameter']/2);assert circ.distance(shape)>=.15,(v,'via-to-via');assert line.distance(shape)>=.15,(v,'top-to-via')
  elif typ=='pcb_trace' and g.key(e)!=key:
   for a,b in zip(e['route'],e['route'][1:]):
    if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']:
     shape=g.LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2);assert circ.distance(shape)>=.15,(v,'via-to-trace',a['layer'],circ.distance(shape))
     if a['layer']=='top':assert line.distance(shape)>=.15,(v,'top-to-top-trace')
STEP=.025;LOW=-17.5;N=1401;xy=lambda x,y:(round((x-LOW)/STEP),round((y-LOW)/STEP));world=lambda s:(LOW+s[0]*STEP,LOW+s[1]*STEP)
im=Image.new('L',(N,N));d=ImageDraw.Draw(im)
def add(shape):
 shape=shape.buffer(.15+width/2+.008)
 for poly in ([shape] if shape.geom_type=='Polygon' else shape.geoms):d.polygon([xy(x,y) for x,y in poly.exterior.coords],fill=1)
for e in j:
 typ=e['type']
 if typ=='pcb_plated_hole' and g.key(e)!=key:add(g.geometry(e))
 elif typ=='pcb_via' and g.key(e)!=key:add(g.Point(e['x'],e['y']).buffer(e['outer_diameter']/2))
 elif typ=='pcb_trace' and g.key(e)!=key:
  for a,b in zip(e['route'],e['route'][1:]):
   if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']=='bottom':add(g.LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2))
 elif typ=='pcb_hole':add(g.Point(e['x'],e['y']).buffer(e['hole_diameter']/2+.1))
 elif typ=='pcb_keepout':
  add(g.keepout_geometry(e))
mask=np.asarray(im,dtype=np.bool_);start=xy(*vias[0]);goal=xy(*vias[1]);assert not mask[start[1],start[0]] and not mask[goal[1],goal[0]]
heap=[(math.dist(start,goal),0,start)];best={start:0};prev={};end=None
while heap:
 _,cost,s=heapq.heappop(heap)
 if cost!=best.get(s):continue
 if s==goal:end=s;break
 x,y=s
 for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
  nx,ny=x+dx,y+dy
  if not(0<=nx<N and 0<=ny<N) or mask[ny,nx]:continue
  if dx and dy and (mask[y,nx] or mask[ny,x]):continue
  t=(nx,ny);nc=cost+(math.sqrt(2) if dx and dy else 1)
  if nc<best.get(t,float('inf'))-1e-8:best[t]=nc;prev[t]=s;heapq.heappush(heap,(nc+math.dist(t,goal),nc,t))
assert end is not None
ns=[end]
while ns[-1]!=start:ns.append(prev[ns[-1]])
ns.reverse();slim=[ns[0]]
for i in range(1,len(ns)-1):
 a,b,c=ns[i-1:i+2]
 if (b[0]-a[0],b[1]-a[1])!=(c[0]-b[0],c[1]-b[1]):slim.append(b)
slim.append(ns[-1]);coords=[world(s) for s in slim];coords[0]=vias[0];coords[-1]=vias[1]
route=[]
for pts,layer in [(toplines[0],'top'),(coords,'bottom'),(toplines[1],'top')]:
 if route:route.append({'route_type':'via','x':pts[0][0],'y':pts[0][1],'from_layer':route[-1]['layer'],'to_layer':layer,'via_diameter':.5,'via_hole_diameter':.25})
 route.extend({'route_type':'wire','x':x,'y':y,'layer':layer,'width':width} for x,y in pts)
route[0]['start_pcb_port_id']=p['pcb_port_id'];route[-1]['end_pcb_port_id']=q['pcb_port_id'];common={'source_net_id':net['source_net_id'],'source_trace_id':trace['source_trace_id'],'subcircuit_connectivity_map_key':key,'subcircuit_id':'subcircuit_source_group_0'}
e={'type':'pcb_trace','pcb_trace_id':'supplier_repair_VBB1_short_bypass','route':route,'pcb_port_ids':[p['pcb_port_id'],q['pcb_port_id']],**common};seeds.append(e)
for i,v in enumerate(vias):seeds.append({'type':'pcb_via','pcb_via_id':e['pcb_trace_id']+'_via'+str(i),'x':v[0],'y':v[1],'hole_diameter':.25,'outer_diameter':.5,'layers':['top','inner1','inner2','bottom'],'tented_on_top':True,'tented_on_bottom':True,**common})
(g.ROOT/'artifacts/supplier-seeds.circuit.json').write_text(json.dumps(seeds,indent=2)+'\n');length=sum(math.dist(a,b) for pts in [*toplines,coords] for a,b in zip(pts,pts[1:]));(g.ROOT/'artifacts/engineering-vbb1-bypass.json').write_text(json.dumps({'lengthMm':length,'viaCount':2,'viaLocations':vias,'minimumClearanceMm':.15,'widthMm':width},indent=2)+'\n');print('VBB1 local bypass',round(length,3),'mm, two ordinary0.5/0.25mm vias')
