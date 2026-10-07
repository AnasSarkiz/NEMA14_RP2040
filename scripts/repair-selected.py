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
   for l in ls:drawrect(ds[l],e['x'],e['y'],w,h,margin)
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
from shapely.geometry import box, Point, LineString
from shapely.strtree import STRtree
from shapely.ops import unary_union

def groups(net):
 elems=[e for e in j if e['type'] in ['pcb_smtpad','pcb_plated_hole','pcb_trace','pcb_via'] and key(e)==net]
 parent=list(range(len(elems)))
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 def union(a,b):
  a,b=root(a),root(b)
  if a!=b:parent[b]=a
 layers=[[],[]];owners=[[],[]]
 def add(i,l,g):layers[l].append(g);owners[l].append(i)
 for i,e in enumerate(elems):
  typ=e['type']
  if typ in ['pcb_smtpad','pcb_plated_hole']:
   w=e.get('width',e.get('outer_width',e.get('outer_diameter',e.get('radius',0)*2)));h=e.get('height',e.get('outer_height',e.get('outer_diameter',e.get('radius',0)*2)))
   if abs(e.get('ccw_rotation',0)%180-90)<.01:w,h=h,w
   g=box(e['x']-w/2,e['y']-h/2,e['x']+w/2,e['y']+h/2)
   for l in e.get('layers',[e.get('layer','top')]):add(i,0 if l=='top' else 1,g)
  elif typ=='pcb_via':
   for l in [0,1]:add(i,l,Point(e['x'],e['y']).buffer(e['outer_diameter']/2))
  else:
   rr=e['route']
   for a,b in zip(rr,rr[1:]):
    if a['route_type']=='wire' and b['route_type']=='wire' and a['layer']==b['layer']:
     add(i,0 if a['layer']=='top' else 1,LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2))
 for l in [0,1]:
  tree=STRtree(layers[l])
  for i,g in enumerate(layers[l]):
   for h in tree.query(g,predicate='intersects'):union(owners[l][i],owners[l][h])
 return elems,[root(i) for i in range(len(elems))]

# Select actual DRC-reported ports; no source or component placements are changed.
report=json.loads((ROOT/'artifacts/drc-report.json').read_text())
names=[]
for e in report['errors']:
 if e['type']=='pcb_port_not_connected_error':
  for pid in e.get('pcb_port_ids',[]):
   pp=ports.get(pid)
   if pp:
    cname=src[comp[pp['pcb_component_id']]['source_component_id']]['name'];pname=sp[pp['source_port_id']]['name'];names.append((cname,pname))
# Native terminal checks can report a port not present in the high-level list.
for pair in [('J_DEBUG','VDD'),('R_BOOT','pin1'),('C_VREG_OUT','pin1'),('C_XIN','pin1')]:
 if pair not in names:names.append(pair)
