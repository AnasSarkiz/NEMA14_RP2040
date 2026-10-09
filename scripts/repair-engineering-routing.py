"""Complete real copper islands with inspectable clearance-aware three-signal-layer paths.
Start from all copper in one existing island, including already reserved via escapes.
"""
import verify_supplier_connectivity as g
import json,math,heapq,numpy as np,sys
from PIL import Image,ImageDraw,ImageChops
from scipy.ndimage import distance_transform_edt
if '--seed' in sys.argv:
 g.j=json.loads((g.ROOT/'artifacts/final-source.circuit.json').read_text())+json.loads((g.ROOT/'artifacts/supplier-seeds.circuit.json').read_text());g.path=g.ROOT/'artifacts/supplier-seeds.circuit.json'
 g.sp={e['source_port_id']:e for e in g.j if e['type']=='source_port'};g.ports={e['pcb_port_id']:e for e in g.j if e['type']=='pcb_port'};g.comp={e['pcb_component_id']:e for e in g.j if e['type']=='pcb_component'};g.src={e['source_component_id']:e['name'] for e in g.j if e['type']=='source_component'}
j=g.j;ROOT=g.ROOT;path=g.path;ports=g.ports;sp=g.sp;comp=g.comp;src=g.src
STEP=.025;LOW=-17.5;N=1401;layers=(['top','bottom']if '--outer-only'in sys.argv else ['top','inner2','bottom']);xy=lambda x,y:(round((x-LOW)/STEP),round((y-LOW)/STEP));world=lambda p:(LOW+p[0]*STEP,LOW+p[1]*STEP);key=g.key
traces={e['subcircuit_connectivity_map_key']:e['source_trace_id'] for e in j if e['type']=='source_trace'};nets={e['subcircuit_connectivity_map_key']:e for e in j if e['type']=='source_net'}
def obstacle(net,width,via=False):
 imgs=[Image.new('L',(N,N)) for l in layers];draws=[ImageDraw.Draw(i) for i in imgs];margin=.15+(.25 if via else width/2)+.04
 def add(l,geom):
  if l not in layers:
   if via:
    # A through-via spans the full stack even when wire routing is outer-only.
    for target in layers:add(target,geom)
   return
  geom=geom.buffer(.15+.02+(.25 if via else (.6 if net==next((k for k,n in nets.items() if n['name']=='PD_VBUS'),None) and l=='inner2' else width)/2))
  for poly in ([geom] if geom.geom_type=='Polygon' else geom.geoms):
   # Draw polygon holes on an isolated local mask: clearing directly on the
   # layer would erase obstacles belonging to other conductors. The previous
   # exterior-only raster incorrectly blocked valid pour-clearance cavities.
   coords=[xy(x,y) for x,y in poly.exterior.coords];xs,ys=zip(*coords);x0=max(0,min(xs));y0=max(0,min(ys));x1=min(N,max(xs)+1);y1=min(N,max(ys)+1)
   if x1<=x0 or y1<=y0:continue
   patch=Image.new('L',(x1-x0,y1-y0));pd=ImageDraw.Draw(patch);pd.polygon([(x-x0,y-y0)for x,y in coords],fill=1)
   for ring in poly.interiors:pd.polygon([(xy(x,y)[0]-x0,xy(x,y)[1]-y0)for x,y in ring.coords],fill=0)
   idx=layers.index(l);rect=(x0,y0,x1,y1);imgs[idx].paste(ImageChops.lighter(imgs[idx].crop(rect),patch),rect)
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
  elif typ=='pcb_copper_pour' and key(e)!=net and not ('--reclear-ground' in sys.argv and g.nets.get(key(e))=='GND'):
   b=e['brep_shape'];pts=lambda r:[(p['x'],p['y']) for p in r['vertices']];add(e['layer'],g.Polygon(pts(b['outer_ring']),[pts(r) for r in b.get('inner_rings',[])]))
  elif typ=='pcb_keepout':
   shape=g.keepout_geometry(e)
   if '--rectangular-heads' in sys.argv and e.get('shape')=='circle':
    c=e['center'];r=e['radius'];shape=g.box(c['x']-r,c['y']-r,c['x']+r,c['y']+r)
   for l in layers:add(l,shape)
  elif typ=='pcb_hole':
   for l in layers:add(l,g.Point(e['x'],e['y']).buffer(e['hole_diameter']/2+.1))
 border=.3+(.25 if via else width/2)
 for d in draws:
  b=math.ceil(border/STEP);d.rectangle([0,0,N-1,b],fill=1);d.rectangle([0,N-1-b,N-1,N-1],fill=1);d.rectangle([0,0,b,N-1],fill=1);d.rectangle([N-1-b,0,N-1,N-1],fill=1)
 return [np.asarray(im,dtype=np.bool_) for im in imgs]
