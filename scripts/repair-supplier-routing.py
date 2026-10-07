"""Add selected missing connections; check the result independently afterward."""
import verify_supplier_connectivity as g
import json,math,heapq,numpy as np
from PIL import Image,ImageDraw
j=g.j;ROOT=g.ROOT;path=g.path;ports=g.ports;sp=g.sp;comp=g.comp;src=g.src
STEP=.025;LOW=-17.5;N=1401;layers=['top','inner2','bottom']
xy=lambda x,y:(round((x-LOW)/STEP),round((y-LOW)/STEP))
world=lambda p:(LOW+p[0]*STEP,LOW+p[1]*STEP)
key=g.key
traces={e['subcircuit_connectivity_map_key']:e['source_trace_id'] for e in j if e['type']=='source_trace'}
nets={e['subcircuit_connectivity_map_key']:e for e in j if e['type']=='source_net'}
def findport(c,p):return next(e for e in ports.values() if src[comp[e['pcb_component_id']]['source_component_id']]==c and sp[e['source_port_id']]['name']==p)
def obstacle(net,width,via=False):
 imgs=[Image.new('L',(N,N)) for l in layers];draws=[ImageDraw.Draw(i) for i in imgs];margin=.15+(.20 if via else width/2)+.005
 def add(l,geom):
  if l not in layers:return
  geom=geom.buffer(margin)
  if geom.geom_type=='Polygon':draws[layers.index(l)].polygon([xy(x,y) for x,y in geom.exterior.coords],fill=1)
 for e in j:
  typ=e['type']
  if typ in ['pcb_smtpad','pcb_plated_hole']:
   if key(e)==net and not via:continue
   for l in e.get('layers',[e.get('layer','top')]):add(l,g.geometry(e))
  elif typ=='pcb_via':
   if key(e)==net and not via:continue
   for l in layers:add(l,g.Point(e['x'],e['y']).buffer(e['outer_diameter']/2))
  elif typ=='pcb_trace' and key(e)!=net:
   for a,b in zip(e['route'],e['route'][1:]):
    if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']:add(a['layer'],g.LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2))
  elif typ=='pcb_keepout':
   c=e['center'];shape=g.box(c['x']-e['width']/2,c['y']-e['height']/2,c['x']+e['width']/2,c['y']+e['height']/2)
   for l in layers:add(l,shape)
  elif typ=='pcb_hole':
   for l in layers:add(l,g.Point(e['x'],e['y']).buffer(e['hole_diameter']/2+.1))
 border=.3+(.20 if via else width/2)
 for d in draws:
  b=math.ceil(border/STEP);d.rectangle([0,0,N-1,b],fill=1);d.rectangle([0,N-1-b,N-1,N-1],fill=1);d.rectangle([0,0,b,N-1],fill=1);d.rectangle([N-1-b,0,N-1,N-1],fill=1)
 return [np.asarray(im,dtype=np.bool_) for im in imgs]
