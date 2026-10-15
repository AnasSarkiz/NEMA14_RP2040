"""Reserve coupled USB trunks and clear affected copper for constrained repair.

Endpoint fanouts remain explicit; all clearances, connectivity and reference
coverage must be checked after repairs and refilling. No hardware/impedance
qualification follows from this construction step.
"""
import json,math,heapq,hashlib
import numpy as np
from PIL import Image,ImageDraw
from shapely.geometry import Point,LineString,Polygon,box
from shapely.ops import unary_union
import verify_supplier_connectivity as g
j=g.j;ROOT=g.ROOT;GRID=.025;LOW=-17.5;N=1401;WIDTH=.25;PITCH=.41
names={e['name']:e for e in j if e['type']=='source_net'};keys={n:e['subcircuit_connectivity_map_key'] for n,e in names.items()};usb={keys[n] for n in ['USB_DP','USB_DM','MCU_DP','MCU_DM'] if n in keys}
components={g.src[e['source_component_id']]:e for e in j if e['type']=='pcb_component'}
def port(ref,role):return next(p for p in g.ports.values() if g.src[g.sp[p['source_port_id']]['source_component_id']]==ref and g.sp[p['source_port_id']]['name']==role)
def midpoint(a,b):return ((a['x']+b['x'])/2,(a['y']+b['y'])/2)
def pixel(p):return tuple(round((v-LOW)/GRID) for v in p)
def world(p):return tuple(LOW+v*GRID for v in p)
removed_usb=[e.get(e['type']+'_id') for e in j if e['type'] in ['pcb_trace','pcb_via'] and g.key(e) in usb]
j[:]=[e for e in j if not(e['type'] in ['pcb_trace','pcb_via','pcb_copper_pour'] and (e['type']=='pcb_copper_pour' or g.key(e) in usb))]
plans=[];rp='R_DP' in components
esd=components['U_ESD']['center']
if rp:
 dp=port('J_DATA','DP1');dm=port('J_DATA','DM1');start=midpoint(dp,dm);plans.append(('connector_to_ESD','bottom','USB_DP','USB_DM',(start[0],components['J_DATA']['center']['y']+.55),(esd['x'],esd['y']-1.95),-.15,-.4,'J_DATA','DP1','U_ESD','DP1'))
 a=port('R_DP','pin2');b=port('R_DM','pin2');end=midpoint(a,b);plans.append(('ESD_to_series','bottom','USB_DP','USB_DM',(esd['x'],esd['y']+1.9),(end[0],end[1]+.67),.4,.4,'U_ESD','DP1','R_DP','pin2'))
 a=port('R_DP','pin1');b=port('R_DM','pin1');start=midpoint(a,b);a=port('U_MCU','USB_DP');b=port('U_MCU','USB_DM');end=midpoint(a,b);plans.append(('series_to_MCU','top','MCU_DP','MCU_DM',(start[0],start[1]-.27),(end[0],end[1]+.62),.25,.20,'R_DP','pin1','U_MCU','USB_DP'))
else:
 a=port('U_MCU','USB_DP');b=port('U_MCU','USB_DM');end=midpoint(a,b);plans.append(('ESD_to_MCU','bottom','USB_DP','USB_DM',(esd['x'],esd['y']+1.9),(end[0],end[1]+.70),.4,.4,'U_ESD','DP1','U_MCU','USB_DP'))
cores=[]
def mask(layer,pair):
 im=Image.new('L',(N,N));draw=ImageDraw.Draw(im);radius=WIDTH/2+PITCH/2+.15+.005
 def add(geometry):
  geom=geometry.buffer(radius,quad_segs=12)
  for poly in list(geom.geoms) if hasattr(geom,'geoms') else [geom]:
   if poly.geom_type=='Polygon':draw.polygon([pixel(p) for p in poly.exterior.coords],fill=1)
 for e in j:
  typ=e['type']
  if typ in ['pcb_smtpad','pcb_plated_hole'] and layer in e.get('layers',[e.get('layer','top')]) and g.key(e) not in pair:add(g.geometry(e).buffer(.1 if typ=='pcb_plated_hole' else 0))
  elif typ=='pcb_via' and g.nets.get(g.key(e))=='GND':add(Point(e['x'],e['y']).buffer(e['outer_diameter']/2+(.465 if e['pcb_via_id'].startswith(('oscillator_','thermal')) else 0)))
  elif typ=='pcb_hole':add(Point(e['x'],e['y']).buffer(e['hole_diameter']/2+.1))
  elif typ=='pcb_keepout':
   c=e['center'];r=e['radius'];add(Point(c['x'],c['y']).buffer(r,quad_segs=128))
 # Keep the coupled input and its reference corridor outside the driver
 # and shunt courtyards, leaving room for ordinary through-via escapes.
 for ref in ['U_DRV','R_SA','R_SB']:
  cid=components[ref]['pcb_component_id']
  courtyard=next(e for e in j if e['type']=='pcb_courtyard_outline' and e['pcb_component_id']==cid)
  add(Polygon([(p['x'],p['y']) for p in courtyard['outline']]).buffer(1.75))
 # Planned ordinary ESD vias must remain clear of both coupled conductors.
 for role in ['DP1','DM1']:
  terminal=port('U_ESD',role);add(Point(terminal['x'],esd['y']).buffer(.225))
 for core in cores:
  if core['layer']==layer:add(LineString(core['centerline']))
 border=round(.8/GRID)
 draw.rectangle((0,0,N-1,border),fill=1);draw.rectangle((0,N-1-border,N-1,N-1),fill=1);draw.rectangle((0,0,border,N-1),fill=1);draw.rectangle((N-1-border,0,N-1,N-1),fill=1)
 return np.array(im,dtype=bool)