def points(e):
 out={}
 if e['type'] in ['pcb_smtpad','pcb_plated_hole']:
  p=ports[e['pcb_port_id']]
  for l in e.get('layers',[e.get('layer','top')]):
   if l in layers:out[(*xy(p['x'],p['y']),layers.index(l))]=(p['x'],p['y'])
  if e['type']=='pcb_smtpad':
   q=g.geometry(e).buffer(-.015)
   if not q.is_empty:
    x0,y0,x1,y1=q.bounds;ix0=math.ceil((x0-LOW)/STEP);ix1=math.floor((x1-LOW)/STEP);iy0=math.ceil((y0-LOW)/STEP);iy1=math.floor((y1-LOW)/STEP)
    # Grid-aligned points strictly inside native pad copper allow real
    # connections when rounding blocks the logical center. No pad is moved.
    for ix in {ix0,ix1,(ix0+ix1)//2}:
     for iy in {iy0,iy1,(iy0+iy1)//2}:
      x,y=world((ix,iy))
      if q.covers(g.Point(x,y)):
       for l in e.get('layers',[e.get('layer','top')]):
        if l in layers:out[(ix,iy,layers.index(l))]=(x,y)

 elif e['type']=='pcb_trace':
  for a in e['route']:
   if a['route_type']=='wire' and a['layer'] in layers:out[(*xy(a['x'],a['y']),layers.index(a['layer']))]=(a['x'],a['y'])
 elif e['type']=='pcb_via':
  for l in e['layers']:
   if l in layers:out[(*xy(e['x'],e['y']),layers.index(l))]=(e['x'],e['y'])
 elif e['type']=='pcb_copper_pour' and e['layer'] in layers:
  b=e['brep_shape'];pts=lambda r:[(p['x'],p['y'])for p in r['vertices']];q=g.Polygon(pts(b['outer_ring']),[pts(r)for r in b.get('inner_rings',[])])
  # Positive points inside actual same-net planes permit a short connection
  # to the nearest conductive region rather than an arbitrary distant pad.
  inset=q.buffer(-.20).simplify(.15,preserve_topology=True)
  for poly in inset.geoms if hasattr(inset,'geoms')else[inset]:
   if poly.is_empty or poly.geom_type!='Polygon':continue
   candidates=list(poly.exterior.coords)+[(poly.representative_point().x,poly.representative_point().y)]
   for x,y in candidates:out[(*xy(x,y),layers.index(e['layer']))]=(x,y)
 return out
repairs=[]
selected=sys.argv[sys.argv.index("--nets")+1].split(",") if "--nets" in sys.argv else None
selected=set(sys.argv[sys.argv.index('--nets')+1].split(',')) if '--nets' in sys.argv else None
priority=['VCP','CP2','CP1','VREG','ENABLE_N','SLEEP','DIR','STEP','VREF','SENSE1','SENSE2','A_PLUS','A_MINUS','B_PLUS','B_MINUS','PD_VBUS','V3V3','GND'] if selected is not None else []
ordered=list(dict.fromkeys([*nets,*traces]));ordered.sort(key=lambda k:priority.index(nets.get(k,{}).get('name')) if nets.get(k,{}).get('name') in priority else len(priority))
for net in ordered:
 if selected is not None and nets.get(net,{}).get('name') not in selected:continue
 if selected and nets.get(net,{}).get("name") not in selected:continue
 for attempt in range(100):
  if '--explicit-ground' in sys.argv and nets.get(net,{}).get('name')=='GND':
   g.j=[e for e in j if e['type']!='pcb_copper_pour'];elems,roots=g.groups(net);g.j=j
  else:elems,roots=g.groups(net)
  padroots={r for e,r in zip(elems,roots) if e.get('pcb_port_id')}
  if len(padroots)<2:break
  # Prefer the island with most existing vias: escape to free routing space first.
  startroot=max(padroots,key=lambda r:sum(e['type']=='pcb_via' for e,rr in zip(elems,roots) if rr==r));starts={};goals={}
  for e,r in zip(elems,roots):
   if r in padroots:(starts if r==startroot else goals).update(points(e))
  width=.35 if nets.get(net,{}).get('name')=='BUCK_SW' else .30 if nets.get(net,{}).get('name') in ['VMOTOR','A_PLUS','A_MINUS','B_PLUS','B_MINUS','SENSE1','SENSE2','LOGIC_IN','PD_VBUS','V3V3'] else .16
  blocked=obstacle(net,width);vb=obstacle(net,width,True)
  starts={s:p for s,p in starts.items() if not blocked[s[2]][s[1],s[0]]};goals={s:p for s,p in goals.items() if not blocked[s[2]][s[1],s[0]]}
  assert starts and goals,('No accessible island nodes',nets.get(net,{}).get('name',net))
  goalmap=np.ones((N,N),dtype=np.bool_)
  for x,y,l in goals:goalmap[y,x]=False
  # Nearest-goal distance remains useful when distant islands surround the
  # start; the old bounding rectangle degenerated to zero over that region.
  distance=distance_transform_edt(goalmap)
  def heuristic(s):return distance[s[1],s[0]]
  heap=[(heuristic(s),0,s) for s in starts];heapq.heapify(heap);best={s:0 for s in starts};prev={};end=None;expanded=0
  while heap:
   _,cost,s=heapq.heappop(heap)
   if cost!=best.get(s):continue
   if s in goals:end=s;break
   expanded+=1
   if expanded>1800000:break
   x,y,l=s;options=[(x+dx,y+dy,l,1.41421356 if dx and dy else 1) for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]]
   if all(not v[y,x] for v in vb):options += [(x,y,nl,45) for nl in range(len(layers)) if nl!=l]
   for nx,ny,nl,dc in options:
    if not(0<=nx<N and 0<=ny<N) or blocked[nl][ny,nx]:continue
    if nl==l and nx!=x and ny!=y and (blocked[l][y,nx] or blocked[l][ny,x]):continue
    t=(nx,ny,nl);nc=cost+dc
    if nc+1e-8<best.get(t,float('inf')):best[t]=nc;prev[t]=s;heapq.heappush(heap,(nc+heuristic(t),nc,t))
  assert end is not None,('No compliant path',nets.get(net,{}).get('name',net),expanded)
  nodes=[end]
  while nodes[-1] not in starts:nodes.append(prev[nodes[-1]])
  nodes.reverse();start=nodes[0];slim=[start]
  for i in range(1,len(nodes)-1):
   a,b,c=nodes[i-1:i+2]
   if a[2]!=b[2] or b[2]!=c[2] or (b[0]-a[0],b[1]-a[1])!=(c[0]-b[0],c[1]-b[1]):slim.append(b)
  slim.append(end);route=[];vias=[];old=None
  if start==end:
   layer=layers[start[2]];ax,ay=starts[start];bx,by=goals[end];bridgewidth=.6 if nets.get(net,{}).get('name')=='PD_VBUS' and layer=='inner2' else width;route=[{'route_type':'wire','x':ax,'y':ay,'width':bridgewidth,'layer':layer},{'route_type':'wire','x':bx,'y':by,'width':bridgewidth,'layer':layer}];slim=[]
  for i,s in enumerate(slim):
   x,y=world(s);layer=layers[s[2]]
   if i==0:x,y=starts[start]
   if i==len(slim)-1:x,y=goals[end]
   if old and old!=layer:
    route.append({'route_type':'via','x':x,'y':y,'from_layer':old,'to_layer':layer,'via_diameter':.5,'via_hole_diameter':.25});vias.append((x,y))
   route.append({'route_type':'wire','x':x,'y':y,'width':(.6 if nets.get(net,{}).get('name')=='PD_VBUS' and layer=='inner2' else width),'layer':layer});old=layer
  tid='supplier_repair_island_'+net.rsplit('_',1)[-1]+'_'+str(sum(e['type']=='pcb_trace' and e['pcb_trace_id'].startswith('supplier_repair_island_'+net.rsplit('_',1)[-1]+'_') for e in j))
  while any(e.get('pcb_trace_id')==tid for e in j):tid+='x'
  common={'source_trace_id':traces[net],'subcircuit_connectivity_map_key':net,'subcircuit_id':'subcircuit_source_group_0'}
  if net in nets:common['source_net_id']=nets[net]['source_net_id']
  j.append({'type':'pcb_trace','pcb_trace_id':tid,'route':route,'pcb_port_ids':[],**common})
  for i,(x,y) in enumerate(vias):j.append({'type':'pcb_via','pcb_via_id':tid+'_via'+str(i),'pcb_trace_id':tid,'x':x,'y':y,'hole_diameter':.25,'outer_diameter':.5,'layers':['top','inner1','inner2','bottom'],'tented_on_top':True,'tented_on_bottom':True,**common})
  repairs.append({'net':nets.get(net,{}).get('name',net),'route':route,'expandedNodes':expanded});print(repairs[-1]['net'],len(route),'points',len(vias),'vias',expanded,'search nodes',flush=True)
  # Persist completed work even if a later net requires another placement adjustment.
  path.write_text(json.dumps([e for e in j if e['type'] in ['pcb_trace','pcb_via']] if '--seed' in sys.argv else j,indent=2)+'\n')
(ROOT/'artifacts/rp-engineering-selected-repairs.json').write_text(json.dumps(repairs,indent=2)+'\n')
