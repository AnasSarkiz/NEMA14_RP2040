"""Reserve standard-via escapes for genuinely open pads after native SES import.

Every via clears every original native pad. Copper/keepout checks use saved
geometry on all layers; paths remain inspectable and replayable. Run before
fill-ground and independent source/CAM acceptance.
"""
import json,math,sys
from shapely.strtree import STRtree
import verify_supplier_connectivity as g
j=g.j;nets={e['subcircuit_connectivity_map_key']:e for e in j if e['type']=='source_net'};traces={e['subcircuit_connectivity_map_key']:e['source_trace_id'] for e in j if e['type']=='source_trace'}
def port(ref,pin):return next(p for p in g.ports.values() if g.src[g.comp[p['pcb_component_id']]['source_component_id']]==ref and g.sp[p['source_port_id']]['name']==pin)
plans=[('U_BUCK','GND'),('U_DRV','GND'),('U_DRV','GND18'),('C_VM2','pin2'),('U_MCU','GPIO7'),('U_MCU','GPIO8'),('U_DRV','DIR'),('U_DRV','ENABLE_N'),('C_VREG_OUT','pin1')]
report=[]
for ref,pin in plans:
 p=port(ref,pin);key=g.sp[p['source_port_id']]['subcircuit_connectivity_map_key'];allpads=[g.geometry(e) for e in j if e['type'] in ['pcb_smtpad','pcb_plated_hole']];foreign_top=[];foreign_all=[];constraints=[]
 for e in j:
  typ=e['type']
  if typ in ['pcb_smtpad','pcb_plated_hole'] and g.key(e)!=key:
   shape=g.geometry(e);foreign_all.append(shape)
   if 'top' in e.get('layers',[e.get('layer','top')]):foreign_top.append(shape)
  elif typ=='pcb_via' and g.key(e)!=key:
   shape=g.Point(e['x'],e['y']).buffer(e['outer_diameter']/2);foreign_top.append(shape);foreign_all.append(shape)
  elif typ=='pcb_trace' and g.key(e)!=key:
   for a,b in zip(e['route'],e['route'][1:]):
    if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']:
     shape=g.LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2);foreign_all.append(shape)
     if a['layer']=='top':foreign_top.append(shape)
  elif typ=='pcb_keepout':constraints.append(g.keepout_geometry(e))
  elif typ=='pcb_hole':constraints.append(g.Point(e['x'],e['y']).buffer(e['hole_diameter']/2+.1))
 via_tree=STRtree(allpads+foreign_all+constraints);line_tree=STRtree(foreign_top+constraints)
 def collide(shape,tree,clear=.158):return any(shape.distance(tree.geometries[i])<clear for i in tree.query(shape.buffer(clear)))
 center=g.comp[p['pcb_component_id']]['center'];dx=p['x']-center['x'];dy=p['y']-center['y'];out=(math.copysign(1,dx),0) if abs(dx)>abs(dy) else (0,math.copysign(1,dy));width=.16;candidates=[]
 for advance in [.4,.5,.65,.8,1.0,1.2]:
  turn=(p['x']+out[0]*advance,p['y']+out[1]*advance);first=g.LineString([(p['x'],p['y']),turn]).buffer(width/2)
  if collide(first,line_tree):continue
  for ix in range(-35,36):
   for iy in range(-35,36):
    via=(round(p['x']+ix*.1,5),round(p['y']+iy*.1,5));circ=g.Point(*via).buffer(.25)
    if not g.box(-17.25,-17.25,17.25,17.25).covers(circ) or collide(circ,via_tree):continue
    pts=[(p['x'],p['y']),turn,via];line=g.LineString(pts).buffer(width/2)
    if collide(line,line_tree):continue
    candidates.append((sum(math.dist(a,b) for a,b in zip(pts,pts[1:])),via,pts))
 assert candidates,('No legal standard-via fanout',ref,pin)
 length,via,pts=min(candidates);tid='supplier_repair_fanout_'+ref+'_'+pin;common={'source_net_id':nets[key]['source_net_id'],'source_trace_id':traces[key],'subcircuit_connectivity_map_key':key,'subcircuit_id':'subcircuit_source_group_0'}
 route=[{'route_type':'wire','x':x,'y':y,'width':width,'layer':'top'} for x,y in pts];route[0]['start_pcb_port_id']=p['pcb_port_id'];j.append({'type':'pcb_trace','pcb_trace_id':tid,'route':route,'pcb_port_ids':[p['pcb_port_id']],**common});j.append({'type':'pcb_via','pcb_via_id':tid+'_via0','x':via[0],'y':via[1],'outer_diameter':.5,'hole_diameter':.25,'layers':['top','inner1','inner2','bottom'],'tented_on_top':True,'tented_on_bottom':True,**common})
 report.append({'reference':ref,'pin':pin,'net':nets[key]['name'],'lengthMm':length,'via':via,'widthMm':width});print(ref,pin,round(length,3),'mm',via,flush=True);g.path.write_text(json.dumps(j,indent=2)+'\n')
(g.ROOT/'artifacts/verified-fanout-adjustments.json').write_text(json.dumps({'minimumClearanceMm':.15,'roundingGuardMm':.008,'viaPadMm':.5,'viaDrillMm':.25,'fanouts':report},indent=2)+'\n')