repairs=[]
for cname,pname in [('U_MCU','QSPI_SD0')]:
 p=findport(cname,pname);net=sp[p['source_port_id']]['subcircuit_connectivity_map_key'];width=.16
 elems,roots=g.groups(net);startroot=next(r for e,r in zip(elems,roots) if e.get('pcb_port_id')==p['pcb_port_id']);goals={}
 for e,r in zip(elems,roots):
  if r==startroot:continue
  if e['type'] in ['pcb_smtpad','pcb_plated_hole']:
   pp=ports[e['pcb_port_id']]
   for l in e.get('layers',[e.get('layer','top')]):
    if l in layers:goals[(*xy(pp['x'],pp['y']),layers.index(l))]=(pp['x'],pp['y'])
  elif e['type']=='pcb_trace':
   for a in e['route']:
    if a['route_type']=='wire' and a['layer'] in layers:goals[(*xy(a['x'],a['y']),layers.index(a['layer']))]=(a['x'],a['y'])
 assert goals,'No disconnected target island'
 blocked=obstacle(net,width);vb=obstacle(net,width,True);start=(*xy(p['x'],p['y']),0)
 pts=np.asarray(list(goals));lo=pts[:,:2].min(axis=0);hi=pts[:,:2].max(axis=0)
 def heuristic(s):return max(lo[0]-s[0],0,s[0]-hi[0])+max(lo[1]-s[1],0,s[1]-hi[1])
 heap=[(heuristic(start),0,start)];best={start:0};prev={};end=None;expanded=0
 while heap:
  _,cost,s=heapq.heappop(heap)
  if cost!=best.get(s):continue
  if s in goals:end=s;break
  expanded+=1
  if expanded>1200000:break
  x,y,l=s;options=[(x+dx,y+dy,l,1.41421356 if dx and dy else 1) for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]]
  if all(not v[y,x] for v in vb):options += [(x,y,nl,45) for nl in range(3) if nl!=l]
  for nx,ny,nl,dc in options:
   if not(0<=nx<N and 0<=ny<N) or blocked[nl][ny,nx]:continue
   if nl==l and nx!=x and ny!=y and (blocked[l][y,nx] or blocked[l][ny,x]):continue
   t=(nx,ny,nl);nc=cost+dc
   if nc+1e-8<best.get(t,float('inf')):best[t]=nc;prev[t]=s;heapq.heappush(heap,(nc+heuristic(t),nc,t))
 assert end is not None,f'No compliant path after {expanded} nodes'
 nodes=[end]
 while nodes[-1]!=start:nodes.append(prev[nodes[-1]])
 nodes.reverse();slim=[nodes[0]]
 for i in range(1,len(nodes)-1):
  a,b,c=nodes[i-1:i+2]
  if a[2]!=b[2] or b[2]!=c[2] or (b[0]-a[0],b[1]-a[1])!=(c[0]-b[0],c[1]-b[1]):slim.append(b)
 slim.append(nodes[-1]);route=[];vias=[]
 for i,s in enumerate(slim):
  x,y=world(s);layer=layers[s[2]]
  if i==0:x,y=p['x'],p['y']
  if i==len(slim)-1:x,y=goals[end]
  if route and route[-1]['layer']!=layer:
   old=route[-1]['layer'];route.append({'route_type':'via','x':x,'y':y,'from_layer':old,'to_layer':layer,'via_diameter':.4,'via_hole_diameter':.2});vias.append((x,y))
  route.append({'route_type':'wire','x':x,'y':y,'width':width,'layer':layer})
 route[0]['start_pcb_port_id']=p['pcb_port_id'];tid='supplier_repair_'+cname+'_'+pname
 j.append({'type':'pcb_trace','pcb_trace_id':tid,'route':route,'source_net_id':nets[net]['source_net_id'],'source_trace_id':traces[net],'subcircuit_connectivity_map_key':net,'subcircuit_id':'subcircuit_source_group_0','pcb_port_ids':[p['pcb_port_id']]})
 for i,(x,y) in enumerate(vias):j.append({'type':'pcb_via','pcb_via_id':tid+'_via'+str(i),'pcb_trace_id':tid,'source_trace_id':traces[net],'source_net_id':nets[net]['source_net_id'],'subcircuit_connectivity_map_key':net,'subcircuit_id':'subcircuit_source_group_0','x':x,'y':y,'hole_diameter':.2,'outer_diameter':.4,'layers':['top','inner1','inner2','bottom'],'tented_on_top':True,'tented_on_bottom':True})
 repairs.append({'connection':cname+'.'+pname,'net':nets[net]['name'],'route':route,'expandedNodes':expanded});print(cname,pname,len(route),'points',len(vias),'vias',expanded,'search nodes',flush=True)
path.write_text(json.dumps(j,indent=2)+'\n');(ROOT/'artifacts/supplier-selected-repairs.json').write_text(json.dumps(repairs,indent=2)+'\n')
