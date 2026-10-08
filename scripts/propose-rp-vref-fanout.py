"""Proposal-only clearance-aware native-pad ground fanouts; never writes board."""
import json,sys,math,heapq,pathlib,hashlib
import numpy as np
from PIL import Image,ImageDraw
from shapely.strtree import STRtree
import verify_supplier_connectivity as g
ROOT=g.ROOT;inputfile=ROOT/'artifacts/rp-vref-fanout-input.circuit.json';j=json.loads(inputfile.read_text());g.j=j
nets={e['subcircuit_connectivity_map_key']:e for e in j if e['type']=='source_net'};traces={e['subcircuit_connectivity_map_key']:e['source_trace_id'] for e in j if e['type']=='source_trace'}
STEP=.025;clear=.158;extra=.012;additions=[];reports=[]
def port(ref,pin):return next(p for p in g.ports.values() if g.src[g.comp[p['pcb_component_id']]['source_component_id']]==ref and g.sp[p['source_port_id']]['name']==pin)
def shapes(key,ignored):
 top=[];allforeign=[];pads=[];constraints=[]
 for e in j:
  typ=e['type'];foreign=g.key(e)!=key
  if typ in ['pcb_smtpad','pcb_plated_hole']:
   s=g.geometry(e);pads.append(s)
   if foreign:
    allforeign.append(s)
    if 'top' in e.get('layers',[e.get('layer','top')]):top.append(s)
  elif typ=='pcb_trace' and foreign and e['pcb_trace_id'] not in ignored:
   for a,b in zip(e['route'],e['route'][1:]):
    if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']:
     s=g.LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2);allforeign.append(s)
     if a['layer']=='top':top.append(s)
  elif typ=='pcb_via' and foreign:s=g.Point(e['x'],e['y']).buffer(e['outer_diameter']/2);top.append(s);allforeign.append(s)
  elif typ=='pcb_keepout':constraints.append(g.keepout_geometry(e))
  elif typ=='pcb_hole':constraints.append(g.Point(e['x'],e['y']).buffer(e['hole_diameter']/2+.1))
 return top+constraints,allforeign+pads+constraints

def route(ref,pin,ignored=[]):
 p=port(ref,pin);key=g.sp[p['source_port_id']]['subcircuit_connectivity_map_key'];top,viaobs=shapes(key,ignored)
 loX=max(-17.5,p['x']-5);loY=max(-17.5,p['y']-5);hiX=min(17.5,p['x']+5);hiY=min(17.5,p['y']+5);W=round((hiX-loX)/STEP)+1;H=round((hiY-loY)/STEP)+1
 xy=lambda x,y:(round((x-loX)/STEP),round((y-loY)/STEP));world=lambda q:(loX+q[0]*STEP,loY+q[1]*STEP)
 def mask(items,margin):
  im=Image.new('L',(W,H));d=ImageDraw.Draw(im)
  for shape in items:
   b=shape.buffer(margin)
   if b.bounds[2]<loX or b.bounds[0]>hiX or b.bounds[3]<loY or b.bounds[1]>hiY:continue
   for poly in ([b] if b.geom_type=='Polygon' else b.geoms):d.polygon([xy(x,y) for x,y in poly.exterior.coords],fill=1)
  return np.asarray(im,dtype=np.bool_)
 blocked=mask(top,clear+.08+extra);vblocked=mask(viaobs,clear+.25+extra)
 start=xy(p['x'],p['y']);assert not blocked[start[1],start[0]],(ref,pin,'starting pad trapped')
 heap=[(0,start)];best={start:0};prev={};end=None
 while heap:
  cost,s=heapq.heappop(heap)
  if cost!=best.get(s):continue
  x,y=s;wx,wy=world(s)
  if not vblocked[y,x] and -17.092<=wx<=17.092 and -17.092<=wy<=17.092:end=s;break
  for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
   nx,ny=x+dx,y+dy
   if not(0<=nx<W and 0<=ny<H) or blocked[ny,nx]:continue
   if dx and dy and (blocked[y,nx] or blocked[ny,x]):continue
   t=(nx,ny);nc=cost+math.hypot(dx,dy)
   if nc<best.get(t,1e20)-1e-9:best[t]=nc;prev[t]=s;heapq.heappush(heap,(nc,t))
 if end is None:return None,{'ref':ref,'pin':pin,'noViaReachable':True,'reachableGridCells':len(best),'ignoredTraces':ignored}
 pts=[end]
 while pts[-1]!=start:pts.append(prev[pts[-1]])
 pts.reverse();slim=[pts[0]]
 for i in range(1,len(pts)-1):
  a,b,c=pts[i-1:i+2]
  if (b[0]-a[0],b[1]-a[1])!=(c[0]-b[0],c[1]-b[1]):slim.append(b)
 slim.append(pts[-1]);coords=[world(q) for q in slim];coords[0]=(p['x'],p['y']);v=coords[-1];line=g.LineString(coords).buffer(.08);ann=g.Point(*v).buffer(.25)
 minline=min(line.distance(s) for s in top);minvia=min(ann.distance(s) for s in viaobs);assert minline>=clear-1e-6 and minvia>=clear-1e-6,(ref,pin,minline,minvia)
 common={'source_net_id':nets[key]['source_net_id'],'source_trace_id':traces[key],'subcircuit_connectivity_map_key':key,'subcircuit_id':'subcircuit_source_group_0'};tid='supplier_repair_VREF_fanout_'+ref+'_'+pin
 r=[{'route_type':'wire','x':x,'y':y,'width':.16,'layer':'top'} for x,y in coords];r[0]['start_pcb_port_id']=p['pcb_port_id']
 es=[{'type':'pcb_trace','pcb_trace_id':tid,'route':r,'pcb_port_ids':[p['pcb_port_id']],**common},{'type':'pcb_via','pcb_via_id':tid+'_via','x':v[0],'y':v[1],'outer_diameter':.5,'hole_diameter':.25,'layers':['top','inner1','inner2','bottom'],'tented_on_top':True,'tented_on_bottom':True,**common}]
 return es,{'ref':ref,'pin':pin,'via':v,'points':coords,'lengthMm':sum(math.dist(a,b) for a,b in zip(coords,coords[1:])),'minimumTopForeignClearanceMm':minline,'minimumViaAllLayerClearanceMm':minvia,'ignoredTraces':ignored,'gridStepMm':STEP}
for ref,pin in [('U_DRV','REF')]:
 es,rep=route(ref,pin)
 if es is None:
  print(rep,flush=True)
  pass
 if es:additions.extend(es);j.extend(es)
 reports.append(rep);print(rep,flush=True)
out={'inputSha256':hashlib.sha256(inputfile.read_bytes()).hexdigest(),'inputSnapshot':str(inputfile.relative_to(ROOT)),'proposalOnly':True,'minimumForeignClearanceMm':clear,'nativeFootprintsChanged':False,'requiresRootIndependentMergeCheck':True,'additions':additions,'fanouts':reports,'removeTraceIds':sorted(set(t for r in reports if 'via' in r for t in r.get('ignoredTraces',[])))}
(ROOT/'artifacts/rp-vref-fanout-proposal.json').write_text(json.dumps(out,indent=2)+'\n')
