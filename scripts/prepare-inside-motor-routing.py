"""Merge reviewed inside-board placement; locally remove obsolete copper for repair.
Pin identities and unaffected component geometry are invariant. Every clipped net
must subsequently pass source, independent copper and actual CAM connectivity.
"""
import json,hashlib,math
import verify_supplier_connectivity as g
from shapely.geometry import box,LineString,Point,Polygon
from shapely.ops import unary_union
j=g.j;fresh=json.loads((g.ROOT/'artifacts/final-source.circuit.json').read_text());rp=g.ROOT.name=='NEMA14_RP2040'
move=['J_MOTOR','U_DRV','R_SA','R_SB','C_CP','C_VM','C_VREG','C_VCP','C_DRV_LOGIC','C_VM2','C_REF','R_REF_H','R_REF_L','C_BOOTSTRAP','Y_MCU','C_XOUT','C_XIN']if rp else ['J_MOTOR','U_DRV','C_VCP','C_VREG']
ids={e['pcb_component_id']for e in j if e['type']=='pcb_component'and g.src[e['source_component_id']]in move}
oldports={e['source_port_id']:e for e in j if e['type']=='source_port'};newports={e['source_port_id']:e for e in fresh if e['type']=='source_port'}
assert oldports.keys()==newports.keys()
for k,e in oldports.items():
 for f in ['source_component_id','pin_number','name','subcircuit_connectivity_map_key']:assert e.get(f)==newports[k].get(f),(k,f)
newpcb={e['pcb_component_id']:e for e in fresh if e['type']=='pcb_component'}
# Follow the driver's required filled/capped exposed-pad via when the chip moves.
thermal_ids=[]
for e in j:
 if e['type']=='pcb_via':
  for id in ids:
   if g.src[g.comp[id]['source_component_id']]!='U_DRV':continue
   c=g.comp[id]['center'];d=newpcb[id]['center']
   if math.hypot(e['x']-c['x'],e['y']-c['y'])<.001:e['x']+=d['x']-c['x'];e['y']+=d['y']-c['y'];thermal_ids.append(e['pcb_via_id'])
selected={g.key(e)for e in j if e['type']in ['pcb_smtpad','pcb_plated_hole']and e.get('pcb_component_id')in ids};selected.discard(None)
bay=box(-6.15,-17.2,10.35,-3.9).union(box(-3.85,-3.9,-1.8,-1.45))if rp else box(-6.8,-17.2,4.3,-4.1)
out=[e for e in j if e['type'].startswith('pcb_')and e.get('pcb_component_id')not in ids and e['type']!='pcb_silkscreen_text'and not e['type'].endswith(('_error','_warning'))]
out += [e for e in fresh if e['type'].startswith('pcb_')and e.get('pcb_component_id')in ids and not e['type'].endswith(('_error','_warning'))]
out += [e for e in fresh if not e['type'].startswith('pcb_')and not e['type'].endswith(('_error','_warning'))]
out += [e for e in fresh if e['type']=='pcb_silkscreen_text'and e.get('pcb_component_id')not in ids]
newpads=[e for e in out if e['type']in ['pcb_smtpad','pcb_plated_hole']and e.get('pcb_component_id')in ids]
cuts={}
for net in set(g.nets)|selected:
 for layer in ['top','inner1','inner2','bottom']:
  cuts[net,layer]=unary_union([g.geometry(e).buffer(.20)for e in newpads if g.key(e)!=net and layer in e.get('layers',[e.get('layer')])])
result=[];clipped=[];affected=set(selected)
def ring(r):return {'vertices':[{'x':x,'y':y}for x,y in list(r.coords)[:-1]]}
for e in out:
 t=e['type'];net=g.key(e)
 if t=='pcb_trace':
  mask=bay if net in selected and e['pcb_trace_id']!='engineering_local_IOVDD10_bridge' else Polygon();changes=False;pieces=[]
  for i,(a,b)in enumerate(zip(e['route'],e['route'][1:])):
   if a['route_type']!=b['route_type']or a['route_type']!='wire'or a['layer']!=b['layer']:continue
   line=LineString([(a['x'],a['y']),(b['x'],b['y'])]);cut=mask.union(cuts.get((net,a['layer']),Polygon()).buffer(max(a['width'],b['width'])/2));remaining=line.difference(cut)
   if abs(remaining.length-line.length)>1e-8:changes=True
   for k,l in enumerate(remaining.geoms if hasattr(remaining,'geoms')else[remaining]):
    if l.geom_type!='LineString'or l.length<.00001:continue
    coords=list(l.coords);pieces.append({**e,'pcb_trace_id':e['pcb_trace_id']+f'_inside_{i}_{k}','pcb_port_ids':[],'route':[{'route_type':'wire','x':x,'y':y,'layer':a['layer'],'width':max(a['width'],b['width'])}for x,y in coords]})
  if changes:affected.add(net);clipped.append(e['pcb_trace_id']);result+=pieces
  else:result.append(e)
 elif t=='pcb_via':
  copper=Point(e['x'],e['y']).buffer(e['outer_diameter']/2)
  if e['pcb_via_id']not in thermal_ids+['engineering_local_IOVDD10_lead_via','engineering_local_IOVDD10_cap_via'] and ((net in selected and bay.contains(copper))or any(copper.intersects(cuts.get((net,l),Polygon()))for l in e['layers'])):affected.add(net);clipped.append(e['pcb_via_id'])
  else:result.append(e)
 elif t=='pcb_copper_pour':
  b=e['brep_shape'];pts=lambda r:[(p['x'],p['y'])for p in r['vertices']];poly=Polygon(pts(b['outer_ring']),[pts(r)for r in b.get('inner_rings',[])]);q=poly.difference(bay.union(cuts.get((net,e['layer']),Polygon())))
  for i,p in enumerate(q.geoms if hasattr(q,'geoms')else[q]):
   if p.geom_type=='Polygon'and p.area>1e-8:result.append({**e,'pcb_copper_pour_id':e['pcb_copper_pour_id']+f'_inside_{i}','brep_shape':{'outer_ring':ring(p.exterior),'inner_rings':[ring(r)for r in p.interiors]}})
 else:result.append(e)
ground=next(k for k,n in g.nets.items()if n=='GND')
result=[e for e in result if not(e['type']=='pcb_copper_pour'and g.key(e)==ground)]
g.path.write_text(json.dumps(result,indent=2)+'\n');names=sorted(g.nets[k]for k in affected if k in g.nets);proof={'source_sha256':hashlib.sha256((g.ROOT/'artifacts/final-source.circuit.json').read_bytes()).hexdigest(),'moved_components':move,'physical_pin_net_identity_preserved':True,'moved_thermal_vias':thermal_ids,'clipped_copper_records':clipped,'nets_requiring_repair':names,'bay_bounds_mm':list(bay.bounds),'status':'ROUTING_CHECKS_REQUIRED'};(g.ROOT/'artifacts/validation/service-inside-placement-repair.json').write_text(json.dumps(proof,indent=2)+'\n');print(','.join(names))
