"""Clearance-aware escape with explicit least-trace rip-up; final rerouting required."""
import json,math,sys
from shapely.strtree import STRtree
import verify_supplier_connectivity as g
j=g.j; nets={e['subcircuit_connectivity_map_key']:e for e in j if e['type']=='source_net'}; traces={e['subcircuit_connectivity_map_key']:e['source_trace_id'] for e in j if e['type']=='source_trace'}
plans=[('U_MCU','GPIO7'),('U_DRV','DIR'),('U_DRV','ENABLE_N'),('C_VREG_OUT','pin1')];report=[]
for ref,pin in plans:
 tid='supplier_repair_fanout_'+ref+'_'+pin
 if any(e.get('pcb_trace_id')==tid for e in j):continue
 p=next(p for p in g.ports.values() if g.src[g.comp[p['pcb_component_id']]['source_component_id']]==ref and g.sp[p['source_port_id']]['name']==pin);key=g.sp[p['source_port_id']]['subcircuit_connectivity_map_key'];fixedall=[];fixedtop=[];ripall=[];riptop=[];ownersall=[];ownerstop=[]
 for e in j:
  typ=e['type']
  if typ in ['pcb_smtpad','pcb_plated_hole']:
   sh=g.geometry(e);fixedall.append(sh)
   if g.key(e)!=key and 'top' in e.get('layers',[e.get('layer','top')]):fixedtop.append(sh)
  elif typ=='pcb_via':
   if g.key(e)!=key:sh=g.Point(e['x'],e['y']).buffer(e['outer_diameter']/2);fixedall.append(sh);fixedtop.append(sh)
  elif typ=='pcb_trace' and g.key(e)!=key:
   protect=not e['pcb_trace_id'].startswith('freerouted_')
   for a,b in zip(e['route'],e['route'][1:]):
    if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']:
     sh=g.LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2)
     if protect:
      fixedall.append(sh)
      if a['layer']=='top':fixedtop.append(sh)
     else:
      ripall.append(sh);ownersall.append(e['pcb_trace_id'])
      if a['layer']=='top':riptop.append(sh);ownerstop.append(e['pcb_trace_id'])
  elif typ in ['pcb_keepout','pcb_hole']:
   sh=g.keepout_geometry(e) if typ=='pcb_keepout' else g.Point(e['x'],e['y']).buffer(e['hole_diameter']/2+.1);fixedall.append(sh);fixedtop.append(sh)
 ft=STRtree(fixedtop);fa=STRtree(fixedall);rt=STRtree(riptop);ra=STRtree(ripall)
 def hits(sh,tree):return [i for i in tree.query(sh.buffer(.158)) if sh.distance(tree.geometries[i])<.158]
 center=g.comp[p['pcb_component_id']]['center'];dx=p['x']-center['x'];dy=p['y']-center['y'];out=(math.copysign(1,dx),0) if abs(dx)>abs(dy) else (0,math.copysign(1,dy));best=None
 for advance in [.4,.5,.65,.8,1,1.2]:
  turn=(p['x']+out[0]*advance,p['y']+out[1]*advance)
  if hits(g.LineString([(p['x'],p['y']),turn]).buffer(.08),ft):continue
  for ix in range(-35,36):
   for iy in range(-35,36):
    via=(round(p['x']+ix*.1,5),round(p['y']+iy*.1,5));circ=g.Point(*via).buffer(.25)
    if not g.box(-17.2,-17.2,17.2,17.2).covers(circ) or hits(circ,fa):continue
    pts=[(p['x'],p['y']),turn,via];sh=g.LineString(pts).buffer(.08)
    if hits(sh,ft):continue
    removals={ownerstop[i] for i in hits(sh,rt)}|{ownersall[i] for i in hits(circ,ra)};length=sum(math.dist(a,b) for a,b in zip(pts,pts[1:]));cost=(len(removals),length)
    if best is None or cost<best[0]:best=(cost,via,pts,removals)
 assert best,('No legal native-pad escape',ref,pin)
 cost,via,pts,removals=best;removed=[e for e in j if e.get('pcb_trace_id') in removals and e['type']=='pcb_trace'];j=[e for e in j if e not in removed]
 common={'source_net_id':nets[key]['source_net_id'],'source_trace_id':traces[key],'subcircuit_connectivity_map_key':key,'subcircuit_id':'subcircuit_source_group_0'};route=[{'route_type':'wire','x':x,'y':y,'width':.16,'layer':'top'} for x,y in pts];route[0]['start_pcb_port_id']=p['pcb_port_id'];j.append({'type':'pcb_trace','pcb_trace_id':tid,'route':route,'pcb_port_ids':[p['pcb_port_id']],**common});j.append({'type':'pcb_via','pcb_via_id':tid+'_via0','x':via[0],'y':via[1],'outer_diameter':.5,'hole_diameter':.25,'layers':['top','inner1','inner2','bottom'],'tented_on_top':True,'tented_on_bottom':True,**common})
 report.append({'reference':ref,'pin':pin,'net':nets[key]['name'],'lengthMm':cost[1],'via':via,'removedRecords':removed});print(ref,pin,cost,via,sorted(removals),flush=True);g.path.write_text(json.dumps(j,indent=2)+'\n');(g.ROOT/'artifacts/trapped-pad-corrections.json').write_text(json.dumps(report,indent=2)+'\n')