names=list(dict.fromkeys(names+[('U_MCU','GPIO8'),('U_MCU','GPIO9'),('R_ENABLE','pin2')]))
reserved={e['connection']:e['via'] for e in json.loads((ROOT/'artifacts/reserved-fanouts.json').read_text())}
names=list(dict.fromkeys(names+[tuple(k.split('.')) for k in reserved]))
repairs=[]; failures=[]
for cname,pname in names:
 p=findport(cname,pname);net=sp[p['source_port_id']].get('subcircuit_connectivity_map_key')
 elems,roots=groups(net);pi=next(i for i,e in enumerate(elems) if e.get('pcb_port_id')==p['pcb_port_id']);myroot=roots[pi]
 other=[(e,r) for e,r in zip(elems,roots) if r!=myroot]
 if not other:
  print(cname+'.'+pname,'already physically joined',flush=True);continue
 # Targets must be outside the source's physical copper island.
 candidates={}
 for e,r in other:
  if e['type']=='pcb_trace':
   for a in e['route']:
    if a['route_type']=='wire':candidates[(*xy(a['x'],a['y']),0 if a['layer']=='top' else 1)]=(a['x'],a['y'])
  elif e['type'] in ['pcb_smtpad','pcb_plated_hole']:
   for l in ([0,1] if e['type']=='pcb_plated_hole' else [0 if e.get('layer','top')=='top' else 1]):candidates[(*xy(e['x'],e['y']),l)]=(e['x'],e['y'])
  elif e['type']=='pcb_via':
   for l in [0,1]:candidates[(*xy(e['x'],e['y']),l)]=(e['x'],e['y'])
 if not candidates:raise RuntimeError('No other copper island for '+cname+'.'+pname)
 # Keep the physically closest candidate endpoints, including both layers.
 goals=dict(sorted(candidates.items(),key=lambda item:math.hypot(item[1][0]-p['x'],item[1][1]-p['y']))[:80])
 netname=nets[net]['name'];widths=[.3,.2,.16] if netname in ['PD_VBUS','A_PLUS','A_MINUS','B_PLUS','B_MINUS','SENSE1','SENSE2'] else [.16]
 end=None
 for width in widths:
  blocked=obstacle(net,width);vb=obstacle(net,width,True)
  via=reserved.get(cname+'.'+pname);origin={'x':via[0],'y':via[1]} if via else p;start=(*xy(origin['x'],origin['y']),1 if via else 0)
  coords=[(g[0],g[1]) for g in goals];lo=(min(a[0] for a in coords),min(a[1] for a in coords));hi=(max(a[0] for a in coords),max(a[1] for a in coords))
  def heuristic(s):return max(lo[0]-s[0],0,s[0]-hi[0])+max(lo[1]-s[1],0,s[1]-hi[1])
  heap=[(heuristic(start),0,start)];best={start:0};prev={};expanded=0
  while heap:
   _,cost,state=heapq.heappop(heap)
   if cost!=best.get(state):continue
   if state in goals:end=state;break
   expanded+=1
   if expanded>750000:break
   x,y,l=state
   options=[(x+dx,y+dy,l,1.41421356 if dx and dy else 1) for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]]
   if not vb[0][y,x] and not vb[1][y,x]:options.append((x,y,1-l,35))
   for nx,ny,nl,dc in options:
    if not(0<=nx<N and 0<=ny<N) or blocked[nl][ny,nx]:continue
    if nl==l and nx!=x and ny!=y and (blocked[l][y,nx] or blocked[l][ny,x]):continue
    t=(nx,ny,nl);nc=cost+dc
    if nc+1e-8<best.get(t,float('inf')):best[t]=nc;prev[t]=state;heapq.heappush(heap,(nc+heuristic(t),nc,t))
  if end is not None:break
 if end is None:
  failures.append(f'{cname}.{pname}'); print(f'FAILED {cname}.{pname} after {expanded} nodes',flush=True); continue
 nodes=[end]
 while nodes[-1]!=start:nodes.append(prev[nodes[-1]])
 nodes.reverse();slim=[nodes[0]]
 for i in range(1,len(nodes)-1):
  a,b,c=nodes[i-1:i+2]
  if a[2]!=b[2] or b[2]!=c[2] or (b[0]-a[0],b[1]-a[1])!=(c[0]-b[0],c[1]-b[1]):slim.append(b)
 slim.append(nodes[-1]);route=[];newvias=[]
 for i,node in enumerate(slim):
  x,y=world(node);layer='top' if node[2]==0 else 'bottom'
  if i==0:x,y=origin['x'],origin['y']
  if i==len(slim)-1:x,y=goals[end]
  if route and route[-1]['layer']!=layer:
   old=route[-1]['layer'];route.append({'route_type':'via','x':x,'y':y,'from_layer':old,'to_layer':layer,'via_diameter':.5,'via_hole_diameter':.25});newvias.append((x,y))
  route.append({'route_type':'wire','x':x,'y':y,'width':width,'layer':layer})
 if not via:route[0]['start_pcb_port_id']=p['pcb_port_id']
 tid=f'manual_repair_{cname}_{pname}';portids=[] if via else [p['pcb_port_id']]
 for pp in ports.values():
  if sp[pp['source_port_id']].get('subcircuit_connectivity_map_key')==net and math.hypot(route[-1]['x']-pp['x'],route[-1]['y']-pp['y'])<.01 and route[-1]['layer']=='top':route[-1]['end_pcb_port_id']=pp['pcb_port_id'];portids.append(pp['pcb_port_id']);break
 j.append({'type':'pcb_trace','pcb_trace_id':tid,'route':route,'source_net_id':nets[net]['source_net_id'],'source_trace_id':traces[net],'subcircuit_connectivity_map_key':net,'subcircuit_id':'subcircuit_source_group_0','pcb_port_ids':portids})
 for i,(x,y) in enumerate(newvias):j.append({'type':'pcb_via','pcb_via_id':tid+'_via'+str(i),'pcb_trace_id':tid,'source_trace_id':traces[net],'source_net_id':nets[net]['source_net_id'],'subcircuit_connectivity_map_key':net,'subcircuit_id':'subcircuit_source_group_0','x':x,'y':y,'hole_diameter':.25,'outer_diameter':.5,'layers':['top','bottom']})
 repairs.append({'connection':cname+'.'+pname,'net':netname,'points':len(route),'vias':len(newvias),'width':width,'expandedNodes':expanded,'route':route})
 print(cname+'.'+pname,netname,len(route),'points',len(newvias),'vias',expanded,'nodes',flush=True)
 path.write_text(json.dumps(j,indent=2)+'\n');(ROOT/'artifacts/manual-repairs.json').write_text(json.dumps(repairs,indent=2)+'\n')
print('Completed',len(repairs),'selected repairs; unresolved:',failures); (ROOT/'artifacts/unresolved-repairs.json').write_text(json.dumps(failures,indent=2)+'\n')
