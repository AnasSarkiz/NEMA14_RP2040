"""Connect the two native driver ground leads directly to its grounded exposed pad."""
import json,copy
import verify_supplier_connectivity as g
j=g.j;ep=next(e for e in j if e['type']=='pcb_smtpad' and g.src[g.comp[g.ports[e['pcb_port_id']]['pcb_component_id']]['source_component_id']]=='U_DRV' and g.sp[g.ports[e['pcb_port_id']]['source_port_id']]['name']=='EP');eg=g.geometry(ep);changes=[]
for pin in ['GND','GND18']:
 p=next(p for p in g.ports.values() if g.src[g.comp[p['pcb_component_id']]['source_component_id']]=='U_DRV' and g.sp[p['source_port_id']]['name']==pin);key=g.sp[p['source_port_id']]['subcircuit_connectivity_map_key'];tid='supplier_repair_ground_fanout_U_DRV_'+pin;old=next(e for e in j if e.get('pcb_trace_id')==tid);removed=[e for e in j if e.get('pcb_trace_id')==tid or e.get('pcb_via_id')==tid+'_via'];x=eg.bounds[0]+.3 if p['x']<eg.centroid.x else eg.bounds[2]-.3;points=[(p['x'],p['y']),(x,p['y'])];sh=g.LineString(points).buffer(.15);assert eg.intersects(sh)
 minimum=10
 for e in j:
  if g.key(e)==key:continue
  shapes=[]
  if e['type'] in ['pcb_smtpad','pcb_plated_hole'] and 'top' in e.get('layers',[e.get('layer','top')]):shapes=[g.geometry(e)]
  elif e['type']=='pcb_via':shapes=[g.Point(e['x'],e['y']).buffer(e['outer_diameter']/2)]
  elif e['type']=='pcb_trace':shapes=[g.LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2) for a,b in zip(e['route'],e['route'][1:]) if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']=='top']
  elif e['type']=='pcb_keepout':shapes=[g.keepout_geometry(e)]
  for other in shapes:minimum=min(minimum,sh.distance(other))
 assert minimum>=.158,(pin,minimum);new=copy.deepcopy(old);new['route']=[{'route_type':'wire','x':xx,'y':yy,'width':.3,'layer':'top'} for xx,yy in points];new['route'][0]['start_pcb_port_id']=p['pcb_port_id'];new['route'][-1]['end_pcb_port_id']=ep['pcb_port_id'];new['pcb_port_ids']=[p['pcb_port_id'],ep['pcb_port_id']];j[:]=[e for e in j if e not in removed];j.append(new);changes.append({'pin':pin,'removed':removed,'replacement':new,'minimumForeignGapMm':minimum});print(pin,'directEP path',round(abs(p['x']-x),3),'mm',minimum,flush=True)
g.path.write_text(json.dumps(j,indent=2)+'\n');(g.ROOT/'artifacts/driver-ground-return-correction.json').write_text(json.dumps(changes,indent=2)+'\n')