def pathfind(start,end,blocked):
 s,t=pixel(start),pixel(end)
 if blocked[s[1],s[0]] or blocked[t[1],t[0]]:raise RuntimeError('Coupled trunk endpoint blocked '+str((start,end)))
 heap=[(math.dist(s,t),0,s)];cost={s:0};prev={};expanded=0
 while heap:
  _,c,p=heapq.heappop(heap)
  if c!=cost[p]:continue
  if p==t:
   pts=[p]
   while pts[-1]!=s:pts.append(prev[pts[-1]])
   pts.reverse();return [world(q) for i,q in enumerate(pts) if not i or i==len(pts)-1 or (pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1])!=(pts[i+1][0]-pts[i][0],pts[i+1][1]-pts[i][1])]
  expanded+=1
  if expanded>1500000:break
  for dx,dy in [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]:
   q=(p[0]+dx,p[1]+dy)
   if (p==s or q==t) and dy*flow<0:continue
   if not(0<=q[0]<N and 0<=q[1]<N) or blocked[q[1],q[0]]:continue
   if dx and dy and (blocked[p[1],q[0]] or blocked[q[1],p[0]]):continue
   nc=c+math.hypot(dx,dy)
   if nc<cost.get(q,math.inf):cost[q]=nc;prev[q]=p;heapq.heappush(heap,(nc+math.dist(q,t),nc,q))
 raise RuntimeError('No coupled route '+str((start,end)))
for name,layer,dn,mn,start,end,slead,elead,sref,srole,eref,erole in plans:
 flow=1 if name=='connector_to_ESD' else -1
 blocked=mask(layer,{keys[dn],keys[mn]});a=(start[0],start[1]-slead);b=(end[0],end[1]+elead);mid=pathfind(a,b,blocked);pts=[start]+mid+[end];line=LineString(pts)
 tracks=[]
 for net,offset in [(dn,PITCH/2 if name=='connector_to_ESD' else -PITCH/2),(mn,-PITCH/2 if name=='connector_to_ESD' else PITCH/2)]:
  curve=line.offset_curve(offset,join_style='mitre');assert curve.geom_type=='LineString' and curve.is_simple,(name,net,curve.geom_type)
  route=[{'route_type':'wire','x':float(x),'y':float(y),'layer':layer,'width':WIDTH} for x,y in curve.coords]
  source=next(e['source_trace_id'] for e in j if e['type']=='source_trace' and e.get('subcircuit_connectivity_map_key')==keys[net])
  uid='usb_coupled_'+name+'_'+net
  j.append({'type':'pcb_trace','pcb_trace_id':uid,'route':route,'source_net_id':names[net]['source_net_id'],'source_trace_id':source,'subcircuit_connectivity_map_key':keys[net],'subcircuit_id':'subcircuit_source_group_0','pcb_port_ids':[]})
  tracks.append({'net':net,'trace_id':uid,'length_mm':curve.length,'points':list(curve.coords)})
 cores.append({'name':name,'layer':layer,'reference_layer':'inner1' if layer=='top' else 'inner2','centerline':pts,'width_mm':WIDTH,'pitch_mm':PITCH,'gap_mm':PITCH-WIDTH,'tracks':tracks,'core_length_difference_mm':abs(tracks[0]['length_mm']-tracks[1]['length_mm']),'fanout_terminals':[[sref,srole],[eref,erole]]})
 print(name,layer,tracks[0]['length_mm'],tracks[1]['length_mm'],flush=True)
# Clear crossing conductors and reference-plane interruptions. Regular routing
# subsequently obeys these reserved reference regions for every non-ground net.
guards=[(c['layer'],c['reference_layer'],LineString(c['centerline']).buffer(.95)) for c in cores]
removed=[];kept=[]
for e in j:
 typ=e['type'];hit=False
 if typ=='pcb_trace' and not e['pcb_trace_id'].startswith('usb_coupled_'):
  for a,b in zip(e['route'],e['route'][1:]):
   if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']:
    geom=LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2)
    if any(a['layer'] in [layer,ref] and geom.intersects(guard) for layer,ref,guard in guards):hit=True
 elif typ=='pcb_via':hit=g.nets.get(g.key(e))!='GND' and any(Point(e['x'],e['y']).buffer(e['outer_diameter']/2).intersects(guard) for _,_,guard in guards)
 if hit:
  assert not e.get(typ+'_id','').startswith(('oscillator_','reviewed_local_critical_')),'USB construction must preserve validated critical copper'
  removed.append(e.get(typ+'_id'))
 else:kept.append(e)
j[:]=kept;g.path.write_text(json.dumps(j,indent=2)+'\n')
report={'driver_and_shunt_courtyard_reservation_mm':1.75,'reserved_driver_and_shunt_references':['U_DRV','R_SA','R_SB'],'connector_core_offset_above_socket_centre_mm':.55,'constructed_not_yet_qualified':True,'coupled_width_mm':WIDTH,'coupled_gap_mm':PITCH-WIDTH,'cores':cores,'all_USB_vias_and_traces_replaced':removed_usb,'crossing_copper_and_reference_vias_removed_for_repair':removed,'reference_corridor_buffer_mm':.95,'requires_independent_DRC_connectivity_CAM_and_reference_coverage':True}
(ROOT/'artifacts/engineering-fixes/usb-routing-plan.json').write_text(json.dumps(report,indent=2)+'\n')
